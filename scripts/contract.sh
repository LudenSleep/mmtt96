#!/usr/bin/env bash
# scripts/contract.sh — the reproducibility contract (plan 1.8 T6): a fresh clone of the committed HEAD plus your
# own dump, following README.md "Build from your own dump" literally and cold (no copied ghidra/, asm/, .run/).
# Usage: bash scripts/contract.sh [--dump PATH] [--asl-zip PATH] [--dir PATH]
#   --dump     your cartridge dump (or env MMTT96_DUMP); required; passed to bootstrap, never committed
#   --asl-zip  the AS snapshot zip (or env MMTT96_ASL_ZIP); optional (bootstrap downloads it otherwise)
#   --dir      scratch clone directory (or env MMTT96_CONTRACT_DIR); default <repo parent>/_contract/<timestamp>.
#              Must be dot-free (Ghidra refuses project paths with an element starting with '.'). Never deleted.
# Env (README step 2): PY, GHIDRA_INSTALL_DIR, JAVA_HOME, PATH with GNU make. Run it detached when a caller has a
#   time limit (`bash tools/run.sh --bg contract -- bash scripts/contract.sh ...`); a cold run takes a few minutes.
# Output: `contract: OK` or `contract: FAIL <step>`; record in .run/contract/result.txt (lines `key value`);
#   step logs in .run/contract/<timestamp>/. Live oracles (MAME, BizHawk; make health-live) are not part of it.
set -u
ROOT=$(cd "$(dirname "$0")/.." && pwd)
TS=$(date +%Y%m%d-%H%M%S)
DUMP=${MMTT96_DUMP:-}; ZIP=${MMTT96_ASL_ZIP:-}; DIR=${MMTT96_CONTRACT_DIR:-}
while [ $# -gt 0 ]; do
  case "$1" in
    --dump) DUMP=$2; shift 2 ;;
    --asl-zip) ZIP=$2; shift 2 ;;
    --dir) DIR=$2; shift 2 ;;
    *) echo "contract: unknown argument $1"; exit 2 ;;
  esac
done
[ -n "$DIR" ] || DIR="$(dirname "$ROOT")/_contract/$TS"
LOGS="$ROOT/.run/contract/$TS"; RES="$ROOT/.run/contract/result.txt"
mkdir -p "$LOGS"; : > "$RES.tmp"
put() { echo "$1 $2" >> "$RES.tmp"; }
fail() { put result "FAIL $1"; mv "$RES.tmp" "$RES"; echo "contract: FAIL $1 (logs: $LOGS)"; exit 1; }
[ -n "$DUMP" ] && [ -f "$DUMP" ] || { echo "contract: --dump PATH (or MMTT96_DUMP) must name your dump"; exit 2; }
case "/$DIR/" in */.*) echo "contract: scratch dir has a dot element (Ghidra refuses it): $DIR"; exit 2 ;; esac
[ -e "$DIR" ] && { echo "contract: scratch dir exists, refusing to reuse it: $DIR"; exit 2; }
DUMP=$(cd "$(dirname "$DUMP")" && pwd)/$(basename "$DUMP")
[ -z "$ZIP" ] || ZIP=$(cd "$(dirname "$ZIP")" && pwd)/$(basename "$ZIP")
put dir "$DIR"

step() {  # step <name> <cmd...>: run in the clone, log, time
  local name=$1; shift; local t0 t1 rc
  t0=$(date +%s); (cd "$DIR" && "$@") > "$LOGS/$name.log" 2>&1; rc=$?; t1=$(date +%s)
  put "t_${name}_s" $((t1 - t0)); echo "contract: $name rc $rc $((t1 - t0)) s"
  return $rc
}

t0=$(date +%s)
git clone -q -c core.autocrlf=true "$ROOT" "$DIR" > "$LOGS/clone.log" 2>&1 || fail clone
put t_clone_s $(( $(date +%s) - t0 ))
put commit "$(git -C "$DIR" log -1 --format='%cI %s')"
CRLF=$(git -C "$DIR" ls-files --eol | grep -c 'w/crlf')
put eol_crlf "$CRLF"; [ "$CRLF" = 0 ] || fail eol
STAMP=$(cd "$DIR" && sha256sum config/regions.retail.tsv config/check.retail.sha config/manifest.retail.jsonl \
  config/campaign/ledger.tsv | sha256sum | cut -c1-16)
put stamp "$STAMP"

ZARG=(); [ -z "$ZIP" ] || ZARG=(--asl-zip "$ZIP")
step bootstrap bash scripts/bootstrap.sh "${ZARG[@]}" --dump "$DUMP" || fail bootstrap
step build make build || fail build
grep -q '^build/mmtt96.bin: OK' "$LOGS/build.log" || fail build
put build "build/mmtt96.bin: OK"
step health make health || fail health
PAIRS=$(grep -o 'health: pairs [0-9]*/[0-9]* agree' "$LOGS/health.log" | tail -1)
[ -n "$PAIRS" ] || fail health
put pairs "${PAIRS#health: pairs }"
(cd "$DIR" && "${PY:-python3}" scripts/census/ledger.py check) > "$LOGS/ledger.log" 2>&1 || fail ledger
put ledger "$(grep '^ledger:' "$LOGS/ledger.log" | tail -1)"
put result OK
mv "$RES.tmp" "$RES"
echo "build/mmtt96.bin: OK"; echo "$PAIRS"; echo "contract: OK (clone $DIR; record $RES)"
