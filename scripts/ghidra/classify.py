"""Classify the code/data gaps of config/regions.retail.tsv from runtime coverage and a seeded Ghidra analysis.

  seeds   write .run/ghidra/seeds.tsv (addr kind): entry = vector targets, 0x000200, 0x015918, 0x035416, 0x03544A,
          config/ghidra/functions.tsv entries; flow = decruncher call sites (jsr/bsr to 0x035416 found by a ROM scan,
          plus decrunch_natural.tsv return addresses) and every config/oracle/coverage.tsv row start
  merge   from .run/ghidra/seed/ (db.py analyse) + coverage.tsv: replace the rows inside GAPS of
          config/regions.retail.tsv with function-level code runs and table-level data runs; mirror config/ghidra/
          functions.tsv, symbols.tsv (kind function) and regions.tsv; print residue counts (config/oracle/decrunch*.tsv
          key parent_start, so renumbering needs no re-key)

Status: code verified iff (executed, or call/jump-reachable from verified code) and Ghidra disassembles it with no
Error bookmark; data verified iff its start is a data-reference target of verified code and nothing in it is executed
or a code-reference target; else inferred with the reason in evidence. Stdlib only.
"""
import argparse
import os
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "scripts", "extract"))
import manifest  # noqa: E402
import rom as romlib  # noqa: E402

RUN = os.path.join(ROOT, ".run", "ghidra")
SEEDS = os.path.join(RUN, "seeds.tsv")
SEED_OUT = os.path.join(RUN, "seed")
REGIONS = os.path.join(ROOT, "config", "regions.retail.tsv")
COVERAGE = os.path.join(ROOT, "config", "oracle", "coverage.tsv")
CONF = os.path.join(ROOT, "config", "ghidra")
DECRUNCH = [os.path.join(ROOT, "config", "oracle", f) for f in ("decrunch.tsv", "decrunch_natural.tsv")]
GAPS = [(0x0002EA, 0x01597A), (0x016DE6, 0x01FACC), (0x020000, 0x0477BA)]
DECRUNCHER = 0x035416
ENTRIES = [0x000200, 0x015918, DECRUNCHER, 0x03544A]
ROM_LIMIT = 0x100000  # Ghidra ROM block


def tsv(path):
    with open(path, encoding="utf-8") as f:
        return [ln.split("\t") for ln in f.read().splitlines()[1:] if ln]


def write_tsv(path, header, rows):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(header) + "\n")
        for r in rows:
            f.write("\t".join(r) + "\n")


def h(n):
    return "0x%06X" % n


def rom_bytes():
    with open(os.path.join(ROOT, manifest.ROM_DEFAULT), "rb") as f:
        return f.read()


def call_sites(data, target):
    """Even addresses of jsr abs.l / jsr d16(pc) / bsr.w / bsr.s whose destination is target."""
    out = []
    for a in range(0x200, min(len(data), ROM_LIMIT) - 6, 2):
        w = struct.unpack_from(">H", data, a)[0]
        if w == 0x4EB9 and struct.unpack_from(">L", data, a + 2)[0] == target:
            out.append(a)
        elif w in (0x6100, 0x4EBA) and a + 2 + struct.unpack_from(">h", data, a + 2)[0] == target:
            out.append(a)
        elif w >> 8 == 0x61 and w & 0xFF not in (0, 0xFF) and a + 2 + struct.unpack_from(">b", data, a + 1)[0] == target:
            out.append(a)
    return out


def seeds():
    data = rom_bytes()
    s = {}
    for v in romlib.parse_vectors(data)[1:]:
        if 0x200 <= v < ROM_LIMIT and v % 2 == 0:  # reset PC 0 is the trace artifact, not code
            s[v] = "entry"
    for a in ENTRIES + [int(r[0], 16) for r in tsv(os.path.join(CONF, "functions.tsv"))]:
        s[a] = "entry"
    sites = call_sites(data, DECRUNCHER)
    rets = {int(r[3], 16) for r in tsv(DECRUNCH[1])}
    for a in sites + sorted(rets) + [int(r[0], 16) for r in tsv(COVERAGE)]:
        s.setdefault(a, "flow")
    os.makedirs(RUN, exist_ok=True)
    text = "addr\tkind\n" + "".join(f"{h(a)}\t{k}\n" for a, k in sorted(s.items()))
    old = open(SEEDS, encoding="utf-8", newline="").read() if os.path.exists(SEEDS) else None
    if old != text:  # missing, truncated or corrupted -> rewritten (newer mtime makes census re-run db.py analyse)
        write_tsv(SEEDS, ["addr", "kind"], [(h(a), k) for a, k in sorted(s.items())])
    print(f"classify: seeds {'unchanged' if old == text else 'rewritten'} {len(s)} (entry {sum(k == 'entry' for k in s.values())}); decruncher call sites "
          f"{len(sites)} by scan ({', '.join(h(a) for a in sites)}), {len(rets)} natural return addresses "
          f"-> {os.path.relpath(SEEDS, ROOT)}")
    return 0


def spans(addrs):
    """Sorted byte addresses -> maximal [start, end) runs."""
    out = []
    for a in sorted(addrs):
        if out and out[-1][1] == a:
            out[-1][1] = a + 1
        else:
            out.append([a, a + 1])
    return out


def generic(name):
    return name.startswith(("FUN_", "thunk_FUN_", "fn_", "code_"))


def load_seed():
    funcs = [(int(e, 16), n, [tuple(int(x, 16) for x in r.split("-")) for r in body.split(";") if r])
             for e, n, body in tsv(os.path.join(SEED_OUT, "functions.tsv"))]
    insns = [(int(s, 16), int(e, 16)) for s, e in tsv(os.path.join(SEED_OUT, "insns.tsv"))]
    refs = [(int(f, 16), int(t, 16), k) for f, t, k in tsv(os.path.join(SEED_OUT, "refs.tsv"))]
    bad = [int(r[0], 16) for r in tsv(os.path.join(SEED_OUT, "bad.tsv"))]
    return funcs, insns, refs, bad


def in_gaps(a):
    return any(lo <= a < hi for lo, hi in GAPS)


def merge():
    funcs, insns, refs, bad = load_seed()
    executed = {}  # byte -> run ids
    for s, e, runs in tsv(COVERAGE):
        for a in range(int(s, 16), int(e, 16)):
            executed[a] = runs.split(";")
    ghidra = {a for s, e in insns for a in range(s, e) if in_gaps(a)}

    # code units: function bodies, then stray instruction runs, then executed bytes Ghidra did not disassemble
    owner, units = {}, []  # byte -> unit index; unit = dict(ranges, entry, name, src)
    for entry, name, body in funcs:
        rs = [(max(s, lo), min(e, hi)) for s, e in body for lo, hi in GAPS if s < hi and e > lo]
        if rs:
            units.append(dict(ranges=rs, entry=entry, name=name, src="ghidra"))
            for s, e in rs:
                for a in range(s, e):
                    owner.setdefault(a, len(units) - 1)
    for src, pool in (("ghidra", ghidra), ("cov", set(executed) - ghidra)):
        for s, e in spans(a for a in pool if a not in owner and in_gaps(a)):
            units.append(dict(ranges=[(s, e)], entry=None, name=None, src=src))
            for a in range(s, e):
                owner[a] = len(units) - 1
    badset = set(bad)
    for u in units:
        u["exec"] = sorted({r for s, e in u["ranges"] for a in range(s, e) for r in executed.get(a, ())})
        u["clean"] = u["src"] == "ghidra" and not any(s <= b <= e for s, e in u["ranges"] for b in badset)
    succ = {}
    for f, t, k in refs:
        if k != "data" and f in owner and t in owner and owner[f] != owner[t]:
            succ.setdefault(owner[f], set()).add(owner[t])
    verified = {i for i, u in enumerate(units) if u["exec"] and u["clean"]}
    todo = list(verified)
    while todo:
        for j in succ.get(todo.pop(), ()):
            if j not in verified and units[j]["clean"]:
                verified.add(j)
                todo.append(j)
    vectors = set(romlib.parse_vectors(rom_bytes())[1:])
    for i, u in enumerate(units):
        cov = "cov:" + ";".join(u["exec"]) if u["exec"] else ""
        if i in verified:
            u["status"], u["why"] = "verified", f"{cov}; ghidra" if cov else "ghidra; xref from verified code; not executed"
        elif u["src"] == "cov":
            u["status"], u["why"] = "inferred", f"{cov}; ghidra did not disassemble"
        elif not u["clean"]:
            u["status"], u["why"] = "inferred", f"ghidra bad instruction in body; {cov or 'not executed'}"
        elif u["entry"] in vectors:
            u["status"], u["why"] = "inferred", "ghidra-only; vector target; not executed"
        else:
            u["status"], u["why"] = "inferred", "ghidra-only; not executed"

    named = {int(r[0], 16): r[1] for r in tsv(os.path.join(CONF, "functions.tsv")) if not generic(r[1])}
    data_refs = {}  # target -> set of source unit statuses
    code_targets = set()
    for f, t, k in refs:
        if in_gaps(t) and t not in owner:
            if k == "data":
                data_refs.setdefault(t, set()).add(units[owner[f]]["status"] if f in owner else "outside")
            else:
                code_targets.add(t)
    new = []  # (start, end, kind, name, status, evidence)
    for lo, hi in GAPS:
        a = lo
        while a < hi:
            if a in owner:
                key = (units[owner[a]]["status"], units[owner[a]]["why"])
                e = a + 1
                while e < hi and e in owner and (units[owner[e]]["status"], units[owner[e]]["why"]) == key \
                        and e not in named:
                    e += 1
                new.append((a, e, "code", named.get(a, "code_%06X" % a), key[0], key[1]))
            else:
                e = a + 1
                while e < hi and e not in owner and e not in data_refs:
                    e += 1
                src = data_refs.get(a, set())
                hit = any(t in code_targets for t in range(a, e))
                if src == {"verified"} and not hit:
                    st, why = "verified", "ghidra; data xref from verified code; not executed"
                elif hit:
                    st, why = "inferred", "ghidra code xref target, not disassembled; not executed"
                elif src:
                    st, why = "inferred", "ghidra; data xref from unverified code; not executed"
                else:
                    st, why = "inferred", "no xref; not executed"
                new.append((a, e, "data", "data_%06X" % a, st, why))
            a = e

    # regions.retail.tsv: drop rows inside GAPS (generated), insert the new rows
    with open(REGIONS, encoding="utf-8") as f:
        lines = f.read().splitlines()
    head, keep = lines[0], []
    for ln in lines[1:]:
        c = ln.split("\t")
        s, e = int(c[0], 16), int(c[1], 16)
        inside = [g for g in GAPS if g[0] <= s and e <= g[1]]
        if any(s < hi and e > lo for lo, hi in GAPS) and not inside:
            sys.exit(f"classify: row {c[3]} {c[0]}-{c[1]} straddles a gap boundary")
        if not inside:
            keep.append(c)
    rows = keep + [[h(s), h(e), k, n, st, ev] for s, e, k, n, st, ev in new]
    rows.sort(key=lambda c: int(c[0], 16))
    write_tsv(REGIONS, head.split("\t"), rows)

    # config/ghidra mirror
    fn = dict(named)
    for entry, name, body in funcs:
        if in_gaps(entry) and entry in owner and entry not in fn and not name.startswith("thunk_"):  # thunks take
            # the thunked function's name in Ghidra, so a fn_ name would not survive the roundtrip
            fn[entry] = "fn_%06X" % entry
    syms = tsv(os.path.join(CONF, "symbols.tsv"))
    labels = {int(r[0], 16) for r in syms if r[2] == "label"}
    clash = sorted(a for a in fn if a in labels)
    for a in clash:
        del fn[a]
    srcs = {int(r[0], 16): r[3] for r in syms if r[2] == "function"}
    syms = [r for r in syms if r[2] == "label"] + [
        [h(a), n, "function", srcs[a] if a in srcs else "ghidra; cov" if units[owner[a]]["exec"] else "ghidra"]
        for a, n in fn.items()]
    write_tsv(os.path.join(CONF, "symbols.tsv"), ["addr", "name", "kind", "source"], sorted(syms))
    write_tsv(os.path.join(CONF, "functions.tsv"), ["entry", "name"], sorted([h(a), n] for a, n in fn.items()))
    write_tsv(os.path.join(CONF, "regions.tsv"), ["start", "end", "type", "note"],
              [[c[0], c[1], c[2], f"{c[3]}; {c[4]}; {c[5]}"] for c in rows])

    # residue
    print(f"classify: {len(new)} rows in gaps; functions mirrored {len(fn)} (label clashes skipped {len(clash)})")
    for kind in ("code", "data"):
        for st in ("verified", "inferred"):
            print(f"classify: {kind} rows {st} {sum(1 for r in new if r[2] == kind and r[4] == st)}")
    for lo, hi in GAPS:
        b = {}
        for s, e, k, n, st, ev in new:
            if lo <= s < hi:
                b[(k, st)] = b.get((k, st), 0) + e - s
        print(f"classify: {lo:06X}-{hi:06X} bytes " + " ".join(
            f"{k}_{st}={b.get((k, st), 0)}/{hi - lo}" for k in ("code", "data") for st in ("verified", "inferred")))
    ex_not_g = sum(1 for a in executed if in_gaps(a) and a not in ghidra)
    g_not_ex = sum(1 for a in ghidra if a not in executed)
    ex_data = sum(1 for a in executed if in_gaps(a) and a not in owner)
    unreached = [u for i, u in enumerate(units) if u["src"] == "ghidra" and i not in verified]
    print(f"classify: disagreements executed-but-data bytes {ex_data}; executed-not-ghidra bytes {ex_not_g}; "
          f"ghidra-code-never-executed bytes {g_not_ex}; unreached ghidra units {len(unreached)} "
          f"({sum(e - s for u in unreached for s, e in u['ranges'])} bytes, unclean {sum(not u['clean'] for u in unreached)})")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["seeds", "merge"])
    a = ap.parse_args(argv)
    return seeds() if a.cmd == "seeds" else merge()


if __name__ == "__main__":
    sys.exit(main())
