"""Generate the retail region manifest (config/manifest.retail.jsonl) from the ROM and config/regions.retail.tsv.

Usage: PY scripts/extract/manifest.py [--rom PATH] [--regions PATH] [--out PATH] [--decrunch PATH] [--check]

Line 1 = the medium; then the partition of 0..size sorted by start (TSV rows, gaps -> kind "unknown"); then decoded
records sorted by parent (T3 decoders). Raw bytes of z80/compressed regions go to extracted/retail/raw/<id>.bin
(gitignored). Exit 2 = refusal (ROM SHA-1 mismatch, TSV overlap, out-of-range or empty row, malformed TSV,
a compressed region that does not decode exactly);
--decrunch (default config/oracle/decrunch.tsv, written by scripts/oracle/decrunch.py --all --write): a decoded record
whose parent's start has rows there (column parent_start = region start hex, so rows survive id renumbering) with its
sha1 gets status verified, evidence "emu:<run>" (first run in sort order); no row keeps inferred; a row with a different
sha1 is exit 1 naming the decoded id and parent.
--check exit 0 identical, 1 differs. Output: sort_keys, compact separators, LF, UTF-8 no BOM.
"""
import argparse
import hashlib
import json
import pathlib
import sys

import decode_imp
import rom as romlib

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
ROM_DEFAULT = "disks/Micro Machines Turbo Tournament 96 (Europe) (v1.1) (J-Cart).md"
ROM_SHA1 = "e8ff759679a0df2b3f9ece37ef686f248d3cf37b"
KINDS = {"vectors", "header", "code", "data", "compressed", "z80", "padding"}
STATUSES = {"verified", "inferred"}
RAW_KINDS = {"z80", "compressed"}
RAW_DIR = "extracted/retail/raw"
DECODERS = {decode_imp.MAGIC: ("imp", decode_imp)}  # magic -> (format, module)


def refuse(msg):
    print(f"manifest: refused: {msg}", file=sys.stderr)
    sys.exit(2)


def sha1(b):
    return hashlib.sha1(b).hexdigest()


def hx(n, w=6):
    return "0x%0*X" % (w, n)


def read_regions(path, size):
    """TSV rows as dicts sorted by start; refuses malformed, empty, out-of-range or overlapping rows."""
    lines = pathlib.Path(path).read_text(encoding="utf-8").splitlines()
    rows = []
    for n, ln in enumerate(lines[1:], start=2):
        if not ln.strip():
            continue
        f = ln.split("\t")
        if len(f) != 6:
            refuse(f"{path}:{n}: expected 6 tab-separated fields, got {len(f)}")
        try:
            start, end = int(f[0], 16), int(f[1], 16)
        except ValueError:
            refuse(f"{path}:{n}: start/end not hex")
        kind, rid, status, evidence = f[2], f[3], f[4], f[5]
        if kind not in KINDS:
            refuse(f"{path}:{n}: unknown kind {kind!r}")
        if status not in STATUSES:
            refuse(f"{path}:{n}: unknown status {status!r}")
        if end <= start:
            refuse(f"{path}:{n}: empty region {hx(start)}-{hx(end)}")
        if start < 0 or end > size:
            refuse(f"{path}:{n}: out of range {hx(start)}-{hx(end)} (size {hx(size)})")
        rows.append({"start": start, "end": end, "kind": kind, "name": rid, "status": status, "evidence": evidence, "line": n})
    rows.sort(key=lambda r: (r["start"], r["end"]))
    for a, b in zip(rows, rows[1:]):
        if b["start"] < a["end"]:
            refuse(f"{path}:{a['line']} and :{b['line']} overlap ({hx(a['start'])}-{hx(a['end'])} / {hx(b['start'])}-{hx(b['end'])})")
    return rows


def partition(rows, size):
    """Cover 0..size: TSV rows plus gaps as unknown, in start order."""
    out, pos = [], 0
    for r in rows:
        if r["start"] > pos:
            out.append({"start": pos, "end": r["start"], "kind": "unknown", "status": "inferred", "evidence": "gap"})
        out.append(r)
        pos = r["end"]
    if pos < size:
        out.append({"start": pos, "end": size, "kind": "unknown", "status": "inferred", "evidence": "gap"})
    return out


def header_facts(data):
    h = romlib.parse_header(data)
    return {
        "checksum_stored": hx(h["checksum"], 4),
        "checksum_computed": hx(romlib.header_checksum(data), 4),
        "rom_end": hx(h["rom_end"]),
        "reset_pc": hx(romlib.parse_vectors(data)[1]),
        "region": h["region"],
        "serial": h["serial"],
    }


def decode_partition(data, rec):
    """T3 hook: return (format, output bytes) for a compressed partition record; refuses (exit 2) when no decoder
    matches its magic, the decoder raises, consumed != size, or the output length != the declared size.
    A decoder module decode_<fmt>.py exposes decode(rom, start, end) -> (bytes, consumed)."""
    s, e = int(rec["start"], 16), int(rec["end"], 16)
    who = f"{rec['id']} ({rec.get('name', '?')})"
    hit = next(((fmt, mod) for magic, (fmt, mod) in DECODERS.items() if data[s:s + len(magic)] == magic), None)
    if hit is None:
        refuse(f"{who}: no decoder for magic {data[s:s + 4]!r}")
    fmt, mod = hit
    try:
        outb, consumed = mod.decode(data, s, e)
    except ValueError as ex:
        refuse(f"{who}: {ex}")
    if consumed != e - s:
        refuse(f"{who}: consumed {consumed} != size {e - s}")
    if len(outb) != mod.declared_size(data, s):
        refuse(f"{who}: output {len(outb)} != declared {mod.declared_size(data, s)}")
    return fmt, outb


def read_decrunch(path):
    """{parent start int: [(sha1, run), ...]} from the live decrunch oracle TSV (header parent_start sha1 run ...);
    {} if absent."""
    p = pathlib.Path(path)
    out = {}
    if not p.is_file():
        return out
    lines = p.read_text(encoding="utf-8").splitlines()
    head = lines[0].split("\t") if lines else []
    if head[:3] != ["parent_start", "sha1", "run"]:
        refuse(f"{path}: header must start parent_start sha1 run")
    for ln in lines[1:]:
        if ln.strip():
            f = ln.split("\t")
            out.setdefault(int(f[0], 16), []).append((f[1], f[2]))
    return out


def build(data, rom_name, rows, live=None):
    live = live or {}
    size = len(data)
    recs = [{"id": "medium", "kind": "medium", "path": rom_name, "size": size, "sha1": sha1(data)}]
    raws, decoded = {}, []
    for i, p in enumerate(partition(rows, size)):
        s, e = p["start"], p["end"]
        rec = {"id": "r%04d" % i, "kind": p["kind"], "start": hx(s), "end": hx(e), "size": e - s,
               "sha1": sha1(data[s:e]), "status": p["status"], "evidence": p["evidence"]}
        if "name" in p:
            rec["name"] = p["name"]
        if p["kind"] == "header":
            rec.update(header_facts(data))
        if p["kind"] in RAW_KINDS:
            raws[f"{RAW_DIR}/{rec['id']}.bin"] = data[s:e]
        if p["kind"] == "compressed":
            got = decode_partition(data, rec)
            if got is not None:
                fmt, outb = got
                out = f"extracted/retail/decoded/{rec['id']}.bin"
                d = {"id": "d" + rec["id"][1:], "kind": "decoded", "parent": rec["id"], "format": fmt,
                     "size": len(outb), "sha1": sha1(outb), "out": out, "status": "inferred"}
                pts = sorted(live.get(s, []), key=lambda x: x[1])
                bad = [x for x in pts if x[0] != d["sha1"]]
                if bad:
                    print(f"manifest: refused: {d['id']} (parent {rec['id']}): decrunch oracle sha1 {bad[0][0]} "
                          f"(run {bad[0][1]}) != offline {d['sha1']}", file=sys.stderr)
                    sys.exit(1)
                if pts:
                    d["status"], d["evidence"] = "verified", f"emu:{pts[0][1]}"
                decoded.append(d)
                raws[out] = outb
        recs.append(rec)
    m = sum(1 for p in rows if p["kind"] == "compressed")
    print(f"manifest: decoded {len(decoded)}/{m} compressed blobs")
    if len(decoded) != m:
        refuse(f"decoded {len(decoded)} of {m} compressed blobs")
    recs += sorted(decoded, key=lambda r: r["parent"])
    text = "".join(json.dumps(r, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n" for r in recs)
    return text, raws


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--rom", default=ROM_DEFAULT)
    ap.add_argument("--regions", default="config/regions.retail.tsv")
    ap.add_argument("--out", default="config/manifest.retail.jsonl")
    ap.add_argument("--decrunch", default="config/oracle/decrunch.tsv")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    dec = pathlib.Path(a.decrunch) if pathlib.Path(a.decrunch).is_absolute() else REPO / a.decrunch
    rom_path = pathlib.Path(a.rom) if pathlib.Path(a.rom).is_absolute() else REPO / a.rom
    regions = pathlib.Path(a.regions) if pathlib.Path(a.regions).is_absolute() else REPO / a.regions
    out = pathlib.Path(a.out) if pathlib.Path(a.out).is_absolute() else REPO / a.out
    if not rom_path.is_file():
        refuse(f"ROM not found: {a.rom}")
    data = rom_path.read_bytes()
    if sha1(data) != ROM_SHA1:
        refuse(f"ROM SHA-1 {sha1(data)} != expected {ROM_SHA1}")
    text, raws = build(data, rom_path.name, read_regions(regions, len(data)), read_decrunch(dec))
    if a.check:
        old = out.read_text(encoding="utf-8").split("\n") if out.is_file() else []
        new = text.split("\n")
        if old == new:
            print("manifest: check OK")
            return 0
        n = next((i for i, (x, y) in enumerate(zip(old, new), 1) if x != y), min(len(old), len(new)) + 1)
        print(f"manifest: check FAILED: first difference at line {n}")
        return 1
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(text.encode("utf-8"))
    for rel, b in sorted(raws.items()):
        p = REPO / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b)
    print(f"manifest: wrote {out.relative_to(REPO).as_posix() if out.is_relative_to(REPO) else out} "
          f"({text.count(chr(10))} records), {len(raws)} raw/decoded files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
