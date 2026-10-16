#!/usr/bin/env bash
# scripts/bootstrap.sh — check a clone's prerequisites, fetch + verify the AS assembler, place the dump.
# Usage: bash scripts/bootstrap.sh [--asl-zip PATH] [--dump PATH]
#   Checks Python 3.11 at PY (+ capstone 5.0.9), Java 21, Ghidra 12.1.4 (GHIDRA_INSTALL_DIR, required),
#   GNU make; installs AS into tools/bin/asl/ from --asl-zip or by downloading the one approved asset
#   (developer decision D1, phase 1.8: the AS zip is the ONLY download; Python, Java, Ghidra, make are manual).
#   Every zip is sha256-checked against tools/bin/asl.zip.sha256 BEFORE extraction; a mismatch is refused.
#   --dump: your own cartridge dump, SHA-1-checked against config/medium.sha1, copied to disks/ (never committed).
# Env: PY (interpreter), GHIDRA_INSTALL_DIR, JAVA_HOME, MMTT96_JDK_PARENT, MMTT96_BIN_DIR (AS target dir,
#   default tools/bin; for testing the download into a scratch dir), MMTT96_ASL_URL (download URL, controls only).
# Idempotent: a second run changes nothing. Exit 0 iff every item is present and verified, else 1.
set -u
ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT" || exit 1

ASL_ZIP=""; DUMP=""
while [ $# -gt 0 ]; do
  case "$1" in
    --asl-zip) ASL_ZIP=${2:?--asl-zip needs a path}; shift 2 ;;
    --dump) DUMP=${2:?--dump needs a path}; shift 2 ;;
    -h|--help) sed -n 2,11p "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "bootstrap: unknown argument $1 (see --help)"; exit 2 ;;
  esac
done

FAIL=0
ok()   { echo "ok      $1"; }
miss() { echo "MISSING $1"; shift; for l in "$@"; do echo "        $l"; done; FAIL=$((FAIL + 1)); }

# ---- Python 3.11 + capstone 5.0.9 ----
if [ -z "${PY:-}" ]; then
  if [ -x "C:/Program Files/Python311/python.exe" ]; then PY="C:/Program Files/Python311/python.exe"
  elif command -v python3.11 >/dev/null 2>&1; then PY=python3.11
  else PY=python3; fi
fi
PYVER=$("$PY" -I -c 'import sys; print("%d.%d.%d" % sys.version_info[:3])' 2>/dev/null)
case "$PYVER" in
  3.11.*)
    ok "python $PYVER ($PY)"
    CSV=$("$PY" -m pip show capstone 2>/dev/null | sed -n 's/^Version: //p')
    if [ "$CSV" = "5.0.9" ]; then ok "capstone 5.0.9"
    else miss "capstone==5.0.9 (found: ${CSV:-none})" \
      "install: \"$PY\" -m pip install --require-hashes -r requirements-python.txt" \
      "source: https://pypi.org/project/capstone/5.0.9/ (wheel sha256s in requirements-python.txt)"; fi ;;
  *) miss "python 3.11 at PY=$PY (found: ${PYVER:-none})" \
       "source: https://www.python.org/downloads/release/python-3119/ (pinned 3.11.9; set PY=<interpreter>)" \
       "expected: Python 3.11.x; hash: the python.org release page lists each installer's sha256" ;;
esac

# ---- Java 21 (same discovery order as scripts/ghidra/db.py) ----
JAVA=""
if command -v java >/dev/null 2>&1; then JAVA=java
elif [ -n "${JAVA_HOME:-}" ] && [ -x "$JAVA_HOME/bin/java" ]; then JAVA="$JAVA_HOME/bin/java"
else
  for d in "${MMTT96_JDK_PARENT:-C:/Program Files/Eclipse Adoptium}"/jdk-21*; do
    [ -x "$d/bin/java" ] && JAVA="$d/bin/java"
  done
fi
JVER=""; [ -n "$JAVA" ] && JVER=$("$JAVA" -version 2>&1 | sed -n '1s/.*version "\([^"]*\)".*/\1/p')
case "$JVER" in
  21|21.*) ok "java $JVER ($JAVA)" ;;
  *) miss "java 21 (found: ${JVER:-none})" \
       "source: https://adoptium.net/temurin/releases/?version=21 (Temurin 21; 21.0.12 used here)" \
       "expected: version 21.x; hash: not pinned (check the vendor's published sha256)" ;;
esac

# ---- Ghidra 12.1.4 ----
GH=${GHIDRA_INSTALL_DIR:-}
GVER=
[ -n "$GH" ] && GVER=$(sed -n 's/^application.version=//p' "$GH/Ghidra/application.properties" 2>/dev/null | tr -d '\r')
if [ "$GVER" = "12.1.4" ] && { [ -f "$GH/support/analyzeHeadless.bat" ] || [ -f "$GH/support/analyzeHeadless" ]; }; then
  ok "ghidra $GVER ($GH)"
else
  miss "ghidra 12.1.4 at GHIDRA_INSTALL_DIR=${GH:-<unset; required>} (found: ${GVER:-none})" \
    "source: https://github.com/NationalSecurityAgency/ghidra/releases/download/Ghidra_12.1.4_build/ghidra_12.1.4_PUBLIC_20260921.zip" \
    "expected: sha256 ddac49f903da9d5bac833e5cc79395098b9c33cfd3279be5f31bd00387d2d4db, 569649598 bytes; unzip, set GHIDRA_INSTALL_DIR"
fi

# ---- GNU make ----
MVER=$(make --version 2>/dev/null | sed -n '1s/^GNU Make //p')
if [ -n "$MVER" ]; then ok "GNU make $MVER"
else miss "GNU make" \
  "source: https://www.gnu.org/software/make/ (Windows: winget install ezwinports.make, add its bin to PATH)" \
  "expected: GNU Make 4.x; hash: not pinned"; fi

# ---- Macroassembler AS (the one approved download) ----
BIN=${MMTT96_BIN_DIR:-tools/bin}
ASL_NAME=asl-windows-x86_64-v1.4.2.20261012-run38215198548.zip
ASL_URL=${MMTT96_ASL_URL:-https://github.com/flamewing/asl-releases/releases/download/snapshot-v1.4.2.20261012-run38215198548/$ASL_NAME}
ASL_SHA=$(sed -n "s|^\([0-9a-f]\{64\}\)  asl/$ASL_NAME\$|\1|p" tools/bin/asl.zip.sha256 2>/dev/null)
sha256of() { sha256sum "$1" | cut -c1-64; }
asl_installed() { [ -f "$BIN/asl/asw.exe" ] && [ -f "$BIN/asl/p2bin.exe" ] && [ -f "$BIN/asl/$ASL_NAME" ] \
                  && [ "$(sha256of "$BIN/asl/$ASL_NAME")" = "$ASL_SHA" ]; }
asl_fail() { miss "AS $1" "source: $ASL_URL" "expected: sha256 $ASL_SHA, 2378577 bytes (tools/bin/asl.zip.sha256)"; }
if [ -z "$ASL_SHA" ]; then
  asl_fail "(tools/bin/asl.zip.sha256 missing or names another file)"
elif [ -n "$ASL_ZIP" ] && [ "$(sha256of "$ASL_ZIP" 2>/dev/null)" != "$ASL_SHA" ]; then
  asl_fail "zip refused: $ASL_ZIP does not match the recorded sha256 (nothing extracted)"
elif asl_installed; then
  ok "AS $BIN/asl (zip sha256 verified)"
elif [ -e "$BIN/asl" ] && [ -n "$(ls -A "$BIN/asl" 2>/dev/null)" ]; then
  asl_fail "$BIN/asl exists but is incomplete or unverified: move it aside, then re-run"
else
  SRC="$ASL_ZIP"
  if [ -z "$SRC" ]; then
    mkdir -p "$BIN"; SRC="$BIN/$ASL_NAME.part"; rm -f "$SRC"
    echo "fetch   $ASL_URL"
    curl -fsSL --retry 2 -o "$SRC" "$ASL_URL" || { rm -f "$SRC"; SRC=""; }
    if [ -n "$SRC" ] && [ "$(sha256of "$SRC")" != "$ASL_SHA" ]; then rm -f "$SRC"; SRC=""; fi
  fi
  if [ -z "$SRC" ]; then
    asl_fail "download failed or sha256 mismatch: partial file removed, nothing extracted"
  else
    STAGE="$BIN/asl.new"; rm -rf "$STAGE"; mkdir -p "$STAGE"
    if command -v unzip >/dev/null 2>&1; then unzip -q "$SRC" -d "$STAGE"; else "$PY" -I -m zipfile -e "$SRC" "$STAGE"; fi
    if [ $? -eq 0 ] && [ -f "$STAGE/asw.exe" ] && [ -f "$STAGE/p2bin.exe" ]; then
      rmdir "$BIN/asl" 2>/dev/null; mv "$STAGE" "$BIN/asl"
      if [ "$SRC" = "$BIN/$ASL_NAME.part" ]; then mv "$SRC" "$BIN/asl/$ASL_NAME"; else cp "$SRC" "$BIN/asl/$ASL_NAME"; fi
      asl_installed && ok "AS installed into $BIN/asl (zip sha256 verified before extraction)" || asl_fail "install check failed"
    else
      rm -rf "$STAGE"; asl_fail "extraction failed"
    fi
  fi
fi
case "$(uname -s)" in MINGW*|MSYS*|CYGWIN*) ;; *)
  echo "note    the AS asset is a Windows build; on Linux build AS from source and pass make ASM=<asw> P2BIN=<p2bin>" ;;
esac

# ---- the dump (yours; never downloaded, never committed) ----
ROM=$(sed -n 's/^ROM_DEFAULT = "\(.*\)"\r\{0,1\}$/\1/p' scripts/extract/manifest.py)
ROM_SHA=$(sed -n "s|^\([0-9a-f]\{40\}\)  ${ROM#disks/}\r\{0,1\}\$|\1|p" config/medium.sha1)
sha1of() { sha1sum "$1" | cut -c1-40; }
dump_fail() { miss "dump $1" "source: your own cartridge dump (never downloaded); pass --dump <path>" \
  "expected: SHA-1 $ROM_SHA (config/medium.sha1) -> $ROM"; }
if [ -z "$ROM" ] || [ -z "$ROM_SHA" ]; then
  dump_fail "(ROM_DEFAULT or its config/medium.sha1 line not found)"
elif [ -n "$DUMP" ] && [ "$(sha1of "$DUMP" 2>/dev/null)" != "$ROM_SHA" ]; then
  dump_fail "refused: $DUMP does not match the recorded SHA-1 (nothing copied)"
elif [ -f "$ROM" ] && [ "$(sha1of "$ROM")" = "$ROM_SHA" ]; then
  ok "dump $ROM (SHA-1 verified)"
elif [ -f "$ROM" ]; then
  dump_fail "$ROM exists with a wrong SHA-1: move it aside, then re-run with --dump"
elif [ -z "$DUMP" ]; then
  dump_fail "not found"
else
  mkdir -p "$(dirname "$ROM")" && cp "$DUMP" "$ROM" && [ "$(sha1of "$ROM")" = "$ROM_SHA" ] \
    && ok "dump copied to $ROM (SHA-1 verified)" || dump_fail "copy failed"
fi

if [ "$FAIL" -eq 0 ]; then echo "bootstrap: OK"; exit 0; fi
echo "bootstrap: FAIL ($FAIL item(s) missing or refused)"; exit 1
