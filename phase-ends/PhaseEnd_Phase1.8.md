# PhaseEnd — Phase 1.8: Publish gate: the reproducibility contract (implements Gen 1.8)
Approved: 2026-10-13 | Closed: 2026-10-13 | Planner: claude-opus-5-5/medium | Tasks: 7 done, 0 superseded

## Milestone
Milestone: a fresh `git clone` of HEAD (with `core.autocrlf=true`) plus the developer's own dump and the documented tools rebuilds `build/mmtt96.bin` byte-identically and passes `make health`, following only README.md (bootstrap, build, health), recorded as a dated contract run carrying only hashes, counts and timings; the no-ROM CI (audit job + no-dump self-test job) is green on the pushed history; the repository stays private and the visibility flip is recorded as deferred, gated and off by default — verified by: `bash scripts/contract.sh && make clean && make build && make health && "C:/Program Files/Python311/python.exe" tools/audit_public.py && "C:/Program Files/Python311/python.exe" tools/card.py check && test -z "$(git ls-files asm build expected disks ghidra)"` (all exit 0; `contract.sh` prints `contract: OK` with `build/mmtt96.bin: OK` and `health: pairs n/n agree` from the clone; main tree `build/mmtt96.bin: OK`, `health: pairs 9/9 agree`; card <= 7000; each call detached via `bash tools/run.sh --bg gate -- ...` + `bash tools/run.sh --wait gate --max 280`, repeated waits allowed, exit code from `.run/logs/gate.exit`); CI green is the developer's word recorded in T7
Verified: git log --oneline origin/main..HEAD → empty (0 commits to push); gh run view 38418641102 → success on 8fcfd83, audits success, selftest success Review: ran: git ls-remote origin main; git log --oneline 87254ed..8fcfd83; gh run list --repo <owner>/Micropool --workflow no-rom.yml --limit 5; gh run view 38418641102 --repo <owner>/Micropool --json conclusion,headSha,jobs (local host, read-only) results: phase-ends/current/logs/T7.md; github.com/<owner>/Micropool/actions/runs/38418641102 seen: the 27 local-only commits are pushed (origin/main = HEAD = 8fcfd83); workflow `no-rom` run 38418641102 on 8fcfd83 is green with both jobs `audits` and `selftest` success. decisions: - Close T7: both CI jobs are green on the pushed HEAD (a red job would have gone back as a T4.1 reopen through the critic) — Recommended: accept edits: - C:/Program Files/Python311/python.exe tools/plan_edit.py set-status T7 done

## Tasks
- T1 — fresh-clone probe and gap list | Done: a committed-HEAD clone (1e69e19) builds `build/mmtt96.bin: OK` cold and passes `make health` 9/9, but only from a dot-free path and after `classify.py seeds`; the native `.run/contract/probe` path fails in Ghidra. Gap list below for T2-T5. | commit: - | tasks/T1.md | logs/T1.md
- T2 — build plumbing: names dir, regions mirror, clone gaps | Done: NAMES is a make variable (ledger: env MMTT96_NAMES); signatures gates build on scratch names; db.py mirror rewrites config/ghidra/regions.tsv; T1 gaps 1, 2, 3, 4, 5, 10 fixed; a cold clone (dot-free and dotted+env) builds and passes health 9/9. | commit: 88d133c | tasks/T2.md | logs/T2.md
- T3 — bootstrap script and Python pin | Done: `bash scripts/bootstrap.sh [--asl-zip PATH] [--dump PATH]` checks Python 3.11 + capstone 5.0.9, Java 21, Ghidra 12.1.4, GNU make; fetches or takes the AS zip, sha256-verifies it before extraction into tools/bin/asl/; places a SHA-1-verified dump in disks/. requirements-python.txt pins capstone with both wheel hashes. | commit: f3172fa | tasks/T3.md | logs/T3.md
- T4 — CI self-test job (no dump) | Done: no-rom.yml keeps `audits` and adds `selftest` (ubuntu-24.04, Py 3.11, hash-pinned capstone) running census/signatures fixtures, commentcheck self-test, asm_leak --plant (rc 1 asserted); header comment rewritten. | commit: 0e9591d | tasks/T4.md | logs/T4.md
- T5 — README, CONTRIBUTING and docs to the contract | Done: README describes the 68000 reassembly (AS, no C, no era compiler), why source is untracked (D1), a numbered 5-step build-from-your-own-dump section, and a private/deferred `## Repository visibility` with the 3 flip conditions; CONTRIBUTING, 68k doc, NOTICE and card match. | commit: ad5e8b4 | tasks/T5.md | logs/T5.md
- T6 — contract script, recorded contract run, milestone | Done: `bash scripts/contract.sh --dump <dump> [--asl-zip <zip>]` reproduces README steps 3-5 in a cold autocrlf clone; one green run recorded in docs/verification.md; milestone chain green in the main tree. | commit: b753b30 | tasks/T6.md | logs/T6.md
- T7 — CI green on the pushed history | Done: the 27 local-only commits are pushed (origin/main = HEAD = 8fcfd83); workflow `no-rom` run 38418641102 on 8fcfd83 is green with both jobs `audits` and `selftest` success. | commit: - | tasks/T7.md | logs/T7.md

## Decisions that still bind
- T2 — a clone whose path has an element starting with `.` sets MMTT96_GHIDRA_PROJ to a dot-free dir; the T6 contract
- T2 — commentcheck --self-test needs no dump (CI no-dump job may run it); regenerate fixtures/commentcheck_starts.txt from a built tree when a fixture row changes.
- T3 — the AS snapshot zip is the only thing bootstrap downloads (D1, 2026-10-13); Python, Java, Ghidra, make are checked only, never installed
- T4 — CI runs only checks needing no dump, Ghidra, Java or the assembler, with the runner's `python`; a new no-dump check goes into the `selftest` job and `docs/ops/ops-tools.md ## ci` together.
- T6 — the contract clone lives outside the repo on a dot-free path (default `<repo parent>/_contract/<ts>`, env MMTT96_CONTRACT_DIR / --dir); dotted or existing dirs are refused; scratch clones are never deleted by the script.
- Repository private; public flip deferred, gated (G17/DK-56 host proof, the developer's copyright decision, G58/G63/G64), off by default: contract, README `## Repository visibility`, `docs/68k-adaptation.md` (T5).
- D1 (b): bootstrap downloads only the AS zip, sha256-verified before extraction; Python, Java, Ghidra, make are checked, never installed: contract, `scripts/bootstrap.sh`, README step 3, `docs/ops/ops-setup-decomp.md` (T3).
- A clone on a dotted path sets `MMTT96_GHIDRA_PROJ` to a dot-free dir; `db.py` refuses dotted project paths: contract, README, `docs/ops/ops-tools.md`, cookbook C0029 (T2).
- `config/names` is written only after all signatures gates pass on a scratch copy; `--plant-gate3` is the control: contract, `docs/ops/ops-tools.md` (T2).
- CI runs only no-dump checks; a new one goes into job `selftest` and `docs/ops/ops-tools.md ## ci` together: contract, `.github/workflows/no-rom.yml` (T4).
- The contract clone lives outside the repo on a dot-free path, never deleted by the script; reproducibility is re-proved with `scripts/contract.sh`, recorded in `docs/verification.md`: contract, `docs/ops/ops-tools.md ## contract` (T6).
- Next task needs: phase 1.9 routes its readability waves to the developer's stated interests first: the camera that follows the pack, scoring by forcing an opponent out of view, the tie-break playoff, and the pool-table levels with the zoomed-out camera (find them via the ledger, signature groups, RAM names such as the slot tables, and MAME traces; the track editor/construction kit and its saved-track format is a lead for how levels are stored).
- Next task needs: the about-27-run waves-2+ plan from 1.7/T8, re-ordered by those subsystems; the value-logging probe aimed at `jcart_38FFFE`.
- Next task needs: the milestone's `verified by` text should not hold prose clauses (`phaseend_index.py verify` executes them) and a contract clause needs its `--dump` argument or env in the clause, or the clause names the record instead.
- Next task needs: the card is at 6991 of 7000 chars after this close; any addition must trim elsewhere. Extend nothing of 1.8's scope.

## Rules proposed
- (none)

## Cookbook entries added
C0029 | Ghidra headless refuses project paths with a dotted element | ghidra,headless,windows,paths,gotcha | 2026-10-13 | 1.8/T1 | T1,T2 summary gotchas
C0030 | Windows path aliases: subst breaks relpath; rm -rf follows junctions | windows,paths,junction,subst,gotcha | 2026-10-13 | 1.8/T1 | T1,T2 summary gotchas
C0031 | python -I hides user site-packages in prerequisite checks | python,bootstrap,gotcha | 2026-10-13 | 1.8/T3 | T3 summary gotcha

## Research
- (none)

## Audit
- seed: no expert runs for phase 1.8
- CLAUDE.md: 983 bytes
- .claude/skills/background-coder-handback/SKILL.md: 685 bytes
- .claude/skills/decrunch-parent-remap/SKILL.md: 953 bytes
- .claude/skills/detached-run-exit-file/SKILL.md: 648 bytes
- .claude/skills/edit-escapes-with-edit-tool/SKILL.md: 725 bytes
- .claude/skills/make-path-detached/SKILL.md: 889 bytes
- .claude/skills/names-edit-mirror/SKILL.md: 630 bytes
- .claude/skills/project-architect/SKILL.md: 13113 bytes
- .claude/skills/propagate-refusal-test/SKILL.md: 731 bytes
- .claude/skills/run-sh-one-step/SKILL.md: 798 bytes
- .claude-state/memory/MEMORY.md: 4262 bytes
- HOW_WE_WORK.md: 7019 bytes
- cookbook/INDEX.md: 5014 bytes
- rules/INDEX.md: 7032 bytes
- audit unavailable: CLI not installed (~/.claude/pa3/pa_ledger.py)

## Agent runs
- (no ledger at ~\.claude\usage-ledger\ledger.sqlite)

## Discussions
- (none)

## Deferred
- from T7: phase close (PHASE-END) once the developer accepts T7. (unconsumed)

## Changes
- 2026-10-13 developer: D1 downloads decided by developer 2026-10-13: option (b): scripts/bootstrap.sh fetches the AS zip itself (flamewing/asl-releases v1.4.2.20261012, 2,378,577 bytes, sha256 fe8b9d78c8ad0db1889b4d32cfc4094d6bbefa2af058e6956846047407870fab, verified before use); Ghidra, Java and Python remain manual installs
- 2026-10-13 router: T1 next -> done
- 2026-10-13 router: T2 next -> done
- 2026-10-13 router: T3 next -> done
- 2026-10-13 router: T4 next -> done
- 2026-10-13 router: T5 next -> done
- 2026-10-13 router: T6 next -> done
- 2026-10-13 router: T7 next -> done

## Plain-English Recap
Phase 1.8 ("Publish gate") made the project reproducible by someone other than its author: a fresh copy of the repository (a `git clone`), plus that person's own legally obtained cartridge dump (the "dump", a file holding the game's ROM) and the documented tools, now rebuilds the game byte for byte and passes the project's self-checks by following README.md alone. The developer decided on 2026-10-13 to finish the plan as written, to keep the repository private (making it public stays deferred, gated and off by default), that the project is a non-commercial learning experiment, and (download decision D1, option b) that the setup script fetches only the AS assembler zip itself, checking its SHA-256 fingerprint before unpacking; Ghidra, Java, Python and make remain manual installs the script only checks.

T1 cloned the repository fresh and tried to build it, which exposed the gaps: Ghidra (the disassembler database the build reads) refuses project paths with a folder name starting with a dot, so a clone under `.run/` could not build; the seed file `seeds.tsv` was never produced by any build step; a failed analysis left a seedless project behind; the comment checker's self-test needed generated source; default paths were specific to this machine; and README lacked steps. T2 fixed them: a `NAMES` build variable (and `MMTT96_NAMES` for the ledger), the names tool now tests a scratch copy and writes `config/names` only after all three of its gates pass (with planted controls that must be refused), `db.py mirror` also rewrites `config/ghidra/regions.tsv`, a `MMTT96_GHIDRA_PROJ` override for dotted paths, seeds regenerated when missing, seedless projects dropped, a standalone self-test, interpreter and Java/Ghidra overrides, and `make health` now stops at the first Ghidra failure; a cold clone built and passed 9 of 9 checks both in a dot-free folder and under a dotted parent with the override (build about 29 s, health about 2 min).

T3 added `scripts/bootstrap.sh` and `requirements-python.txt` (capstone 5.0.9 pinned by hash; Ghidra 12.1.4 zip named with its size and hash in the ops docs); its controls showed a wrong-hash zip refused, a partial download deleted, a wrong dump refused, and a second run changing nothing. T4 added a second CI job, `selftest` (CI: the automatic checks GitHub runs on every push, here without any dump), and T5 rewrote README, CONTRIBUTING and the docs to this contract, including a numbered build-from-your-own-dump section and a "Repository visibility: private" section. T6 added `scripts/contract.sh` and the dated record `docs/verification.md` (clone 1 s, bootstrap 2 s, build 27 s, health 108 s, 0 CRLF files, build OK, health 9/9, ledger 252/252 undecoded 0, input stamp `63819e85ed41648c`). T7: the developer pushed 27 commits and GitHub run 38418641102 succeeded on `8fcfd83` with both jobs green, the first Linux evidence for `selftest`.

Milestone evidence (this session, 2026-10-13, main tree at `3a017a8`): `tools/phaseend_index.py verify` did not run cleanly this time: RED 0/2, because clause 1 starts with `bash scripts/contract.sh`, which exits 2 without `--dump`/`MMTT96_DUMP` (the closer's brief excluded re-running the cold contract), and clause 2 is the prose "CI green is the developer's word recorded in T7", which the tool ran as a shell command (quote error). The main-tree chain was then run step by step through `run.sh`: `make clean` exit 0; `make build` exit 0, `build/mmtt96.bin: OK` (`.run/logs/gbuild.log`); `make health` exit 0, `health: pairs 9/9 agree` (`.run/logs/ghealth.log`); `ledger.py check` `code regions 252/252 undecoded 0; inferred 31 without-verdict 0`; `audit_public: OK` 0 offenders among 556 paths (re-run after the closer's CONTRIBUTING edit, still OK); `git ls-files asm build expected disks ghidra` empty; `card.py check` chars 6991 of 7000 after this close. Contract record currency: the input stamp recomputed in the main tree is `63819e85ed41648c`, equal to the recorded one, and no `config/` file changed between `8fcfd83` and HEAD, so `docs/verification.md` is current. CI: `gh run list --workflow no-rom.yml` shows run 38418641102 `completed success` (title "T6: Set T6 done", the push of `8fcfd83`). Push state: `origin/main` is `8fcfd83`, HEAD 2 commits ahead before the close commits; the developer pushes.
