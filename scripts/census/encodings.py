"""Encoding-form census (plan 1.6 T5, G12/encoding map): every Capstone instruction of every verified code region,
classified into encoding forms, checked against the coverage section of docs/encoding-map.md.

  encodings.py [--write-map] [--plant]

Form = `<mn>[.<sz>]:<modes>`: Capstone mnemonic lowercased, size suffix stripped, not aliased; conditions collapsed
(b<cc> -> bcc, db<cc>/dbra -> dbcc, s<cc> -> scc; bra/bsr kept); branches take `.s`/`.w` from the instruction size and
drop the displacement operand; mode tokens joined by `,`; no operands -> `none`; a rejected word -> `invalid`.
The sweep is boundaries.py's (same decoder `_MD`, same data-run skips, invalid steps 2); its total must equal the sum
of boundaries.compare()'s sweep sizes. Writes ignored .run/encodings/forms.tsv + summary.txt; prints
`encmap: forms <m>/<n> mapped` and `insns <N> regions <R>` (form names and counts only on stdout).
  --write-map  regenerate the section between the encmap markers of docs/encoding-map.md
  --plant      assemble a synthetic one-line source (a form absent from the game), add it to the census; must exit 1
Exit 1 on a form absent from or count-stale in the map, a map row with no census form, a sweep count mismatch,
or a missing Ghidra listing tsv. Stdlib + capstone (pin: docs/ops/ops-setup-decomp.md).
"""
import argparse
import os
import re
import subprocess
import sys

from capstone import m68k

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "scripts", "oracle"))
sys.path.insert(0, os.path.join(ROOT, "scripts", "build"))
import boundaries as bd  # noqa: E402
from split import AS_HEADER  # noqa: E402

OUT = os.path.join(ROOT, ".run", "encodings")
MAP = os.path.join(ROOT, "docs", "encoding-map.md")
ASL = os.path.join(ROOT, "tools", "bin", "asl")
BEGIN, END = "<!-- encmap:begin -->", "<!-- encmap:end -->"
CC = "t|f|hi|ls|cc|cs|ne|eq|vc|vs|pl|mi|ge|lt|gt|le|hs|lo"
RE_B, RE_DB, RE_S = (re.compile(p % CC) for p in (r"b(?:%s)$", r"db(?:%s|ra)$", r"s(?:%s)$"))
PROBES = {"A": "P16T5-A", "A2": "P16T5-A2", "B": "P16T5-B", "C": "P16T5-C", "D": "P16T5-D", "E": "P16T5-E"}

AM = {
    m68k.M68K_AM_REG_DIRECT_DATA: "dn", m68k.M68K_AM_REG_DIRECT_ADDR: "an", m68k.M68K_AM_REGI_ADDR: "ind",
    m68k.M68K_AM_REGI_ADDR_POST_INC: "postinc", m68k.M68K_AM_REGI_ADDR_PRE_DEC: "predec",
    m68k.M68K_AM_REGI_ADDR_DISP: "d16an", m68k.M68K_AM_AREGI_INDEX_8_BIT_DISP: "d8anxn",
    m68k.M68K_AM_ABSOLUTE_DATA_SHORT: "absw", m68k.M68K_AM_ABSOLUTE_DATA_LONG: "absl",
    m68k.M68K_AM_PCI_DISP: "d16pc", m68k.M68K_AM_PCI_INDEX_8_BIT_DISP: "d8pcxn", m68k.M68K_AM_IMMEDIATE: "imm",
    # Capstone reports a brief-extension index with a zero d8 as the base-displacement mode; same 68000 encoding
    m68k.M68K_AM_AREGI_INDEX_BASE_DISP: "d8anxn", m68k.M68K_AM_PCI_INDEX_BASE_DISP: "d8pcxn",
}
SPECIAL = {m68k.M68K_REG_CCR: "ccr", m68k.M68K_REG_SR: "sr", m68k.M68K_REG_USP: "usp"}


def mode(op):
    if op.type == m68k.M68K_OP_REG_BITS:
        return "reglist"
    if op.type == m68k.M68K_OP_IMM:
        return "imm"
    if op.type == m68k.M68K_OP_REG and op.reg in SPECIAL:
        return SPECIAL[op.reg]
    if op.type == m68k.M68K_OP_REG:
        return "an" if m68k.M68K_REG_A0 <= op.reg <= m68k.M68K_REG_A7 else "dn"
    t = AM.get(op.address_mode)
    if t is None:
        return "?%d.%d" % (op.type, op.address_mode)  # unknown operand kind: an unmapped form, never silent
    if t == "d16an" and op.mem.disp == 0:
        t = "d16an0"  # class E
    return t


def form(ins):
    """Encoding-form name of one Capstone instruction (None / dc.* -> 'invalid')."""
    if ins is None or ins.mnemonic.startswith("dc."):
        return "invalid"
    mn, sz = ins.mnemonic.lower(), ""
    if len(mn) > 2 and mn[-2] == "." and mn[-1] in "bwls":
        mn, sz = mn[:-2], mn[-1]
    if RE_DB.match(mn):
        mn = "dbcc"
    elif mn not in ("bra", "bsr") and RE_B.match(mn):
        mn = "bcc"
    elif RE_S.match(mn):
        mn = "scc"
    ops = list(ins.operands)
    if any(o.type == m68k.M68K_OP_BR_DISP for o in ops):
        sz = "s" if ins.size == 2 else "w"
        ops = [o for o in ops if o.type != m68k.M68K_OP_BR_DISP]
    modes = ",".join(mode(o) for o in ops) or "none"
    return "%s%s:%s" % (mn, "." + sz if sz else "", modes)


def classes(f):
    """Disagreement classes (docs/encoding-map.md) a form belongs to."""
    mn, modes = f.split(":", 1) if ":" in f else (f, "")
    base, toks = mn.split(".")[0], modes.split(",")
    out = []
    if base == "cmp" and modes == "imm,dn" and mn != "cmp":
        out.append("A")
    if base in ("addi", "subi", "andi", "ori") and modes == "imm,dn":
        out.append("A2")
    if base == "movem" and "d16pc" in toks:
        out.append("B")
    if base in ("ori", "andi", "eori") and ("ccr" in toks or "sr" in toks):
        out.append("C")
    if "d8pcxn" in toks:
        out.append("D")
    if "d16an0" in toks:
        out.append("E")
    return out


def sweep(rid, s, e, rows, rom):
    """boundaries.compare()'s sweep, keeping the full instruction: [form, ...] in address order."""
    data = [(r[0], r[0] + r[1]) for r in rows if r[2] == "data"]
    dend = {a: b for a, b in data}
    out, pos = [], s
    while pos < e:
        if pos in dend:
            pos = dend[pos]
            continue
        ins = next(bd._MD.disasm(rom[pos:pos + 10], pos, count=1), None)
        f = form(ins)
        n = 2 if f == "invalid" else ins.size
        out.append(f)
        if pos + n > e:
            break
        nxt = pos + n
        inside = next((b for a, b in data if a < nxt < b), None)
        pos = inside if inside is not None else nxt
    return out


def assemble(src, d, name):
    """Synthetic AS source -> flat bytes via asw + p2bin in d; None on assembler failure (log: d/<name>.log)."""
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, name + ".asm"), "w", encoding="ascii", newline="\n") as f:
        f.write(AS_HEADER + "\torg\t0\n" + src)
    for x in (".p", ".bin"):
        if os.path.exists(os.path.join(d, name + x)):
            os.remove(os.path.join(d, name + x))
    with open(os.path.join(d, name + ".log"), "w", encoding="utf-8", errors="replace") as f:
        rc = subprocess.call([os.path.join(ASL, "asw.exe"), "-q", "-xx", "-n", "-U", "-i", ".", name + ".asm"],
                             stdout=f, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, cwd=d)
        if rc == 0 and os.path.exists(os.path.join(d, name + ".p")):
            rc = subprocess.call([os.path.join(ASL, "p2bin.exe"), name + ".p", name + ".bin"],
                                 stdout=f, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, cwd=d)
    if rc != 0 or not os.path.exists(os.path.join(d, name + ".bin")):
        return None
    with open(os.path.join(d, name + ".bin"), "rb") as f:
        return f.read()


def plant_form():
    """One synthetic source line (PEA abs.l, absent from the game code) classified by form()."""
    code = assemble("\tpea\t($00001000).l\n", os.path.join(OUT, "plant"), "plant")
    if code is None:
        sys.exit("encodings: --plant: assembler failed, see .run/encodings/plant/plant.log")
    return form(next(bd._MD.disasm(code, 0, count=1), None))


def read_map():
    with open(MAP, encoding="utf-8") as f:
        text = f.read()
    if text.count(BEGIN) != 1 or text.count(END) != 1:
        sys.exit("encodings: %s: need exactly one %s ... %s section" % (os.path.relpath(MAP, ROOT), BEGIN, END))
    i, j = text.index(BEGIN), text.index(END)
    rows = {}
    for l in text[i:j].split("\n"):
        c = [x.strip() for x in l.strip().strip("|").split("|")]
        if l.startswith("|") and len(c) == 3 and c[1].isdigit():
            rows[c[0].strip("`")] = int(c[1])
    return text, i, j, rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write-map", action="store_true")
    ap.add_argument("--plant", action="store_true")
    a = ap.parse_args(argv)
    regions = sorted(bd.code_regions("verified"), key=lambda r: r[1])
    with open(os.path.join(ROOT, bd.ROM_DEFAULT), "rb") as f:
        rom = f.read()
    exempt = bd.exceptions()
    counts, where, own, ref = {}, {}, 0, 0
    for rid, s, e in regions:
        path = os.path.join(ROOT, ".run", "boundaries", "ghidra", rid + ".tsv")
        if not os.path.exists(path):
            print("encodings: missing %s: run boundaries --refresh / make health" % os.path.relpath(path, ROOT))
            return 1
        rows = bd.read_rows(path)
        fs = sweep(rid, s, e, rows, rom)
        own += len(fs)
        ref += bd.compare(rid, s, e, rows, rom, rid in exempt, [])["n"]
        for f in fs:
            counts[f] = counts.get(f, 0) + 1
            w = where.setdefault(f, [])
            if not w or w[-1] != rid:
                w.append(rid)
    if own != ref:
        print("encodings: sweep count %d != boundaries sweep count %d" % (own, ref))
        return 1
    if a.plant:
        f = plant_form()
        counts[f] = counts.get(f, 0) + 1
        where.setdefault(f, []).append("plant")
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "forms.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("form\tcount\tregions\tfirst_region\n")
        for k in sorted(counts):
            f.write("%s\t%d\t%d\t%s\n" % (k, counts[k], len(where[k]), where[k][0]))
    text, i, j, rows = read_map()
    if a.write_map:
        lines = [BEGIN,
                 "Denominators: %d verified code regions, %d instructions (Capstone sweep, boundaries.py skip rules). "
                 "Evidence = the first verified region (address order) holding the form, i.e. assembled back to the "
                 "original under AS by the srcform health pair; class A-E forms also cite their synthetic probe "
                 "(%s; log T5.c1). Generated by `scripts/census/encodings.py --write-map`; never hand-edited."
                 % (len(regions), own, ", ".join(PROBES.values())),
                 "", "| Form | Count | Evidence |", "|---|---|---|"]
        for k in sorted(counts):
            pr = ", ".join(PROBES[c] for c in classes(k))
            lines.append("| `%s` | %d | %s%s |" % (k, counts[k], pr + "; " if pr else "", where[k][0]))
        text = text[:i] + "\n".join(lines) + "\n" + text[j:]
        with open(MAP, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        rows = read_map()[3]
    bad = sorted(k for k in counts if rows.get(k) != counts[k])
    extra = sorted(k for k in rows if k not in counts)
    m = len(counts) - len(bad)
    summary = ["encmap: forms %d/%d mapped" % (m, len(counts)), "insns %d regions %d" % (own, len(regions))]
    summary += ["unmapped %s" % k if k not in rows else "stale %s" % k for k in bad]
    summary += ["extra %s" % k for k in extra]
    with open(os.path.join(OUT, "summary.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(summary) + "\n")
    print("\n".join(summary))
    return 1 if bad or extra else 0


if __name__ == "__main__":
    sys.exit(main())
