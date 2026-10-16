"""Routine signatures over verified code: exact / normalised / sequence layers, groups, fail-closed name propagation.

  signatures.py scan [--rom P] [--out .run/signatures]
  signatures.py propagate --name N --addr A [--member ADDR=NAME ...] [--evidence E] [--rom P] [--registry config/names/routines.tsv]
  signatures.py check [--rom P] [--registry config/names/routines.tsv]
  signatures.py bulk-neutral [--dry-run] [--rom P] [--registry config/names/routines.tsv]
  signatures.py --fixture [--fixture-alter CASE]

Bodies (config/regions.retail.tsv kind=code status=verified; config/ghidra/functions.tsv entries):
  kind function = entry in a verified code region .. min(next entry, region end); bytes before a region's first
  entry are unowned. kind region = each verified code region whole. Coverage assert: function bodies + unowned ==
  verified code bytes, no byte in two bodies (exit 2 otherwise). Linear decode from the body start; an insn
  crossing the body end counts as an overrun and is tokenised whole.
Layers: exact = sha1(body bytes); normalised = sha1 of per-insn tokens (mnemonic with size, insn size, operand
  type/mode/regs/index/d16-d8 An displacements/immediates) with absolute addresses, branch and PC displacements and
  address-like .l immediates (value&0xFFFFFF < 0x100000 or >= 0xFF0000) masked; sequence = sha1 of the mnemonic-class
  skeleton (census `sweep`). Group id = f|r + E|N|S + first 10 hex of the layer hash; a group = >= 2 bodies.
  Sequence groups are families: reported, never propagated.
propagate: names the function at entry A and every member of its normalised group, only if every member passes
  (1) layer hash recomputed from --rom, (2) `db.py listing --names .run/signatures/names` self-check match of its
  region, (3) `make build SRC=.run/signatures/src NAMES=.run/signatures/names` hash OK. Gates 2+3 read a scratch
  copy of the registry's dir with the candidate registry written there; the real registry is written only after all
  gates pass and only if unchanged during the run; any failure never touches it, exit 1. Control: --plant-gate3
  appends one line AS rejects to a scratch src .asm after gate 2, so propagate refuses at gate 3. Members are named
  <N>_<ADDR6>; repeatable --member ADDR=NAME names that member NAME instead, refused (exit 1, registry untouched)
  when ADDR is not a non-anchor member of the group or NAME is not lower_snake, a bare mnemonic word or a duplicate
  (registry clashes refuse as for any name).
bulk-neutral: one exact-layer row `fn_<addr6 lower>` per function body without a registry row whose functions.tsv
  name is the Ghidra default fn_<ADDR6> (other names: skip-named); an unregistered default member of an N-group with
  a non-neutral member is named `<seed>_<addr6 lower>`. Gated once per batch (gate 1 exact hash from --rom, gate 2
  listing self-check of every target region, gate 3 make build, both on the scratch names copy as for propagate);
  any failure or clash refuses the batch; the real registry is written only after all gates pass.
check: every registry row still a function body in verified code with equal region, sighash and group id; exit 1
  on drift.
Firewall: stdout carries counts, ids, names and group ids only; detail goes to the ignored --out dir.
Stdlib + capstone (decoder: scripts/oracle/boundaries.py).
"""
import argparse
import bisect
import hashlib
import os
import re
import shutil
import subprocess
import sys

from capstone import m68k

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "scripts", "oracle"))
sys.path.insert(0, os.path.join(ROOT, "scripts", "census"))
sys.path.insert(0, os.path.join(ROOT, "scripts", "health"))
from boundaries import decode, _MD, MASK, ROM_DEFAULT  # noqa: E402
from census import load_regions, REGIONS_HEADER  # noqa: E402
from asm_leak import MNEMONICS  # noqa: E402

REGIONS = os.path.join(ROOT, "config", "regions.retail.tsv")
FUNCTIONS = os.path.join(ROOT, "config", "ghidra", "functions.tsv")
REGISTRY = os.path.join(ROOT, "config", "names", "routines.tsv")
OUT = os.path.join(ROOT, ".run", "signatures")
FUNCTIONS_HEADER = "entry\tname"
REGISTRY_HEADER = "addr\tname\tkind\tgroup\tlayer\tsighash\tregion\tevidence"
LAYERS = (("E", "exact"), ("N", "normalised"), ("S", "sequence"))
LAYER_LETTER = {"exact": "E", "normalised": "N"}
NAME_RE = re.compile(r"[a-z][a-z0-9_]*\Z")
MNEMONIC_RE = re.compile(r"(?:%s)\Z" % MNEMONICS, re.IGNORECASE)
ABS = (m68k.M68K_AM_ABSOLUTE_DATA_SHORT, m68k.M68K_AM_ABSOLUTE_DATA_LONG)
PCREL = (m68k.M68K_AM_PCI_DISP, m68k.M68K_AM_PCI_INDEX_8_BIT_DISP, m68k.M68K_AM_PCI_INDEX_BASE_DISP,
         m68k.M68K_AM_PC_MEMI_POST_INDEX, m68k.M68K_AM_PC_MEMI_PRE_INDEX)


def sha1(b):
    return hashlib.sha1(b).hexdigest()


def gid(kind, letter, h):
    return ("f" if kind == "function" else "r") + letter + h[:10]


# ---- decode ----

def op_token(op, long_size):
    t, am = op.type, op.address_mode
    if t == m68k.M68K_OP_BR_DISP:
        return "br:%d" % op.br_disp.disp_size
    if t == m68k.M68K_OP_REG:
        return "r:%d:%d" % (am, op.reg)
    if t == m68k.M68K_OP_REG_BITS:
        return "rb:%X" % op.register_bits
    if t == m68k.M68K_OP_REG_PAIR:
        return "rp:%d:%d" % (op.reg_pair.reg_0, op.reg_pair.reg_1)
    if am in ABS:
        return "a:%d:*" % am
    if t == m68k.M68K_OP_IMM:
        v = op.imm & 0xFFFFFFFF
        if long_size and ((v & MASK) < 0x100000 or (v & MASK) >= 0xFF0000):
            return "i:*"
        return "i:%X" % v
    if t == m68k.M68K_OP_MEM:
        m = op.mem
        disp = "*" if am in PCREL else "%d" % m.disp
        return "m:%d:%d:%d:%d:%d:%s" % (am, m.base_reg, m.index_reg, m.index_size, m.scale, disp)
    return "o:%d:%d" % (t, am)


class Decoder:
    """Per-ROM insn cache: pos -> (size, mnemonic class, normalised token)."""

    def __init__(self, rom):
        self.rom, self.cache = rom, {}

    def insn(self, pos):
        c = self.cache.get(pos)
        if c is None:
            n, cls, _ = decode(self.rom, pos)
            if cls == "invalid":
                tok = "invalid:%s" % self.rom[pos:pos + 2].hex()
            else:
                ins = next(_MD.disasm(self.rom[pos:pos + 10], pos, count=1))
                assert ins.size == n
                mn = ins.mnemonic.lower()
                lsz = mn.endswith(".l")
                tok = "%s|%d|%s" % (mn, n, ",".join(op_token(o, lsz) for o in ins.operands))
            c = self.cache[pos] = (n, cls, tok)
        return c

    def body(self, s, e):
        """-> (exact, normalised, sequence, overrun)"""
        toks, sk, pos, over = [], [], s, 0
        while pos < e:
            n, cls, tok = self.insn(pos)
            toks.append(tok)
            sk.append(cls)
            if pos + n > e:
                over = 1
            pos += n
        return (sha1(self.rom[s:e]), sha1("\n".join(toks).encode()), sha1("\n".join(sk).encode()), over)


# ---- model ----

def load_functions(path):
    with open(path, encoding="utf-8") as f:
        lines = f.read().split("\n")
    if lines[0].rstrip("\r") != FUNCTIONS_HEADER:
        sys.exit("signatures: %s: bad header" % path)
    out = []
    for l in lines[1:]:
        l = l.rstrip("\r")
        if l:
            a, n = l.split("\t")
            out.append((int(a, 16), n))
    return sorted(out)


def model(rom, regions_path, functions_path):
    """Bodies, coverage and groups. Exits 2 on a coverage failure."""
    code = [r for r in load_regions(regions_path) if r["kind"] == "code" and r["status"] == "verified"]
    total_rows, total_bytes = len(code), sum(r["end"] - r["start"] for r in code)
    starts = [r["start"] for r in code]
    funcs = load_functions(functions_path)
    entries = [a for a, _ in funcs]
    dec = Decoder(rom)
    bodies, unowned, unowned_regions, outside = [], 0, 0, 0
    for i, (a, name) in enumerate(funcs):
        k = bisect.bisect_right(starts, a) - 1
        if k < 0 or not code[k]["start"] <= a < code[k]["end"]:
            outside += 1
            continue
        r = code[k]
        e = min(entries[i + 1] if i + 1 < len(entries) else r["end"], r["end"])
        bodies.append({"kind": "function", "id": name, "start": a, "end": e, "region": r["id"]})
    for r in code:
        first = next((b["start"] for b in bodies if b["region"] == r["id"]), r["end"])
        if first > r["start"]:
            unowned += first - r["start"]
            unowned_regions += 1
        bodies.append({"kind": "region", "id": r["id"], "start": r["start"], "end": r["end"], "region": r["id"]})
    fb = sorted((b for b in bodies if b["kind"] == "function"), key=lambda b: b["start"])
    owned = sum(b["end"] - b["start"] for b in fb)
    overlap = sum(1 for x, y in zip(fb, fb[1:]) if y["start"] < x["end"])
    if owned + unowned != total_bytes or overlap:
        print("signatures: coverage FAIL: bodies %d + unowned %d != %d or %d overlaps"
              % (owned, unowned, total_bytes, overlap))
        sys.exit(2)
    for b in bodies:
        b["E"], b["N"], b["S"], b["over"] = dec.body(b["start"], b["end"])
    groups = {}
    for kind in ("function", "region"):
        for L, _ in LAYERS:
            by = {}
            for b in bodies:
                if b["kind"] == kind:
                    by.setdefault(b[L], []).append(b)
            for h, mem in by.items():
                for b in mem:
                    b["g" + L], b["n" + L] = gid(kind, L, h), len(mem)
                if len(mem) >= 2:
                    groups[gid(kind, L, h)] = (kind, L, sorted(mem, key=lambda b: b["start"]))
    return {"bodies": bodies, "groups": groups, "rows": total_rows, "bytes": total_bytes, "owned": owned,
            "unowned": unowned, "unowned_regions": unowned_regions, "outside": outside, "dec": dec}


def ranked(m, kind, L):
    gs = [(g, mem) for g, (k, l, mem) in m["groups"].items() if k == kind and l == L]
    return sorted(gs, key=lambda x: (-len(x[1]), x[1][0]["start"], x[0]))


# ---- scan ----

def scan(a):
    with open(a.rom, "rb") as f:
        rom = f.read()
    m = model(rom, REGIONS, FUNCTIONS)
    os.makedirs(a.out, exist_ok=True)
    bodies = sorted(m["bodies"], key=lambda b: (b["kind"], b["start"]))
    with open(os.path.join(a.out, "functions.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("kind\tid\tregion\tstart\tend\tsize\toverrun\texact\tnormalised\tsequence\tgE\tgN\tgS\tnE\tnN\tnS\n")
        for b in bodies:
            f.write("%s\t%s\t%s\t0x%06X\t0x%06X\t%d\t%d\t%s\t%s\t%s\t%s\t%s\t%s\t%d\t%d\t%d\n" % (
                b["kind"], b["id"], b["region"], b["start"], b["end"], b["end"] - b["start"], b["over"],
                b["E"], b["N"], b["S"], b["gE"], b["gN"], b["gS"], b["nE"], b["nN"], b["nS"]))
    with open(os.path.join(a.out, "groups.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("group\tkind\tlayer\tsize\tmembers\n")
        for g in sorted(m["groups"]):
            k, L, mem = m["groups"][g]
            f.write("%s\t%s\t%s\t%d\t%s\n" % (g, k, L, len(mem), ";".join(b["id"] for b in mem)))
    nf = sum(1 for b in m["bodies"] if b["kind"] == "function")
    out = ["signatures: verified code %d rows %d bytes" % (m["rows"], m["bytes"]),
           "coverage: function bodies %d (%d bytes) + unowned %d bytes in %d regions = %d; entries outside verified code %d"
           % (nf, m["owned"], m["unowned"], m["unowned_regions"], m["bytes"], m["outside"]),
           "overrun: function %d region %d" % tuple(sum(b["over"] for b in m["bodies"] if b["kind"] == k)
                                                   for k in ("function", "region"))]
    for kind in ("function", "region"):
        for L, lname in LAYERS:
            gs = ranked(m, kind, L)
            out.append("%s %s: %d groups, %d bodies in groups, largest %d" % (
                kind, lname, len(gs), sum(len(x[1]) for x in gs), len(gs[0][1]) if gs else 0))
    for kind in ("function", "region"):
        for L, lname in LAYERS:
            for g, mem in ranked(m, kind, L)[:10]:
                ids = [b["id"] for b in mem]
                more = " +%d more" % (len(ids) - 8) if len(ids) > 8 else ""
                out.append("top %s %s: %s n=%d %s%s" % (kind, lname, g, len(ids), " ".join(ids[:8]), more))
    with open(os.path.join(a.out, "summary.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out) + "\n")
    print("\n".join(out))
    return 0


# ---- registry ----

def read_registry(path):
    with open(path, encoding="utf-8", newline="") as f:
        lines = f.read().split("\n")
    if lines[0].rstrip("\r") != REGISTRY_HEADER:
        sys.exit("signatures: %s: bad header" % path)
    rows = []
    for l in lines[1:]:
        l = l.rstrip("\r")
        if l:
            c = l.split("\t")
            if len(c) != 8:
                sys.exit("signatures: %s: row with %d fields" % (path, len(c)))
            rows.append(dict(zip(REGISTRY_HEADER.split("\t"), c)))
    return rows


def check(a):
    rows = read_registry(a.registry)
    if not rows:
        print("check: 0 rows")
        return 0
    with open(a.rom, "rb") as f:
        rom = f.read()
    m = model(rom, REGIONS, FUNCTIONS)
    fb = {b["start"]: b for b in m["bodies"] if b["kind"] == "function"}
    drift = []
    for r in rows:
        b = fb.get(int(r["addr"], 16))
        L = LAYER_LETTER.get(r["layer"])
        ok = (b is not None and L is not None and r["kind"] == "code" and b["region"] == r["region"]
              and b["N"][:16] == r["sighash"] and gid("function", L, b[L]) == r["group"])
        if not ok:
            drift.append(r["name"])
    print("check: %d rows, %d ok, %d drift" % (len(rows), len(rows) - len(drift), len(drift)))
    for n in drift:
        print("check: drift %s" % n)
    return 1 if drift else 0


def log_run(cmd, log):
    with open(log, "a", encoding="utf-8", newline="\n") as f:
        p = subprocess.run(cmd, cwd=ROOT, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT)
        out = p.stdout.decode("utf-8", errors="replace")
        f.write("$ %s\n%s[exit %d]\n" % (" ".join(cmd), out, p.returncode))
    return p.returncode, out


def gates23(registry, cand, rids, rom, log, plant=False):
    """Scratch names dir .run/signatures/names (copy of dirname(registry), candidate registry written there);
    gate 2 = db.py listing of rids --names <scratch>, gate 3 = make build SRC=<src> NAMES=<scratch>.
    Returns (gate, rc, region ids that failed gate 2) with gate 0 on success. The real registry is never touched.
    plant (gate-3 control): after gate 2 passes, one line AS rejects is appended to the first scratch src .asm."""
    names, src = os.path.join(OUT, "names"), os.path.join(OUT, "src")
    try:
        for d in (names, src):
            shutil.rmtree(d, ignore_errors=True)
            os.makedirs(d)
        rdir = os.path.dirname(os.path.abspath(registry))
        for f in sorted(os.listdir(rdir)):
            if os.path.isfile(os.path.join(rdir, f)):
                shutil.copyfile(os.path.join(rdir, f), os.path.join(names, f))
        with open(os.path.join(names, os.path.basename(registry)), "wb") as f:
            f.write(cand)
        rc, out = log_run([sys.executable, os.path.join(ROOT, "scripts", "ghidra", "db.py"), "listing"] + rids
                          + ["--out", src, "--rom", os.path.abspath(rom), "--names", names], log)
        matched = {l.split()[1].rstrip(":") for l in out.splitlines() if l.startswith("listing ") and l.endswith(", match")}
        bad = [r for r in rids if rc != 0 or r not in matched]
        if bad:
            return 2, rc, bad
        if plant:
            with open(os.path.join(src, rids[0] + ".asm"), "a", encoding="utf-8", newline="\n") as f:
                f.write("\tplant_gate3_not_an_op\n")
        rel = lambda p: os.path.relpath(p, ROOT).replace("\\", "/")  # noqa: E731
        rc, out = log_run([os.environ.get("MAKE") or "make", "build", "SRC=" + rel(src), "NAMES=" + rel(names)], log)
        if rc != 0 or "build/mmtt96.bin: OK" not in out:
            return 3, rc, []
        return 0, 0, []
    finally:
        shutil.rmtree(src, ignore_errors=True)
        shutil.rmtree(names, ignore_errors=True)


def registry_text(rows):
    cols = REGISTRY_HEADER.split("\t")
    return (REGISTRY_HEADER + "\n" + "".join("\t".join(r[c] for c in cols) + "\n" for r in rows)).encode("utf-8")


def propagate(a):
    if not NAME_RE.match(a.name) or MNEMONIC_RE.match(a.name):
        print("propagate: refused: name not lower_snake or a bare mnemonic word")
        return 1
    addr = int(a.addr, 16)
    with open(a.registry, "rb") as f:
        before = f.read()
    rows = read_registry(a.registry)
    with open(os.path.join(ROOT, ROM_DEFAULT), "rb") as f:
        m = model(f.read(), REGIONS, FUNCTIONS)
    anchor = next((b for b in m["bodies"] if b["kind"] == "function" and b["start"] == addr), None)
    if anchor is None:
        print("propagate: refused: 0x%06X is not a function entry in verified code" % addr)
        return 1
    members = sorted((b for b in m["bodies"] if b["kind"] == "function" and b["N"] == anchor["N"]),
                     key=lambda b: b["start"])
    names = {b["start"]: a.name if b is anchor else "%s_%06X" % (a.name, b["start"]) for b in members}
    for spec in a.member or []:
        ma, _, mn = spec.partition("=")
        try:
            ms = int(ma, 16)
        except ValueError:
            ms = None
        if ms is None or ms not in names or ms == addr:
            print("propagate: refused: --member %s is not a non-anchor member of group %s"
                  % (ma, gid("function", "N", anchor["N"])))
            return 1
        if not NAME_RE.match(mn) or MNEMONIC_RE.match(mn) or mn in names.values():
            print("propagate: refused: --member name %s not lower_snake, a bare mnemonic word or a duplicate" % mn)
            return 1
        names[ms] = mn
    have_n, have_a = {r["name"] for r in rows}, {int(r["addr"], 16) for r in rows}
    clash = [n for n in names.values() if n in have_n] + ["0x%06X" % s for s in names if s in have_a]
    if clash:
        print("propagate: refused: already in registry: %s" % " ".join(clash))
        return 1
    os.makedirs(OUT, exist_ok=True)
    log = os.path.join(OUT, "propagate.log")
    # gate 1: layer hash recomputed from --rom
    with open(a.rom, "rb") as f:
        dec = Decoder(f.read())
    layer = {}
    for b in members:
        L = "E" if b["E"] == anchor["E"] else "N"
        layer[b["start"]] = L
        got = dec.body(b["start"], b["end"])[0 if L == "E" else 1]
        if got != b[L]:
            print("propagate: refused: member %s gate 1 (%s hash)" % (b["id"], "exact" if L == "E" else "normalised"))
            return 1
    ng = gid("function", "N", anchor["N"])
    ev = a.evidence or "sig:%s anchor 0x%06X" % (ng, addr)
    new = [{"addr": "0x%06X" % b["start"], "name": names[b["start"]], "kind": "code",
            "group": gid("function", layer[b["start"]], b[layer[b["start"]]]),
            "layer": "exact" if layer[b["start"]] == "E" else "normalised", "sighash": b["N"][:16],
            "region": b["region"], "evidence": ev} for b in members]
    cand = registry_text(sorted(rows + new, key=lambda r: (int(r["addr"], 16), r["name"])))
    # gate 2: listing self-check of every member region; gate 3: build from that source, hash OK; both against the
    # candidate in a scratch names dir (gates23), the real registry is written only after both pass
    rids = sorted({b["region"] for b in members})
    gate, rc, badr = gates23(a.registry, cand, rids, a.rom, log, a.plant_gate3)
    if gate == 2:
        bad = [b["id"] for b in members if b["region"] in badr]
        print("propagate: refused: member %s gate 2 (listing self-check, db.py exit %d)" % (" ".join(bad), rc))
        return 1
    if gate == 3:
        print("propagate: refused: member %s gate 3 (make build exit %d)" % (" ".join(b["id"] for b in members), rc))
        return 1
    with open(a.registry, "rb") as f:
        if f.read() != before:
            print("propagate: refused: registry changed during the run")
            return 1
    with open(a.registry, "wb") as f:
        f.write(cand)
    print("propagate: %s: %d members named (group %s, %d exact, %d normalised)" % (
        a.name, len(new), ng, sum(1 for r in new if r["layer"] == "exact"),
        sum(1 for r in new if r["layer"] == "normalised")))
    return 0


DEFAULT_RE = re.compile(r"fn_[0-9A-Fa-f]{6}\Z")


def bulk_neutral(a):
    with open(a.registry, "rb") as f:
        before = f.read()
    rows = read_registry(a.registry)
    with open(os.path.join(ROOT, ROM_DEFAULT), "rb") as f:
        m = model(f.read(), REGIONS, FUNCTIONS)
    have_a = {int(r["addr"], 16): r["name"] for r in rows}
    fb = sorted((b for b in m["bodies"] if b["kind"] == "function"), key=lambda b: b["start"])
    default = {b["start"]: b["id"] == "fn_%06X" % b["start"] for b in fb}
    targets = [b for b in fb if b["start"] not in have_a and default[b["start"]]]
    skip = sum(1 for b in fb if b["start"] not in have_a and not default[b["start"]])
    # named-group fan-out: an N-group with a non-neutral member and unregistered default members
    label = lambda b: have_a.get(b["start"], b["id"])  # noqa: E731
    names, fan = {b["start"]: "fn_%06x" % b["start"] for b in targets}, 0
    for g, (k, L, mem) in sorted(m["groups"].items()):
        if k != "function" or L != "N":
            continue
        seeds = [label(b) for b in mem if not DEFAULT_RE.match(label(b))]
        open_ = [b for b in mem if b["start"] in names]
        if seeds and open_:
            fan += 1
            for b in open_:
                names[b["start"]] = "%s_%06x" % (seeds[0], b["start"])
    print("bulk-neutral: fan-out groups %d" % fan)
    # clashes: registry, ram.tsv, region ids (case-insensitive), NAME_RE / MNEMONIC_RE
    taken = {r["name"].lower() for r in rows} | {r["id"].lower() for r in load_regions(REGIONS)}
    ram = os.path.join(os.path.dirname(a.registry), "ram.tsv")
    if os.path.isfile(ram):
        with open(ram, encoding="utf-8") as f:
            ls = [l.rstrip("\r").split("\t") for l in f.read().split("\n") if l.strip()]
        ni = ls[0].index("name")
        taken |= {l[ni].lower() for l in ls[1:]}
    clash = sorted(n for n in names.values() if n.lower() in taken or not NAME_RE.match(n) or MNEMONIC_RE.match(n))
    if len({n.lower() for n in names.values()}) != len(names):
        clash.append("duplicate")
    if clash:
        print("bulk-neutral: refused: clash %s" % " ".join(clash))
        return 1
    if a.dry_run or not targets:
        print("bulk-neutral: %d named, skip-named %d%s" % (0 if not targets else len(targets), skip,
                                                           " (dry-run)" if a.dry_run else ""))
        return 0
    new = [{"addr": "0x%06X" % b["start"], "name": names[b["start"]], "kind": "code",
            "group": gid("function", "E", b["E"]), "layer": "exact", "sighash": b["N"][:16],
            "region": b["region"], "evidence": "T8 bulk neutral entry"} for b in targets]
    cand = registry_text(sorted(rows + new, key=lambda r: (int(r["addr"], 16), r["name"])))
    os.makedirs(OUT, exist_ok=True)
    log = os.path.join(OUT, "bulk_neutral.log")
    # gate 1: exact hash of every target recomputed from --rom
    with open(a.rom, "rb") as f:
        dec = Decoder(f.read())
    bad = ["0x%06X" % b["start"] for b in targets if dec.body(b["start"], b["end"])[0] != b["E"]]
    if bad:
        print("bulk-neutral: refused: gate1 %s" % " ".join(bad))
        return 1
    # gates 2+3 run against the candidate in a scratch names dir (gates23); the real registry is written only after
    rids = sorted({b["region"] for b in targets})
    gate, rc, bad = gates23(a.registry, cand, rids, a.rom, log)
    if gate == 2:
        print("bulk-neutral: refused: gate2 %s" % " ".join(bad))
        return 1
    if gate == 3:
        print("bulk-neutral: refused: gate3 make build exit %d" % rc)
        return 1
    with open(a.registry, "rb") as f:
        if f.read() != before:
            print("bulk-neutral: refused: registry changed during the run")
            return 1
    with open(a.registry, "wb") as f:
        f.write(cand)
    print("bulk-neutral: %d named, skip-named %d" % (len(new), skip))
    return 0


# ---- fixture ----

def fixture(alter, out):
    """Synthetic ROM (hand-made 68000 sequences, not game bytes) with planted answers; exit 1 on any wrong answer."""
    d = os.path.join(out, "fixture")
    os.makedirs(d, exist_ok=True)
    rom = bytearray(0x200)
    funcs = [
        (0x014, "f1", "30010640" "00034E75"),                          # exact pair with f2
        (0x01C, "f2", "30010640" "00034E75"),
        (0x024, "f3", "4EB90001" "23403039" "00FF0010" "207C00FF" "80004E75"),  # abs.l targets / .l address imm
        (0x038, "f4", "4EB90001" "56703039" "00FF0020" "207C00FF" "81004E75"),  # differ only in those from f3
        (0x080, "f5", "36025243" "E54B4E75"),                          # skeleton pair with f6 (regs, imms differ)
        (0x088, "f6", "3A045445" "E74D4E75"),
        (0x090, "u1", "4E714E71" "70054E75"),                          # unique
        (0x004, "x0", "4E75"),                                        # entry in a data region: outside
    ]
    for a, _, hx in funcs:
        b = bytes.fromhex(hx)
        rom[a:a + len(b)] = b
    rom[0x010:0x014] = bytes.fromhex("4E714E71")                      # unowned prefix of R1
    layout = [(0x000, 0x010, "data", "D0"), (0x010, 0x04C, "code", "R1"), (0x04C, 0x080, "data", "D1"),
              (0x080, 0x098, "code", "R2"), (0x098, 0x200, "data", "D2")]
    with open(os.path.join(d, "rom.bin"), "wb") as f:
        f.write(rom)
    rp, fp = os.path.join(d, "regions.tsv"), os.path.join(d, "functions.tsv")
    with open(rp, "w", encoding="utf-8", newline="\n") as f:
        f.write(REGIONS_HEADER + "\n" + "".join("0x%06X\t0x%06X\t%s\t%s\tverified\tfixture\n" % r for r in layout))
    with open(fp, "w", encoding="utf-8", newline="\n") as f:
        f.write(FUNCTIONS_HEADER + "\n" + "".join("0x%06X\t%s\n" % (a, n) for a, n, _ in sorted(funcs)))
    m = model(bytes(rom), rp, fp)
    b = {x["id"]: x for x in m["bodies"] if x["kind"] == "function"}

    def grp(i, L):
        return b[i]["g" + L] if b[i]["n" + L] >= 2 else None

    got = {"exact": (grp("f1", "E") is not None and grp("f1", "E") == grp("f2", "E"),
                     [x["id"] for x in m["groups"].get(grp("f1", "E"), (0, 0, []))[2]]),
           "abs": (grp("f3", "N") is not None and grp("f3", "N") == grp("f4", "N"), grp("f3", "E"), grp("f4", "E")),
           "skeleton": (grp("f5", "S") is not None and grp("f5", "S") == grp("f6", "S"), grp("f5", "N"), grp("f5", "E")),
           "unique": tuple(grp("u1", L) for L in "ENS"),
           "coverage": (m["unowned"], m["unowned_regions"], m["outside"], m["owned"] + m["unowned"], m["bytes"])}
    want = {"exact": (True, ["f1", "f2"]), "abs": (True, None, None), "skeleton": (True, None, None),
            "unique": (None, None, None), "coverage": (4, 1, 1, 0x3C + 0x18, 0x3C + 0x18)}
    if alter:
        if alter not in want:
            sys.exit("signatures: --fixture-alter: unknown case %s (cases: %s)" % (alter, " ".join(sorted(want))))
        want[alter] = ("altered", want[alter])
    bad = 0
    for k in sorted(want):
        ok = got[k] == want[k]
        bad += not ok
        print("fixture: %-8s %s" % (k, "ok" if ok else "FAIL"))
    print("fixture: %d/%d cases ok" % (len(want) - bad, len(want)))
    return 1 if bad else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", nargs="?", choices=["scan", "propagate", "check", "bulk-neutral"])
    ap.add_argument("--rom", default=os.path.join(ROOT, ROM_DEFAULT))
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--registry", default=REGISTRY)
    ap.add_argument("--name")
    ap.add_argument("--addr")
    ap.add_argument("--evidence")
    ap.add_argument("--member", action="append", metavar="ADDR=NAME")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--fixture", action="store_true")
    ap.add_argument("--fixture-alter", help=argparse.SUPPRESS)
    ap.add_argument("--plant-gate3", action="store_true", help=argparse.SUPPRESS)
    a = ap.parse_args(argv)
    if a.fixture:
        return fixture(a.fixture_alter, a.out)
    if a.cmd == "scan":
        return scan(a)
    if a.cmd == "check":
        return check(a)
    if a.cmd == "propagate":
        if not a.name or not a.addr:
            ap.error("propagate needs --name and --addr")
        return propagate(a)
    if a.cmd == "bulk-neutral":
        return bulk_neutral(a)
    ap.error("a subcommand or --fixture is required")


if __name__ == "__main__":
    sys.exit(main())
