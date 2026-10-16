# Build the retail ROM from split sources: split (ROM -> asm/), assemble (asm/ -> build/mmtt96.bin), hash check.
# Run from Git bash. Variables PY ROM ASM REGIONS SRC NAMES are overridable on the command line.
# SRC: dir of hand/decompiled region sources (asm/src/<id>.asm); SRC= builds all data.
# Default SRC=asm/src is generated (target src): db.py listing --all-code, every code region (verified + inferred), self-checked;
# needs Ghidra + Java (docs/ops/ops-setup-decomp.md). asm/src is ignored, never tracked (G12).
# NAMES: names registry dir (ram.tsv, routines.tsv, ...) for split.py and db.py listing; default config/names.

# PY default: python3 if it actually runs (a Windows Store stub exists but may not), else python
PY      ?= $(shell python3 -c "import sys" >/dev/null 2>&1 && echo python3 || echo python)
ROM     ?= disks/Micro Machines Turbo Tournament 96 (Europe) (v1.1) (J-Cart).md
ASM     ?= tools/bin/asl/asw.exe
P2BIN   ?= tools/bin/asl/p2bin.exe
REGIONS ?= config/regions.retail.tsv
SRC     ?= asm/src
NAMES   ?= config/names

OUT     := build/mmtt96.bin
STAMP   := asm/.stamp
SRCLIST := asm/.srclist
SRCSTAMP := asm/src/.stamp
NAMESTAMP := asm/.names
SRCLOG  := .run/src/listing.log
empty   :=
space   := $(empty) $(empty)
ROM_DEP  = $(subst $(space),\ ,$(ROM))
# the assembler runs with cwd = asm/, so a relative ASM/P2BIN is anchored at the repo root
ASM_RUN  = $(if $(filter /% %:/%,$(ASM)),$(ASM),$(CURDIR)/$(ASM))
P2BIN_RUN = $(if $(filter /% %:/%,$(P2BIN)),$(P2BIN),$(CURDIR)/$(P2BIN))
SRC_ASM := $(if $(SRC),$(wildcard $(SRC)/*.asm))
# asm/.srclist = SRC value + sorted src ids, rewritten only when its content changes, so a SRC switch or an
# added/removed src file re-splits while an unchanged set leaves the stamp alone
SRCLIST_TEXT := SRC=$(SRC) $(sort $(basename $(notdir $(SRC_ASM))))
ifeq ($(filter clean,$(MAKECMDGOALS)),)
# T1 gap 5: PY must run and import capstone (split/listing/health need it); checked once at parse time
PY_OK := $(shell "$(PY)" -c "import capstone" >/dev/null 2>&1 && echo ok)
ifneq ($(PY_OK),ok)
$(error PY=$(PY) does not run or cannot import capstone; pass PY=<python with capstone> (see docs/ops/ops-setup-decomp.md))
endif
ifneq ($(SRCLIST_TEXT),$(shell cat $(SRCLIST) 2>/dev/null))
$(shell mkdir -p asm && printf '%s\n' '$(SRCLIST_TEXT)' > $(SRCLIST))
endif
# asm/.names = NAMES value, same pattern: switching NAMES re-lists and re-splits
ifneq (NAMES=$(NAMES),$(shell cat $(NAMESTAMP) 2>/dev/null))
$(shell mkdir -p asm && printf '%s\n' 'NAMES=$(NAMES)' > $(NAMESTAMP))
endif
endif

.DEFAULT_GOAL := build
.DELETE_ON_ERROR:
.PHONY: src split build expected clean health health-live

src: $(SRCSTAMP)

split: $(STAMP)

build: $(OUT)
	sha1sum -c config/check.retail.sha

expected: build
	mkdir -p expected
	cp $(OUT) expected/mmtt96.bin

clean:
	rm -rf build asm/src asm/rom asm/main.asm asm/imp.asm asm/.stamp asm/.srclist asm/.names asm/names.inc asm/hw.inc asm/ram.inc asm/rom.inc asm/main.p asm/main.lst

$(ROM_DEP):
	@echo "make: no ROM dump at $(ROM); copy your own dump there (see docs/ops/ops-setup-decomp.md)" >&2
	@exit 2

# instruction source: all verified code regions listed and self-checked in one run (~12 s, no per-region cache); any
# failure removes asm/src and stops (no dc.b fallback); success writes asm/.srclist in the parse-time format above
$(SRCSTAMP): $(ROM_DEP) $(REGIONS) $(NAMESTAMP) $(wildcard config/ghidra/*.tsv $(NAMES)/*.tsv) scripts/ghidra/db.py \
             scripts/ghidra/Mmtt96Listing.java scripts/build/split.py
	rm -rf asm/src
	mkdir -p $(dir $(SRCLOG))
	"$(PY)" scripts/ghidra/db.py listing --all-code --out asm/src --names "$(NAMES)" > $(SRCLOG) 2>&1; rc=$$?; cat $(SRCLOG); \
	if [ $$rc -ne 0 ]; then \
	  rm -rf asm/src; \
	  bad=$$(grep '^listing ' $(SRCLOG) | grep -v -e ', match$$' -e '(unrendered)$$' | cut -d' ' -f2 | tr -d ':' | tr '\n' ' ' | sed 's/ $$//'); \
	  echo "make: db.py listing failed ($${bad:-see output above}); asm/src removed" >&2; exit 1; \
	fi
	printf '%s\n' "SRC=asm/src $$(ls asm/src | sed -n 's/\.asm$$//p' | LC_ALL=C sort | tr '\n' ' ' | sed 's/ $$//')" > $(SRCLIST)
	touch $@

$(STAMP): $(ROM_DEP) $(REGIONS) scripts/build/split.py $(SRCLIST) $(NAMESTAMP) $(wildcard $(NAMES)/*.tsv) \
          $(if $(filter asm/src,$(SRC)),$(SRCSTAMP))
	"$(PY)" scripts/build/split.py --rom "$(ROM)" --regions "$(REGIONS)" --out asm --src "$(SRC)" --names "$(NAMES)"

# written at parse time above; these empty rules only stop "no rule" errors when absent (after clean)
$(SRCLIST) $(NAMESTAMP) asm/main.asm asm/hw.inc asm/ram.inc asm/rom.inc: ;

# asw -> asm/main.p (an `error` assert leaves none), p2bin -> flat bin; any failure leaves no bin
$(OUT): $(STAMP) $(ASM) $(P2BIN) asm/main.asm asm/hw.inc asm/ram.inc asm/rom.inc $(wildcard asm/rom/*.asm asm/imp.asm) $(SRC_ASM)
	mkdir -p build
	rm -f $(OUT) asm/main.p
	cd asm && "$(ASM_RUN)" -q -xx -n -U -i . main.asm && "$(P2BIN_RUN)" main.p ../$(OUT) || { rm -f ../$(OUT); exit 1; }

# health chain (differential pairs + firewall rung): make health, make health-live
include mk/health.mk
