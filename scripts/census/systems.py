"""System map and wave queue (plan 1.9 T11): every code row of config/campaign/ledger.tsv -> a game system, then
config/campaign/batches.tsv (the wave queue).

  systems.py {map|show} [--src DIR] [--force]

  map   writes the ledger columns `system` and `system_basis` and config/campaign/batches.tsv. Refuses to rewrite
        batches.tsv when a batch is not `open` unless --force (the waves own the status column).
  show  prints the assignment counts per system and basis, the batches per group, and the doubtful regions; no write.

Assignment, in order:
  located    the region is named in a `Located:` line of docs/mechanics.md (region ids, `code_A to code_B` ranges, fn_
             and group names via config/names/routines.tsv); a region located in several groups takes the group with
             the most sections naming it (tie: earlier group). basis `located: <sections>`.
  proximity  votes per group from the Ghidra refs (.run/ghidra/seed/refs.tsv: call/jump across regions, data refs to
             located tables) and from the listing's RAM operands (--src, default .run/ledger/src from `ledger.py
             write`) against the RAM named in each group's `Located:` lines. Caller of a located region 2 (0 when the
             callee has more than HUB callers), callee of one 1, shared located RAM word 1 (0.5 when more than HUB
             regions use it), located table read 1. Assigned when the best group has >= 2 votes and at least twice the
             runner-up. Up to 3 passes (pass 2+ also counts proximity-assigned regions). basis `proximity<k>: ...`.
  rest       else `rest:<family>`: sound-driver (z80_ regions, Z80 RAM operands), menus (mode word ram_FFE69A), initialisation (reached from
             init/entry only, or VDP setup), decompression (imp_ regions), input (pad ports), attract (executed only in
             the attract coverage run), other. basis `rest: <why>`.
Batches: whole regions; small rows (insns < 50) -> comments-only batches (system `comments-only`, wave T24); the rest
per system in caller-family order (connected components of the system's call graph, largest first, address order
inside), packed to about TARGET instructions. Queue order: the plan's group order, then comments-only, then rest
families. Waves: each mechanics group's first 2 batches -> its wave task; comments-only -> T24; the remaining batches
2 per R wave T25..T31 in queue order (mechanics overflow first); beyond T31 `excess`.
Firewall: ids, names, counts and section titles only. Stdlib only.
"""
import argparse
import math
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from census import REFS, REGIONS, ROOT, load_regions  # noqa: E402

LEDGER = os.path.join(ROOT, "config", "campaign", "ledger.tsv")
BATCHES = os.path.join(ROOT, "config", "campaign", "batches.tsv")
DOC = os.path.join(ROOT, "docs", "mechanics.md")
NAMES = os.environ.get("MMTT96_NAMES") or os.path.join(ROOT, "config", "names")
COVERAGE = os.path.join(ROOT, "config", "oracle", "coverage.tsv")
BHEADER = "batch order system wave route kind regions insns status".split()
GROUPS = ["view-and-scrolling", "rules", "course", "collisions", "vehicle-handling", "data"]
WAVES = {"view-and-scrolling": "T12", "rules": "T14", "course": "T16", "collisions": "T18",
         "vehicle-handling": "T20", "data": "T22"}
RWAVES = ["T%d" % n for n in range(25, 32)]
FAMILIES = ["menus", "sound-driver", "music-effects", "attract", "input", "initialisation", "decompression", "other"]
SMALL, TARGET, HUB = 50, 1500, 8
# Located in several groups: the group whose section names the region's main role (judgement, T11); else by count.
OVERRIDE = {
    "code_01CE34": ("data", "course setup; the other sections read what it copies"),
    "code_001978": ("data", "kit race setup"),
    "code_004D34": ("data", "EEPROM access of the kit; eight-car collision copy not reached"),
    "code_005426": ("data", "EEPROM image transfer of the kit"),
    "code_01F4F0": ("course", "lap count and quarter flags"),
    "code_042012": ("vehicle-handling", "computer driver (opponent AI)"),
}
TOK = re.compile(r"\b(?:code|data|fn|ram|imp|img|z80|vdp)_\w+|\bslot\w+|\b[0-9A-F]{6}\b")
IDENT = re.compile(r"(?<![\w.$])[A-Za-z_]\w*")
HEXOP = re.compile(r"(#?)(-?)\$([0-9A-Fa-f]+)(\(\s*(?:a[0-7]|sp)\b)?")


def tsv(path):
    with open(path, encoding="utf-8") as f:
        lines = [l.rstrip("\r") for l in f.read().split("\n")]
    cols = lines[0].split("\t")
    return cols, [dict(zip(cols, l.split("\t"))) for l in lines[1:] if l]


class Map:
    def __init__(self, src):
        self.regions = load_regions(REGIONS)
        self.cols, self.rows = tsv(LEDGER)
        self.code = [r for r in self.rows if r["kind"] == "code"]
        self.reg = {r["id"]: r for r in self.regions}
        self.starts = [(r["start"], r["end"], r["id"]) for r in self.regions]
        _, rt = tsv(os.path.join(NAMES, "routines.tsv"))
        self.rname = {r["name"]: r["region"] for r in rt}
        _, ram = tsv(os.path.join(NAMES, "ram.tsv"))
        self.ram = {r["name"]: (int(r["addr"], 16), int(r["size"], 16)) for r in ram}
        self.src = src
        self.graph()

    def region_of(self, a):
        lo, hi = 0, len(self.starts)
        while lo < hi:
            m = (lo + hi) // 2
            if self.starts[m][1] <= a:
                lo = m + 1
            else:
                hi = m
        return self.starts[lo][2] if lo < len(self.starts) and self.starts[lo][0] <= a else None

    def graph(self):
        code = {r["id"] for r in self.code}
        self.calls = defaultdict(set)   # caller region -> callee regions (call/jump across regions)
        self.reads = defaultdict(set)   # region -> data regions it references
        _, refs = tsv(REFS)
        for r in refs:
            f, t = self.region_of(int(r["from"], 16)), self.region_of(int(r["to"], 16))
            if f in code and t and t != f:
                (self.calls if t in code and r["type"] != "data" else self.reads)[f].add(t)
        self.callers = defaultdict(set)
        for f, ts in self.calls.items():
            for t in ts:
                self.callers[t].add(f)
        self.ramuse = defaultdict(set)  # region -> RAM addresses its operands name
        for r in self.code:
            p = os.path.join(self.src, r["id"] + ".asm")
            if not os.path.exists(p):
                sys.exit("systems: %s missing; run ledger.py write first" % os.path.relpath(p, ROOT))
            with open(p, encoding="ascii") as fh:
                for line in fh.read().split("\n"):
                    st = line.strip()
                    if not st or st.startswith(";") or st.endswith(":"):
                        continue
                    f_ = line.split(";")[0].strip().split("\t")
                    ops = f_[1].strip() if len(f_) > 1 else ""
                    for m in IDENT.finditer(HEXOP.sub(" ", ops)):
                        t = m.group(0)
                        if t in self.ram:
                            self.ramuse[r["id"]].add(self.ram[t][0])
                        elif t in self.rname and self.rname[t] != r["id"]:
                            self.calls[r["id"]].add(self.rname[t])
                            self.callers[self.rname[t]].add(r["id"])
                    for m in HEXOP.finditer(ops):
                        if not (m.group(1) or m.group(2) or m.group(4)):
                            v = int(m.group(3), 16)
                            v = v | 0xFF0000 if ops[m.end():].startswith(").w") and v >= 0x8000 else v
                            if v >= 0xA00000:
                                self.ramuse[r["id"]].add(v & 0xFFFFFF)

    def located(self):
        """docs/mechanics.md Located: lines -> {group: {sections, regions{id: [sections]}, ram set, tables}}."""
        with open(DOC, encoding="utf-8") as f:
            lines = f.read().split("\n")
        grp, sec, par, out = None, None, None, []
        for l in lines + [""]:
            m = re.match(r"## Group (\d+):", l)
            if m:
                grp = int(m.group(1)) - 1
            elif l.startswith("### "):
                sec = l[4:].split(" (")[0]
            elif l.startswith("Located:"):
                par = [l[8:]]
            elif par is not None and l.strip():
                par.append(l)
            elif par is not None:
                out.append((grp, sec, " ".join(par)))
                par = None
        loc = {g: dict(regions=defaultdict(list), ram=set(), tables=set()) for g in GROUPS}
        rams = sorted(self.ram.items(), key=lambda kv: kv[1][0])
        for gi, sec, text in out:
            if gi is None or gi >= len(GROUPS):
                continue
            g = loc[GROUPS[gi]]
            text = re.sub(r"\(\+ 2 per car\)", "", text)
            for a, b in re.findall(r"(code_[0-9A-F]{6}) to (code_[0-9A-F]{6})", text):
                lo, hi = self.reg[a]["start"], self.reg[b]["start"]
                for r in self.code:
                    s = self.reg[r["id"]]["start"]
                    if lo <= s <= hi:
                        g["regions"][r["id"]].append(sec)
            for a, b in re.findall(r"(ram_\w+) to (ram_\w+)", text):
                lo, hi = self.ram[a][0], self.ram[b][0]
                g["ram"] |= {v[0] for k, v in rams if lo <= v[0] <= hi}
            for t in TOK.findall(text):
                rid = self.reg.get(t) and t or self.rname.get(t)
                if t in self.ram:
                    a, n = self.ram[t]
                    g["ram"].add(a)
                elif re.fullmatch(r"[0-9A-F]{6}", t) and int(t, 16) >= 0xFF0000:
                    g["ram"].add(int(t, 16))
                elif rid and self.reg[rid]["kind"] == "code":
                    if sec not in g["regions"][rid]:
                        g["regions"][rid].append(sec)
                elif rid:
                    g["tables"].add(rid)
        return loc

    def assign(self):
        loc = self.located()
        sysof, basis = {}, {}
        insns = {r["id"]: int(r["insns"]) for r in self.code}
        for r in self.code:
            rid = r["id"]
            hits = [(len(loc[g]["regions"][rid]), -i, g) for i, g in enumerate(GROUPS) if rid in loc[g]["regions"]]
            if hits:
                secs = [s for _, _, h in sorted(hits, reverse=True) for s in loc[h]["regions"][rid]]
                g, why = OVERRIDE.get(rid, (max(hits)[2], ""))
                sysof[rid] = g
                basis[rid] = "located: " + ", ".join(dict.fromkeys(secs)) + (" (%s)" % why if why else "")
        service = set(loc["data"]["regions"]) & {rid for rid in loc["data"]["regions"]
                                                 if "Sound cues" in loc["data"]["regions"][rid]}
        cov = self.coverage()
        for r in self.code:  # identity anchors: the region's own name says what it is
            rid = r["id"]
            if rid in sysof:
                continue
            if rid.startswith("z80_"):
                sysof[rid], basis[rid] = "rest:sound-driver", "rest: z80_ region (Z80 driver)"
            elif rid.startswith("imp_"):
                sysof[rid], basis[rid] = "rest:decompression", "rest: imp_ decompressor region"
            elif rid == "init":
                sysof[rid], basis[rid] = "rest:initialisation", "rest: reset entry region"
        for r in self.code:  # rest anchors on hardware and the mode word: before proximity (identity evidence)
            rid = r["id"]
            if rid in sysof:
                continue
            ram = self.ramuse[rid]
            if any(0xA00000 <= a < 0xA10000 for a in ram):  # Z80 RAM; a bus request alone is also VDP DMA
                sysof[rid], basis[rid] = "rest:sound-driver", "rest: Z80 RAM operands"
            elif 0xFFE69A in ram:
                sysof[rid], basis[rid] = "rest:menus", "rest: uses mode word ram_FFE69A"
            elif any(0xA10003 <= a <= 0xA1000D for a in ram):
                sysof[rid], basis[rid] = "rest:input", "rest: pad port operands"
        ramusers = defaultdict(int)
        for rid, s in self.ramuse.items():
            for a in s:
                ramusers[a] += 1
        for k in (1, 2):
            new = {}
            for r in self.code:
                rid = r["id"]
                if rid in sysof:
                    continue
                v, why = defaultdict(float), defaultdict(list)
                for t in sorted(self.calls[rid]):
                    if sysof.get(t) in GROUPS and t not in service and len(self.callers[t]) <= HUB:
                        v[sysof[t]] += 2
                        why[sysof[t]].append("calls " + t)
                cg = {sysof.get(c) for c in self.callers[rid]}
                if len(self.callers[rid]) <= 3 and len(cg) == 1 and cg <= set(GROUPS):
                    for c in sorted(self.callers[rid]):
                        v[sysof[c]] += 1
                        why[sysof[c]].append("called by " + c)
                for g in GROUPS:
                    shared = loc[g]["ram"] & self.ramuse[rid]
                    if shared:
                        v[g] += sum(1 if ramusers[a] <= HUB else 0.5 for a in shared)
                        why[g].append("%d located RAM words" % len(shared))
                    tabs = loc[g]["tables"] & self.reads[rid]
                    if tabs:
                        v[g] += len(tabs)
                        why[g].append("reads " + " ".join(sorted(tabs)))
                ranked = sorted(v.items(), key=lambda kv: (-kv[1], GROUPS.index(kv[0])))
                if ranked and ranked[0][1] >= 2 and (len(ranked) == 1 or ranked[0][1] >= 2 * ranked[1][1]):
                    g = ranked[0][0]
                    new[rid] = (g, "proximity%d: %s" % (k, "; ".join(why[g][:3])))
            for rid, (g, b) in new.items():
                sysof[rid], basis[rid] = g, b
            if not new:
                break
        changed = True
        while changed:  # rest families flow down the call graph: every assigned caller in one rest family
            changed = False
            for r in self.code:
                rid = r["id"]
                fams = {sysof.get(c) for c in self.callers[rid]}
                if rid not in sysof and self.callers[rid] and len(fams) == 1 and None not in fams                         and next(iter(fams)).startswith("rest:"):
                    f = next(iter(fams))
                    sysof[rid], basis[rid] = f, "rest: called only from %s" % f
                    changed = True
        for r in self.code:
            rid = r["id"]
            if rid in sysof:
                continue
            if cov[rid] == {"attract"}:
                fam, why = "attract", "executed only in the attract coverage run"
            elif cov[rid] == {"boot"}:
                fam, why = "initialisation", "executed only in the boot coverage runs"
            else:
                fam, why = "other", "no located link (callers %d, coverage %s)" % (
                    len(self.callers[rid]), "+".join(sorted(cov[rid])) or "none")
            sysof[rid], basis[rid] = "rest:" + fam, "rest: " + why
        self.loc, self.sysof, self.basis, self.insns = loc, sysof, basis, insns
        return sysof, basis

    def coverage(self):
        cov = defaultdict(set)
        _, crow = tsv(COVERAGE)
        iv = [(int(c["start"], 16), int(c["end"], 16), {x.split("_")[1] for x in c["runs"].split(";")}) for c in crow]
        for r in self.code:
            s, e = self.reg[r["id"]]["start"], self.reg[r["id"]]["end"]
            for cs, ce, kinds in iv:
                if cs < e and ce > s:
                    cov[r["id"]] |= kinds
        return cov

    def batches(self):
        route = {r["id"]: r["route"] for r in self.code}
        small = [r["id"] for r in self.code if int(r["insns"]) < SMALL]
        out = []
        for sysname in GROUPS:
            ids = self.families([i for i in self.sysof if self.sysof[i] == sysname and i not in small])
            out += [(sysname, b) for b in self.pack(ids)]
        ids = sorted(small, key=lambda i: (order_index(self.sysof[i]), self.reg[i]["start"]))
        tot = sum(self.insns[i] for i in ids)  # comments-only: balanced runs of at most about TARGET
        out += [("comments-only", b) for b in self.pack(ids, math.ceil(tot / max(1, math.ceil(tot / TARGET))))]
        ids = [x for f in FAMILIES  # the rest: one stream in family order, so small families share a batch
               for x in self.families([i for i in self.sysof if self.sysof[i] == "rest:" + f and i not in small])]
        for b in self.pack(ids):
            fams = list(dict.fromkeys(self.sysof[i][5:] for i in b))
            out.append(("rest:" + "+".join(fams), b))
        rows, per, rq = [], defaultdict(int), list(RWAVES)
        overflow = []
        for n, (sysname, ids) in enumerate(out, 1):
            per[sysname] += 1
            if sysname in WAVES and per[sysname] <= 2:
                wave = WAVES[sysname]
            elif sysname == "comments-only":
                wave = "T24"
            else:
                wave = None
                overflow.append(n - 1)
            kind = "comments-only" if sysname == "comments-only" else "names-and-comments"
            rt = "developer-review" if any(route[i] == "developer-review" for i in ids) else "unattended"
            rows.append(dict(batch="", order=n, system=sysname, wave=wave, route=rt, kind=kind,
                             regions=",".join(ids), insns=sum(self.insns[i] for i in ids), status="open"))
        # R waves: mechanics overflow first, then the rest families, 2 per wave
        ov = sorted(overflow, key=lambda i: (rows[i]["system"] not in GROUPS, i))
        for k, i in enumerate(ov):
            rows[i]["wave"] = rq[k // 2] if k // 2 < len(rq) else "excess"
        rows.sort(key=lambda r: (self.wave_rank(r["wave"]), r["order"]))
        for n, r in enumerate(rows, 1):
            r["order"], r["batch"] = n, "B%03d" % n
        return rows

    @staticmethod
    def wave_rank(w):
        return 999 if w == "excess" else int(w[1:])

    def families(self, ids):
        """Connected components of the call graph restricted to ids; largest (insns) first, address order inside."""
        s, seen, comps = set(ids), set(), []
        for i in sorted(ids, key=lambda x: self.reg[x]["start"]):
            if i in seen:
                continue
            comp, stack = [], [i]
            seen.add(i)
            while stack:
                x = stack.pop()
                comp.append(x)
                for y in (self.calls[x] | self.callers[x]) & s:
                    if y not in seen:
                        seen.add(y)
                        stack.append(y)
            comps.append(sorted(comp, key=lambda x: self.reg[x]["start"]))
        comps.sort(key=lambda c: (-sum(self.insns[x] for x in c), self.reg[c[0]]["start"]))
        return [x for c in comps for x in c]

    def pack(self, ids, target=TARGET):
        """Whole regions in the given order into batches of about TARGET insns; a region of TARGET or more stands
        alone without closing the open batch."""
        out, cur, n = [], [], 0
        for i in ids:
            k = self.insns[i]
            if k >= target:
                out.append([i])
                continue
            if cur and n + k > target * (1.15 if target == TARGET else 1.05):
                out.append(cur)
                cur, n = [], 0
            cur.append(i)
            n += k
        if cur:
            out.append(cur)
        return out


def order_index(sysname):
    order = GROUPS + ["rest:" + f for f in FAMILIES]
    return order.index(sysname) if sysname in order else len(order)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["map", "show"])
    ap.add_argument("--src", default=os.path.join(ROOT, ".run", "ledger", "src"))
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--verbose", action="store_true", help="show: every region and batch")
    a = ap.parse_args()
    m = Map(os.path.abspath(a.src))
    sysof, basis = m.assign()
    rows = m.batches()
    cnt = defaultdict(lambda: [0, 0])
    for r in m.code:
        c = cnt[(sysof[r["id"]], basis[r["id"]].split(":")[0])]
        c[0] += 1
        c[1] += m.insns[r["id"]]
    for k in sorted(cnt, key=lambda k: (order_index(k[0]), k[1])):
        print("systems: %s %s rows %d insns %d" % (k[0], k[1], cnt[k][0], cnt[k][1]))
    per = defaultdict(lambda: [0, 0])
    for r in rows:
        per[r["system"]][0] += 1
        per[r["system"]][1] += r["insns"]
    for s in sorted(per, key=order_index):
        print("systems: batches %s %d insns %d" % (s, per[s][0], per[s][1]))
    print("systems: batches %d, waves %s" % (len(rows), " ".join(sorted({r["wave"] for r in rows}, key=m.wave_rank))))
    if a.cmd == "show":
        if a.verbose:
            for r in m.code:
                print("  %s %d %s | %s" % (r["id"], m.insns[r["id"]], sysof[r["id"]], basis[r["id"]]))
            for r in rows:
                print("  %s %s %s %s %d %s" % (r["batch"], r["wave"], r["system"], r["route"], r["insns"], r["regions"]))
        return 0
    if os.path.exists(BATCHES) and not a.force:
        _, old = tsv(BATCHES)
        if any(r["status"] != "open" for r in old):
            sys.exit("systems: batches.tsv has non-open batches; rerun with --force to replace it")
    cols = m.cols + [c for c in ("system", "system_basis") if c not in m.cols]
    with open(LEDGER, "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(cols) + "\n")
        for r in m.rows:
            r["system"] = sysof.get(r["id"], r.get("system", "-") or "-") if r["kind"] == "code" else "-"
            r["system_basis"] = basis.get(r["id"], "-") if r["kind"] == "code" else "-"
            f.write("\t".join(str(r.get(c, "")) for c in cols) + "\n")
    with open(BATCHES, "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(BHEADER) + "\n")
        for r in rows:
            f.write("\t".join(str(r[c]) for c in BHEADER) + "\n")
    print("systems: wrote %d ledger rows, %d batches" % (len(m.rows), len(rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
