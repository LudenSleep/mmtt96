# 1.9 T2: aggregate writers.lua runs into config/oracle/writers.tsv (who writes which RAM word, VDP register, VDP table).
# Env: any Python 3; input .run/oracle/<run>.jsonl + <run>_{writes,vdp}.tsv from scripts/oracle/lua/writers.lua.
# Run: PY scripts/oracle/writers_agg.py <run id or jsonl>... [--out PATH]   (refuses a run whose controls fail)
import argparse, collections, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ORACLE = os.path.join(ROOT, ".run", "oracle")
OUT = os.path.join(ROOT, "config", "oracle", "writers.tsv")
COLS = ["run", "scen", "addr", "size", "writes", "writers", "first", "last"]
HEADER = """# 1.9 T2 writer census: per run, every watched RAM word, VDP register and VDP access-command target with its writers.
# Env: MAME 0.289 via scripts/oracle/mame.py run scripts/oracle/lua/writers.lua (taps reinstalled per frame; controls
#   ram_frame_counter FFC220 written every frame from frame 10, ROM header 000100 never written; a failing run is refused).
# addr: RAM word (hex, size 2 bytes); vdp_reg_XX (register number, size 1); access commands <space>[:<table>][:<dma>]:
#   space vram|cram|vsram (+_r = read); VRAM table from the register values live at the command (hscroll reg 0D,
#   sprite reg 05, window reg 03, plane_a reg 02, plane_b reg 04, sizes reg 10; else tiles; ? = bases not yet set);
#   dma = dma:<RAM source, mirror folded to FFxxxx; tiles: dma:ram>|dma:rom|fill|copy (regs 15-17);
#   size = distinct target addresses.
# writes = words written (RAM) or register sets / commands; writers = distinct writer pcs: pc*count, top 8 by count
#   (pc is cpu PC at the tap, may be ahead of the writing insn, C0015); first/last = frame numbers (frame 1 not recorded).
# Built by: PY scripts/oracle/writers_agg.py <run>..."""
CTRL_POS, CTRL_NEG, POS_FROM = "FFC220", "000100", 10  # not 000000: written once at frame 595 of boot runs


def tsv(path):
    with open(path, encoding="utf-8") as f:
        rows = [l.rstrip("\n").split("\t") for l in f]
    return rows[1:]


def prefix(run):
    run = os.path.basename(run)
    return os.path.join(ORACLE, run[:-6] if run.endswith(".jsonl") else run)


def frames_of(p):
    ev = [json.loads(l) for l in open(p + ".jsonl", encoding="utf-8") if l.strip()]
    done = [e for e in ev if e["ev"] == "done"]
    if not done or not any(e["ev"] == "writers" for e in ev):
        return None, None
    return done[0]["frames"], done[0].get("scen", "-")


def controls(run, pos_from=None):
    """(pass, detail, pos_ok, neg_ok) for the writers.lua controls of one run: positive = FFC220 written in every
    frame from POS_FROM on (boot runs: no counter write in frames 3-7, 3/3 runs), negative = 000100 never written."""
    p = prefix(run)
    frames, _ = frames_of(p)
    if frames is None:
        return False, "run incomplete", False, False
    pos, neg = set(), 0
    for fr, addr, pc, c in tsv(p + "_writes.tsv"):
        if addr == CTRL_POS:
            pos.add(int(fr))
        elif addr == CTRL_NEG:
            neg += int(c)
    pos_from = pos_from or POS_FROM
    win = range(pos_from, frames + 1)
    hit = sum(1 for f in win if f in pos)
    pos_ok, neg_ok = hit == len(win) > 0, neg == 0
    return (pos_ok and neg_ok, f"positive {CTRL_POS} {hit}/{len(win)} frames {pos_from}..{frames}; "
            f"negative {CTRL_NEG} {neg} writes", pos_ok, neg_ok)


SIZES = {0: 32, 1: 64, 3: 128}


def table_of(a, regs):
    if not all(r in regs for r in (2, 3, 4, 5, 13)):
        return "?"
    plane = SIZES.get(regs.get(16, 0) & 3, 32) * SIZES.get((regs.get(16, 0) >> 4) & 3, 32) * 2
    for name, base, size in (("hscroll", (regs[13] & 0x3F) << 10, 0x380), ("sprite", (regs[5] & 0x7F) << 9, 0x280),
                             ("window", (regs[3] & 0x3E) << 10, 0x1000), ("plane_a", (regs[2] & 0x38) << 10, plane),
                             ("plane_b", (regs[4] & 0x07) << 13, plane)):
        if base <= a < base + size:
            return name
    return "tiles"


def dma_of(regs):
    r17 = regs.get(0x17, 0)
    if r17 & 0x80:
        return "copy" if r17 & 0x40 else "fill"
    src = ((r17 & 0x7F) << 17) | (regs.get(0x16, 0) << 9) | (regs.get(0x15, 0) << 1)
    return f"dma:{0xFF0000 | (src & 0xFFFF):06X}" if src >= 0xE00000 else "dma:rom"  # RAM mirrors E00000-FFFFFF


def rows_of(run):
    p = prefix(run)
    rid = os.path.basename(p)
    frames, scen = frames_of(p)
    ok, detail, _, _ = controls(run)
    if not ok:
        sys.exit(f"writers_agg: refusing {rid}: {detail}")
    agg = collections.OrderedDict()

    def add(key, size_key, pc, n, fr):
        r = agg.setdefault(key, {"w": 0, "pcs": collections.Counter(), "first": fr, "last": fr, "sz": set()})
        r["w"] += n
        r["pcs"][pc] += n
        r["last"] = fr
        r["sz"].add(size_key)

    for fr, addr, pc, c in tsv(p + "_writes.tsv"):
        add(addr, 2, pc, int(c), int(fr))
    regs = {}
    for fr, kind, pc, a, b, dma, dw in tsv(p + "_vdp.tsv"):
        if kind == "reg":
            regs[int(a, 16)] = int(b, 16)
            add(f"vdp_reg_{a}", 1, pc, 1, int(fr))
            continue
        addr = int(b, 16)
        tab = table_of(addr, regs) if a.startswith("vram") else ""
        d = dma_of(regs) if dma == "1" else ""
        if tab == "tiles" and d.startswith("dma:F"):
            d = "dma:ram"  # tile uploads: many sources, one row
        key = a + (":" + tab if tab else "") + (":" + d if d else "")
        add(key, addr, pc, 1, int(fr))
    out = []
    for key, r in agg.items():
        size = 2 if key[0] in "0123456789ABCDEF" else 1 if key.startswith("vdp_reg") else len(r["sz"])
        top = sorted(r["pcs"].items(), key=lambda x: (-x[1], x[0]))[:8]
        out.append([rid, scen, key, str(size), str(r["w"]), f"{len(r['pcs'])}:" + ",".join(f"{a}*{c}" for a, c in top),
                    str(r["first"]), str(r["last"])])
    print(f"writers_agg: {rid} {scen} frames {frames}: {detail}; {len(out)} rows")
    return sorted(out, key=lambda x: x[2])


def main(argv=None):
    ap = argparse.ArgumentParser(description="writers.lua runs -> config/oracle/writers.tsv")
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args(argv)
    rows = [r for run in a.runs for r in rows_of(run)]
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(HEADER + "\n" + "\t".join(COLS) + "\n")
        for r in rows:
            f.write("\t".join(r) + "\n")
    print(f"writers_agg: {len(rows)} rows -> {os.path.relpath(a.out, ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
