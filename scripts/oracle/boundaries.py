"""Second-disassembler boundary oracle: Ghidra listing rows vs a Capstone 68000 linear sweep, per code region.

  boundaries.py [--scope verified|inferred|all] [--refresh] [--plant ID] [--out .run/boundaries]

  --refresh   one headless batch `db.py listing --out <out>/asm <scope ids>`, then copy
              .run/ghidra/listing/<id>.tsv -> <out>/ghidra/<id>.tsv; without it <out>/ghidra/ is read
  --plant ID  shift the first Ghidra insn boundary of region ID by +2 in memory; must exit 1

Per region: Capstone sweeps from the start (rejected word -> class `invalid`, step 2), skipping Ghidra `data`
runs (resync at the next Ghidra insn). phantom = a boundary in one set only; truncation = same start, different
length, or a Capstone insn crossing the region end; unexplained = a Ghidra data run or a Capstone `invalid`,
unless the region id has a row in config/oracle/boundary_exceptions.tsv. Mnemonic-class and target
disagreements are counted, not fatal. Prints one summary line plus one line per disagreement pair (class names
and counts only); exit 0 iff phantoms = truncations = unexplained = 0 over the scope. Detail rows (addresses
allowed) go to <out>/<scope>.tsv (ignored; firewall: nothing instruction-level reaches stdout).
Stdlib + capstone (pin: docs/ops/ops-setup-decomp.md "Version pins (decomp)").
"""
import argparse
import os
import shutil
import subprocess
import sys
import time

import capstone
from capstone import m68k

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "scripts", "extract"))
from manifest import ROM_DEFAULT  # noqa: E402

REGIONS = os.path.join(ROOT, "config", "regions.retail.tsv")
EXCEPTIONS = os.path.join(ROOT, "config", "oracle", "boundary_exceptions.tsv")
LISTING = os.path.join(ROOT, ".run", "ghidra", "listing")
LISTING_HEADER = "addr\tlen\tkind\ttext\tops\ttargets"  # Mmtt96Listing.java:40
MASK = 0xFFFFFF

# Mnemonic aliases applied after lowercasing and stripping the size suffix; same encoding family only.
ALIAS = {
    "cmpi": "cmp",   # immediate form of cmp
    "cmpa": "cmp",   # address-register form of cmp
    "cmpm": "cmp",   # memory-to-memory form of cmp
    "addi": "add",   # immediate form of add
    "adda": "add",   # address-register form of add
    "subi": "sub",   # immediate form of sub
    "suba": "sub",   # address-register form of sub
    "movea": "move",  # address-register form of move
    "andi": "and",   # immediate form of and (incl. to ccr/sr)
    "ori": "or",     # immediate form of or (incl. to ccr/sr)
    "eori": "eor",   # immediate form of eor (incl. to ccr/sr)
    "bhs": "bcc",    # Bcc condition spelling: hs == cc
    "blo": "bcs",    # Bcc condition spelling: lo == cs
    "shs": "scc",    # Scc condition spelling: hs == cc
    "slo": "scs",    # Scc condition spelling: lo == cs
    "dbhs": "dbcc",  # DBcc condition spelling: hs == cc
    "dblo": "dbcs",  # DBcc condition spelling: lo == cs
    "dbra": "dbf",   # DBcc condition spelling: ra == f (always false)
}

_MD = capstone.Cs(capstone.CS_ARCH_M68K, capstone.CS_MODE_M68K_000 | capstone.CS_MODE_BIG_ENDIAN)
_MD.detail = True


def mclass(mnemonic):
    m = mnemonic.lower()
    if len(m) > 2 and m[-2] == "." and m[-1] in "bwls":
        m = m[:-2]
    return ALIAS.get(m, m)


def decode(rom: bytes, addr: int) -> tuple[int, str, tuple[int, ...]]:
    """(length, mnemonic class, absolute targets masked to 24 bits); rejected -> (2, 'invalid', ())."""
    ins = next(_MD.disasm(rom[addr:addr + 10], addr, count=1), None)
    if ins is None or ins.mnemonic.startswith("dc."):
        return 2, "invalid", ()
    cls = mclass(ins.mnemonic)
    tg = []
    for op in ins.operands:
        if op.type == m68k.M68K_OP_BR_DISP:
            tg.append(addr + 2 + op.br_disp.disp)
        elif cls in ("jmp", "jsr"):
            am = op.address_mode
            if am == m68k.M68K_AM_ABSOLUTE_DATA_SHORT:
                v = op.imm & 0xFFFF
                tg.append(v - 0x10000 if v >= 0x8000 else v)
            elif am == m68k.M68K_AM_ABSOLUTE_DATA_LONG:
                tg.append(op.imm)
            elif am == m68k.M68K_AM_PCI_DISP:
                tg.append(addr + 2 + op.mem.disp)
    return ins.size, cls, tuple(sorted({t & MASK for t in tg}))


def code_regions(scope):
    out = []
    with open(REGIONS, encoding="utf-8") as f:
        for line in f.read().split("\n")[1:]:
            if not line:
                continue
            r = line.split("\t")
            if r[2] == "code" and (scope == "all" or r[4] == scope):
                out.append((r[3], int(r[0], 16), int(r[1], 16)))
    return out


def exceptions():
    with open(EXCEPTIONS, encoding="utf-8") as f:
        lines = f.read().split("\n")
    if lines[0] != "region_id\tclass\treason":
        sys.exit("boundaries: %s: bad header" % EXCEPTIONS)
    return {l.split("\t")[0] for l in lines[1:] if l}


def refresh(regions, out):
    """One headless listing batch; copy the raw TSVs. Returns the db.py exit code."""
    t0 = time.time()
    cmd = [sys.executable, os.path.join(ROOT, "scripts", "ghidra", "db.py"), "listing",
           "--out", os.path.join(out, "asm")] + [r[0] for r in regions]
    log = os.path.join(out, "refresh.log")
    with open(log, "w", encoding="utf-8", errors="replace") as f:
        rc = subprocess.call(cmd, stdout=f, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, cwd=ROOT)
    os.makedirs(os.path.join(out, "ghidra"), exist_ok=True)
    for rid, _, _ in regions:
        src = os.path.join(LISTING, rid + ".tsv")
        if not os.path.exists(src) or os.path.getmtime(src) < t0 - 1:
            sys.exit("boundaries: refresh: no fresh listing for %s (db.py exit %d, see %s)"
                     % (rid, rc, os.path.relpath(log, ROOT)))
        shutil.copyfile(src, os.path.join(out, "ghidra", rid + ".tsv"))
    print("refresh: db.py listing exit %d, %d regions, %.0f s" % (rc, len(regions), time.time() - t0))
    return rc


def read_rows(path):
    """Raw listing -> [[addr, len, kind, class, targets]] in address order."""
    with open(path, encoding="utf-8") as f:
        lines = f.read().split("\n")
    if lines[0] != LISTING_HEADER:
        sys.exit("boundaries: %s: bad header" % path)
    rows = []
    for l in lines[1:]:
        if not l:
            continue
        a, n, kind, text, _ops, tg = l.split("\t")
        targets = frozenset(int(t, 16) & MASK for t in tg.split(";") if t)
        rows.append([int(a, 16), int(n), kind, mclass(text) if kind == "insn" else "", targets])
    return rows


def plant(rows):
    """Shift the first insn's end boundary by +2: grow it, shrink (or absorb) the next row."""
    i = next(i for i, r in enumerate(rows) if r[2] == "insn")
    rows[i][1] += 2
    if i + 1 < len(rows):
        nxt = rows[i + 1]
        if nxt[1] > 2:
            nxt[0] += 2
            nxt[1] -= 2
        else:
            del rows[i + 1]


def compare(rid, s, e, rows, rom, exempt, detail):
    """Returns per-region counts dict; appends detail rows."""
    c = {"p": 0, "t": 0, "u": 0, "m": {}, "g": 0}
    gins = {r[0]: r for r in rows if r[2] == "insn"}
    data = [(r[0], r[0] + r[1]) for r in rows if r[2] == "data"]
    for a, b in data:
        detail.append((rid, a, "unexplained-data", "data/%d" % (b - a), "", "exempt" if exempt else ""))
        if not exempt:
            c["u"] += 1
    dend = {a: b for a, b in data}
    cs = {}
    pos = s
    while pos < e:
        if pos in dend:
            pos = dend[pos]
            continue
        n, cls, tg = decode(rom, pos)
        cs[pos] = (n, cls, tg)
        if cls == "invalid":
            detail.append((rid, pos, "unexplained-invalid", "", "invalid/2", "exempt" if exempt else ""))
            if not exempt:
                c["u"] += 1
        if pos + n > e:
            detail.append((rid, pos, "truncation-end", "", "%s/%d" % (cls, n), ""))
            c["t"] += 1
            break
        nxt = pos + n
        inside = next((b for a, b in data if a < nxt < b), None)
        pos = inside if inside is not None else nxt
    for a in sorted(set(gins) | set(cs)):
        g, k = gins.get(a), cs.get(a)
        if g is None:
            detail.append((rid, a, "phantom-capstone", "", "%s/%d" % (k[1], k[0]), ""))
            c["p"] += 1
        elif k is None:
            detail.append((rid, a, "phantom-ghidra", "%s/%d" % (g[3], g[1]), "", ""))
            c["p"] += 1
        elif g[1] != k[0]:
            detail.append((rid, a, "truncation", "%s/%d" % (g[3], g[1]), "%s/%d" % (k[1], k[0]), ""))
            c["t"] += 1
        else:
            if g[3] != k[1]:
                pair = "%s/%s" % (g[3], k[1])
                c["m"][pair] = c["m"].get(pair, 0) + 1
                detail.append((rid, a, "mnemonic-class", g[3], k[1], ""))
            miss = [t for t in k[2] if t not in g[4]]
            if miss:
                c["g"] += 1
                detail.append((rid, a, "target", g[3], k[1], ";".join("0x%06X" % t for t in miss)))
    c["n"] = len(cs)  # sweep size; scripts/census/encodings.py asserts its own sweep count against it
    return c


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scope", choices=["verified", "inferred", "all"], default="verified")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--plant", metavar="ID")
    ap.add_argument("--out", default=os.path.join(ROOT, ".run", "boundaries"))
    ap.add_argument("--ids", nargs="+", help=argparse.SUPPRESS)  # dev filter: restrict the scope to these ids
    a = ap.parse_args(argv)
    regions = code_regions(a.scope)
    if a.ids:
        regions = [r for r in regions if r[0] in set(a.ids)]
    if a.plant and a.plant not in {r[0] for r in regions}:
        sys.exit("boundaries: --plant %s: not a code region of scope %s" % (a.plant, a.scope))
    os.makedirs(a.out, exist_ok=True)
    if a.refresh:
        refresh(regions, a.out)
    with open(os.path.join(ROOT, ROM_DEFAULT), "rb") as f:
        rom = f.read()
    exempt = exceptions()
    detail, tot, pairs, tsites = [], {"p": 0, "t": 0, "u": 0}, {}, [0, set()]
    clean = 0
    for rid, s, e in regions:
        path = os.path.join(a.out, "ghidra", rid + ".tsv")
        if not os.path.exists(path):
            sys.exit("boundaries: missing %s (run with --refresh)" % os.path.relpath(path, ROOT))
        rows = read_rows(path)
        if rid == a.plant:
            plant(rows)
        c = compare(rid, s, e, rows, rom, rid in exempt, detail)
        for k in ("p", "t", "u"):
            tot[k] += c[k]
        clean += c["p"] == c["t"] == c["u"] == 0
        for pair, n in c["m"].items():
            pairs.setdefault(pair, [0, set()])
            pairs[pair][0] += n
            pairs[pair][1].add(rid)
        if c["g"]:
            tsites[0] += c["g"]
            tsites[1].add(rid)
    with open(os.path.join(a.out, a.scope + ".tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("region_id\taddr\tclass\tghidra\tcapstone\tnote\n")
        for rid, addr, cls, g, k, note in detail:
            f.write("%s\t0x%06X\t%s\t%s\t%s\t%s\n" % (rid, addr, cls, g, k, note))
    m = sum(v[0] for v in pairs.values())
    print("boundaries: %s %d/%d phantoms %d truncations %d unexplained %d mnemonic-class %d targets %d"
          % (a.scope, clean, len(regions), tot["p"], tot["t"], tot["u"], m, tsites[0]))
    for pair in sorted(pairs, key=lambda p: (-pairs[p][0], p)):
        print("class %s: %d sites %d regions" % (pair, pairs[pair][0], len(pairs[pair][1])))
    if tsites[0]:
        print("targets: %d sites %d regions" % (tsites[0], len(tsites[1])))
    return 0 if tot["p"] == tot["t"] == tot["u"] == 0 and clean == len(regions) else 1


if __name__ == "__main__":
    sys.exit(main())
