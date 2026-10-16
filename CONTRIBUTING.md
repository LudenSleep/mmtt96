# Contributing to Micro Machines Turbo Tournament 96 decomp

## Bring your own copy of the game

Every contributor extracts from their own legally obtained copy. No byte of the game is committed: no ROM, extracted
payloads, disassembly listing, converted assembly source, assets, build output, memory images, Ghidra database, vendor
SDK, or notes that paste the game's instructions. Analysis notes that contain no game bytes are welcome: address-keyed
names and comments, ledger rows, and documentation of how the game works. The `.gitignore` firewall stops the ordinary case; `tools/audit_public.py` refuses the rest and runs in CI
on every push; review `git status` before every commit. CI (`.github/workflows/no-rom.yml`) has two jobs, neither
needing a dump: `audits` (the public-repo audit) and `selftest` (census and signatures fixtures, the commentcheck
self-test, a planted `asm_leak` control); see `docs/ops/ops-tools.md` `## ci`.

## What "done" means

The game is hand-written 68000 assembly; there is no C and no compiler here. A change is done when `make build` still
prints `build/mmtt96.bin: OK` (the byte gate: the rebuilt ROM hashes identical to the original) **and** `make health`
still ends with every pair agreeing. Verify from a clean rebuild (`make clean && make build`), never an incremental one.
"Looks equivalent" is never done.

## Where changes go

The assembly source under `asm/` (including `asm/src/`) is generated from your dump on every build: never hand-edit it,
never commit it. Every change goes into a tracked sidecar row keyed by address, which the build renders into the source:
names in `config/names/*.tsv` (`routines.tsv` is written by the signature tools, not by hand; `ram.tsv` and
`structs.tsv` take RAM, I/O and struct names), comments in `config/ghidra/comments.tsv`, and each region's state on the
campaign ledger `config/campaign/ledger.tsv`. Run `scripts/census/commentcheck.py` after editing comments (it checks
every comment's mechanical claims against the tables), then the byte gate and `make health`.

## Names and comments

A symbol is renamed only on recorded evidence: a string it prints, a cross-reference chain, a debug menu, at least three
consistent live-memory datapoints, a community label with provenance. **If you are not sure what something does, leave
it unnamed rather than name it wrongly**; the address-named placeholder is honest and greppable. One definition per
structure; a duplicate is a defect. A comment states what the evidence shows; mark an original bug as such in its comment.

## AI use — conduct

This project uses Claude Code to assist with analysis and tooling; a person reviews every change, and the byte-identical build check is the only proof that anything matches.

The rules that keep that honest, for every contributor and every agent:

1. **The byte gate is the only claim of success.** Never report a match the gate has not proven; "it compiled" and "looks
   equivalent" are not results. "Banked" is written from a tool's printed success line.
2. **Names and types are evidence-based, never guessed.** A model may propose a name; a person with recorded evidence asserts
   one. Hallucinated meaning is the specific way a model damages a decompilation without any test catching it.
3. **Outward text is written by a person.** Issues, pull requests, forum posts and outreach to other projects are written
   by their author the way a developer writes — short, plain, from the facts — never a model draft with the tells removed.
   Before contributing to another project, read and follow its own AI-contribution policy.
4. **No automated traffic against community infrastructure.** Shared services are used by a person in a browser; anything
   repetitive is replicated locally.
5. **Agents assist; a person owns.** Every change is justifiable by a person from the record (the phase logs, the decision
   log, the cookbook's byte proofs).

## Submitting

Small, per-routine or per-family changes; `make clean && make build` and `make health` green; a commit message that
names what changed and how it was verified; no AI-attribution trailers.

## Community files

Conduct: `CODE_OF_CONDUCT.md`. Security concerns: `SECURITY.md`. Issues use the forms in `.github/ISSUE_TEMPLATE/`
(bug report, question); pull requests use `.github/pull_request_template.md`.
