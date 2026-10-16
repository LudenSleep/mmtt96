# How we work — Micro Machines Turbo Tournament 96 decomp

<!-- The card: standing facts for every agent. Never appended to; the cap is
     card.max_chars in .claude/pa.json (default 7000), enforced by the archive.
     Each role prints its slice with `tools/card.py slice <role>`.
     Written at install (interview) and edited in the same task as whatever changed it (H7). -->

## Project <!-- roles: expert coder router planner review critic discuss auditor curator -->
Micro Machines Turbo Tournament 96 decomp — Matching decompilation of Micro Machines Turbo Tournament 96 (Mega Drive, Europe v1.1). Constitution `PROJECT_CONTEXT.md`; roadmap `GENERATION_PLAN.md`;
rules `rules/INDEX.md`; techniques `cookbook/INDEX.md`; ops detail `docs/ops/INDEX.md`.

## Developer <!-- roles: router planner review discuss auditor curator -->
Who: <!-- TODO DEVELOPER_NAME: no source found -->. Experience: <!-- TODO DEVELOPER_EXPERIENCE: no source found -->. Domain: <!-- TODO DEVELOPER_DOMAIN: no source found -->.
Preferences: recommendations, not questions. Plain-English recaps at phase end. A notification
whenever anything waits on them. Autonomy: <!-- TODO AUTONOMY_POSTURE: no source found -->. Notification channel: <!-- TODO NOTIFY_CHANNEL: no source found -->.
The developer pushes; agents never do. They ratify rules at the next planner session.

## Rhythm <!-- roles: router planner review discuss auditor curator -->
autonomous  <!-- autonomous: the router runs the phase end to end, stopping only at the two gates.
                  review: tasks marked `review: yes` end the turn with REVIEW.md and wait. -->
Gates: plan approval (planner session) and the milestone (verified by the closer expert).

## Tools <!-- roles: expert coder router planner review critic discuss auditor curator -->
PY = C:/Program Files/Python311/python.exe

| Name | Command | Purpose |
|---|---|---|
| launch | `PY tools/launch.py --seed-only` | pa-session state detector; writes `.run/seed.md` |
| plan_edit | `PY tools/plan_edit.py` | the only writer of `PHASE_PLAN.md` (status, Changes, add/reopen) |
| status | `PY tools/status.py` | `.run/status.json` for the statusline; INBOX consume; waiting flags |
| task_log | `PY tools/task_log.py` | lint and finish a task summary (`Verified:` required) |
| research_add | `PY tools/research_add.py` | allocate a report id, write the index line |
| rules_add | `PY tools/rules_add.py` | add, supersede, promote, retire a rule |
| skill_add | `PY tools/skill_add.py` | turn a `workflow:` gotcha into `.claude/skills/<name>/SKILL.md` |
| cookbook_add | `bash tools/cookbook_add.sh` | add a cookbook entry and its index line |
| phaseend_index | `PY tools/phaseend_index.py` | assemble, lint and archive a PhaseEnd |
| genend_index | `PY tools/genend_index.py` | assemble and lint a GenerationEnd |
| commit_task | `bash tools/commit_task.sh` | the only commit path; explicit paths, no trailers, never pushes |
| run | `bash tools/run.sh` | any command that may print >40 lines; `--bg` / `--wait` for long compute |
| expert_ttl | `PY tools/expert_ttl.py --coder <coder>` | prints `1h` or `5m` (expert or its `-5m` twin) |
| extract | `PY scripts/extract/manifest.py [--check]` | ROM -> `config/manifest.retail.jsonl` + `extracted/retail/`; `--check` exit 1 on drift |
| build | `make {build|clean|expected}` | split, assemble `build/mmtt96.bin`, `sha1sum -c`; `expected` -> `expected/` |
| ghidra_db | `PY scripts/ghidra/{db,classify}.py` | Ghidra db `ghidra/` <-> `config/ghidra/*.tsv`; detail `docs/ops/ops-tools.md` |
| oracle | `PY scripts/oracle/{mame,bizhawk,probe,check_maps,coverage}.py` | MAME/BizHawk runtime oracles; detail `docs/ops/ops-tools.md` |
| census | `PY scripts/census/{census,progress,ledger,sweep,commentcheck}.py` | census; progress exit 1 on gap; rungs ledger, commentcheck; numbers never typed |
| boundaries | `PY scripts/oracle/boundaries.py [--scope S]` | Ghidra vs Capstone; exit 0 iff 0 phantoms/truncations/unexplained |
| names | `PY scripts/census/{signatures,encodings,constants}.py` | `config/names/*.tsv` -> `asm/{hw,ram,rom}.inc`; pairs signatures, names; rungs encmap, constants |
| health | `make health` / `make health-live` | green `health: pairs n/n agree`; report `.run/mmtt96-health/report.txt` |

## Skills <!-- roles: expert planner -->
<!-- one line per captured workflow; the SKILL.md is the canonical text -->
- run-sh-one-step — One run.sh call per step; bash -c trips the rm guard
- edit-escapes-with-edit-tool — Backslash source: Edit tool, never a heredoc
- detached-run-exit-file — After run.sh --wait read .run/logs/<name>.exit
- propagate-refusal-test — Test propagate refusal on a header-only copy
- names-edit-mirror — After a names edit: mirror, roundtrip, pairs names
- make-path-detached — make/Java PATH; gate, health detached via run.sh
- background-coder-handback — After a forced hand-back: edit directly
- mame-probe-recipes — MAME probe recipes
- coder-commit-regate — Re-gate after a dead coder

## Paths <!-- roles: expert coder router planner review critic discuss auditor curator -->
- Oracles: MAME 0.289 primary, BizHawk 2.11 second, Ghidra 12.1.4 db; claims `config/maps/*.tsv`, datapoints `config/oracle/*.tsv`
- Data: `disks/` (ROM copy, ignored); `extracted/retail/{raw,decoded}/` (ignored, purged)
- Generated (never hand-edited, H1): `config/manifest.retail.jsonl`, `extracted/`, `asm/`, `build/`, `expected/` (ignored, G12)
- Hand-edited: `config/regions.retail.tsv`, `config/medium.sha1`, `config/firewall.txt`
- Scratch: `.run/` (gitignored; never the system temp)

## Build / run / test <!-- roles: expert coder router planner review critic discuss auditor curator -->
- Build: clone: `bash scripts/bootstrap.sh --dump <dump>` once; `make build` (ezwinports make on PATH): `db.py listing` -> ignored `asm/src/`, split, assemble -> `build/mmtt96.bin`, `sha1sum -c`; contract: `scripts/contract.sh`
- Run: n/a (no runnable target; MAME via Tools `oracle`)
- Test / the gate: `make build` — green means `build/mmtt96.bin: OK`, exit 0; phase-close gate = `make clean && make build && make health` (binding)
- Modes: decisive = `make clean && make build` (clean rebuild, G9)

## Conventions & house style <!-- roles: expert coder router planner review critic discuss auditor curator -->
<!-- project-specific only; the general house style is in the project-architect skill -->

## Environment <!-- roles: expert coder router planner review critic discuss auditor curator -->
- OS / shells: Windows / bash, powershell
- Pins: Python 3.11.9; AS V1.42 Bld 313 (`tools/bin/asl/`, `asw` + `p2bin`); Capstone 5.0.9 — detail in `docs/ops/INDEX.md`, `docs/encoding-map.md`

## Docs map <!-- roles: expert coder router planner review critic discuss auditor curator -->
- `phase-ends/TASK_INDEX.md`, `phase-ends/RESEARCH_INDEX.md` — what was done and what was learned
- `docs/research-archive/` — migrated legacy reports
- `docs/retired/` — everything moved out of the load order
