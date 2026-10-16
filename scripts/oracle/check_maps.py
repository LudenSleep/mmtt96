"""Check address-map claims against oracle datapoints; exit 1 naming every failing claim.

  check_maps.py [--live] [--manifest] [--claim ID] [--maps PATH ...] [--boot PATH] [--decrunch PATH] [--facts PATH]
                [--bizhawk PATH]

Maps (config/maps/rom.tsv, ram.tsv if present): `claim_id addr_start addr_end claim probe datapoints status expect second`
(`expect` = `key=value[;key=value]`, every pair must hold in every row of a datapoint run; `second` = semicolon-separated
second-oracle run ids: when non-empty, >= 3 of them must have `run key value` rows in --bizhawk (config/oracle/bizhawk.tsv,
written by bizhawk.py run --tsv) with value == expect for every expect pair, else FAIL naming both values).
A claim passes iff >= 3 distinct run ids in `datapoints` each have rows in --boot (config/oracle/boot.tsv) and every
row of those runs agrees, and `status` is verified. Claim kinds (column `claim`):
  entry_after_trap   boot column entry_after_trap == addr_start (6 hex digits)
  bp_hit             boot column hit_<addr_start> == yes
  decrunch_dest      rows from --decrunch (config/oracle/decrunch_natural.tsv, written by decrunch.py --natural; blobs keyed
                     by parent_start = region start hex, never by manifest id): the run has
                     >= 1 natural decrunch call with dest == addr_start, and every such call ends <= addr_end
  fact               rows from --facts (config/oracle/rammap.tsv, `run key value`, written by mame.py run rammap --tsv):
                     the run has a row key=value for every expect pair (expect required). A claim expecting
                     z80_sha1_after_upload must equal the manifest sha1 of the z80 region starting 0x01597A.
--live re-runs each claim's probe once (scripts/oracle/mame.py run <probe>) and requires the fresh rows to agree
(decrunch_dest: the fresh calls must also match the offline sha1, decrunch.match); a claim with `second` also gets one
fresh lua/bizhawk_rammap.lua run (bizhawk.run, shared by all such claims) compared the same way.
--manifest also fails every decoded record of config/manifest.retail.jsonl whose status is `inferred`, and every
record of kind `unknown`.
Stdlib only.
"""
import argparse
import csv
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mame  # noqa: E402
import decrunch  # noqa: E402
import bizhawk  # noqa: E402

MAPS = [os.path.join(ROOT, "config", "maps", n) for n in ("rom.tsv", "ram.tsv")]
BOOT = os.path.join(ROOT, "config", "oracle", "boot.tsv")
FACTS = os.path.join(ROOT, "config", "oracle", "rammap.tsv")
SECOND = os.path.join(ROOT, "config", "oracle", "bizhawk.tsv")
SECOND_PROBE = "bizhawk_rammap.lua"
KINDS = ("entry_after_trap", "bp_hit", "decrunch_dest", "fact")
RAMMAP_FRAMES = 600
Z80_DRIVER = "0x01597A"
MANIFEST = os.path.join(ROOT, "config", "manifest.retail.jsonl")
MIN_POINTS = 3


def read_tsv(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))


def expects(claim):
    """`expect` column -> list of (key, value) pairs."""
    return [tuple(p.split("=", 1)) for p in (claim.get("expect") or "").split(";") if p]


def agrees(claim, row):
    """True iff one boot row supports the claim (kind rule and every expect pair as a row column)."""
    addr = "%06X" % int(claim["addr_start"], 16)
    if not all(row.get(k) == v for k, v in expects(claim)):
        return False
    if claim["claim"] == "entry_after_trap":
        return row.get("entry_after_trap") == addr
    if claim["claim"] == "bp_hit":
        return row.get("hit_" + addr) == "yes"
    return False


def agrees_run(claim, rows):
    """True iff all rows of one run support the claim (decrunch_dest, fact: per-run rule over its rows)."""
    if claim["claim"] == "fact":
        have = {(r.get("key"), r.get("value")) for r in rows}
        return bool(expects(claim)) and all(p in have for p in expects(claim))
    if claim["claim"] != "decrunch_dest":
        return bool(rows) and all(agrees(claim, row) for row in rows)
    start, end = int(claim["addr_start"], 16), int(claim["addr_end"], 16)
    mine = [r for r in rows if int(r["dest"], 16) == start]
    return bool(mine) and all(start + int(r["size"]) - 1 <= end for r in mine)


def second_errs(claim, run_id, rows):
    """Second-oracle check of one run's fact rows -> list of failure messages (empty iff every expect pair holds)."""
    if not rows:
        return [f"{claim['claim_id']}: second run {run_id} has no rows (or no done)"]
    have = {r.get("key"): r.get("value") for r in rows}
    return [f"{claim['claim_id']}: second run {run_id} {k}={have.get(k)} != expect {k}={v}"
            for k, v in expects(claim) if have.get(k) != v]


def live_rows(claim):
    """One fresh run of the claim's probe -> (run_id, rows as dicts); rows empty on no done or any mismatch."""
    if claim["claim"] == "decrunch_dest":
        run_id, events, done = mame.run(claim["probe"], frames=decrunch.FRAMES, tag="live")
        rows, errs = decrunch.match(run_id, events, decrunch.blobs()) if done else ([], ["no done"])
        for e in errs:
            print(f"check_maps: live {e}")
        return run_id, [] if errs else [dict(zip(decrunch.HEADER, r)) for r in rows]
    if claim["claim"] == "fact":
        run_id, events, done = mame.run(claim["probe"], frames=RAMMAP_FRAMES, tag="live")
        return run_id, [dict(zip(mame.FACT_HEADER, r)) for r in (mame.fact_rows(run_id, events) if done else [])]
    run_id, events, done = mame.run(claim["probe"], tag="live")
    return run_id, [dict(zip(mame.BOOT_HEADER, r)) for r in (mame.boot_rows(run_id, events) if done else [])]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--manifest", action="store_true")
    ap.add_argument("--claim")
    ap.add_argument("--maps", action="append")
    ap.add_argument("--boot", default=BOOT)
    ap.add_argument("--decrunch", default=decrunch.NATURAL_TSV)
    ap.add_argument("--facts", default=FACTS)
    ap.add_argument("--bizhawk", default=SECOND)
    a = ap.parse_args(argv)
    claims = []
    for p in a.maps or [m for m in MAPS if os.path.isfile(m)]:
        claims += read_tsv(p)
    if a.claim:
        claims = [c for c in claims if c["claim_id"] == a.claim]
        if not claims:
            print(f"check_maps: FAIL {a.claim}: no such claim")
            return 1
    by_run = {}
    for path in (a.boot, a.decrunch, a.facts):  # run ids are tagged by probe, so the sources never share a run
        if os.path.isfile(path):
            for row in read_tsv(path):
                by_run.setdefault(row["run"], []).append(row)
    second = {}
    if os.path.isfile(a.bizhawk):
        for row in read_tsv(a.bizhawk):
            second.setdefault(row["run"], []).append(row)
    fails = []
    live = {}
    with open(MANIFEST, encoding="utf-8") as f:
        records = [json.loads(line) for line in f]
    z80_sha1 = next((r["sha1"] for r in records if r.get("kind") == "z80" and r.get("start") == Z80_DRIVER), None)
    for c in claims:
        cid = c["claim_id"]
        if c["claim"] not in KINDS:
            fails.append(f"{cid}: unknown claim kind {c['claim']!r}")
            continue
        want = dict(expects(c)).get("z80_sha1_after_upload")
        if want is not None and want != z80_sha1:
            fails.append(f"{cid}: expect z80_sha1_after_upload {want} != manifest z80 region {Z80_DRIVER} sha1 {z80_sha1}")
        runs = sorted({r for r in c["datapoints"].split(";") if r})
        bad = [r for r in runs if not agrees_run(c, by_run.get(r, []))]
        good = len(runs) - len(bad)
        if bad:
            fails.append(f"{cid}: disagrees or missing in datapoints for {', '.join(bad)}")
        if good < MIN_POINTS:
            fails.append(f"{cid}: {good} consistent datapoints < {MIN_POINTS}")
        if c["status"] != "verified":
            fails.append(f"{cid}: status {c['status']} != verified")
        sruns = sorted({r for r in (c.get("second") or "").split(";") if r})
        if sruns:
            if not expects(c):
                fails.append(f"{cid}: second set but no expect")
            serrs = {r: second_errs(c, r, second.get(r, [])) for r in sruns}
            for r in sruns:
                fails += serrs[r]
            sgood = sum(1 for r in sruns if not serrs[r])
            if sgood < MIN_POINTS:
                fails.append(f"{cid}: {sgood} consistent second-oracle runs < {MIN_POINTS}")
            if a.live:
                if SECOND_PROBE not in live:
                    run_id, events, done = bizhawk.run(SECOND_PROBE, frames=RAMMAP_FRAMES, tag="live_bh")
                    live[SECOND_PROBE] = (run_id, [dict(zip(mame.FACT_HEADER, r))
                                                   for r in (mame.fact_rows(run_id, events) if done else [])])
                run_id, rows = live[SECOND_PROBE]
                errs = second_errs(c, run_id, rows)
                fails += [e.replace(": second run", ": live second run", 1) for e in errs]
                if not errs:
                    print(f"check_maps: {cid}: live second run {run_id} agrees")
        if a.live:
            if c["probe"] not in live:
                live[c["probe"]] = live_rows(c)
            run_id, rows = live[c["probe"]]
            if not agrees_run(c, rows):
                fails.append(f"{cid}: live run {run_id} disagrees (or no done)")
            else:
                print(f"check_maps: {cid}: live run {run_id} agrees ({len(rows)} rows)")
    if a.manifest:
        for rec in records:
            if rec.get("kind") == "decoded" and rec.get("status") == "inferred":
                fails.append(f"{rec['id']}: decoded record inferred (parent {rec.get('parent')})")
            if rec.get("kind") == "unknown":
                fails.append(f"{rec['id']}: unknown record {rec.get('start')}-{rec.get('end')}")
    for msg in fails:
        print(f"check_maps: FAIL {msg}")
    if not fails:
        print(f"check_maps: OK {len(claims)} claims")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
