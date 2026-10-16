"""ROM census over config/regions.retail.tsv: coverage, duplicates, structural families, reach x size, unique tail.

  census.py [--out .run/census] [--no-refresh] [--fixture [--fixture-alter CASE]]

Asserts coverage first (regions partition [0, ROM size), TSV rows == manifest region records, every code row
swept to its end); exit 1 on any failure. Metrics:
  dup group  = content hash (manifest sha1 by region id, else sha1 of the ROM slice) shared by >= 2 regions
  family     = Capstone mnemonic-class skeleton (linear sweep start..end, operands stripped) shared by >= 2
               code regions with distinct content hashes
  reach      = distinct `from` addresses outside the region whose `to` lies inside (.run/ghidra/seed/refs.tsv;
               refreshed with `db.py analyse` when missing or older than .run/ghidra/seeds.tsv,
               which `classify.py seeds` rewrites first when missing or different)
  size bucket = bit_length(size); reach buckets 0/1/2-3/4+
  unique tail = regions in no dup group and no family
Stdout: counts, buckets and region ids only (firewall). Detail (addresses, hashes) only under --out (ignored).
--fixture runs a synthetic known-answer ROM under .run/census/fixture/; --fixture-alter CASE flips one expected
answer and must exit 1 (negative control). Shared loader/partition check for progress.py lives here.
Stdlib + capstone (decoder: scripts/oracle/boundaries.py decode).
"""
import argparse
import bisect
import hashlib
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "scripts", "extract"))
sys.path.insert(0, os.path.join(ROOT, "scripts", "oracle"))
from manifest import ROM_DEFAULT  # noqa: E402
from boundaries import decode  # noqa: E402

REGIONS = os.path.join(ROOT, "config", "regions.retail.tsv")
MANIFEST = os.path.join(ROOT, "config", "manifest.retail.jsonl")
REFS = os.path.join(ROOT, ".run", "ghidra", "seed", "refs.tsv")
SEEDS = os.path.join(ROOT, ".run", "ghidra", "seeds.tsv")
REGIONS_HEADER = "start\tend\tkind\tid\tstatus\tevidence"
REFS_HEADER = "from\tto\ttype"
REGION_KEYS = {"start", "end", "id", "kind", "sha1"}
REACH_BUCKETS = ("0", "1", "2-3", "4+")
BIG = 4096


# ---- shared loaders (progress.py imports these) ----

def load_regions(path):
    """TSV rows as dicts in start order (id tie-break); exits on a bad header or malformed row."""
    with open(path, encoding="utf-8") as f:
        lines = f.read().split("\n")
    if lines[0].rstrip("\r") != REGIONS_HEADER:
        sys.exit("census: %s: bad header" % path)
    rows = []
    for n, l in enumerate(lines[1:], start=2):
        l = l.rstrip("\r")
        if not l:
            continue
        f = l.split("\t")
        if len(f) != 6:
            sys.exit("census: %s:%d: expected 6 fields" % (path, n))
        rows.append({"start": int(f[0], 16), "end": int(f[1], 16), "kind": f[2], "id": f[3], "status": f[4]})
    rows.sort(key=lambda r: (r["start"], r["end"], r["id"]))
    return rows


def load_manifest(path):
    """Region records (keys start/end/id/kind/sha1; excludes `decoded` and `medium`) -> {region name: sha1}, count."""
    sha, n = {}, 0
    with open(path, encoding="utf-8") as f:
        for l in f:
            if not l.strip():
                continue
            r = json.loads(l)
            if REGION_KEYS <= r.keys() and "parent" not in r and r["kind"] not in ("decoded", "medium"):
                n += 1
                sha[r.get("name", r["id"])] = r["sha1"]
    return sha, n


def partition_errors(rows, size):
    """Gap / overlap / out-of-range / empty findings as id-only strings; [] when rows partition [0, size)."""
    errs, pos, prev = [], 0, "<start>"
    for r in rows:
        if r["end"] <= r["start"]:
            errs.append("empty region %s" % r["id"])
        if r["start"] > pos:
            errs.append("gap after %s" % prev)
        elif r["start"] < pos:
            errs.append("overlap %s/%s" % (prev, r["id"]))
        pos, prev = max(pos, r["end"]), r["id"]
    if pos < size:
        errs.append("gap after %s (to ROM end)" % prev)
    elif pos > size:
        errs.append("past ROM end at %s" % prev)
    return errs


# ---- metrics ----

def content_hashes(rows, rom, msha):
    return {r["id"]: msha.get(r["id"]) or hashlib.sha1(rom[r["start"]:r["end"]]).hexdigest() for r in rows}


def sweep(rom, start, end):
    """Linear decode start..end -> (skeleton tuple of mnemonic classes, final position)."""
    sk, pos = [], start
    while pos < end:
        ln, cls, _ = decode(rom, pos)
        sk.append(cls)
        pos += ln
    return tuple(sk), pos


def dup_groups(rows, hashes):
    by = {}
    for r in rows:
        by.setdefault(hashes[r["id"]], []).append(r["id"])
    return sorted((sorted(v) for v in by.values() if len(v) >= 2), key=lambda g: (g[0], len(g)))


def families(code_rows, hashes, skeletons):
    """Groups of code ids sharing a skeleton with >= 2 distinct content hashes; also {id: skeleton hash}."""
    skh = {r["id"]: hashlib.sha1("\n".join(skeletons[r["id"]]).encode()).hexdigest() for r in code_rows}
    by = {}
    for r in code_rows:
        by.setdefault(skh[r["id"]], []).append(r["id"])
    fams = [sorted(v) for v in by.values() if len({hashes[i] for i in v}) >= 2]
    return sorted(fams, key=lambda g: (g[0], len(g))), skh


def load_refs(path):
    with open(path, encoding="utf-8") as f:
        lines = f.read().split("\n")
    if lines[0].rstrip("\r") != REFS_HEADER:
        sys.exit("census: %s: bad header" % path)
    out = []
    for l in lines[1:]:
        l = l.rstrip("\r")
        if l:
            f = l.split("\t")
            out.append((int(f[0], 16), int(f[1], 16)))
    return out


def reach(rows, refs):
    """{id: number of distinct `from` outside the region with `to` inside}."""
    starts = [r["start"] for r in rows]

    def owner(a):
        i = bisect.bisect_right(starts, a) - 1
        return i if i >= 0 and a < rows[i]["end"] else -1

    froms = [set() for _ in rows]
    for fr, to in refs:
        i = owner(to)
        if i >= 0 and owner(fr) != i:
            froms[i].add(fr)
    return {r["id"]: len(froms[i]) for i, r in enumerate(rows)}


def reach_bucket(n):
    return "0" if n == 0 else "1" if n == 1 else "2-3" if n <= 3 else "4+"


def size_bucket(n):
    return n.bit_length()


def analyse(rom, rows, msha, refs):
    """All metrics as a dict; raises nothing, the caller checks."""
    hashes = content_hashes(rows, rom, msha)
    code = [r for r in rows if r["kind"] == "code"]
    skeletons, swept = {}, 0
    for r in code:
        sk, pos = sweep(rom, r["start"], r["end"])
        skeletons[r["id"]] = sk
        swept += pos >= r["end"]
    dups = dup_groups(rows, hashes)
    fams, skh = families(code, hashes, skeletons)
    rc = reach(rows, refs)
    in_dup = {i for g in dups for i in g}
    in_fam = {i for g in fams for i in g}
    unique = [r["id"] for r in rows if r["id"] not in in_dup and r["id"] not in in_fam]
    unique_code = [r["id"] for r in code if r["id"] in set(unique)]
    grid = {}
    for r in rows:
        k = (reach_bucket(rc[r["id"]]), size_bucket(r["end"] - r["start"]))
        grid[k] = grid.get(k, 0) + 1
    big0 = sorted(r["id"] for r in rows if rc[r["id"]] == 0 and r["end"] - r["start"] >= BIG)
    return {"hashes": hashes, "skh": skh, "code": len(code), "swept": swept, "dups": dups, "fams": fams,
            "reach": rc, "unique": unique, "unique_code": unique_code, "grid": grid, "big0": big0}


def grid_lines(grid):
    sbs = sorted({k[1] for k in grid})
    out = ["reach\\size " + " ".join("<2^%d" % b for b in sbs)]
    for rb in REACH_BUCKETS:
        out.append("%-10s " % rb + " ".join("%*d" % (len("<2^%d" % b), grid.get((rb, b), 0)) for b in sbs))
    return out


def write_detail(out, rows, m, summary):
    os.makedirs(out, exist_ok=True)
    dup_of = {i: n for n, g in enumerate(m["dups"]) for i in g}
    fam_of = {i: n for n, g in enumerate(m["fams"]) for i in g}
    with open(os.path.join(out, "regions.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("id\tkind\tstatus\tstart\tend\tsize\tsha1\tskeleton_sha1\tdup_group\tfamily\treach\treach_bucket\tsize_bucket\n")
        for r in rows:
            i = r["id"]
            f.write("%s\t%s\t%s\t0x%06X\t0x%06X\t%d\t%s\t%s\t%s\t%s\t%d\t%s\t%d\n" % (
                i, r["kind"], r["status"], r["start"], r["end"], r["end"] - r["start"], m["hashes"][i],
                m["skh"].get(i, "-"), dup_of.get(i, "-"), fam_of.get(i, "-"), m["reach"][i],
                reach_bucket(m["reach"][i]), size_bucket(r["end"] - r["start"])))
    with open(os.path.join(out, "big0.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("".join(i + "\n" for i in m["big0"]))
    with open(os.path.join(out, "summary.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("".join(l + "\n" for l in summary))


def census(rom, rows, msha, mcount, refs, out):
    """Coverage asserts + metrics; prints the summary; returns exit code."""
    errs = partition_errors(rows, len(rom))
    if len(rows) != mcount:
        errs.append("TSV rows %d != manifest region records %d" % (len(rows), mcount))
    m = analyse(rom, rows, msha, refs)
    if m["swept"] != m["code"]:
        errs.append("code rows swept %d != code rows %d" % (m["swept"], m["code"]))
    for e in errs:
        print("census: FAIL " + e)
    if errs:
        return 1
    nbytes = sum(r["end"] - r["start"] for r in rows)
    summary = ["census: regions %d/%d bytes %d/%d dup-groups %d families %d unique-tail %d" % (
        len(rows), mcount, nbytes, len(rom), len(m["dups"]), len(m["fams"]), len(m["unique"])),
        "census: code rows %d swept %d; family members %d; unique-tail code %d/%d" % (
        m["code"], m["swept"], sum(len(g) for g in m["fams"]), len(m["unique_code"]), m["code"]),
        "census: reach 0 and size >= %d: %d rows (ids in %s)" % (
        BIG, len(m["big0"]), os.path.relpath(os.path.join(out, "big0.txt"), ROOT).replace("\\", "/"))]
    summary += grid_lines(m["grid"])
    for l in summary:
        print(l)
    write_detail(out, rows, m, summary)
    return 0


def refresh_refs(no_refresh):
    if not no_refresh:  # (re)generate seeds.tsv first: a fresh clone has none; a damaged one is rewritten, never trusted
        rc = subprocess.call([sys.executable, os.path.join(ROOT, "scripts", "ghidra", "classify.py"), "seeds"],
                             stdin=subprocess.DEVNULL, cwd=ROOT)
        if rc != 0 or not os.path.exists(SEEDS):
            sys.exit("census: classify.py seeds failed (exit %d)" % rc)
    stale = not os.path.exists(REFS) or (os.path.exists(SEEDS) and os.path.getmtime(REFS) < os.path.getmtime(SEEDS))
    if stale and not no_refresh:
        print("census: refs stale or missing, running db.py analyse")
        rc = subprocess.call([sys.executable, os.path.join(ROOT, "scripts", "ghidra", "db.py"), "analyse"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, cwd=ROOT)
        if rc != 0 or not os.path.exists(REFS):
            sys.exit("census: db.py analyse failed (exit %d)" % rc)


# ---- fixture ----

def fixture(alter, out):
    """Synthetic ROM with planted answers; returns exit code (1 on any wrong answer)."""
    d = os.path.join(out, "fixture")
    os.makedirs(d, exist_ok=True)
    rom = bytearray(0x2000)
    rom[0x0000:0x0004] = bytes.fromhex("70014E75")   # A: moveq #1,d0; rts
    rom[0x0004:0x0008] = bytes.fromhex("70024E75")   # B: moveq #2,d0; rts   (family with A, operands differ)
    rom[0x0008:0x000C] = bytes.fromhex("70014E75")   # F: exact dup of A
    rom[0x000C:0x0010] = bytes.fromhex("4E714E75")   # E: nop; rts           (unique code)
    rom[0x0010:0x0018] = bytes(range(1, 9))          # C: data
    rom[0x0018:0x0020] = bytes(range(1, 9))          # D: dup of C
    rom[0x0020:0x1000] = bytes((i * 7 + 3) & 0xFF for i in range(0xFE0))  # G: unique data
    # H 0x1000..0x2000: zeros, reach 0, size 4 KiB
    layout = [(0x0000, 0x0004, "code", "A"), (0x0004, 0x0008, "code", "B"), (0x0008, 0x000C, "code", "F"),
              (0x000C, 0x0010, "code", "E"), (0x0010, 0x0018, "data", "C"), (0x0018, 0x0020, "data", "D"),
              (0x0020, 0x1000, "data", "G"), (0x1000, 0x2000, "data", "H")]
    refs = [(0x000C, 0x0000), (0x000E, 0x0002), (0x000C, 0x0002), (0x0004, 0x0000), (0x0002, 0x0000),  # A: 3
            (0x0000, 0x000C),                                                                       # E: 1
            (0x0000, 0x0020), (0x0004, 0x0100), (0x0010, 0x0FFF), (0x1000, 0x0800),                 # G: 4
            (0x0100, 0x0200), (0x0000, 0x5000)]                                                     # internal, off-ROM
    with open(os.path.join(d, "rom.bin"), "wb") as f:
        f.write(rom)
    with open(os.path.join(d, "regions.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write(REGIONS_HEADER + "\n" + "".join("0x%06X\t0x%06X\t%s\t%s\tverified\tfixture\n" % r for r in layout))
    with open(os.path.join(d, "refs.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write(REFS_HEADER + "\n" + "".join("0x%06X\t0x%06X\tjump\n" % r for r in refs))
    with open(os.path.join(d, "manifest.jsonl"), "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps({"id": "medium", "kind": "medium", "sha1": "-", "size": len(rom)}) + "\n")
        for n, (s, e, k, i) in enumerate(layout):
            rec = {"end": "0x%06X" % e, "id": "r%04d" % n, "kind": k, "name": i, "start": "0x%06X" % s}
            if i in ("C", "D"):   # manifest sha1 path; others take the slice-hash fallback
                rec["sha1"] = hashlib.sha1(rom[s:e]).hexdigest()
            else:
                rec["sha1"] = ""
            f.write(json.dumps(rec, sort_keys=True) + "\n")
        f.write(json.dumps({"id": "d0004", "kind": "decoded", "parent": "r0004", "sha1": "-",
                            "start": "0x0", "end": "0x0"}) + "\n")
    with open(os.path.join(d, "rom.bin"), "rb") as f:
        rom = f.read()
    rows = load_regions(os.path.join(d, "regions.tsv"))
    msha, mcount = load_manifest(os.path.join(d, "manifest.jsonl"))
    m = analyse(rom, rows, msha, load_refs(os.path.join(d, "refs.tsv")))
    gap = [dict(r) for r in rows]
    gap[3]["end"] -= 2
    got = {"count": mcount, "dup": m["dups"], "family": m["fams"], "unique": m["unique"],
           "reach": [m["reach"][i] for i in "ABFECDGH"], "big0": m["big0"],
           "swept": (m["swept"], m["code"]), "partition": (partition_errors(rows, len(rom)), len(partition_errors(gap, len(rom))))}
    want = {"count": 8, "dup": [["A", "F"], ["C", "D"]], "family": [["A", "B", "F"]], "unique": ["E", "G", "H"],
            "reach": [3, 0, 0, 1, 0, 0, 4, 0], "big0": ["H"],
            "swept": (4, 4), "partition": ([], 1)}
    if alter:
        if alter not in want:
            sys.exit("census: --fixture-alter: unknown case %s (cases: %s)" % (alter, " ".join(sorted(want))))
        want[alter] = ("altered", want[alter])
    bad = 0
    for k in sorted(want):
        ok = got[k] == want[k]
        bad += not ok
        print("fixture: %-9s %s" % (k, "ok" if ok else "FAIL"))
    print("fixture: %d/%d cases ok" % (len(want) - bad, len(want)))
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=os.path.join(ROOT, ".run", "census"))
    ap.add_argument("--no-refresh", action="store_true")
    ap.add_argument("--fixture", action="store_true")
    ap.add_argument("--fixture-alter", help=argparse.SUPPRESS)
    a = ap.parse_args()
    if a.fixture:
        return fixture(a.fixture_alter, a.out)
    refresh_refs(a.no_refresh)
    with open(os.path.join(ROOT, ROM_DEFAULT), "rb") as f:
        rom = f.read()
    msha, mcount = load_manifest(MANIFEST)
    return census(rom, load_regions(REGIONS), msha, mcount, load_refs(REFS), a.out)


if __name__ == "__main__":
    sys.exit(main())
