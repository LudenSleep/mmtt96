# mk/health.mk — the health chain (phase 1.5 T3), included from the Makefile. Each rung's comment names the incident or
# rule that earned it. Pair lines are `-` prefixed so every pair runs; the summary line decides the exit code.
# `make health`: one `pair <name>: agree|DISAGREE` per pair + `health: pairs <a>/<n> agree`, report
# .run/mmtt96-health/report.txt (never .run/health.json, harness-owned). Controls: `pairs.py <pair> --plant` exits 1.
# Child tool output: .run/mmtt96-health/logs/<pair>.log. `make health-live`: the live oracle rung, run detached.

HEALTH_PAIRS = MAKE="$(MAKE)" "$(PY)" scripts/health/pairs.py

health:
	# stale results from a previous run must not count: the summary reads only this run's pair files
	rm -rf .run/mmtt96-health/pairs
	# T1 gap 10: Ghidra/Java must answer before any pair runs; hard stop (no `-`) on a probe failure
	"$(PY)" scripts/ghidra/db.py probe
	# DK-9 pair 1 (G25/C0008 control: --plant code_0002FA): Ghidra listing boundaries vs a Capstone linear sweep
	-$(HEALTH_PAIRS) boundaries
	# DK-9 pair 2, P1.4-1: forced make src (db.py listing --all-code -> asm/src) + instruction-form build vs all-data
	# SRC= build, both hash OK and identical; a last make build leaves asm/src and the default tree in instruction form
	# (asm/src is local-only, ignored, never tracked: G12, decision D1)
	-$(HEALTH_PAIRS) srcform
	# DK-9 pair 3, G9: incremental build vs clean rebuild, equal and hash OK
	-$(HEALTH_PAIRS) incremental
	# DK-9 pair 4: census partition vs TSV rows, manifest region records and ROM size; progress.py partition check
	-$(HEALTH_PAIRS) census
	# DK-9 pair 5, H1: the hand-edited regions TSV vs its generated Ghidra mirror, row for row
	-$(HEALTH_PAIRS) mirror
	# DK-9 pair 6: MAME executed PCs (coverage.tsv) vs code rows
	-$(HEALTH_PAIRS) coverage
	# DK-9 pair 7, P1.2-1: check_maps offline, MAME datapoints vs BizHawk second-oracle runs (live form: health-live)
	-$(HEALTH_PAIRS) checkmaps
	# plan 1.6 T2, G6/G62: routine-name registry rows vs signatures recomputed from the ROM (drift fails; control row)
	-$(HEALTH_PAIRS) signatures
	# plan T3: names-on vs --no-names db.py listing over a verified code subset, plus the config/names -> symbols.tsv
	# mirror (control: --plant moves one ram.tsv equate in a scratch copy of config/names)
	-$(HEALTH_PAIRS) names
	# G12 firewall: no run of AS-style instruction lines in any tracked text file; hard fail, not a pair
	"$(PY)" scripts/health/asm_leak.py
	# plan 1.6 T5, G12/encoding map: every encoding form of the verified code has a docs/encoding-map.md coverage row; hard fail
	"$(PY)" scripts/census/encodings.py
	# plan 1.7 T8: milestone census, 0 undecoded, every ledger row classed/routed; hard fail
	"$(PY)" scripts/census/ledger.py check
	# plan 1.7 T8: wave 1 had 23/42 draft comments wrong; comment claims vs tables, then the planted-failure control
	"$(PY)" scripts/census/commentcheck.py
	"$(PY)" scripts/census/commentcheck.py --self-test
	# plan 1.9 T3: every immediate at a VDP control / Z80 bus / I/O port renders over hw.tsv (0 raw), then the
	# negative control: a planted wrong hw value (scratch names copy) must leave raw candidates; hard fail
	"$(PY)" scripts/census/constants.py check
	"$(PY)" scripts/census/constants.py check --plant
	# DK-9: the chain is green iff every pair agrees
	"$(PY)" scripts/health/pairs.py summary

health-live:
	# P1.2-1: re-run each map claim's probe live under MAME (and BizHawk for second-oracle claims); run detached
	"$(PY)" scripts/oracle/check_maps.py --live
