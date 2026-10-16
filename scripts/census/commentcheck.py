#!/usr/bin/env python3
"""commentcheck.py -- check the factual claims of Ghidra comments against the tracked tables (plan 1.7 T8).

Wave 1 (T7): 23 of 42 draft comments were wrong or inexact, caught only by hand. This checks the mechanical claims:
  addr     the comment address lies in a region; in a code region it is an instruction start (asm/src listing)
  name     every identifier with an underscore is a name of config/names/{ram,routines,structs}.tsv, a region id or a
           config/maps claim id (a ram_<hex6> range end may instead lie inside a tracked RAM span); a name ending in
           _<hex6> sits at that address
  hex      every 6-digit hex address: ROM inside a region (code: an instruction start unless a range end), or work RAM
  range    A-B ranges (hex or names): A <= B
  sig      `signature group fE../fN..`: the comment address is a member; a `: a, b, c` list equals the group;
           `one of N ... (signature group G` has N = group size
  family   `(group NAME`: NAME is a routine name and the comment's routine is NAME or NAME_<hex6>
  such     `N such ... at a, b, c`: N = list length
  cov      `executed in [all] N [qual] coverage run(s)`: the runs of config/oracle/coverage.tsv at the address
Usage: commentcheck.py [--table PATH] [--src DIR] [--self-test] [--doc PATH]
  default table config/ghidra/comments.tsv; prints one `FAIL <addr> <check>: <why>` per failed claim and
  `commentcheck: comments <n> claims <c> failed <f>`; exit 1 on any failure, 2 on missing inputs.
  --self-test: the good fixture must pass and every row of the bad fixture must fail (scripts/census/fixtures/);
  standalone: instruction starts come from fixtures/commentcheck_starts.txt (addresses only), not asm/src.
  --doc PATH (plan 1.9 T4; docs/mechanics.md grammar): every `- ` bullet under a `## `/`### ` heading (outside code
  fences) ends with `[confirmed: p, ...]` or `[hypothesis: p, ...]` (bare `[hypothesis]` = open, no evidence yet);
  pointer kinds: a path (contains `/`, optional `:line`) exists; `P<nnn>` is a probe id of config/oracle/probes.tsv;
  `<tag>_<YYYYMMDD>T<HHMMSS>` (or `a+b`) are run ids of config/oracle/*.tsv (`run`/`runs` columns); anything else is a
  region id or a ram/routine/hw name, struct or struct.field. `confirmed` needs >= 3 distinct run ids or one probe
  of kind `controlled`. Prints `FAIL <path>:<line> <kind>: <why>` and `commentcheck: doc <path> bullets b pointers
  p failed f`; exit 1 on a failure or no bullets. Needs no listing. --self-test also runs the doc fixtures
  (fixtures/commentcheck_doc_{good,bad}.md): good passes; every bad bullet fails and each kind is caught.
"""
import argparse
import csv
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FIX = os.path.join(ROOT, "scripts", "census", "fixtures")
NUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
       "ten": 10, "eleven": 11, "twelve": 12}
HEX6 = r"0x[0-9A-Fa-f]{6}"
IDENT = re.compile(r"\b[A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)+\b")
HEXTOK = re.compile(r"(?<![0-9A-Za-z])(" + HEX6 + r")(?![0-9A-Za-z])")
RANGE = re.compile(r"(" + HEX6 + r"|\b[A-Za-z][A-Za-z0-9]*_[0-9A-Fa-f]{6})-(" + HEX6
                   + r"|[A-Za-z][A-Za-z0-9]*_[0-9A-Fa-f]{6})\b")
ALIST = HEX6 + r"(?:\s*,\s*(?:and\s+)?" + HEX6 + r"|\s+and\s+" + HEX6 + r")*"
SIG = re.compile(r"signature group (f[EN][0-9a-f]{10})(?::\s*(" + ALIST + r"))?")
ONEOF = re.compile(r"\b[Oo]ne of (\w+)\b[^()]*\(signature group (f[EN][0-9a-f]{10})")
FAMILY = re.compile(r"\(group ([a-z][a-z0-9_]*)")
SUCH = re.compile(r"\b(\w+) such [^,.;()]*? at (" + ALIST + r")")
COV = re.compile(r"executed in (all )?(\w+) (?:(\w+) )?coverage runs?\b")


def num(word):
    return NUM.get(word.lower(), int(word) if word.isdigit() else None)


def rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


class Tables:
    def __init__(self, src, starts=None):
        self.regions = [(int(r["start"], 16), int(r["end"], 16), r["kind"], r["id"])
                        for r in rows(os.path.join(ROOT, "config", "regions.retail.tsv"))]
        self.rom_end = max(e for _, e, _, _ in self.regions)
        self.names, self.spans = {}, []
        for r in rows(os.path.join(ROOT, "config", "names", "ram.tsv")):
            self.names[r["name"]] = int(r["addr"], 16)
            self.spans.append((int(r["addr"], 16), int(r["addr"], 16) + int(r["size"], 16)))
        self.routines = rows(os.path.join(ROOT, "config", "names", "routines.tsv"))
        self.rname = {}
        for r in self.routines:
            self.names[r["name"]] = int(r["addr"], 16)
            self.rname[int(r["addr"], 16)] = r["name"]
        for r in rows(os.path.join(ROOT, "config", "names", "structs.tsv")):
            self.names.setdefault(r["struct"], None)
        for _, _, _, rid in self.regions:
            self.names.setdefault(rid, None)
        for m in ("ram.tsv", "rom.tsv"):
            p = os.path.join(ROOT, "config", "maps", m)
            if os.path.exists(p):
                for r in rows(p):
                    self.names.setdefault(r["claim_id"], None)
        self.cov = [(int(r["start"], 16), int(r["end"], 16), r["runs"].split(";"))
                    for r in rows(os.path.join(ROOT, "config", "oracle", "coverage.tsv"))]
        self.allruns = sorted({x for _, _, rs in self.cov for x in rs})
        self.starts = set(starts) if starts is not None else set()
        pat = re.compile(r";\s*\$([0-9A-Fa-f]{6})\s*$")
        for fn in (os.listdir(src) if starts is None else []):
            if fn.endswith(".asm"):
                with open(os.path.join(src, fn), encoding="utf-8", errors="replace") as f:
                    for line in f:
                        m = pat.search(line)
                        if m:
                            self.starts.add(int(m.group(1), 16))

    def region(self, a):
        for s, e, k, rid in self.regions:
            if s <= a < e:
                return k, rid
        return None

    def group(self, g):
        if g.startswith("fN"):
            return {int(r["addr"], 16) for r in self.routines if r["sighash"].startswith(g[2:]) or r["group"] == g}
        return {int(r["addr"], 16) for r in self.routines if r["group"] == g}

    def runs_at(self, a):
        for s, e, rs in self.cov:
            if s <= a < e:
                return rs
        return []


def addrs(text):
    return [int(x, 16) for x in re.findall(HEX6, text)]


def value(tok, t):
    return int(tok, 16) if tok.startswith("0x") else t.names.get(tok)


def check(addr, text, t):
    """Return (claims, failures) for one comment."""
    fails, n = [], 0

    def claim(ok, kind, why):
        nonlocal n
        n += 1
        if not ok:
            fails.append((kind, why))

    reg = t.region(addr)
    claim(reg is not None, "addr", "comment address outside every region")
    if reg and reg[0] == "code":
        claim(addr in t.starts, "addr", "comment address is not an instruction start")
    range_ends = {m.group(2) for m in RANGE.finditer(text)}
    for tok in sorted(set(IDENT.findall(text))):
        m = re.fullmatch(r"ram_([0-9A-Fa-f]{6})", tok)
        if tok not in t.names and tok in range_ends and m:
            a = int(m.group(1), 16)
            claim(any(s <= a < e for s, e in t.spans), "name", tok + " (range end) lies in no tracked RAM span")
            continue
        claim(tok in t.names, "name", tok + " is not a tracked name, region id or claim id")
        m = re.search(r"_([0-9A-Fa-f]{6})$", tok)
        if tok in t.names and m and t.names[tok] is not None:
            claim(t.names[tok] == int(m.group(1), 16), "name", tok + " is tracked at a different address")
    for tok in sorted(set(HEXTOK.findall(text))):
        a = int(tok, 16)
        if 0xFF0000 <= a <= 0xFFFFFF:
            continue
        r = t.region(a) if a < t.rom_end else None
        claim(r is not None, "hex", tok + " is neither inside a region nor work RAM")
        if r and r[0] == "code" and tok not in range_ends:
            claim(a in t.starts, "hex", tok + " lies in code but is not an instruction start")
    for m in RANGE.finditer(text):
        a, b = value(m.group(1), t), value(m.group(2), t)
        if a is not None and b is not None:
            claim(a <= b, "range", m.group(0) + " runs backwards")
    for m in SIG.finditer(text):
        mem = t.group(m.group(1))
        claim(bool(mem), "sig", m.group(1) + " has no member in routines.tsv")
        claim(addr in mem, "sig", "comment address is not a member of " + m.group(1))
        if m.group(2):
            claim(set(addrs(m.group(2))) == mem, "sig", "listed members differ from " + m.group(1)
                  + " (%d in table)" % len(mem))
    for m in ONEOF.finditer(text):
        k, mem = num(m.group(1)), t.group(m.group(2))
        claim(k == len(mem), "sig", "'one of %s' but %s has %d members" % (m.group(1), m.group(2), len(mem)))
    for m in FAMILY.finditer(text):
        fam, own = m.group(1), t.rname.get(addr, "")
        claim(fam in t.names, "family", fam + " is not a routine name")
        claim(own == fam or re.fullmatch(re.escape(fam) + r"_[0-9A-Fa-f]{6}", own) is not None, "family",
              "comment routine %s is not in family %s" % (own or "(none)", fam))
    for m in SUCH.finditer(text):
        k = num(m.group(1))
        if k is not None:
            claim(k == len(addrs(m.group(2))), "such", "'%s such' lists %d addresses" % (m.group(1),
                                                                                        len(addrs(m.group(2)))))
    for m in COV.finditer(text):
        rs, k, qual = t.runs_at(addr), num(m.group(2)), m.group(3)
        if m.group(1):
            claim(sorted(rs) == t.allruns and k == len(t.allruns), "cov",
                  "'all %s' but %d of %d runs execute it" % (m.group(2), len(rs), len(t.allruns)))
        else:
            claim(k == len(rs), "cov", "'%s' runs but %d runs execute it" % (m.group(2), len(rs)))
        if qual:
            claim(all(qual in r for r in rs), "cov", "not every executing run is a %s run" % qual)
    return n, fails


def run(path, t, quiet=False):
    total = claims = 0
    failed = []
    for r in rows(path):
        a = int(r["addr"], 16)
        n, fails = check(a, r["text"], t)
        total += 1
        claims += n
        failed += [(r["addr"], k, w) for k, w in fails]
        if not quiet:
            for k, w in fails:
                print("FAIL %s %s: %s" % (r["addr"], k, w))
    return total, claims, failed


MARKER = re.compile(r"\[(confirmed|hypothesis)(?::\s*([^\]]*))?\]\s*$")
RUNID = re.compile(r"^[A-Za-z0-9_]+_\d{8}T\d{6}$")
DOC_KINDS = ("marker", "name", "run", "probe", "path", "confirmed")


def trows(path):
    """TSV rows, skipping `#` comment lines (config/oracle tables carry provenance headers)."""
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader((l for l in f if not l.startswith("#")), delimiter="\t"))


class DocTables:
    """Pointer targets of a mechanics doc: tracked tables only (no listing, ROM or Ghidra; CI no-dump job)."""

    def __init__(self):
        cfg = os.path.join(ROOT, "config")
        self.names = {r["id"] for r in trows(os.path.join(cfg, "regions.retail.tsv"))}
        nd = os.path.join(cfg, "names")
        self.names |= {r["name"] for f in ("ram.tsv", "routines.tsv", "hw.tsv") for r in trows(os.path.join(nd, f))}
        for r in trows(os.path.join(nd, "structs.tsv")):
            self.names |= {r["struct"], r["struct"] + "." + r["field"]}
        self.runs, self.probes = set(), {}
        od = os.path.join(cfg, "oracle")
        for fn in sorted(os.listdir(od)):
            if fn.endswith(".tsv"):
                for r in trows(os.path.join(od, fn)):
                    self.runs |= set((r.get("run") or "").split("+")) | set((r.get("runs") or "").split(";"))
                    if r.get("probe_id"):
                        self.probes[r["probe_id"]] = r.get("kind", "")
        self.runs.discard("")
        self.runs.discard("-")


def check_doc(path, t, quiet=False):
    """Return (bullets, pointers, failures [(line, kind, why)]) for one mechanics doc."""
    fails, bullets, ptrs = [], 0, 0
    in_sec = fence = False
    with open(path, encoding="utf-8") as f:
        lines = f.read().split("\n")
    for i, line in enumerate(lines, 1):
        if line.lstrip().startswith("```"):
            fence = not fence
            continue
        if fence:
            continue
        if re.match(r"#{1,6} ", line):
            in_sec = bool(re.match(r"#{2,3} ", line))
            continue
        if not in_sec or not re.match(r"\s*- ", line):
            continue
        bullets += 1
        m = MARKER.search(line)
        if not m:
            fails.append((i, "marker", "bullet has no [confirmed: ...] or [hypothesis: ...] marker"))
            continue
        runs, controlled = set(), False
        for p in [x.strip().strip("`") for x in (m.group(2) or "").split(",") if x.strip()]:
            ptrs += 1
            if "/" in p:
                if not os.path.exists(os.path.join(ROOT, p.split(":")[0])):
                    fails.append((i, "path", p + " does not exist"))
            elif re.fullmatch(r"P\d{3,}", p):
                if p not in t.probes:
                    fails.append((i, "probe", p + " is not a probe id of config/oracle/probes.tsv"))
                controlled |= t.probes.get(p) == "controlled"
            elif all(RUNID.match(x) for x in p.split("+")):
                for x in p.split("+"):
                    if x not in t.runs:
                        fails.append((i, "run", x + " is not a run id of config/oracle/*.tsv"))
                    else:
                        runs.add(x)
            elif p not in t.names:
                fails.append((i, "name", p + " is not a region id or a ram/routine/struct/hw name"))
        if m.group(1) == "confirmed" and len(runs) < 3 and not controlled:
            fails.append((i, "confirmed", "confirmed with %d run ids and no controlled probe" % len(runs)))
    if not quiet:
        for i, k, w in fails:
            print("FAIL %s:%d %s: %s" % (os.path.relpath(path, ROOT).replace("\\", "/"), i, k, w))
    return bullets, ptrs, fails


def self_test_doc(t):
    good = check_doc(os.path.join(FIX, "commentcheck_doc_good.md"), t)
    bad = check_doc(os.path.join(FIX, "commentcheck_doc_bad.md"), t, quiet=True)
    hit = {i for i, _, _ in bad[2]}
    kinds = {k for _, k, _ in bad[2]}
    missing = [k for k in DOC_KINDS if k not in kinds]
    for k in missing:
        print("MISSED planted doc failure kind %s" % k)
    print("commentcheck doc self-test: good %d bullets %d failed; bad %d bullets %d caught, kinds %d/%d"
          % (good[0], len(good[2]), bad[0], len(hit), len(DOC_KINDS) - len(missing), len(DOC_KINDS)))
    return 1 if good[2] or not good[0] or missing or len(hit) != bad[0] else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--table", default=os.path.join(ROOT, "config", "ghidra", "comments.tsv"))
    ap.add_argument("--src", default=os.path.join(ROOT, "asm", "src"))
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--doc", metavar="PATH", help="check a mechanics doc's claim lines instead of comments")
    a = ap.parse_args()
    if a.doc:
        b, p, fails = check_doc(a.doc, DocTables())
        print("commentcheck: doc %s bullets %d pointers %d failed %d" % (a.doc, b, p, len(fails)))
        return 1 if fails or not b else 0
    if a.self_test:  # standalone (no asm/src, ROM or Ghidra): instruction starts from the tracked address fixture
        with open(os.path.join(FIX, "commentcheck_starts.txt"), encoding="utf-8") as f:
            starts = {int(x, 16) for x in f.read().split() if x.startswith("0x")}
        return max(self_test(Tables(None, starts)), self_test_doc(DocTables()))
    if not os.path.isdir(a.src) or not any(f.endswith(".asm") for f in os.listdir(a.src)):
        print("commentcheck: no instruction listing in %s (run make build first)" % a.src)
        return 2
    t = Tables(a.src)
    total, claims, failed = run(a.table, t)
    print("commentcheck: comments %d claims %d failed %d" % (total, claims, len(failed)))
    return 1 if failed else 0


def self_test(t):
    good = run(os.path.join(FIX, "commentcheck_good.tsv"), t)
    bad_rows = rows(os.path.join(FIX, "commentcheck_bad.tsv"))
    missed = [r["addr"] for r in bad_rows if not check(int(r["addr"], 16), r["text"], t)[1]]
    for m in missed:
        print("MISSED planted failure at %s" % m)
    print("commentcheck self-test: good %d comments %d failed; bad %d rows %d caught"
          % (good[0], len(good[2]), len(bad_rows), len(bad_rows) - len(missed)))
    return 1 if good[2] or missed or not bad_rows else 0


if __name__ == "__main__":
    sys.exit(main())
