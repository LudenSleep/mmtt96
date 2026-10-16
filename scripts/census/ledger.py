"""Campaign ledger: one row per `kind code` region of config/regions.retail.tsv, plus one per inferred non-code
region -> config/campaign/ledger.tsv.

  ledger.py {write|check|report} [--src DIR] [--skip-listing] [--ledger PATH]

  write   `db.py listing <all code ids> --out DIR` (default .run/ledger/src, scratch; never asm/src), timed;
          wall secs + per-region self-check result -> .run/ledger/meta.json; parse listings; write the TSV.
          --skip-listing reuses DIR and the meta.json listing record. Rows whose evidence is not `auto` keep
          class/blocker/route/evidence (hand-set preservation). Auto code rows: route `unattended` if insns < 50
          else `developer-review`; an empty computed blocker (closeness 0) becomes `comments and meaning names
          pending`.
  check   `ledger: code regions <r>/<n> undecoded <u>; inferred <i> without-verdict <w>` (r/n: code rows; i:
          inferred rows of any kind; w: those with evidence `auto`); exit 1 if u > 0, w > 0, the TSV is stale
          (id/kind/status/bytes set differs from the regions code + inferred non-code rows) or incomplete
          (`ledger: INCOMPLETE <n> rows`: empty class/closeness/blocker, or a code row with empty route).
          T33: also exit 1 on `ledger: ROUTE <n> rows` (a code or hand-set row whose route is not one of ROUTES:
          unattended developer-review promote re-kind keep-inferred; a route's condition lives in its blocker).
          undecoded = code ids absent from asm/.srclist + inferred/lone-return code rows whose evidence is `auto`.
          --ledger PATH checks another TSV (default config/campaign/ledger.tsv; negative controls).
          T11: also exit 1 on `ledger: NO-SYSTEM <n> code rows` (empty `system`; systems.py map sets it, write
          keeps it) and `ledger: BATCHES ...` (a code row not in exactly one batch of config/campaign/batches.tsv,
          or a batch region that is no code row).
          --complete (plan 1.9 T4) also prints `ledger: complete <c>/<n> code rows; no-plate <p>; entries pending
          <e>/<E>; operands raw <r>, neutral names pending <o>/<O>` from asm/src (make build; exit 2 without it) and
          exits 1 unless every code row has a plate comment (comments.tsv type plate in the region), every function
          entry (.run/signatures/functions.tsv) and every named operand is meaning-named or its evidence carries
          `unresolved:`, and no raw nameable operand remains. Neutral = a `_<hex6>` suffix or evidence saying
          neutral/structural. o/O are distinct names; r counts operand occurrences.
  report  strata over verified rows (insns <50, 50-300, >300), embedded bytes/runs, listing wall time,
          raw_abs/nameable totals, class counts, then per stratum the top 2 executed candidates
          (config/oracle/coverage.tsv overlap > 0; key: group member desc, covered fraction desc, insns asc, id);
          then (T11) rows/insns per system, batches/insns/waves per batch system, one line per batch.

Columns: insns = instruction lines; raw_abs = `$hex` operand tokens; nameable (internal) = raw_abs not after `#`
nor inside an operand starting with `#` (T34, in_imm) and not an An/SP displacement, value (24-bit, .w sign-extended) a ROM address, RAM $FF0000-$FFFFFF or IO
$A00000-$C0001F; named_ops = operand identifiers that are known names (config/names ram/structs/routines, region
ids); labels = `L_` definitions; embedded_bytes = dc.b bytes (run = consecutive dc.b lines); comments =
config/ghidra/comments.tsv rows in region; entries / named_entries from .run/signatures/functions.tsv;
closeness = nameable + unnamed entries + embedded runs. Inferred code rows are listed like verified ones
(default class `inferred`/`lone-return`); inferred non-code rows: insns and listing-derived columns `-`, class
`inferred`.
Names dir: env MMTT96_NAMES (default config/names); sweep.py and the other importers use the same NAMES.
Firewall: stdout and the TSV carry ids, counts, class names and prose only. Stdlib only.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from census import REGIONS, ROOT, ROM_DEFAULT, load_regions  # noqa: E402

LEDGER = os.path.join(ROOT, "config", "campaign", "ledger.tsv")
HEADER = ("id kind status insns bytes raw_abs named_ops labels embedded_bytes comments entries named_entries "
          "closeness class blocker route evidence system system_basis").split()
ROUTES = ("unattended", "developer-review", "promote", "re-kind", "keep-inferred")  # route vocabulary (T33)
BATCHES = os.path.join(ROOT, "config", "campaign", "batches.tsv")
BHEADER = "batch\torder\tsystem\twave\troute\tkind\tregions\tinsns\tstatus"
RUN = os.path.join(ROOT, ".run", "ledger")
META = os.path.join(RUN, "meta.json")
DB = os.path.join(ROOT, "scripts", "ghidra", "db.py")
SIGS = os.path.join(ROOT, "scripts", "census", "signatures.py")
FUNCS = os.path.join(ROOT, ".run", "signatures", "functions.tsv")
GROUPS = os.path.join(ROOT, ".run", "signatures", "groups.tsv")
COMMENTS = os.path.join(ROOT, "config", "ghidra", "comments.tsv")
NAMES = os.environ.get("MMTT96_NAMES") or os.path.join(ROOT, "config", "names")
EXCEPTIONS = os.path.join(ROOT, "config", "oracle", "boundary_exceptions.tsv")
COVERAGE = os.path.join(ROOT, "config", "oracle", "coverage.tsv")
SRCLIST = os.path.join(ROOT, "asm", ".srclist")
REGS = {"d%d" % i for i in range(8)} | {"a%d" % i for i in range(8)} | {"sp", "pc", "sr", "ccr", "usp"}
HEX = re.compile(r"(#?)(-?)\$([0-9A-Fa-f]+)(\(\s*(?:a[0-7]|sp)\b)?")
IDENT = re.compile(r"(?<![\w.$])[A-Za-z_]\w*")
FN = re.compile(r"fn_[0-9A-F]{6}")


def in_imm(ops, i):
    """True if position i of ops lies in an immediate operand (one starting with `#`), e.g. the `$2` of
    `#vdp_reg_autoinc|$2` or the VRAM address of `#vdp_cmd_hi($C000,...)` (T34: not address operands)."""
    j, depth = 0, 0
    for k, c in enumerate(ops[:i]):
        depth += {"(": 1, ")": -1}.get(c, 0)
        if c == "," and depth == 0:
            j = k + 1
    return ops[j:].lstrip().startswith("#")


def tsv(path, header=None):
    with open(path, encoding="utf-8") as f:
        lines = [l.rstrip("\r") for l in f.read().split("\n")]
    if header is not None and lines[0] != header:
        sys.exit("ledger: %s: bad header" % os.path.relpath(path, ROOT))
    cols = lines[0].split("\t")
    return [dict(zip(cols, l.split("\t"))) for l in lines[1:] if l]


def code_rows():
    return [r for r in load_regions(REGIONS) if r["kind"] == "code"]


def ledger_rows():
    """Code rows + inferred non-code rows, in regions order."""
    return [r for r in load_regions(REGIONS) if r["kind"] == "code" or r["status"] == "inferred"]


def known_names(regions):
    n = {r["id"] for r in regions}
    n |= {r["name"] for r in tsv(os.path.join(NAMES, "ram.tsv"))}
    n |= {r["name"] for r in tsv(os.path.join(NAMES, "routines.tsv"))}
    for r in tsv(os.path.join(NAMES, "structs.tsv")):
        n |= {r["struct"], r["field"], "%s_%s" % (r["struct"], r["field"])}
    return n


def nameable(v, size, rom_size):
    if v > 0xFFFFFF:
        v &= 0xFFFFFF
    elif size == "w" and v >= 0x8000 and v <= 0xFFFF:
        v |= 0xFF0000
    return v < rom_size or 0xFF0000 <= v <= 0xFFFFFF or 0xA00000 <= v <= 0xC0001F


def parse(path, names, rom_size):
    """Listing -> counts (insns, raw_abs, nameable, named_ops, labels, embedded_bytes, runs)."""
    c = dict(insns=0, raw_abs=0, nameable=0, named_ops=0, labels=0, embedded_bytes=0, runs=0)
    prev_dc = False
    with open(path, encoding="ascii") as f:
        for line in f.read().split("\n"):
            if not line.strip() or line.strip().startswith(";"):
                continue  # blank or comment-only line (plate comment): not an instruction
            if re.fullmatch(r"L_[0-9A-F]{6}:", line.strip()):
                c["labels"] += 1
                prev_dc = False
                continue
            f_ = line.split(";")[0].strip().split("\t")
            mn, ops = f_[0].strip(), (f_[1].strip() if len(f_) > 1 else "")
            if mn == "dc.b":
                c["embedded_bytes"] += len(ops.split(","))
                c["runs"] += 0 if prev_dc else 1
                prev_dc = True
                continue
            prev_dc = False
            c["insns"] += 1
            for m in HEX.finditer(ops):
                c["raw_abs"] += 1
                if m.group(1) or m.group(2) or m.group(4) or in_imm(ops, m.start()):
                    continue
                rest = ops[m.end():]
                size = "w" if rest.startswith(").w") else "l"
                if nameable(int(m.group(3), 16), size, rom_size):
                    c["nameable"] += 1
            stripped = HEX.sub(" ", ops)
            for m in IDENT.finditer(stripped):
                t = m.group(0)
                if t.lower() in REGS or t.startswith("L_"):
                    continue
                if t in names:
                    c["named_ops"] += 1
    return c


def run_listing(ids, src):
    os.makedirs(src, exist_ok=True)
    t0 = time.time()
    p = subprocess.run([sys.executable, DB, "listing"] + ids + ["--out", src], capture_output=True, text=True)
    wall = time.time() - t0
    with open(os.path.join(RUN, "listing.log"), "w", encoding="utf-8") as f:
        f.write(p.stdout + p.stderr)
    checks = {}
    for l in p.stdout.split("\n"):
        m = re.match(r"listing (\S+): (.*)", l)
        if m:
            r = m.group(2)
            checks[m.group(1)] = "match" if r.endswith("match") and "mismatch" not in r else (
                "mismatch" if "mismatch" in r else "error")
    meta = {"wall_secs": round(wall, 1), "rc": p.returncode, "regions": len(ids), "self_check": checks}
    with open(META, "w", encoding="utf-8", newline="\n") as f:
        json.dump(meta, f, indent=1, sort_keys=True)
    return meta


def write(a):
    os.makedirs(RUN, exist_ok=True)
    regions = ledger_rows()
    with open(os.path.join(ROOT, ROM_DEFAULT), "rb") as f:
        rom = f.read()
    ver = [r["id"] for r in regions if r["kind"] == "code"]
    if a.skip_listing:
        with open(META, encoding="utf-8") as f:
            meta = json.load(f)
    else:
        meta = run_listing(ver, a.src)
        print("ledger: listing %d regions, %.1f s, rc %d" % (len(ver), meta["wall_secs"], meta["rc"]))
    if not os.path.exists(FUNCS):
        subprocess.run([sys.executable, SIGS, "scan"], stdout=subprocess.DEVNULL, check=True)
    funcs = [r for r in tsv(FUNCS) if r["kind"] == "function"]
    routines = {int(r["addr"], 16) for r in tsv(os.path.join(NAMES, "routines.tsv"))}
    comments = [int(r["addr"], 16) for r in tsv(COMMENTS, "addr\ttype\ttext")]
    exc = {r["region_id"] for r in tsv(EXCEPTIONS, "region_id\tclass\treason")}
    names = known_names(code_rows())
    old = {r["id"]: r for r in tsv(LEDGER)} if os.path.exists(LEDGER) else {}  # tolerant: pre-T11 header
    out = []
    for r in regions:
        rid, s, e = r["id"], r["start"], r["end"]
        ents = sorted(int(f["start"], 16) for f in funcs if f["region"] == rid)
        named = sum(1 for f in funcs if f["region"] == rid
                    and (int(f["start"], 16) in routines or not FN.fullmatch(f["id"])))
        row = dict(id=rid, kind=r["kind"], status=r["status"], bytes=e - s,
                   comments=sum(1 for c in comments if s <= c < e), entries=len(ents), named_entries=named,
                   route="", evidence="auto", system="" if r["kind"] == "code" else "-", system_basis="-")
        if r["kind"] != "code":
            row.update(insns="-", raw_abs="-", named_ops="-", labels="-", embedded_bytes="-", closeness="-")
            row["class"] = "inferred"
            row["blocker"] = "inferred region; no verdict"
        else:
            c = parse(os.path.join(a.src, rid + ".asm"), names, len(rom))
            unnamed = len(ents) - named
            row.update(insns=c["insns"], raw_abs=c["raw_abs"], named_ops=c["named_ops"], labels=c["labels"],
                       embedded_bytes=c["embedded_bytes"], closeness=c["nameable"] + unnamed + c["runs"])
            head = (ents[0] - s) if ents else e - s
            issues = []
            if c["embedded_bytes"]:
                issues.append("embedded data %d bytes in %d runs" % (c["embedded_bytes"], c["runs"]))
            if head:
                issues.append("unowned head %d bytes" % head if ents else "no function entry")
            sc = meta.get("self_check", {}).get(rid, "missing")
            if sc != "match":
                issues.append("listing self-check %s" % sc)
            if c["nameable"]:
                issues.append("%d raw nameable addresses" % c["nameable"])
            if unnamed:
                issues.append("%d unnamed entries" % unnamed)
            row["class"] = "embedded-data" if c["embedded_bytes"] else "unowned-head" if head else "srcform-ok"
            row["blocker"] = "; ".join(issues)
            if r["status"] != "verified":
                row["class"] = "lone-return" if rid in exc else "inferred"
                row["blocker"] = "inferred region; no verdict"
            row["blocker"] = row["blocker"] or "comments and meaning names pending"  # empty only at closeness 0
            row["route"] = "unattended" if c["insns"] < 50 else "developer-review"
        o = old.get(rid)
        if o and o["evidence"] != "auto":
            for k in ("class", "blocker", "route", "evidence"):
                row[k] = o[k]
        if o and o.get("system"):  # set by systems.py map (plan 1.9 T11); kept across write
            row["system"], row["system_basis"] = o["system"], o.get("system_basis") or "-"
        out.append(row)
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    with open(LEDGER, "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(HEADER) + "\n")
        for row in out:
            f.write("\t".join(str(row[k]) for k in HEADER) + "\n")
    print("ledger: wrote %d rows -> %s" % (len(out), os.path.relpath(LEDGER, ROOT).replace("\\", "/")))
    return 0


def check(a):
    regions = code_rows()
    rows = tsv(a.ledger, "\t".join(HEADER)) if os.path.exists(a.ledger) else []
    want = {(r["id"], r["kind"], r["status"], str(r["end"] - r["start"])) for r in ledger_rows()}
    have = {(r["id"], r["kind"], r["status"], r["bytes"]) for r in rows}
    src = set()
    if os.path.exists(SRCLIST):
        with open(SRCLIST, encoding="utf-8") as f:
            src = set(f.read().split()[1:])
    und = {r["id"] for r in regions if r["id"] not in src}
    und |= {r["id"] for r in rows if r["kind"] == "code" and r["class"] in ("inferred", "lone-return")
            and r["evidence"] == "auto"}
    inf = [r for r in rows if r["status"] == "inferred"]
    wo = sum(1 for r in inf if r["evidence"] == "auto")
    print("ledger: code regions %d/%d undecoded %d; inferred %d without-verdict %d" % (
        sum(1 for r in rows if r["kind"] == "code"), len(regions), len(und), len(inf), wo))
    if want != have:
        print("ledger: STALE %d rows differ" % len(want ^ have))
    inc = sum(1 for r in rows if not (r["class"] and r["closeness"] and r["blocker"])
              or (r["kind"] == "code" and not r["route"]))
    if inc:
        print("ledger: INCOMPLETE %d rows" % inc)
    badr = sum(1 for r in rows if (r["kind"] == "code" or r["evidence"] != "auto") and r["route"] not in ROUTES)
    if badr:
        print("ledger: ROUTE %d rows" % badr)
    nosys = sum(1 for r in rows if r["kind"] == "code" and r["system"] in ("", "-"))
    if nosys:
        print("ledger: NO-SYSTEM %d code rows (run systems.py map)" % nosys)
    bad = batch_check(rows)
    rc = 1 if und or wo or inc or badr or nosys or bad or want != have else 0
    return max(rc, complete(a)) if a.complete else rc


def batch_check(rows):
    """Every code row in exactly one batch of batches.tsv, every batch region a code row (plan 1.9 T11)."""
    if not os.path.exists(BATCHES):
        print("ledger: BATCHES missing %s" % os.path.relpath(BATCHES, ROOT))
        return 1
    seen = {}
    for b in tsv(BATCHES, BHEADER):
        for rid in b["regions"].split(","):
            seen[rid] = seen.get(rid, 0) + 1
    code = {r["id"] for r in rows if r["kind"] == "code"}
    miss, dup, extra = code - set(seen), sum(1 for v in seen.values() if v > 1), set(seen) - code
    if miss or dup or extra:
        print("ledger: BATCHES code rows unbatched %d, in two batches %d, unknown regions %d" % (
            len(miss), dup, len(extra)))
    return 1 if miss or dup or extra else 0


NEUTRAL = re.compile(r"_[0-9A-Fa-f]{6}$")


def complete(a):
    """--complete (plan 1.9 T4): readability completeness over every code row of the listing in asm/src."""
    src = os.path.join(ROOT, "asm", "src")
    regions = code_rows()
    if not all(os.path.exists(os.path.join(src, r["id"] + ".asm")) for r in regions):
        print("ledger: --complete needs the asm/src listing (run make build first)")
        return 2
    if not os.path.exists(FUNCS):
        subprocess.run([sys.executable, SIGS, "scan"], stdout=subprocess.DEVNULL, check=True)
    info = {}  # name -> (meaning-named, unresolved recorded)
    for f, col in (("ram.tsv", "name"), ("routines.tsv", "name")):
        for r in tsv(os.path.join(NAMES, f)):
            ev = r["evidence"].lower()
            info[r[col]] = (not NEUTRAL.search(r[col]) and "neutral" not in ev and "structural" not in ev,
                            "unresolved:" in ev)
    routines = {int(r["addr"], 16): r["name"] for r in tsv(os.path.join(NAMES, "routines.tsv"))}
    plates = [int(r["addr"], 16) for r in tsv(COMMENTS, "addr\ttype\ttext") if r["type"] == "plate"]
    funcs = [r for r in tsv(FUNCS) if r["kind"] == "function"]
    rom_end = max(r["end"] for r in load_regions(REGIONS))
    pending = lambda n: n not in info or not (info[n][0] or info[n][1])  # noqa: E731
    noplate = done = ents = ents_p = raw = 0
    ops_p, ops_all = set(), set()
    for r in regions:
        s, e = r["start"], r["end"]
        has_plate = any(s <= p < e for p in plates)
        ent = [routines.get(int(f["start"], 16), "") for f in funcs if f["region"] == r["id"]]
        ep = sum(1 for n in ent if pending(n))
        rr, used = 0, set()
        with open(os.path.join(src, r["id"] + ".asm"), encoding="ascii") as fh:
            for line in fh.read().split("\n"):
                st = line.strip()
                if not st or st.startswith(";") or st.endswith(":"):
                    continue
                f_ = line.split(";")[0].strip().split("\t")
                ops = f_[1].strip() if len(f_) > 1 else ""
                if f_[0].strip() == "dc.b":
                    continue
                for m in HEX.finditer(ops):
                    if not (m.group(1) or m.group(2) or m.group(4) or in_imm(ops, m.start())) and nameable(
                            int(m.group(3), 16), "w" if ops[m.end():].startswith(").w") else "l", rom_end):
                        rr += 1
                used |= {m.group(0) for m in IDENT.finditer(HEX.sub(" ", ops)) if m.group(0) in info}
        noplate += not has_plate
        ents += len(ent)
        ents_p += ep
        raw += rr
        ops_all |= used
        ops_p |= {n for n in used if pending(n)}
        done += has_plate and not ep and not rr and not any(pending(n) for n in used)
    print("ledger: complete %d/%d code rows; no-plate %d; entries pending %d/%d; operands raw %d, "
          "neutral names pending %d/%d" % (done, len(regions), noplate, ents_p, ents, raw, len(ops_p), len(ops_all)))
    return 0 if done == len(regions) else 1


def report(a):
    rows = tsv(LEDGER, "\t".join(HEADER))
    ver = [r for r in rows if r["status"] == "verified"]
    with open(META, encoding="utf-8") as f:
        meta = json.load(f)
    with open(os.path.join(ROOT, ROM_DEFAULT), "rb") as f:
        rom_size = len(f.read())
    names = known_names(code_rows())
    nameable_total, runs = 0, 0
    for r in ver:
        c = parse(os.path.join(a.src, r["id"] + ".asm"), names, rom_size)
        nameable_total += c["nameable"]
        runs += c["runs"]

    def stratum(r):
        n = int(r["insns"])
        return "small" if n < 50 else "medium" if n <= 300 else "large"
    strata = {"small": [], "medium": [], "large": []}
    for r in ver:
        strata[stratum(r)].append(r)
    print("ledger: strata small(<50) %d medium(50-300) %d large(>300) %d" % tuple(len(v) for v in strata.values()))
    print("ledger: embedded bytes %d runs %d" % (sum(int(r["embedded_bytes"]) for r in ver), runs))
    sc = meta.get("self_check", {})
    print("ledger: listing wall %.1f s, self-check match %d/%d" % (
        meta["wall_secs"], sum(1 for v in sc.values() if v == "match"), meta["regions"]))
    print("ledger: raw_abs %d nameable %d named_ops %d" % (
        sum(int(r["raw_abs"]) for r in ver), nameable_total, sum(int(r["named_ops"]) for r in ver)))
    cls = {}
    for r in rows:
        cls[r["class"]] = cls.get(r["class"], 0) + 1
    print("ledger: classes " + " ".join("%s %d" % (k, cls[k]) for k in sorted(cls)))
    cov = [(int(r["start"], 16), int(r["end"], 16)) for r in tsv(COVERAGE, "start\tend\truns")]
    members = set()
    for g in tsv(GROUPS):
        if g["kind"] == "function":
            members |= set(g["members"].split(";"))
    funcs = [f for f in tsv(FUNCS) if f["kind"] == "function"]
    regs = {r["id"]: (r["start"], r["end"]) for r in code_rows()}
    print("candidates")
    for name, rs in strata.items():
        cand = []
        for r in rs:
            s, e = regs[r["id"]]
            got = sum(max(0, min(e, ce) - max(s, cs)) for cs, ce in cov)
            if got <= 0:
                continue
            grp = any(f["id"] in members for f in funcs if f["region"] == r["id"])
            cand.append((-int(grp), -got / (e - s), int(r["insns"]), r["id"]))
        for g, fr, n, rid in sorted(cand)[:2]:
            print("  %s %s insns %d covered %.2f group %s" % (name, rid, n, -fr, "yes" if g else "no"))
    systems(rows)
    return 0


def systems(rows):
    """Plan 1.9 T11: rows and insns per system (ledger), batches/insns/waves per batch system (batches.tsv)."""
    per = {}
    for r in rows:
        if r["kind"] == "code":
            p = per.setdefault(r["system"], [0, 0])
            p[0] += 1
            p[1] += int(r["insns"])
    print("systems")
    for k in sorted(per):
        print("  %s rows %d insns %d" % (k, per[k][0], per[k][1]))
    if not os.path.exists(BATCHES):
        return
    bs = tsv(BATCHES, BHEADER)
    per = {}
    for b in bs:
        p = per.setdefault(b["system"], [0, 0, []])
        p[0] += 1
        p[1] += int(b["insns"])
        p[2].append(b["wave"])
    print("batches %d (open %d)" % (len(bs), sum(1 for b in bs if b["status"] == "open")))
    for k in sorted(per, key=lambda k: min(int(b["order"]) for b in bs if b["system"] == k)):
        print("  %s batches %d insns %d waves %s" % (k, per[k][0], per[k][1], " ".join(dict.fromkeys(per[k][2]))))
    for b in bs:
        print("  %s %s %s %s %s regions %d insns %s %s" % (b["batch"], b["wave"], b["system"], b["route"], b["kind"],
                                                         len(b["regions"].split(",")), b["insns"], b["status"]))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["write", "check", "report"])
    ap.add_argument("--src", default=os.path.join(RUN, "src"))
    ap.add_argument("--skip-listing", action="store_true")
    ap.add_argument("--ledger", default=LEDGER, help="check: ledger TSV to check (default config/campaign/ledger.tsv)")
    ap.add_argument("--complete", action="store_true", help="check: also readability completeness (plan 1.9 T4)")
    a = ap.parse_args()
    a.src = os.path.abspath(a.src)
    if os.path.normcase(a.src).startswith(os.path.normcase(os.path.join(ROOT, "asm"))):
        sys.exit("ledger: --src must not be under asm/")
    return {"write": write, "check": check, "report": report}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
