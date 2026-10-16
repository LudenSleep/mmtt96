"""Live Imploder cross-check: decrunch calls captured in MAME vs the offline decoder (scripts/extract/decode_imp.py).

  decrunch.py --natural [--runs N] [--frames F] [--write [--tsv PATH]]
  decrunch.py --all [--write]
      N runs (default 3) of lua/decrunch.lua (boot + attract, F frames); each captured call is matched to its blob
      (src == start of a `compressed` record of config/manifest.retail.jsonl) and the sha1 of the live dest buffer is
      compared with the blob's decoded record. With --write the matching calls replace --tsv (default
      config/oracle/decrunch_natural.tsv, the datapoints of config/maps/ram.tsv decrunch_dest claims; columns parent_start sha1 run pc_entry dest size name; parent_start = blob start `0x%06X` as in config/regions.retail.tsv; pc_entry = caller return address). Exit 1 on any sha1
      mismatch or unknown src (naming the blob id), on a run without done, or on fewer than 3 matched natural calls.
  --all: one run of lua/decrunch.lua mode all: after boot the wrapper 0x035416 is force-called for every `compressed`
      record (A0 = start, A1 = 0xFF0100); each saved buffer must match the decoded record (sha1, size), D0 must be
      success, and every row must equal the existing config/oracle/decrunch.tsv row of its parent_start (run ignored).
      Exit 1 naming every mismatched or missing blob id. Without --write no tracked file is touched. --write rewrites
      config/oracle/decrunch.tsv (one row per parent_start, pc_entry = 035416; read by scripts/extract/manifest.py) and sets
      the compressed rows of config/regions.retail.tsv to status verified, evidence `emu:<run>; <prior evidence>`.
Raw run output stays under .run/oracle/. Stdlib only.
"""
import argparse
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mame  # noqa: E402

MANIFEST = os.path.join(ROOT, "config", "manifest.retail.jsonl")
TSV = os.path.join(ROOT, "config", "oracle", "decrunch.tsv")
NATURAL_TSV = os.path.join(ROOT, "config", "oracle", "decrunch_natural.tsv")
REGIONS = os.path.join(ROOT, "config", "regions.retail.tsv")
HEADER = ["parent_start", "sha1", "run", "pc_entry", "dest", "size", "name"]
FRAMES = 1200
MIN_CALLS = 3
FRAMES_ALL = 6000  # cap; the run ends when every blob is done
ENTRY, DEST, OK = "035416", "FF0100", "FFFFFFFF"


def hx(n):
    return "0x%06X" % n


def blobs():
    """{src start int: (region id, name, decoded sha1, decoded size)} from the manifest."""
    recs = [json.loads(line) for line in open(MANIFEST, encoding="utf-8") if line.strip()]
    dec = {r["parent"]: r for r in recs if r.get("kind") == "decoded"}
    return {int(r["start"], 16): (r["id"], r.get("name", r["id"]), dec[r["id"]]["sha1"], dec[r["id"]]["size"])
            for r in recs if r.get("kind") == "compressed" and r["id"] in dec}


def match(run_id, events, table):
    """Captured call events -> (rows, errors). A call without a saved buffer is skipped (not a datapoint)."""
    rows, errs = [], []
    for e in events:
        if e.get("ev") != "call":
            continue
        src = int(e["src"], 16) if e.get("src") else None
        if src not in table:
            errs.append(f"{run_id} call {e['n']}: src {e.get('src')} is not a compressed region start")
            continue
        rid, name, want, size = table[src]
        if e.get("dest_in") != e["dest"]:
            errs.append(f"{run_id} call {e['n']} {rid} ({name}): dest at entry {e.get('dest_in')} != at rts {e['dest']}")
            continue
        if not e.get("file"):
            print(f"decrunch: {run_id} call {e['n']} {rid}: buffer not saved (two returns in one frame), skipped")
            continue
        data = open(os.path.join(ROOT, e["file"]), "rb").read()
        got = hashlib.sha1(data).hexdigest()
        if got != want or len(data) != size or e["size"] != size:
            errs.append(f"{run_id} call {e['n']} {rid} ({name}): live sha1 {got} size {len(data)} != offline {want} "
                        f"size {size}")
            continue
        rows.append([hx(src), got, run_id, e["ret"], e["dest"], str(size), name])
    return rows, errs


def natural(runs, frames, tsv, write):
    table = blobs()
    rows, errs = [], []
    for _ in range(runs):
        run_id, events, done = mame.run("decrunch", frames=frames)
        if not done:
            errs.append(f"{run_id}: no done")
            continue
        r, e = match(run_id, events, table)
        print(f"decrunch: run {run_id}: {len(r)} calls match offline ({', '.join(table[int(x[0], 16)][0] for x in r)})")
        rows += r
        errs += e
    for msg in errs:
        print(f"decrunch: FAIL {msg}")
    if len(rows) < MIN_CALLS:
        print(f"decrunch: FAIL {len(rows)} matched natural calls < {MIN_CALLS}")
        return 1
    if errs:
        return 1
    if not write:
        print(f"decrunch: OK {len(rows)} natural calls, {len({x[0] for x in rows})} blobs (no --write)")
        return 0
    rows.sort(key=lambda x: (x[0], x[2], x[3]))
    write_tsv(tsv, rows)
    print(f"decrunch: OK {len(rows)} natural calls, {len({x[0] for x in rows})} blobs -> {os.path.relpath(tsv, ROOT)}")
    return 0


def write_tsv(tsv, rows):
    os.makedirs(os.path.dirname(os.path.abspath(tsv)), exist_ok=True)
    with open(tsv, "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(HEADER) + "\n")
        for row in rows:
            f.write("\t".join(row) + "\n")


def mark_regions(run_id):
    """compressed rows of regions.retail.tsv -> status verified, evidence `emu:<run>; <prior minus older emu:>`."""
    lines = open(REGIONS, encoding="utf-8", newline="").read().split("\n")
    n = 0
    for i, ln in enumerate(lines[1:], start=1):
        f = ln.split("\t")
        if len(f) == 6 and f[2] == "compressed":
            prior = [x for x in f[5].split("; ") if x and not x.startswith("emu:")]
            f[4], f[5] = "verified", "; ".join([f"emu:{run_id}"] + prior)
            lines[i] = "\t".join(f)
            n += 1
    with open(REGIONS, "w", encoding="utf-8", newline="") as fh:
        fh.write("\n".join(lines))
    return n


def forced(write):
    table = blobs()
    starts = sorted(table)
    lst = os.path.join(mame.OUT, "decrunch_all_blobs.txt")
    os.makedirs(mame.OUT, exist_ok=True)
    with open(lst, "w", encoding="utf-8", newline="\n") as f:
        f.write("".join("%06X\n" % s for s in starts))
    os.environ["ORACLE_MODE"], os.environ["ORACLE_BLOBS"] = "all", lst.replace("\\", "/")
    try:
        run_id, events, done = mame.run("decrunch", frames=FRAMES_ALL, tag="decrunch_all")
    finally:
        del os.environ["ORACLE_MODE"], os.environ["ORACLE_BLOBS"]
    errs = [] if done else [f"{run_id}: no done"]
    errs += [f"{run_id}: {e.get('msg')}" for e in events if e.get("ev") == "error"]
    rows = {}
    for e in events:
        if e.get("ev") != "forced":
            continue
        src = int(e["src"], 16)
        rid, name, want, size = table[src]
        data = open(os.path.join(ROOT, e["file"]), "rb").read() if e.get("file") else b""
        got = hashlib.sha1(data).hexdigest()
        if e.get("src_in") != e["src"] or e["dest"] != DEST or e.get("ok") != OK:
            errs.append(f"{rid} ({name}): src_in {e.get('src_in')} dest {e['dest']} ok {e.get('ok')} "
                        f"(want {e['src']} {DEST} {OK})")
        elif got != want or len(data) != size or e["size"] != size:
            errs.append(f"{rid} ({name}): live sha1 {got} size {len(data)} != offline {want} size {size}")
        else:
            rows[src] = [hx(src), got, run_id, ENTRY, e["dest"], str(size), name]
    for s in starts:
        rid, name = table[s][:2]
        if s not in rows and not any(m.startswith(f"{rid} ") for m in errs):
            errs.append(f"{rid} ({name}): no forced call captured")
    if os.path.isfile(TSV):
        old = [line.rstrip("\n").split("\t") for line in open(TSV, encoding="utf-8")][1:]
        for o in old:
            new = rows.get(int(o[0], 16))
            if new and o[:2] + o[3:] != new[:2] + new[3:]:
                errs.append(f"{o[0]} ({o[6]}): live row differs from decrunch.tsv (run ignored): {o} vs {new}")
        print(f"decrunch: {len(old)} rows of decrunch.tsv compared; "
              f"{len(set(rows) - {int(o[0], 16) for o in old})} live parents absent there")
    for msg in errs:
        print(f"decrunch: FAIL {msg}")
    print(f"decrunch: run {run_id}: {len(rows)}/{len(starts)} blobs equal offline")
    if errs:
        return 1
    if write:
        write_tsv(TSV, [rows[k] for k in sorted(rows)])
        n = mark_regions(run_id)
        print(f"decrunch: wrote {len(rows)} rows -> {os.path.relpath(TSV, ROOT)}; {n} regions rows verified")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--natural", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--frames", type=int, default=FRAMES)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--tsv", default=NATURAL_TSV)
    a = ap.parse_args(argv)
    if a.all == a.natural:
        ap.error("exactly one mode is required (--natural or --all)")
    if a.all:
        return forced(a.write)
    return natural(a.runs, a.frames, a.tsv, a.write)


if __name__ == "__main__":
    sys.exit(main())
