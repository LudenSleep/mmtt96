"""Split the retail ROM into assembler sources, one file per region row (all data, dc.b).

Usage: PY scripts/build/split.py [--rom PATH] [--regions PATH] [--out asm] [--src asm/src] [--dialect as|asm68k]
                                 [--names config/names]

Writes <out>/main.asm (AS default: cpu/supmode/padding header; org 0, then include lines in regions.tsv order), <out>/rom/<id>.asm per non-compressed row,
all compressed rows (imp_NNN, one contiguous run) in <out>/imp.asm, and <out>/.stamp. Deletes only those generated
outputs first (never <out>/src or the --src dir). Each region opens with "<id>:" and ends with a boundary assert
(current address == end, end exclusive). A non-compressed row with <src>/<id>.asm gets a wrapper instead of dc.b:
label, include of the src file (path relative to --out, the assembler's cwd), assert. --src "" = all data.
Exit 2 = refusal (absent ROM, SHA-1 mismatch, gap in regions, unimplemented dialect, src id not a non-compressed
row). Stdlib only.
Names: <out>/{hw,ram,rom}.inc (names_inc(): equates from --names hw/ram/structs/routines .tsv) are included right
after the header; after the last include, one assert per routines.tsv code name (equate == <region_id>+$<off>; a code name
equal to a region id has no equate and asserts == $<addr6>). Exit 1 = names
refusal (mnemonic, duplicate name/address, code name outside its region).
"""
import argparse
import os
import pathlib
import re
import shutil
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "scripts" / "extract"))
from manifest import ROM_DEFAULT, ROM_SHA1, read_regions, refuse, sha1  # noqa: E402,F401  (refuse: manifest's own refusals in read_regions)


# AS (asw) source header; db.py listing self-check imports it so both assemble alike
AS_HEADER = "\tcpu\t68000\n\tsupmode\ton\n\tpadding\toff\n"
NAMES_DIR = "config/names"
INCS = ("hw.inc", "ram.inc", "rom.inc")  # generated next to main.asm (ignored asm/); db.py self-check writes its own copies
sys.path.insert(0, str(REPO / "scripts" / "health"))
from asm_leak import MNEMONICS  # noqa: E402  (a name that is a mnemonic would read as an instruction)


def names_inc(out_dir, names_dir=NAMES_DIR, no_names=False, region_ids=()):
    """Write the three include files into <out_dir> (T3 1.9; replaces names.inc):
    hw.inc  <- hw.tsv (name value kind evidence): `<name> equ $<value>` per constant row; kind form rows
               (value `args:expr`) -> `<name> function args,expr`; kind fact/basereg rows emit nothing.
    ram.inc <- ram.tsv kind ram/io rows (addr >= $FF0000 as the sign-extended 32-bit `$FF<addr6>`, so `(name).l`
               reassembles the game's $FFxxxxxx operands; io 24-bit) + `<struct>_<field> equ $<offset>` per structs.tsv row.
    rom.inc <- ram.tsv kind rom rows + routines.tsv kind=code rows (24-bit); a code row whose name is in region_ids
               gets no equ (the region label defines it; main() asserts its absolute address).
    no_names: header comments only. Refuses (exit 1) a name that is a 68000 mnemonic, a duplicate name (across all
    three files) or a duplicate address. Returns {"ram": [...], "structs": {struct: {offset: field}},
    "fsize": {struct: {offset: size}}, "code": [...], "hw": [...], "consts": [...]} (ram/code rows as dicts,
    addr/offset/size as ints; hw rows as dicts with int value where numeric; consts rows {addr:int, opnd:int, expr})."""
    def rows(fname):
        p = pathlib.Path(names_dir) / fname
        if not p.is_file():
            return []
        lines = [l.split("\t") for l in p.read_text(encoding="utf-8").split("\n") if l.strip()]
        return [dict(zip(lines[0], l)) for l in lines[1:]]
    names = {"ram": [], "structs": {}, "fsize": {}, "code": [], "hw": [], "consts": []}
    if not no_names:
        names["ram"] = [dict(r, addr=int(r["addr"], 16), size=int(r["size"], 16)) for r in rows("ram.tsv")]
        names["code"] = [dict(r, addr=int(r["addr"], 16)) for r in rows("routines.tsv") if r["kind"] == "code"]
        for r in rows("structs.tsv"):
            names["structs"].setdefault(r["struct"], {})[int(r["offset"], 16)] = r["field"]
            names["fsize"].setdefault(r["struct"], {})[int(r["offset"], 16)] = int(r["size"], 16)
        for r in rows("hw.tsv"):
            if r["kind"] not in ("form", "fact"):
                r = dict(r, value=int(r["value"], 16))
            names["hw"].append(r)
        names["consts"] = [dict(r, addr=int(r["addr"], 16), opnd=int(r["opnd"])) for r in rows("consts.tsv")]
    out = {"hw.inc": [], "ram.inc": [], "rom.inc": []}
    seen_name, seen_addr = set(), set()
    mnem = re.compile(r"(?:%s)$" % MNEMONICS, re.IGNORECASE)

    def claim(name):
        if mnem.match(name):
            print(f"split: names: {name!r} is a 68000 mnemonic", file=sys.stderr)
            sys.exit(1)
        if name in seen_name:
            print(f"split: names: duplicate name {name}", file=sys.stderr)
            sys.exit(1)
        seen_name.add(name)
    for r in names["ram"] + names["code"]:
        if r["addr"] in seen_addr:
            print(f"split: names: duplicate name or address {r['name']} 0x{r['addr']:06X}", file=sys.stderr)
            sys.exit(1)
        claim(r["name"])
        seen_addr.add(r["addr"])
        if r in names["code"] and r["name"] in region_ids:
            continue
        wide = "FF" if r in names["ram"] and r["addr"] >= 0xFF0000 else ""
        f = "ram.inc" if r in names["ram"] and r["kind"] in ("ram", "io") else "rom.inc"
        out[f].append(f"{r['name']}\tequ\t${wide}{r['addr']:06X}\n")
    for s, fields in sorted(names["structs"].items()):
        for off, field in sorted(fields.items()):
            claim(f"{s}_{field}")
            out["ram.inc"].append(f"{s}_{field}\tequ\t${off:X}\n")
    for r in names["hw"]:
        if r["kind"] in ("fact", "basereg"):
            continue
        claim(r["name"])
        if r["kind"] == "form":
            args, expr = r["value"].split(":", 1)
            out["hw.inc"].append(f"{r['name']}\tfunction\t{args},{expr}\n")
        else:
            out["hw.inc"].append(f"{r['name']}\tequ\t${r['value']:X}\n")
    src = "none (no_names)" if no_names else pathlib.Path(os.path.relpath(names_dir, REPO)).as_posix()
    for f in INCS:
        write(pathlib.Path(out_dir) / f, f"; generated by split.py names_inc from {src}; do not edit\n" + "".join(out[f]))
    return names


def refuse_split(msg):
    print(f"split: refused: {msg}", file=sys.stderr)
    sys.exit(2)


def assert_end(rid, end, dialect):
    """Boundary assert: assembly fails unless the current address equals the region's exclusive end."""
    if dialect == "as":
        return f'\tif\t* <> ${end:06X}\n\terror\t"{rid}: end mismatch"\n\tendif\n'
    if dialect == "asm68k":
        return f'\tif\t* <> ${end:06X}\n\tinform\t3,"{rid}: end mismatch"\n\tendc\n'
    refuse_split(f"dialect {dialect!r} not implemented")


def region_text(rid, data, end, dialect):
    out = [f"{rid}:\n"]
    for i in range(0, len(data), 16):
        out.append("\tdc.b\t" + ",".join(f"${b:02X}" for b in data[i:i + 16]) + "\n")
    out.append(assert_end(rid, end, dialect))
    return "".join(out)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="ascii", newline="\n") as f:
        f.write(text)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--rom", default=ROM_DEFAULT)
    ap.add_argument("--regions", default="config/regions.retail.tsv")
    ap.add_argument("--out", default="asm")
    ap.add_argument("--src", default="asm/src")
    ap.add_argument("--dialect", default="as", choices=["as", "asm68k"])
    ap.add_argument("--names", default=NAMES_DIR, help="names dir (hw/ram/structs/routines/consts .tsv) -> <out>/{hw,ram,rom}.inc")
    a = ap.parse_args(argv)
    rom_path = pathlib.Path(a.rom)
    if not rom_path.is_file():
        refuse_split(f"no ROM dump at {a.rom}")
    rom = rom_path.read_bytes()
    if sha1(rom) != ROM_SHA1:
        refuse_split(f"{a.rom}: SHA-1 {sha1(rom)} != {ROM_SHA1}")
    rows = read_regions(a.regions, len(rom))
    pos = 0
    for r in rows:
        if r["start"] != pos:
            refuse_split(f"{a.regions}:{r['line']}: gap or overlap at 0x{pos:06X}")
        pos = r["end"]
    if pos != len(rom):
        refuse_split(f"{a.regions}: regions end at 0x{pos:06X}, ROM size 0x{len(rom):06X}")

    kinds = {r["name"]: r["kind"] for r in rows}
    src_ids = []
    if a.src and pathlib.Path(a.src).is_dir():
        src_ids = sorted(f.stem for f in pathlib.Path(a.src).glob("*.asm"))
    for sid in src_ids:
        if sid not in kinds:
            refuse_split(f"{a.src}/{sid}.asm: {sid!r} is not a region row")
        if kinds[sid] == "compressed":
            refuse_split(f"{a.src}/{sid}.asm: {sid!r} is a compressed row")
    print(f"split: src {len(src_ids)} regions {','.join(src_ids)}".rstrip())

    out = pathlib.Path(a.out)
    # remove only generated outputs; <out>/src and the --src dir are never touched
    if (out / "rom").exists():
        shutil.rmtree(out / "rom")
    for name in ("main.asm", "imp.asm", ".stamp", "names.inc") + INCS:  # names.inc: the pre-1.9 single include
        (out / name).unlink(missing_ok=True)
    names = names_inc(out, a.names, region_ids=set(kinds))
    main_lines = ([AS_HEADER] if a.dialect == "as" else []) + [f'\tinclude\t"{i}"\n' for i in INCS] + ["\torg\t0\n"]
    imp_parts, files, nbytes, imp_open, imp_done = [], 0, 0, False, False
    for r in rows:
        rid, data = r["name"], rom[r["start"]:r["end"]]
        if rid in src_ids:
            inc = os.path.relpath(pathlib.Path(a.src) / f"{rid}.asm", out).replace("\\", "/")
            text = f'{rid}:\n\tinclude\t"{inc}"\n' + assert_end(rid, r["end"], a.dialect)
        else:
            text = region_text(rid, data, r["end"], a.dialect)
        nbytes += len(data)
        if r["kind"] == "compressed":
            if imp_done:
                refuse_split(f"{a.regions}:{r['line']}: compressed rows are not one contiguous run")
            if not imp_open:
                main_lines.append('\tinclude\t"imp.asm"\n')
                imp_open = True
            imp_parts.append(text)
        else:
            if imp_open:
                imp_open, imp_done = False, True
            write(out / "rom" / f"{rid}.asm", text)
            files += 1
            main_lines.append(f'\tinclude\t"rom/{rid}.asm"\n')
    # per code name: equate == region label + offset (C0008: the error branch is taken on a mismatch)
    for c in names["code"]:
        r = next((r for r in rows if r["start"] <= c["addr"] < r["end"]), None)
        if r is None or c.get("region", "-") not in ("-", "", r["name"]):
            print(f"split: names: {c['name']} 0x{c['addr']:06X} not in region {c.get('region')}", file=sys.stderr)
            sys.exit(1)
        want = f'${c["addr"]:06X}' if c["name"] in kinds else f'{r["name"]}+${c["addr"] - r["start"]:X}'
        main_lines.append(f'\tif\t{c["name"]} <> {want}\n'
                          f'\terror\t"names: {c["name"]}"\n\tendif\n')
    if imp_parts:
        write(out / "imp.asm", "".join(imp_parts))
        files += 1
    write(out / "main.asm", "".join(main_lines))
    write(out / ".stamp", f"{ROM_SHA1}\n")
    print(f"regions {len(rows)}/{len(rows)} files {files} bytes {nbytes}/{len(rom)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
