"""Mechanical naming sweep: neutral config/names/ram.tsv rows for raw operand addresses (T8).

  sweep.py operands [--layer ram|io|rom] [--dry-run]

  operands  `db.py listing <all code ids> --out .run/sweep/src` (scratch; never asm/src); collect every
            raw `$hex` operand that ledger.py `nameable()` counts (same tokenizer as ledger.py `parse()`); append
            neutral rows for addresses not yet named, evidence `T8 sweep neutral (operand census)`; rows re-sorted
            by address (stable); a rerun is a no-op.
  Layers (default: all, in order ram, io, rom):
    ram  $FF0000-$FFFFFF -> `ram_<ADDR6>`; io  $A00000-$A0FFFF `z80_`, $C00000-$C0001F `vdp_`, else `io_`;
    rom  < ROM size, not a function entry (.run/signatures/functions.tsv) nor a code region start ->
         `dat_<ADDR6>` (non-code region) / `lbl_<ADDR6>` (code region). A Ghidra-only function entry
         (interior call target, fall-through region start) is swept too: db.py rebuild applies labels
         after auto-analysis (T34.c2), so the label neither seeds nor renames the Ghidra function.
  size = widest access width seen (b 1, w 2, l 4; unsized 1). Skipped: already named, interior of a struct-typed
  row, name collision, (rom) entries / code region starts.
Firewall: stdout and the TSV carry names, addresses, ids and counts only. Stdlib only.
"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from census import REGIONS, ROOT, ROM_DEFAULT, load_regions  # noqa: E402
from ledger import DB, FUNCS, HEX, NAMES, code_rows, in_imm, known_names, nameable, tsv  # noqa: E402

RAM = os.path.join(NAMES, "ram.tsv")
HEADER = "addr\tsize\tname\tkind\tstruct\tevidence"
EVIDENCE = "T8 sweep neutral (operand census)"
WIDTH = {"b": 1, "w": 2, "l": 4}


def effective(v, size):
    """ledger.nameable() normalisation: 24-bit, abs.w sign-extended."""
    if v > 0xFFFFFF:
        v &= 0xFFFFFF
    elif size == "w" and 0x8000 <= v <= 0xFFFF:
        v |= 0xFF0000
    return v


def operands(src, rom_size):
    """addr -> widest access width over every nameable raw operand (tokenizer of ledger.parse())."""
    seen = {}
    for fn in sorted(os.listdir(src)):
        if not fn.endswith(".asm"):
            continue
        with open(os.path.join(src, fn), encoding="ascii") as f:
            for line in f.read().split("\n"):
                s = line.strip()
                if not s or s.startswith(";") or s.endswith(":"):
                    continue
                f_ = line.split(";")[0].strip().split("\t")
                mn, ops = f_[0].strip(), (f_[1].strip() if len(f_) > 1 else "")
                if mn == "dc.b":
                    continue
                suf = mn.rsplit(".", 1)[1].lower() if "." in mn else ""
                w = WIDTH.get(suf, 1)
                for m in HEX.finditer(ops):
                    if m.group(1) or m.group(2) or m.group(4) or in_imm(ops, m.start()):
                        continue
                    size = "w" if ops[m.end():].startswith(").w") else "l"
                    v = int(m.group(3), 16)
                    if not nameable(v, size, rom_size):
                        continue
                    a = effective(v, size)
                    seen[a] = max(seen.get(a, 0), w)
    return seen


def layer_of(a, rom_size):
    if 0xFF0000 <= a <= 0xFFFFFF:
        return "ram"
    if 0xA00000 <= a <= 0xC0001F:
        return "io"
    return "rom" if a < rom_size else None


def name_for(layer, a, regions):
    if layer == "ram":
        return "ram_%06X" % a
    if layer == "io":
        return ("z80_%06X" if a <= 0xA0FFFF else "vdp_%06X" if a >= 0xC00000 else "io_%06X") % a
    reg = next((r for r in regions if r["start"] <= a < r["end"]), None)
    return ("lbl_%06X" if reg and reg["kind"] == "code" else "dat_%06X") % a


def run(a):
    with open(os.path.join(ROOT, ROM_DEFAULT), "rb") as f:
        rom_size = len(f.read())
    regions = load_regions(REGIONS)
    os.makedirs(a.src, exist_ok=True)
    ids = [r["id"] for r in code_rows()]
    p = subprocess.run([sys.executable, DB, "listing"] + ids + ["--out", a.src], capture_output=True, text=True)
    with open(os.path.join(os.path.dirname(a.src), "listing.log"), "w", encoding="utf-8") as f:
        f.write(p.stdout + p.stderr)
    if p.returncode:
        sys.exit("sweep: db.py listing rc %d (see .run/sweep/listing.log)" % p.returncode)
    seen = operands(a.src, rom_size)
    rows = tsv(RAM, HEADER)
    have = {int(r["addr"], 16) for r in rows}
    structs = [(int(r["addr"], 16), int(r["addr"], 16) + int(r["size"], 16)) for r in rows if r["struct"] != "-"]
    names = known_names(regions)
    entries = {int(r["start"], 16) for r in tsv(FUNCS) if r["kind"] == "function"}
    starts = {r["start"] for r in regions if r["kind"] == "code"}
    layers = [a.layer] if a.layer else ["ram", "io", "rom"]
    new, skip = [], {}
    for addr in sorted(seen):
        lay = layer_of(addr, rom_size)
        if lay not in layers:
            continue
        why = None
        if addr in have:
            why = "named"
        elif any(s <= addr < e for s, e in structs):
            why = "struct-interior"
        elif lay == "rom" and (addr in entries or addr in starts):
            why = "entry-or-region-start"
        else:
            nm = name_for(lay, addr, regions)
            if nm in names:
                why = "name-collision"
        if why:
            skip[(lay, why)] = skip.get((lay, why), 0) + 1
            continue
        new.append(dict(addr="0x%06X" % addr, size="0x%X" % seen[addr], name=nm, kind=lay, struct="-",
                        evidence=EVIDENCE))
    for lay in layers:
        print("sweep: %s new %d %s" % (lay, sum(1 for r in new if r["kind"] == lay), " ".join(
            "skip-%s %d" % (w, n) for (l, w), n in sorted(skip.items()) if l == lay)))
    if new and not a.dry_run:
        out = sorted(rows + new, key=lambda r: int(r["addr"], 16))
        cols = HEADER.split("\t")
        with open(RAM, "w", encoding="utf-8", newline="\n") as f:
            f.write(HEADER + "\n")
            for r in out:
                f.write("\t".join(r[k] for k in cols) + "\n")
        print("sweep: wrote %d rows -> config/names/ram.tsv" % len(out))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["operands"])
    ap.add_argument("--layer", choices=["ram", "io", "rom"])
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    a.src = os.path.join(ROOT, ".run", "sweep", "src")
    return run(a)


if __name__ == "__main__":
    sys.exit(main())
