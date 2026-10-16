"""Constants census (plan 1.9 T3): hardware constants (config/names/hw.tsv) and game constants (consts.tsv).

Usage: PY scripts/census/constants.py check [--names DIR] [--plant]

check    renders every kind=code region from the raw Ghidra listings (.run/ghidra/listing/<id>.tsv, written by
         `make build` / db.py listing; exit 2 if one is missing) through db.py translate with the names dir, and counts
         the in-scope candidates: an immediate stored or bit-tested at a VDP control / Z80 bus / I/O port (db.py
         HW_PORTS: absolute, or via a port base register). Prints `RAW $ADDR <class>` per candidate left raw,
         `BASE $ADDR <reg>` per write breaking a hw.tsv basereg row (allowed: lea of the base, movem from (SP)+,
         region init), `CONSTS $ADDR <opnd>: <why>` per consts.tsv row not rendered, `HW <name>: <why>` per malformed
         hw.tsv row, then `constants: hw <sym>/<n> symbolic, game <k>`. Exit 1 on any of those lines.
--plant  control: the same check on a scratch copy of the names dir with one wrong hw value (z80_bus_request
         $100 -> $200); exit 0 iff the planted check fails with RAW lines (`constants: plant caught`).
Stdlib only (db.py, split.py by path). Prints addresses, classes and counts only, never instruction text (G12).
"""
import argparse
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "scripts", "ghidra"))
import db  # noqa: E402

KINDS = ("vdp_reg", "vdp_cd", "form", "fact", "basereg")
PREFIXES = ("field:", "value:", "bit:", "bitno:")
PLANT = ("z80_bus_request", "0x100", "0x200")


def hw_rows_check(hw):
    """Structural checks of hw.tsv rows -> list of `HW <name>: <why>` lines."""
    bad, seen = [], {}
    for r in hw:
        n, k = r["name"], r["kind"]
        if k not in KINDS and not k.startswith(PREFIXES):
            bad.append("HW %s: unknown kind %s" % (n, k))
            continue
        want = "rom:" if k == "basereg" else "published-doc:"
        if not r.get("evidence", "").startswith(want):
            bad.append("HW %s: evidence must start with %s" % (n, want))
        if k == "vdp_reg" and (r["value"] & 0xE0FF != 0x8000 or (r["value"] >> 8) & 0x1F > 0x17):
            bad.append("HW %s: not a register-set word $8000|reg<<8, reg <= $17" % n)
        if k not in ("form", "fact", "basereg"):
            if (k, r["value"]) in seen:
                bad.append("HW %s: value $%X repeats %s in kind %s" % (n, r["value"], seen[(k, r["value"])], k))
            seen[(k, r["value"])] = n
    return bad


def check(names_dir, quiet=False):
    """-> (exit code, number of RAW lines). Prints the report unless quiet (the summary line always)."""
    ids = db.code_ids()
    regions = db.regions_by_id(ids)
    raw_dir = os.path.join(db.RUN, "listing")
    missing = [i for i in ids if not os.path.isfile(os.path.join(raw_dir, i + ".tsv"))]
    if missing:
        print("constants: raw listing missing for %d regions (run make build first): %s" % (len(missing), missing[0]))
        return 2, 0
    t = db.names_inc(os.path.join(ROOT, ".run", "constants", "inc"), names_dir)
    names = db.name_tables(t)
    with open(os.path.join(ROOT, db.ROM_DEFAULT), "rb") as f:
        rom = f.read()
    stats = {"hw": 0, "sym": 0, "game": 0, "raw": [], "base": [], "consts_bad": [], "consts_done": set()}
    for rid, (s, e) in regions.items():
        with open(os.path.join(raw_dir, rid + ".tsv"), encoding="utf-8") as f:
            db.translate(rid, s, e, f.read(), rom, names, None, stats)
    lines = ["RAW $%06X %s" % x for x in stats["raw"]]
    lines += ["BASE $%06X %s" % x for x in stats["base"]]
    lines += ["CONSTS $%06X %d: not an immediate" % x for x in stats["consts_bad"]]
    lines += ["CONSTS $%06X %d: no such instruction in a code region" % k for k in names["consts"]
              if k not in stats["consts_done"] and k not in stats["consts_bad"]]
    lines += hw_rows_check(t["hw"])
    if not quiet:
        for l in lines:
            print(l)
    print("constants: hw %d/%d symbolic, game %d" % (stats["sym"], stats["hw"], stats["game"]))
    return (1 if lines else 0), len(stats["raw"])


def plant(names_dir):
    d = os.path.join(ROOT, ".run", "constants", "plant")
    if os.path.isdir(d):
        shutil.rmtree(d)
    shutil.copytree(names_dir, d)
    p = os.path.join(d, "hw.tsv")
    with open(p, encoding="utf-8") as f:
        text = f.read()
    name, old, new = PLANT
    row = next((l for l in text.split("\n") if l.split("\t")[:2] == [name, old]), None)
    if row is None:
        print("constants: plant row %s %s not in hw.tsv" % (name, old))
        return 1
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(text.replace(row, "\t".join([name, new] + row.split("\t")[2:])))
    rc, nraw = check(d, quiet=True)
    if rc == 1 and nraw > 0:
        print("constants: plant caught (%s %s -> %s: %d raw)" % (name, old, new, nraw))
        return 0
    print("constants: plant MISSED (%s %s -> %s: exit %d, %d raw)" % (name, old, new, rc, nraw))
    return 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["check"])
    ap.add_argument("--names", default=os.path.join(ROOT, "config", "names"))
    ap.add_argument("--plant", action="store_true", help="control: a planted wrong hw value must fail the check")
    a = ap.parse_args(argv)
    if a.plant:
        return plant(a.names)
    return check(a.names)[0]


if __name__ == "__main__":
    sys.exit(main())
