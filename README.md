# Micro Machines Turbo Tournament 96 decomp

A byte-identical, readable reassembly of **Micro Machines Turbo Tournament 96** (Sega Mega Drive / Genesis, Motorola
68000 main CPU and Z80 sound CPU; Europe v1.1, J-Cart; Codemasters; ROM SHA-1 e8ff759679a0df2b3f9ece37ef686f248d3cf37b).

The game was written by hand in 68000 assembly, so this project has no C and no era compiler. It turns your own dump of
the cartridge back into 68000 assembly source, gives that source names and comments, and assembles it again with the
Macroassembler AS. Every build ends with a hash check: the rebuilt ROM must be identical to the original, byte for byte.
The next goal is a modified build that switches the half-scale view (the "Mini Micro" pool-table view) on for every
stage; after that, reviewing sprite and graphics changes, and understanding the four-player rules and the tie-break
playoff.

## Status

Progress numbers are never typed into this file; they come from the tools. Run `scripts/census/progress.py` (rows and
bytes by kind and status, read from your build) and see the campaign ledger `config/campaign/ledger.tsv`
(`scripts/census/ledger.py check` prints its counts). Phase 1.9 is complete, and the reassembly is readable: every code region builds from
instruction source and carries a header comment, and every routine entry and memory operand has a meaning name or a
recorded note of what would settle it (`scripts/census/ledger.py check --complete` passes). Every system of the game is
explained, with the evidence for each statement, in `docs/mechanics.md`; start at its overview. Many behaviours there
are still open hypotheses.

## Why the assembly source is not in this repository

The converted assembly is derived from the game, so it is never committed (decision D1,
`docs/decisions/source-location.md`). What the repository holds instead is everything needed to regenerate it: the
tools, and small tracked tables keyed by address (names, comments, the campaign ledger). The build combines those
tables with your own dump and writes the source into the ignored folder `asm/src/` on your machine. To read the code,
build it.

## Build from your own dump

This repository contains **no byte of the game**: no ROM, no disassembly listing, no memory image. You need your own
legally obtained dump of the Europe v1.1 cartridge (SHA-1 above, also in `config/medium.sha1`). Run every command
from Git bash (Windows) or a shell (Linux), in the root of your clone.

1. **Clone to a suitable path.** No folder in the clone's path may start with a dot (Ghidra refuses such project
   paths), and do not build from a `subst` drive (use a junction instead). If the clone must live under a dotted
   path, set `MMTT96_GHIDRA_PROJ` to a dot-free directory for the Ghidra project.
2. **Install the prerequisites** (none of them is downloaded for you, except the assembler in step 3):
   - Python 3.11 (pinned 3.11.9, https://www.python.org/downloads/release/python-3119/), then its one package,
     Capstone 5.0.9, hash-pinned: `<python> -m pip install --require-hashes -r requirements-python.txt`.
   - Java 21 (Temurin, https://adoptium.net/temurin/releases/?version=21), on `PATH` or via `JAVA_HOME`.
   - Ghidra 12.1.4 (`ghidra_12.1.4_PUBLIC_20260921.zip`,
     https://github.com/NationalSecurityAgency/ghidra/releases/tag/Ghidra_12.1.4_build; its sha256 is in
     `docs/ops/ops-setup-decomp.md`). Unzip it and set `GHIDRA_INSTALL_DIR` to the unzipped folder.
   - GNU make and `sha1sum`: on Windows, Git bash (https://git-scm.com/download/win) supplies the shell and `sha1sum`;
     add GNU make (`winget install ezwinports.make`, https://www.gnu.org/software/make/) and put its `bin` on `PATH`.
   - Tell the build which Python to use: `export PY=<python>` (the `Makefile` default is a Windows install path,
     `C:/Program Files/Python311/python.exe`), or pass `make <target> PY=<python>` every time. A Python without
     Capstone is rejected when make starts.
3. **Bootstrap:** `bash scripts/bootstrap.sh --dump <your dump>`. It checks every prerequisite above (printing the
   source link of anything missing), downloads the Macroassembler AS snapshot from
   https://github.com/flamewing/asl-releases/releases/tag/snapshot-v1.4.2.20261012-run38215198548, checks it against
   `tools/bin/asl.zip.sha256` and unpacks it into the ignored `tools/bin/asl/`, and checks your dump against
   `config/medium.sha1` before copying it into the ignored `disks/` folder under the name the `Makefile` expects.
   Already have the zip? Add `--asl-zip <zip>`. It exits 0 and prints `bootstrap: OK` only when everything is
   present and verified; running it again changes nothing. The AS snapshot is a Windows build; on Linux build AS
   from source and pass `make build ASM=<asw> P2BIN=<p2bin>`.
4. **Build:** `make build`. It imports your dump into a local Ghidra project, writes the instruction source to
   `asm/src/`, splits the ROM into `asm/`, assembles `build/mmtt96.bin` and runs
   `sha1sum -c config/check.retail.sha`. Green is `build/mmtt96.bin: OK` and exit 0. The first build takes about
   30 seconds.
5. **Check health:** `make health`. It runs every offline cross-check (the second disassembler, the census, the
   ledger, the comment checker and the others) and must end with `health: pairs n/n agree` and exit 0. The first run
   takes about 2 minutes.

Verify it yourself: `bash scripts/contract.sh --dump <your dump>` repeats steps 3-5 in a fresh clone (record:
`docs/verification.md`).

`make clean && make build` is the clean rebuild. The emulators (MAME, BizHawk) are oracles used only for research
(`make health-live`); you do not need them to build. More setup detail: `docs/ops/ops-setup-decomp.md`.

## The no-ROM policy

No byte of the game enters git: no ROM, no disassembly listing, no memory image, and no converted assembly source. The repository does hold analysis notes derived from studying the game, such as address-keyed names and comments and documentation of how it works; these contain no game bytes and no pasted code. The `.gitignore`, `tools/audit_public.py` (its sources in `config/firewall.txt`) and `scripts/health/asm_leak.py` keep game data out, and the audit runs in CI on every push. A pasted listing of the game's instructions counts too. See `src/NOTICE.md`.

## How this project is made

This project uses Claude Code to assist with analysis and tooling; a person reviews every change, and the
byte-identical build check is the only proof that anything matches.

The standard it holds itself to: a change counts only when the whole ROM still hashes identical after a clean rebuild;
names and meanings are evidence-based, never guessed (an address-named placeholder is honest); every outward message
to another project is written by a person; the project makes no automated requests to community services. The record
(the phase syntheses, the decision log, the cookbook of byte-proven techniques) is what makes the work auditable.

## Repository visibility

This repository is public. It contains no game data; the audit above runs in CI on every push to keep it that way. The
developer decided to publish the project's own tools, tables and documentation.

## Acknowledgements

Prior community work used as reference only (read, linked, never copied; their licences apply to their own code):

- hivvu/scale-miniatures (https://github.com/hivvu/scale-miniatures, GPL-3.0): a TypeScript rewrite of the 1994 PC game.
- NymanLauri/micro-machines (https://github.com/NymanLauri/micro-machines, no licence stated): a C++ clone.
- maxim-zhao/micromachineseditor (https://github.com/maxim-zhao/micromachineseditor, MIT): a Master System editor and
  disassembly.

The governance and method come from ProjectArchitect
and the decomp-architect kit distilled from a finished matching decompilation.

## License

The project's own work (the tooling, the build system, the documentation) is licensed under MIT (`LICENSE`). No
license is asserted over anything derived from the game (`src/NOTICE.md`). *Micro Machines Turbo Tournament 96* is the
property of its rights holder.

This is an independent, unofficial fan project. It is not affiliated with, sponsored by or endorsed by Codemasters,
Electronic Arts (EA) or Sega. All trademarks belong to their respective owners. You must supply your own legally
dumped ROM; none is provided here.

## Contributing

See `CONTRIBUTING.md`: bring your own dump, never commit anything derived from it, and read the AI-use conduct section
before your first change.
