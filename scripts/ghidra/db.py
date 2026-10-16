"""Headless Ghidra database driver: the RE database is tracked only as the text export config/ghidra/*.tsv.

  probe                     one headless call on ghidra/probe; exit 0 + Ghidra version
  rebuild [--rom R]         fresh ghidra/mmtt96: import ROM (68000:BE:32:default, base 0), blocks, apply
                            config/ghidra/*.tsv before auto-analysis (Mmtt96Apply.java), analyse, then the
                            kind=label symbols as the last postScript (Mmtt96Apply.java ... labels; after any
                            Mmtt96Seed pass), so a label never seeds or names a function
  export                    ghidra/mmtt96 -> config/ghidra/*.tsv (Mmtt96Export.java, read-only)
  roundtrip [--expect DIR]  rebuild into fresh ghidra/rt_<ts>, export to .run/ghidra/rt/, byte-compare with DIR
                            (default config/ghidra); exit 0 iff identical, else prints the first differing file:line
  analyse [--seeds F]       rebuild into fresh ghidra/mmtt96_seed, then Mmtt96Seed.java: disassemble from the seeds
                            (default .run/ghidra/seeds.tsv, written by classify.py seeds), re-analyse, export
                            functions/insns/refs/bad to .run/ghidra/seed/ (input of classify.py merge); on failure
                            ghidra/mmtt96_seed is dropped
  listing ID...|--all-code [--out D] [--names DIR] [--no-names]
                            regions (config/regions.retail.tsv ids) from ghidra/mmtt96_seed if its seed marker exists (else
                            ghidra/mmtt96; rebuilt if neither) -> raw .run/ghidra/listing/<id>.tsv
                            (Mmtt96Listing.java, read-only) -> AS text <D>/<id>.asm (default asm/src; no org,
                            label or assert; locals L_xxxxxx); self-check: split's AS header+org+include,
                            asw+p2bin in .run/ghidra/listing/as/, compares with the ROM. Names: split.py
                            names_inc() writes .run/ghidra/listing/as/{hw,ram,rom}.inc (wrapper includes them); abs.w/abs.l
                            operands and cross-region branch/pc-rel targets render as names where AS reassembles the
                            same bytes; immediates at VDP/Z80/IO control ports as hw.tsv expressions, consts.tsv rows as
                            `#<expr>` (hw_operands); --no-names = raw hex everywhere (includes empty); --all-code instead of ids =
                            every kind=code region (verified and inferred), stale <D>/*.asm deleted first (make src);
                            config/ghidra/comments.tsv plate/eol rows render as `;` comments (other types not)
  mirror [--names DIR]      config/names ram.tsv + routines.tsv kind=code -> config/ghidra/symbols.tsv (same addr:
                            rename, source names:<file>; new addr: label row); idempotent; also rewrites
                            config/ghidra/regions.tsv from config/regions.retail.tsv (only if it differs); then validate
  validate [--expect DIR]   duplicate/conflict checks of config/ghidra/*.tsv (also run by rebuild/roundtrip)

Stdlib only; drives support/analyzeHeadless.bat (GHIDRA_INSTALL_DIR = Ghidra 12.1.4 install dir, required).
Env: MMTT96_GHIDRA_PROJ = project dir (default <repo>/ghidra; no path element may start with '.');
MMTT96_JDK_PARENT = dir holding jdk-21* (used when JAVA_HOME is unset and no java is on PATH).
Raw headless output goes to .run/ghidra/<step>.log, never stdout.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "scripts", "extract"))
from manifest import ROM_DEFAULT  # noqa: E402

JDK_PARENT = os.environ.get("MMTT96_JDK_PARENT") or "C:/Program Files/Eclipse Adoptium"
SCRIPTS = os.path.join(ROOT, "scripts", "ghidra")
CONF = os.path.join(ROOT, "config", "ghidra")
# MMTT96_GHIDRA_PROJ: project dir override (T1 gap 1); refused under a dot dir (Ghidra rejects those)
PROJ_DIR = os.environ.get("MMTT96_GHIDRA_PROJ") or os.path.join(ROOT, "ghidra")
RUN = os.path.join(ROOT, ".run", "ghidra")
LANG = "68000:BE:32:default"
FILES = {"symbols.tsv": ["addr", "name", "kind", "source"], "comments.tsv": ["addr", "type", "text"],
         "regions.tsv": ["start", "end", "type", "note"], "functions.tsv": ["entry", "name"]}
KINDS = {"label", "function"}
COMMENT_TYPES = {"plate", "pre", "eol", "post", "repeatable"}
ADDR = re.compile(r"0x[0-9A-F]{6}$")


def ghidra_home():
    home = os.environ.get("GHIDRA_INSTALL_DIR")
    if not home:
        sys.exit("db: GHIDRA_INSTALL_DIR is not set (Ghidra 12.1.4 install dir)")
    return home


def version():
    with open(os.path.join(ghidra_home(), "Ghidra", "application.properties"), encoding="utf-8") as f:
        for line in f:
            if line.startswith("application.version="):
                return line.split("=", 1)[1].strip()
    return "unknown"


def env():
    e = dict(os.environ)
    if shutil.which("java") is None and not e.get("JAVA_HOME"):
        jdks = sorted(d for d in os.listdir(JDK_PARENT) if d.startswith("jdk-21")) if os.path.isdir(JDK_PARENT) else []
        if not jdks:
            sys.exit("db: no java: JAVA_HOME unset, none on PATH, no jdk-21* under %s (set JAVA_HOME, add java to PATH,"
                     " or set MMTT96_JDK_PARENT)" % JDK_PARENT)
        e["JAVA_HOME"] = os.path.join(JDK_PARENT, jdks[-1])
    if e.get("JAVA_HOME"):
        e["PATH"] = os.path.join(e["JAVA_HOME"], "bin") + os.pathsep + e.get("PATH", "")
    return e


def headless(project, args, step):
    """One analyzeHeadless call; full output to .run/ghidra/<step>.log. Returns the exit code."""
    if any(e.startswith(".") for e in re.split(r"[\\/]",os.path.abspath(PROJ_DIR)) if e):
        sys.exit("db: Ghidra project dir %s has a path element starting with '.' (Ghidra refuses it); set"
                 " MMTT96_GHIDRA_PROJ to a dir without one" % os.path.abspath(PROJ_DIR))
    os.makedirs(PROJ_DIR, exist_ok=True)
    os.makedirs(RUN, exist_ok=True)
    bat = os.path.join(ghidra_home(), "support", "analyzeHeadless.bat")
    if not os.path.isfile(bat):
        sys.exit("db: no Ghidra at %s (install it there or set GHIDRA_INSTALL_DIR; see docs/ops/ops-setup-decomp.md)"
                 % ghidra_home())
    log = os.path.join(RUN, step + ".log")
    cmd = [bat, PROJ_DIR, project] + args + ["-scriptPath", SCRIPTS]
    with open(log, "w", encoding="utf-8", errors="replace") as f:
        rc = subprocess.call(cmd, stdout=f, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, env=env(), cwd=ROOT)
    if rc != 0:
        print("db: analyzeHeadless exit %d, see %s" % (rc, os.path.relpath(log, ROOT)))
    return rc


def read_tsv(path, header):
    with open(path, encoding="utf-8", newline="") as f:
        text = f.read()
    if "\r" in text:
        sys.exit("db: %s: CR in file" % path)
    lines = text.split("\n")
    if lines[-1] != "":
        sys.exit("db: %s: missing final LF" % path)
    lines = lines[:-1]
    if not lines or lines[0].split("\t") != header:
        sys.exit("db: %s: header must be %s" % (path, "\\t".join(header)))
    rows = []
    for n, line in enumerate(lines[1:], 2):
        r = line.split("\t")
        if len(r) != len(header):
            sys.exit("db: %s:%d: expected %d fields" % (path, n, len(header)))
        rows.append((n, r))
    return rows


def validate(d):
    """Refuse duplicates and conflicts before Ghidra sees the files."""
    t = {k: read_tsv(os.path.join(d, k), h) for k, h in FILES.items()}
    owned, funcs = {}, {}
    for n, (a, name, kind, src) in t["symbols.tsv"]:
        if not ADDR.match(a) or kind not in KINDS or not name or not src:
            sys.exit("db: symbols.tsv:%d: bad addr/kind/name/source" % n)
        if a in owned:
            sys.exit("db: symbols.tsv:%d: second symbol at %s (one owned symbol per address)" % (n, a))
        owned[a] = (name, kind)
    for n, (a, name) in t["functions.tsv"]:
        if not ADDR.match(a) or a in funcs:
            sys.exit("db: functions.tsv:%d: bad or duplicate entry %s" % (n, a))
        if owned.get(a) != (name, "function"):
            sys.exit("db: functions.tsv:%d: %s %s has no matching kind=function row in symbols.tsv" % (n, a, name))
        funcs[a] = name
    for a, (name, kind) in owned.items():
        if kind == "function" and a not in funcs:
            sys.exit("db: symbols.tsv: function %s %s missing from functions.tsv" % (a, name))
    for n, (a, typ, text) in t["comments.tsv"]:
        if not ADDR.match(a) or typ not in COMMENT_TYPES or not text:
            sys.exit("db: comments.tsv:%d: bad addr/type/text" % n)
    starts = set()
    for n, (s, e, typ, note) in t["regions.tsv"]:
        if not ADDR.match(s) or not ADDR.match(e) or int(e, 16) <= int(s, 16) or s in starts or not typ:
            sys.exit("db: regions.tsv:%d: bad or duplicate region" % n)
        starts.add(s)


def drop_project(name):
    for p in (os.path.join(PROJ_DIR, name + ".gpr"), os.path.join(PROJ_DIR, name + ".rep")):
        if os.path.isdir(p):
            shutil.rmtree(p)
        elif os.path.exists(p):
            os.remove(p)


def rebuild(project, rom, conf, post=()):
    validate(conf)
    if not os.path.isfile(rom):
        sys.exit("db: no ROM at " + rom)
    drop_project(project)
    # analyzeHeadless.bat breaks on '(' in arguments (the ROM name has them): import an ignored copy
    os.makedirs(RUN, exist_ok=True)
    local = os.path.join(RUN, "mmtt96.md")
    shutil.copyfile(rom, local)
    rom = local
    ok = os.path.join(RUN, project + ".apply.ok")
    lab = os.path.join(RUN, project + ".labels.ok")
    for m in (ok, lab):
        if os.path.exists(m):
            os.remove(m)
    # preScript: blocks, functions, comments, regions; kind=label symbols only after analysis and any `post`
    # script (T34.c2: a label applied before analysis seeds/names a function and fails roundtrip)
    rc = headless(project, ["-import", os.path.abspath(rom), "-loader", "BinaryLoader", "-loader-blockName", "ROM",
                            "-loader-baseAddr", "0", "-processor", LANG,
                            "-preScript", "Mmtt96Apply.java", conf, ok] + list(post) +
                  ["-postScript", "Mmtt96Apply.java", conf, lab, "labels"], project + ".rebuild")
    if rc != 0 or not os.path.exists(ok) or not os.path.exists(lab):
        print("db: rebuild failed (apply or labels marker missing), see .run/ghidra/%s.rebuild.log" % project)
        return 1
    return 0


def export(project, out):
    os.makedirs(out, exist_ok=True)
    done = os.path.join(RUN, project + ".export.ok")
    if os.path.exists(done):
        os.remove(done)
    rc = headless(project, ["-process", "-noanalysis", "-readOnly",
                            "-postScript", "Mmtt96Export.java", out, done], project + ".export")
    if rc != 0 or not os.path.exists(done):
        print("db: export failed (marker missing), see .run/ghidra/%s.export.log" % project)
        return 1
    return 0


def compare(got, expect):
    for name in sorted(FILES):
        a, b = os.path.join(got, name), os.path.join(expect, name)
        if not os.path.exists(b):
            print("roundtrip: differs %s: missing in %s" % (name, expect))
            return 1
        with open(a, "rb") as f:
            la = f.read().split(b"\n")
        with open(b, "rb") as f:
            lb = f.read().split(b"\n")
        if la != lb:
            i = next((i for i in range(min(len(la), len(lb))) if la[i] != lb[i]), min(len(la), len(lb)))
            print("roundtrip: differs %s:%d" % (name, i + 1))
            return 1
    return 0


def regions_by_id(ids):
    with open(os.path.join(ROOT, "config", "regions.retail.tsv"), encoding="utf-8") as f:
        rows = {r[3]: (int(r[0], 16), int(r[1], 16)) for r in (l.split("\t") for l in f.read().split("\n")[1:] if l)}
    missing = [i for i in ids if i not in rows]
    if missing:
        sys.exit("db: listing: unknown region id(s): " + " ".join(missing))
    return {i: rows[i] for i in ids}


def code_ids():
    """--all-code: ids of every region row with kind=code (verified and inferred)."""
    with open(os.path.join(ROOT, "config", "regions.retail.tsv"), encoding="utf-8") as f:
        rows = [l.split("\t") for l in f.read().split("\n")[1:] if l]
    return [r[3] for r in rows if r[2] == "code"]


def load_comments():
    """comments.tsv plate/eol rows -> {addr: {type: text}}; other comment types are not rendered."""
    out = {}
    for n, (a, t, text) in read_tsv(os.path.join(CONF, "comments.tsv"), FILES["comments.tsv"]):
        if t not in ("plate", "eol"):
            continue
        if not text.isascii():
            sys.exit("db: comments.tsv:%d: non-ASCII comment text (listings are ASCII)" % n)
        out.setdefault(int(a, 16), {})[t] = text
    return out


def raw_listing(regions):
    """Mmtt96Listing.java on the existing project (read-only) -> .run/ghidra/listing/<id>.tsv."""
    # mmtt96_seed only when its last analyse succeeded (marker), else mmtt96 (T1 gap 3)
    seed_ok = os.path.exists(os.path.join(RUN, "mmtt96_seed.seed.ok"))
    project = next((p for p in ("mmtt96_seed", "mmtt96") if (p != "mmtt96_seed" or seed_ok)
                    and os.path.isdir(os.path.join(PROJ_DIR, p + ".rep"))), None)
    if project is None:
        if rebuild("mmtt96", os.path.join(ROOT, ROM_DEFAULT), CONF):
            return None
        project = "mmtt96"
    out = os.path.join(RUN, "listing")
    os.makedirs(out, exist_ok=True)
    ranges, done = os.path.join(out, "ranges.tsv"), os.path.join(RUN, project + ".listing.ok")
    with open(ranges, "w", encoding="utf-8", newline="\n") as f:
        for i, (s, e) in regions.items():
            f.write("%s\t0x%06X\t0x%06X\n" % (i, s, e))
    if os.path.exists(done):
        os.remove(done)
    rc = headless(project, ["-process", "-noanalysis", "-readOnly",
                            "-postScript", "Mmtt96Listing.java", ranges, out, done], project + ".listing")
    if rc != 0 or not os.path.exists(done):
        print("db: listing failed (marker missing), see .run/ghidra/%s.listing.log" % project)
        return None
    return out


ASL = os.path.join(ROOT, "tools", "bin", "asl")
sys.path.insert(0, os.path.join(ROOT, "scripts", "build"))
from split import AS_HEADER, INCS, names_inc  # noqa: E402  (same header and names as the build)
NUM = r"-?0x[0-9a-fA-F]+"
REGS = ["d%d" % i for i in range(8)] + ["a%d" % i for i in range(8)]


def reg(r):
    """Ghidra register (D0b, D0w, A1w, SP) -> AS (asw) name."""
    r = r.lower()
    return "sp" if r == "sp" else r[:2]


def word_abs(v):
    """abs.w operand value -> AS (asw) text: sign-extended RAM form $FFFFxxxx for x >= $8000 (T1)."""
    v &= 0xFFFF
    return "$FFFF%04X" % v if v >= 0x8000 else "$%04X" % v


def num(s):
    return int(s, 16) if not s.startswith("-") else -int(s[1:], 16)


def abs_name(names, v, size):
    """abs operand value -> name text or None, only where AS reassembles the same bytes (T3.c1 probe; RAM equates
    are 32-bit $FFxxxxxx, others 24-bit, T7.c1): .w iff the sign-extended word address is the named address; .l iff
    high byte 0 and value < $FF0000 (io/rom/code), or high byte $FF and low 24 bits >= $FF0000 (RAM)."""
    if not names:
        return None
    if size == "w":
        v &= 0xFFFF
        a = v | 0xFF0000 if v >= 0x8000 else v
    else:
        a = v & 0xFFFFFFFF
        if a >> 24 == 0xFF and a & 0xFFFFFF >= 0xFF0000:
            a &= 0xFFFFFF
        elif a >= 0xFF0000:  # high byte 0 RAM (24-bit) or another high byte: the 32-bit equate would not match
            return None
    if a in names["exact"]:
        return names["exact"][a]
    for r in names["ram"]:  # (base+<struct>_<field>[+d]) for a ram row typed by a struct
        if r.get("struct", "-") not in ("-", "") and r["addr"] < a < r["addr"] + r["size"]:
            fields, off = names["structs"].get(r["struct"], {}), a - r["addr"]
            if off in fields:
                return "%s+%s_%s" % (r["name"], r["struct"], fields[off])
            # interior: d (decimal) past the greatest field <= off, a multiple of its size, below the smallest gap
            fo = max((o for o in fields if o <= off), default=None)
            if fo is None:
                return None
            ks = sorted(fields)
            gap = min((b - a_ for a_, b in zip(ks, ks[1:])), default=r["size"])
            d, fs = off - fo, names["fsize"].get(r["struct"], {}).get(fo, 0)
            if fs and d % fs == 0 and d < gap:
                return "%s+%s_%s+%d" % (r["name"], r["struct"], fields[fo], d)
            return None
    return None


# hw.tsv rendering (plan 1.9 T3). Control ports by published Mega Drive memory map address -> hw.tsv row class.
HW_PORTS = {0xC00004: "vdp_ctrl", 0xC00006: "vdp_ctrl", 0xA11100: "z80_busreq", 0xA11200: "z80_reset",
            0xA10003: "io_data", 0xA10005: "io_data", 0xA10007: "io_data",
            0xA10009: "io_ctrl", 0xA1000B: "io_ctrl", 0xA1000D: "io_ctrl"}
SIZE_MASK = {"b": 0xFF, "w": 0xFFFF, "l": 0xFFFFFFFF}


def hw_tables(hw):
    """hw.tsv rows (split.names_inc) -> lookup tables for hw_operands()."""
    t = {"reg": {}, "field": {}, "cd": {}, "value": {}, "bit": {}, "bitno": {}, "base": {}, "form": set()}
    for r in hw:
        k = r["kind"]
        if k == "vdp_reg":
            t["reg"][r["value"]] = r["name"]
        elif k == "vdp_cd":
            t["cd"][r["value"]] = r["name"]
        elif k == "form":
            t["form"].add(r["name"])
        elif k == "basereg":
            t["base"][r["name"].rsplit("_", 1)[1].upper()] = r["value"]
        elif ":" in k:
            kk, cls = k.split(":", 1)
            if kk in ("field", "bit"):
                t[kk].setdefault(cls, []).append((r["value"], r["name"]))
            elif kk in ("value", "bitno"):
                t[kk].setdefault(cls, {})[r["value"]] = r["name"]
    return t


def hw_greedy(v, rows):
    """Bit-field rows [(mask, name)] covering v: widest masks first, a mask taken only when all its bits are set."""
    parts = []
    for m, n in sorted(rows, key=lambda x: (-bin(x[0]).count("1"), -x[0])):
        if m and v & m == m:
            parts.append(n)
            v &= ~m
    return parts, v


def hw_join(parts, res):
    return "|".join(parts + (["$%X" % res] if res else []))


def hw_cd(t, cd):
    if cd in t["cd"]:
        return t["cd"][cd]
    if cd & 0x20 and cd & ~0x20 in t["cd"] and 0x20 in t["cd"]:
        return t["cd"][cd & ~0x20] + "|" + t["cd"][0x20]
    return "$%X" % cd


def hw_abs(op):
    """Absolute operand -> 24-bit address as the CPU drives it, else None."""
    m = re.fullmatch(r"\(?(%s)\)?\.([wl])" % NUM, op)
    if not m:
        return None
    v = num(m.group(1))
    if m.group(2) == "w":
        v &= 0xFFFF
        return v | 0xFF0000 if v >= 0x8000 else v
    return v & 0xFFFFFF


def hw_dest(op, bases):
    """Destination operand -> HW_PORTS class or None: absolute, (An) or d16(An) with An a known port base (a set of
    possible addresses, e.g. pad 1 or pad 2 data port; every base+d must be a port of the same class)."""
    a = hw_abs(op)
    if a is not None:
        return HW_PORTS.get(a)
    m = re.fullmatch(r"\((?:(%s),)?(A\d)\)" % NUM, op)
    if m and m.group(2) in bases:
        cls = {HW_PORTS.get(x + (num(m.group(1)) if m.group(1) else 0)) for x in bases[m.group(2)]}
        return cls.pop() if len(cls) == 1 and None not in cls else None
    return None


def hw_store(mn, ops, bases):
    """(port class, sized immediate value, size) when the insn stores/tests an immediate at a control port, else None."""
    if len(ops) != 2 or not re.fullmatch(r"#%s" % NUM, ops[0]):
        return None
    cls = hw_dest(ops[1], bases)
    if cls is None:
        return None
    sz = mn.split(".")[1] if "." in mn else "l"
    return cls, num(ops[0][1:]) & SIZE_MASK.get(sz, 0xFFFFFFFF), sz


def hw_writes(mn, ops):
    """Address registers (raw names A0..A7/SP) an insn writes: An destination, movem list, exg, (An)+ / -(An)."""
    if mn.split(".")[0] == "exg":
        return [r for o in ops for r in re.findall(r"\b(A\d|SP)\b", o)]
    w = []
    for o in ops:
        m = re.fullmatch(r"-\((A\d|SP)\)|\((A\d|SP)\)\+", o)
        if m:
            w.append(m.group(1) or m.group(2))
    if len(ops) == 2 and re.fullmatch(r"A\d|SP|\{.*\}", ops[1]):
        w += re.findall(r"\b(A\d|SP)\b", ops[1])
    return w


def hw_value(t, cls, v, mn, sz):
    """Immediate -> hw.tsv expression or None (vdp_ctrl command words are rendered by hw_operands)."""
    if mn.split(".")[0] in ("btst", "bset", "bclr", "bchg"):
        return t["bitno"].get(cls, {}).get(v)
    if v in t["value"].get(cls, {}):
        return t["value"][cls][v]
    if cls == "vdp_ctrl":
        if sz != "w" or v >> 14 != 2 or (v & 0xFF00) not in t["reg"]:
            return None
        r = t["reg"][v & 0xFF00]
        parts, res = hw_greedy(v & 0xFF, t["field"].get(r, []))
        return hw_join([r] + parts, res)
    parts, res = hw_greedy(v, t["bit"].get(cls, []))
    return hw_join(parts, res) if parts else None


def hw_operands(rows, names, rid, stats=None):
    """Raw listing rows -> {insn addr: {operand index: text}} for immediates at control ports (hw.tsv) and consts.tsv
    rows. A known port base: a hw.tsv basereg row (global, e.g. a6 = vdp_data) or a lea/movea.l of a port address in
    this region, moved by addq/subq/adda/suba/lea d16(An) (a set of possible addresses); dropped on any other write
    and at rts/rte/jmp/bra; an in-region call passes the caller's bases to the callee (merged over every call site,
    3 passes) and keeps those its linear span to rts does not write (else all dropped). A vdp_ctrl access-command
    word followed by another immediate word to vdp_ctrl renders as the pair vdp_cmd_hi/vdp_cmd_lo(adr,cd); a lone word
    with bits only in $00F3 as vdp_cmd_lo, else vdp_cmd_hi, with numeric adr/cd parts. stats (constants.py): counts
    hw (in scope), sym, game; lists raw [(addr, class)], base [(addr, reg)], consts_bad [(addr, opnd)], consts_done."""
    t = names.get("hw") if names else None
    consts = names.get("consts", {}) if names else {}
    if not t and not consts and stats is None:
        return {}
    t = t or hw_tables([])
    glob = {r: frozenset([v]) for r, v in t["base"].items()}
    entry = {}
    ins = [(int(r[0], 16), r[3], [o for o in r[4].split("\x1f") if o],
            int(r[5].split(";")[0], 16) & 0xFFFFFF if r[5] else None) for r in rows if r[2] == "insn"]
    idx = {x[0]: i for i, x in enumerate(ins)}

    def merge(x, y):  # registers known on both paths; their possible addresses united
        return {r: x[r] | y[r] for r in x if r in y}

    def span(tg, seen=()):  # registers written from tg to its first rts/rte/jmp/bra, in-region callees included;
        w, j = set(), idx[tg]  # None if it calls outside the region, recurses or runs off the region
        while j < len(ins):
            bj = ins[j][1].split(".")[0]
            if bj in ("jsr", "bsr"):
                sub = span(ins[j][3], seen + (tg,)) if ins[j][3] in idx and ins[j][3] not in seen + (tg,) else None
                if sub is None:
                    return None
                w |= sub
            w |= set(hw_writes(ins[j][1], ins[j][2]))
            if bj in ("rts", "rte", "jmp", "bra"):
                return w
            j += 1
        return None
    for final in (False, False, True):  # passes 1-2 settle the call-target bases (entry), pass 3 renders
        bases, over, prev_end, st = dict(glob), {}, False, (stats if final else None)
        for i, (a, mn, ops, _) in enumerate(ins):
            if a in entry:  # a call target: after a flow end it starts with its callers' bases, else both paths merge
                bases = dict(entry[a]) if prev_end else merge(bases, entry[a])
                bases.update(glob)
            for (ca, n), expr in consts.items():
                if ca != a:
                    continue
                if 0 < n <= len(ops) and (re.fullmatch(r"#%s" % NUM, ops[n - 1]) or mn.split(".")[0] in
                                          ("moveq", "addq", "subq") and re.fullmatch(NUM, ops[n - 1])):
                    over.setdefault(a, {})[n - 1] = "#" + expr
                    if st is not None:
                        st["game"] += 1
                        st["consts_done"].add((a, n))
                else:
                    if final:
                        print("listing %s: consts $%06X operand %d not an immediate (unrendered)" % (rid, a, n))
                    if st is not None:
                        st["consts_bad"].append((a, n))
            s = hw_store(mn, ops, bases)
            if s and a not in over:
                cls, v, sz = s
                text = hw_value(t, cls, v, mn, sz)
                if text is None and cls == "vdp_ctrl" and sz == "w" and v >> 14 != 2 and {"vdp_cmd_hi", "vdp_cmd_lo"} <= t["form"]:
                    nx = ins[i + 1] if i + 1 < len(ins) else None
                    s2 = nx and hw_store(nx[1], nx[2], bases)
                    if s2 and s2[0] == "vdp_ctrl" and s2[2] == "w" and s2[1] & 0xFF0C == 0:
                        lo = s2[1]
                        adr, cd = (lo & 3) << 14 | v & 0x3FFF, v >> 14 | ((lo >> 4) & 0xF) << 2
                        text = "vdp_cmd_hi($%04X,%s)" % (adr, hw_cd(t, cd))
                        over.setdefault(nx[0], {})[0] = "#vdp_cmd_lo($%04X,%s)" % (adr, hw_cd(t, cd))
                    elif v & 0xFF0C == 0:
                        text = "vdp_cmd_lo($%04X,$%X)" % ((v & 3) << 14, ((v >> 4) & 0xF) << 2)
                    else:
                        text = "vdp_cmd_hi($%04X,$%X)" % (v & 0x3FFF, v >> 14)
                if text is not None:
                    over.setdefault(a, {})[0] = "#" + text
                if st is not None:
                    st["hw"] += 1
                    if text is None:
                        st["raw"].append((a, cls))
                    else:
                        st["sym"] += 1
            elif s and st is not None and 0 in over.get(a, {}) and over[a][0].startswith("#vdp_cmd_lo"):
                st["hw"] += 1
                st["sym"] += 1
            # port-base tracking
            b = mn.split(".")[0]
            if b in ("jsr", "bsr"):
                tg = ins[i][3]
                sw = None
                if tg in idx:  # in-region call: the callee starts with the caller's bases
                    loc = {r: v for r, v in bases.items() if r not in glob}
                    entry[tg] = merge(entry[tg], loc) if tg in entry else loc
                    sw = span(tg)
                bases = dict(glob) if sw is None else {r: v for r, v in bases.items() if r in glob or r not in sw}
                prev_end = False
                continue
            if b in ("rts", "rte", "jmp", "bra"):
                bases, prev_end = dict(glob), True
                continue
            prev_end = False
            dst = hw_writes(mn, ops)
            for r in dst:
                p = None
                if b == "lea":
                    p = hw_abs(ops[0])
                    m = re.fullmatch(r"\((%s),(A\d)\)" % NUM, ops[0])
                    if m and m.group(2) in bases:
                        p = frozenset(x + num(m.group(1)) for x in bases[m.group(2)])
                elif b == "movea" and ops[0].startswith("#"):
                    p = num(ops[0][1:]) & 0xFFFFFF
                elif b in ("addq", "subq", "adda", "suba") and r in bases and re.fullmatch(r"#?%s" % NUM, ops[0]):
                    n = num(ops[0].lstrip("#"))
                    p = frozenset(x + (n if b in ("addq", "adda") else -n) for x in bases[r])
                if isinstance(p, int):
                    p = frozenset([p])
                if r in glob:
                    ok = p == glob[r] or (b == "movem" and ops[0] == "(SP)+") or rid == "init"
                    if not ok and st is not None:
                        st["base"].append((a, r))
                    continue
                if p and len(dst) == 1 and all(0xA10000 <= x < 0xA12000 or 0xC00000 <= x < 0xC00020 for x in p):
                    bases[r] = p
                else:
                    bases.pop(r, None)
    return over


def operand(op, mn, addr, targets, label, names=None):
    """One Ghidra default operand repr -> AS (asw) text (T1 explicit-size forms). label(t) -> in-region label or None.
    names: abs_name tables (None = raw hex); cross-region targets with a routines.tsv code name render as the name,
    else an in-ROM ram.tsv name (kind rom: data tables, non-function code labels)."""
    def tgt(t):
        return (label(t) or (names and (names["code"].get(t) or (t < 0x400000 and names["exact"].get(t))))
                or "$%06X" % t)
    m = re.fullmatch(r"\{\s*(.*)\}", op)
    if m:  # movem list -> canonical d0-d7/a0-a7 order, '/'-joined
        rs = {reg(r).replace("sp", "a7") for r in m.group(1).split()}
        return "/".join(r for r in REGS if r in rs)
    m = re.fullmatch(r"#(%s)" % NUM, op)
    if m:
        v = num(m.group(1))
        return "#-$%X" % -v if v < 0 else "#$%X" % v
    m = re.fullmatch(r"\(?(%s)\)?\.([wl])" % NUM, op)
    if m:  # absolute: (x).w / (x).l / x.w / x.l
        v = num(m.group(1))
        n = abs_name(names, v, m.group(2))
        if n:
            return "(%s).%s" % (n, m.group(2))
        return "(%s).w" % word_abs(v) if m.group(2) == "w" else "($%08X).l" % (v & 0xFFFFFFFF)
    m = re.fullmatch(r"\((%s),PC(?:,([AD]\d|SP)([bwl]?)\*0x1)?\)" % NUM, op)
    if m:  # pc-relative: target(pc) / target(pc,Xn.s)
        if m.group(2):  # Ghidra prints the target itself (extension-word address + d8)
            t = num(m.group(1)) & 0xFFFFFF
            return "%s(pc,%s.%s)" % (tgt(t), reg(m.group(2)), "l" if m.group(3) in ("", "l") else "w")
        # movem: the register mask word precedes the displacement
        t = targets[0] if len(targets) == 1 else addr + (4 if mn.startswith("movem") else 2) + num(m.group(1))
        return "%s(pc)" % tgt(t)
    m = re.fullmatch(r"\((%s),(A\d|SP),([AD]\d|SP)([bwl]?)\*0x1\)" % NUM, op)
    if m:  # d8(An,Xn.s)
        d = num(m.group(1))
        return "%s%s(%s,%s.%s)" % ("-" if d < 0 else "", "$%X" % abs(d), reg(m.group(2)), reg(m.group(3)),
                                   "l" if m.group(4) in ("", "l") else "w")
    m = re.fullmatch(r"\((%s),(A\d|SP)\)" % NUM, op)
    if m:  # d16(An); 0 kept (4 bytes) as 0.w(An), AS shrinks a bare 0 to (An)
        d = num(m.group(1))
        if d == 0:
            return "0.w(%s)" % reg(m.group(2))
        return "%s$%X(%s)" % ("-" if d < 0 else "", abs(d), reg(m.group(2)))
    m = re.fullmatch(r"(-)?\((A\d|SP)\)(\+)?", op)
    if m:
        return "%s(%s)%s" % (m.group(1) or "", reg(m.group(2)), m.group(3) or "")
    if re.fullmatch(r"[AD]\d[bw]?|SP|SR|CCR|USP", op):
        return reg(op) if op[0] in "AD" or op == "SP" else op.lower()
    m = re.fullmatch(NUM, op)
    if m:  # bare number: branch/dbcc target, else moveq/addq/subq immediate
        if mn[0] == "b" and not mn.startswith(("bchg", "bclr", "bset", "btst")) or mn.startswith("db"):
            return tgt(num(op) & 0xFFFFFF)
        v = num(op)
        return "#-$%X" % -v if v < 0 else "#$%X" % v
    raise ValueError("unhandled operand %r" % op)


def mnemonic(mn):
    m = re.fullmatch(r"(b(?:ra|sr|hi|ls|cc|cs|ne|eq|vc|vs|pl|mi|ge|lt|gt|le))\.([bw])", mn)
    return m.group(1) + (".s" if m.group(2) == "b" else ".w") if m else mn


def translate(rid, start, end, raw, rom, names=None, comments=None, stats=None):
    """Raw listing rows -> (AS text, insn count). comments (load_comments()): plate -> `; <text>` line(s) above the
    line at its addr (above its L_ label); eol -> `\\t<insn>\\t; <text> ; $ADDR`. Comments change no bytes.
    Immediates at control ports render over hw.tsv, consts.tsv rows as `#<expr>` (hw_operands; stats for constants.py)."""
    rows = [l.split("\t") for l in raw.split("\n")[1:] if l]
    starts = {int(r[0], 16) for r in rows}
    used = set()
    over = hw_operands(rows, names, rid, stats)

    def label(t):
        if start <= t < end and t in starts:
            used.add(t)
            return "L_%06X" % t
        return None
    body, n = [], 0
    for a, ln, kind, mn, ops, tg in rows:
        a, ln = int(a, 16), int(ln)
        if kind == "data":
            for o in range(a, a + ln, 16):
                chunk = rom[o:min(o + 16, a + ln)]
                body.append((o, "\tdc.b\t%s\t; $%06X" % (",".join("$%02X" % b for b in chunk), o)))
            continue
        targets = [int(t, 16) & 0xFFFFFF for t in tg.split(";") if t]
        ov = over.get(a, {})
        text = ",".join(ov.get(i) or operand(o, mn, a, targets, label, names)
                        for i, o in enumerate(o for o in ops.split("\x1f") if o))
        if re.fullmatch(r"(ori|andi|eori)(\.[bw])?", mn) and "," not in text:  # Ghidra drops ,ccr / ,sr
            text += ",sr" if rom[a + 1] & 0x40 else ",ccr"
        body.append((a, "\t%s%s\t; $%06X" % (mnemonic(mn), "\t" + text if text else "", a)))
        n += 1
    cm = comments or {}
    at = {a for a, _ in body}
    for c in sorted(c for c in cm if start <= c < end and c not in at):
        print("listing %s: comment $%06X not at a line start (unrendered)" % (rid, c))
    lines, seen = [], set()
    for a, line in body:
        c = cm.get(a, {})
        if "plate" in c:
            lines.extend(("; " + p).rstrip() for p in c["plate"].split("\\n"))
        if "eol" in c:  # the `; $ADDR` trailer stays last
            line = line[:line.rindex("\t; $")] + "\t; %s ; $%06X" % (c["eol"].replace("\\n", " "), a)
        if a in used and a not in seen:
            lines.append("L_%06X:" % a)
            seen.add(a)
        lines.append(line)
    return "\n".join(lines) + "\n", n, rows


def self_check(rid, start, end, path, rom):
    """AS header + include hw/ram/rom.inc + org $start + include <path>, asw + p2bin in .run/ghidra/listing/as/; compare with the ROM bytes."""
    d = os.path.join(RUN, "listing", "as")
    os.makedirs(d, exist_ok=True)
    wrap, objp, binp = (os.path.join(d, rid + x) for x in (".asm", ".p", ".bin"))  # asw: <rid>.asm -> <rid>.p
    inc = os.path.relpath(path, d).replace("\\", "/")
    with open(wrap, "w", encoding="ascii", newline="\n") as f:
        f.write("%s%s\torg\t$%06X\n\tinclude\t\"%s\"\n" % (AS_HEADER, "".join("\tinclude\t\"%s\"\n" % i for i in INCS),
                                                           start, inc))
    for p in (objp, binp):
        if os.path.exists(p):
            os.remove(p)
    with open(os.path.join(d, rid + ".asm.log"), "w", encoding="utf-8", errors="replace") as f:
        rc = subprocess.call([os.path.join(ASL, "asw.exe"), "-q", "-xx", "-n", "-U", rid + ".asm"], stdout=f,
                             stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, cwd=d)
        if rc == 0 and os.path.exists(objp):
            rc = subprocess.call([os.path.join(ASL, "p2bin.exe"), rid + ".p", rid + ".bin"], stdout=f,
                                 stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, cwd=d)
    if rc != 0 or not os.path.exists(binp):
        return None, "assembler rc %d, see .run/ghidra/listing/as/%s.asm.log" % (rc, rid)
    with open(binp, "rb") as f:
        got = f.read()
    if len(got) == end:  # flat output padded from 0
        got = got[start:]
    want = rom[start:end]
    if got == want:
        return -1, None
    return next((i for i in range(min(len(got), len(want))) if got[i] != want[i]), min(len(got), len(want))), None


def name_tables(t):
    """split.names_inc() result -> the names argument of translate()/operand() (also used by constants.py)."""
    return {"exact": {r["addr"]: r["name"] for r in t["ram"] + t["code"]}, "ram": t["ram"],
            "structs": t["structs"], "fsize": t["fsize"], "code": {r["addr"]: r["name"] for r in t["code"]},
            "hw": hw_tables(t["hw"]) if t["hw"] else None,
            "consts": {(r["addr"], r["opnd"]): r["expr"] for r in t["consts"]}}


def listing(regions, out, rom, names_dir, no_names=False):
    comments = load_comments()  # exit on non-ASCII text before Ghidra runs
    raw = raw_listing(regions)
    if not raw:
        return 1
    names = name_tables(names_inc(os.path.join(RUN, "listing", "as"), names_dir, no_names))  # exit 1 on a refused name
    with open(rom, "rb") as f:
        data = f.read()
    os.makedirs(out, exist_ok=True)
    rc = 0
    for rid, (s, e) in regions.items():
        with open(os.path.join(raw, rid + ".tsv"), encoding="utf-8") as f:
            text, n, rows = translate(rid, s, e, f.read(), data, names, comments)
        path = os.path.join(out, rid + ".asm")
        with open(path, "w", encoding="ascii", newline="\n") as f:
            f.write(text)
        off, err = self_check(rid, s, e, path, data)
        if err:
            print("listing %s: %d insns, %s" % (rid, n, err))
            rc = 1
        elif off < 0:
            print("listing %s: %d insns, match" % (rid, n))
        else:
            at = next((int(r[0], 16) for r in rows if int(r[0], 16) <= s + off < int(r[0], 16) + int(r[1])), s + off)
            print("listing %s: mismatch at +0x%X (insn at $%06X)" % (rid, off, at))
            rc = 1
    return rc


def mirror(names_dir, conf=CONF):
    """config/names ram.tsv + routines.tsv kind=code rows -> <conf>/symbols.tsv (and functions.tsv names): same addr
    and name -> untouched; same addr -> rename, source names:<file>; new addr -> kind label row. Idempotent."""
    t = names_inc(os.path.join(RUN, "mirror"), names_dir)  # same refusals as the build; hw/consts rows not mirrored
    want = {"0x%06X" % r["addr"]: (r["name"], "ram.tsv") for r in t["ram"]}
    want.update({"0x%06X" % r["addr"]: (r["name"], "routines.tsv") for r in t["code"]})
    syms = [r for _, r in read_tsv(os.path.join(conf, "symbols.tsv"), FILES["symbols.tsv"])]
    funcs = [r for _, r in read_tsv(os.path.join(conf, "functions.tsv"), FILES["functions.tsv"])]
    by_name = {r[1]: r[0] for r in syms}
    by_addr = {r[0]: r for r in syms}
    changed = added = 0
    for a, (name, f) in sorted(want.items()):
        if by_name.get(name, a) != a:
            sys.exit("db: mirror: %s %s: name already used at %s in symbols.tsv" % (a, name, by_name[name]))
        r = by_addr.get(a)
        if r is None:
            syms.append([a, name, "label", "names:" + f])
            added += 1
        elif r[1] != name:
            funcs = [[e, name] if e == a else [e, n] for e, n in funcs]
            r[1], r[3] = name, "names:" + f
            changed += 1
    for fname, rows in (("symbols.tsv", syms), ("functions.tsv", funcs)):
        lines = sorted("\t".join(r) for r in rows)  # Mmtt96Export.java order: fixed-width addr first
        with open(os.path.join(conf, fname), "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\t".join(FILES[fname]) + "\n" + "".join(l + "\n" for l in lines))
    # regions.tsv = config/regions.retail.tsv rows (classify.py merge format), written only when it differs
    with open(os.path.join(ROOT, "config", "regions.retail.tsv"), encoding="utf-8") as f:
        rr = [l.rstrip("\r").split("\t") for l in f.read().split("\n")[1:] if l.strip()]
    text = "\t".join(FILES["regions.tsv"]) + "\n" + "".join(
        "%s\t%s\t%s\t%s; %s; %s\n" % tuple(r[:6]) for r in rr)
    path = os.path.join(conf, "regions.tsv")
    old = open(path, encoding="utf-8", newline="").read() if os.path.isfile(path) else None
    if old != text:
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
    validate(conf)
    print("mirror: %d names, %d renamed, %d added; regions %d%s" % (len(want), changed, added, len(rr),
                                                                   " rewritten" if old != text else ""))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["probe", "rebuild", "export", "roundtrip", "analyse", "listing", "mirror",
                                    "validate"])
    ap.add_argument("ids", nargs="*", help="listing: region ids")
    ap.add_argument("--out", default=os.path.join(ROOT, "asm", "src"))
    ap.add_argument("--rom", default=os.path.join(ROOT, ROM_DEFAULT))
    ap.add_argument("--expect", default=CONF)
    ap.add_argument("--seeds", default=os.path.join(RUN, "seeds.tsv"))
    ap.add_argument("--names", default=os.path.join(ROOT, "config", "names"), help="listing: names dir")
    ap.add_argument("--no-names", action="store_true", help="listing: raw hex everywhere")
    ap.add_argument("--all-code", action="store_true",
                    help="listing: every kind=code region; stale <out>/*.asm deleted first")
    a = ap.parse_intermixed_args(argv)
    if a.cmd == "probe":
        empty = os.path.join(RUN, "empty")  # import of an empty dir: creates/opens ghidra/probe, imports nothing
        os.makedirs(empty, exist_ok=True)
        rc = headless("probe", ["-import", empty, "-noanalysis"], "probe")
        print("Ghidra %s headless: exit %d" % (version(), rc))
        return rc
    if a.cmd == "rebuild":
        return rebuild("mmtt96", a.rom, CONF)
    if a.cmd == "export":
        return export("mmtt96", CONF)
    if a.cmd == "analyse":
        out, done = os.path.join(RUN, "seed"), os.path.join(RUN, "mmtt96_seed.seed.ok")
        if os.path.exists(done):
            os.remove(done)
        rc = rebuild("mmtt96_seed", a.rom, CONF, ["-postScript", "Mmtt96Seed.java", os.path.abspath(a.seeds), out, done])
        if rc or not os.path.exists(done):
            print("db: analyse failed (seed marker missing), see .run/ghidra/mmtt96_seed.rebuild.log;"
                  " ghidra/mmtt96_seed dropped")
            drop_project("mmtt96_seed")
            return 1
        with open(done, encoding="utf-8") as f:
            print("db: analyse " + f.read().strip())
        return 0
    if a.cmd == "listing":
        if a.all_code:
            if a.ids:
                sys.exit("db: listing: --all-code takes no region ids")
            a.ids = code_ids()
            if os.path.isdir(a.out):
                for n in os.listdir(a.out):
                    if n.endswith(".asm"):
                        os.remove(os.path.join(a.out, n))
        if not a.ids:
            sys.exit("db: listing needs at least one region id")
        return listing(regions_by_id(a.ids), a.out, a.rom, a.names, a.no_names)
    if a.cmd == "mirror":
        return mirror(a.names)
    validate(a.expect)
    if a.cmd == "validate":
        print("validate: ok (%s)" % os.path.relpath(a.expect, ROOT))
        return 0
    project = time.strftime("rt_%Y%m%d_%H%M%S")
    out = os.path.join(RUN, "rt")
    if os.path.isdir(out):
        shutil.rmtree(out)
    if rebuild(project, a.rom, CONF) or export(project, out):
        return 2
    rc = compare(out, a.expect)
    if rc == 0:
        drop_project(project)
        print("roundtrip: identical (%s)" % ", ".join(sorted(FILES)))
    return rc


if __name__ == "__main__":
    sys.exit(main())
