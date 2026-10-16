<!-- Cookbook index. One line per entry, appended by tools/cookbook_add.sh. Grep this file by tag or title; never read it whole; never read an entry you did not find here. -->
<!-- C<nnnn> | <title> | <tags> | <date> | <phase>/<task> | origin: <source section or report id> -->
C0001 | Name probe scripts uniquely; never shadow a stdlib module | python,scratch,gotcha | 2026-10-11 | 1.1/T2 | T2 summary gotcha
C0002 | Locate Amiga-packed blobs in an MD ROM: magic, header bound, packer checksum | megadrive,compression,imploder,extraction | 2026-10-11 | 1.1/T2 | R1.1-003
C0003 | Resolve an ambiguous compression spec by variant grid, all-or-nothing | compression,decoder,verification | 2026-10-11 | 1.1/T3 | T3 summary gotcha
C0004 | Headless Ghidra on Windows: paren args, stdin, markers, thunks | ghidra,headless,windows,gotcha | 2026-10-12 | 1.2/T1 | T1,T4 summary gotchas
C0005 | MAME debugger+Lua as a 68000 oracle: sp, pc+2, soft_reset, trace | mame,oracle,lua,68000,gotcha | 2026-10-12 | 1.2/T2 | T2,T3,T4 summary gotchas
C0006 | BizHawk Lua second oracle: reboot drops callbacks, firmware modal | bizhawk,oracle,lua,megadrive,gotcha | 2026-10-12 | 1.2/T5 | T5 summary gotchas
C0007 | Native Windows /x switches from Git bash/make: MSYS path rewrite | windows,msys,make,assembler,gotcha | 2026-10-12 | 1.3/T1 | T1 summary gotchas
C0008 | Prove a boundary assert fires: taken branch, short region file | assembler,assert,build,split,gotcha | 2026-10-12 | 1.3/T3 | T1,T3 summary gotchas
C0009 | Probe assembler encodings with per-case size asserts per switch | assembler,probe,encoding,assert | 2026-10-12 | 1.4/T1 | T1 summary gotchas
C0010 | Prove a source-include hook is live: grep wrapper, not only hash | build,split,include,hash,gotcha | 2026-10-12 | 1.4/T2 | T2 summary gotchas
C0011 | Choose assembler by full-region scan: converter defect vs rewrite | assembler,listing,matching,ghidra | 2026-10-12 | 1.4/T3 | T3 summary gotchas
C0012 | MAME read taps vanish after remap: reinstall per frame, positive control | mame,oracle,lua,coverage,gotcha | 2026-10-12 | 1.5/T4 | T4 summary gotchas
C0013 | Ghidra Bad Instruction on valid 68000 words: Capstone cross-check first | ghidra,capstone,oracle,boundaries,gotcha | 2026-10-12 | 1.5/T4 | T4 summary gotchas
C0014 | MAME breakpoint indices are hex: format with %X before bpdisable | mame,oracle,debugger,gotcha | 2026-10-13 | 1.6/T1 | T1 summary gotchas
C0015 | 68000 read tap hit on a row's first word is prefetch, not a read | mame,oracle,68000,prefetch,gotcha | 2026-10-13 | 1.6/T1 | T1 summary gotchas
C0016 | make skips rebuild on same-second edits: delete target before controls | make,build,negative-control,gotcha | 2026-10-13 | 1.6/T3 | T3 summary gotchas
C0017 | Write census proves a field is written, not its meaning: name neutrally | naming,oracle,ram,struct,evidence | 2026-10-13 | 1.6/T4 | T4 summary gotchas
C0018 | Struct field at +0 renders as bare base name; 0 uses is expected | naming,listing,struct,gotcha | 2026-10-13 | 1.6/T4 | T4 summary gotchas
C0019 | Project script named like a stdlib module: load by path via importlib | python,import,stdlib,gotcha | 2026-10-13 | 1.6/T5 | T5 summary gotchas
C0020 | Capstone m68k reports d8(An,Xn) with d8=0 as base-displacement mode | capstone,68000,encoding,gotcha | 2026-10-13 | 1.6/T5 | T5 summary gotchas
C0021 | Draft comments written away from the listing are wrong about half the time | comments,listing,verification,wave | 2026-10-13 | 1.7/T7 | T7 summary harvest (T8)
C0022 | Neutral RAM names spill over: name RAM before comments | naming,ram,sweep,wave | 2026-10-13 | 1.7/T7 | T7 summary harvest (T8)
C0023 | Readability closeness is mechanical: sweep it by script before manual waves | naming,sweep,routing,wave | 2026-10-13 | 1.7/T7 | T7 summary harvest (T8)
C0024 | Code name equal to a region id double-defines the label | naming,build,as,gotcha | 2026-10-13 | 1.7/T7 | T7 summary harvest (T8)
C0025 | Sidecar names need renderer support for every addressing form | naming,renderer,68000,listing | 2026-10-13 | 1.7/T7 | T7 summary harvest (T8)
C0026 | CRLF checkouts under core.autocrlf=true: ship .gitattributes eol=lf | git,windows,eol,gotcha | 2026-10-13 | 1.7/T4 | T4 summary gotchas
C0027 | Prove a never-raised exception handler by injecting a 68000 frame in MAME | mame,68000,exception,oracle,verification | 2026-10-13 | 1.7/T5 | T5 summary gotchas
C0028 | Claim checker for prose comments: fixed claim grammar plus planted bad fixture | comments,verification,health,fixture | 2026-10-13 | 1.7/T8 | T8 summary gotchas
C0029 | Ghidra headless refuses project paths with a dotted element | ghidra,headless,windows,paths,gotcha | 2026-10-13 | 1.8/T1 | T1,T2 summary gotchas
C0030 | Windows path aliases: subst breaks relpath; rm -rf follows junctions | windows,paths,junction,subst,gotcha | 2026-10-13 | 1.8/T1 | T1,T2 summary gotchas
C0031 | python -I hides user site-packages in prerequisite checks | python,bootstrap,gotcha | 2026-10-13 | 1.8/T3 | T3 summary gotcha
C0032 | MAME runs: per-run EEPROM copy, save-state machine time, EEPROM layout by diff | mame,oracle,eeprom,savestate,gotcha | 2026-10-16 | 1.9/T1,T10 | T1,T10 summary gotchas
C0033 | Scripted menu input on MAME: spacing, poke plus press, state overwrite | mame,oracle,input,savestate,scenario | 2026-10-16 | 1.9/T1,T5,T6 | T1,T5,T6 summary gotchas
C0034 | MAME Lua env: loadfile into _ENV, proxy env to wrap a probe, tap pitfalls | mame,lua,oracle,probe,gotcha | 2026-10-16 | 1.9/T2,T38,T10,T32 | T2,T38,T10,T32 summary gotchas
C0035 | Probe design: positive and negative controls, discriminating pokes | oracle,probe,verification,controls | 2026-10-16 | 1.9/T2,T5,T6 | T2,T5,T6 summary gotchas
C0036 | Per-frame RAM sampling lands mid game-frame: read through it with taps | mame,oracle,ram,timing,probe | 2026-10-16 | 1.9/T5,T6,T8,T9 | T5,T6,T8,T9 summary gotchas
C0037 | Measure from recorded RAM series: raw dumps and single-frame prediction | oracle,ram,measurement,model | 2026-10-16 | 1.9/T7,T9 | T7,T9 summary gotchas
C0038 | MAME debugger breakpoints from a Lua hook: load census and blob swap | mame,debugger,lua,decompression,probe | 2026-10-16 | 1.9/T10,T43 | T10,T43 summary gotchas
C0039 | 68000/Mega Drive immediates: signed print, boot-loaded base reg, DMA mirror | 68000,megadrive,vdp,ghidra,constants | 2026-10-16 | 1.9/T2,T3 | T2,T3 summary gotchas
C0040 | comments.tsv: sort by address, eol before plate, or roundtrip differs | ghidra,comments,roundtrip,gotcha | 2026-10-16 | 1.9/T12,T30,T31 | T12,T30,T31 summary gotchas
C0041 | Comments and claims the checkers read: plate start, RANGE form, run ids | comments,commentcheck,claims,gotcha | 2026-10-16 | 1.9/T12,T16,T40.1,T43,T44 | phase 1.9 summary gotchas
C0042 | signatures propagate refusals and region-id label names | naming,signatures,build,gotcha | 2026-10-16 | 1.9/T20,T22,T24,T34,T42 | phase 1.9 summary gotchas
C0043 | Ghidra: label at a default function entry renames it; apply labels post-analysis | ghidra,headless,labels,gotcha | 2026-10-16 | 1.9/T34 | T34 summary gotchas
C0044 | Call-graph system assignment: hub votes mislead; identity evidence first | callgraph,census,routing,systems | 2026-10-16 | 1.9/T11 | T11 summary gotcha
C0045 | Claim checker: classify pointers by shape, one planted-bad line per kind | verification,fixture,commentcheck,claims | 2026-10-16 | 1.9/T4 | T4 summary gotcha
