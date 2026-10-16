"""Progress report: rows and bytes by kind x status, denominators read from the build, the TSV and the manifest.

  progress.py [--tsv PATH]

Denominators: ROM size = len(build/mmtt96.bin); TSV row count; manifest region-record count
(config/manifest.retail.jsonl, records with start/end/id/kind/sha1; `decoded` and `medium` excluded).
Exit 1 when the TSV rows do not partition [0, ROM size) or TSV rows != manifest region records.
Stdout: counts and bytes only. Loader/partition check shared with census.py.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from census import MANIFEST, REGIONS, ROOT, load_manifest, load_regions, partition_errors  # noqa: E402

BIN = os.path.join(ROOT, "build", "mmtt96.bin")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--tsv", default=REGIONS)
    a = ap.parse_args()
    if not os.path.exists(BIN):
        sys.exit("progress: %s missing (make build)" % os.path.relpath(BIN, ROOT))
    size = os.path.getsize(BIN)
    rows = load_regions(a.tsv)
    _, mcount = load_manifest(MANIFEST)
    print("progress: rom bytes %d; tsv rows %d; manifest region records %d" % (size, len(rows), mcount))
    agg = {}
    for r in rows:
        for key in ((r["kind"], r["status"]), (r["kind"], "all"), ("all", r["status"])):
            n, b = agg.get(key, (0, 0))
            agg[key] = (n + 1, b + r["end"] - r["start"])
    for key in sorted(agg, key=lambda k: (k[0] == "all", k[0], k[1] == "all", k[1])):
        n, b = agg[key]
        print("progress: %-10s %-8s rows %4d/%d bytes %7d/%d" % (key[0], key[1], n, len(rows), b, size))
    errs = partition_errors(rows, size)
    if len(rows) != mcount:
        errs.append("TSV rows %d != manifest region records %d" % (len(rows), mcount))
    for e in errs:
        print("progress: FAIL " + e)
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
