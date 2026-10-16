# NOTICE — game-derived source

This repository tracks **no source derived from *Micro Machines Turbo Tournament 96*** (Sega Mega Drive / Genesis,
Motorola 68000 + Z80; Europe v1.1 (J-Cart), Codemasters; ROM SHA-1 e8ff759679a0df2b3f9ece37ef686f248d3cf37b). The game's
reassembled 68000 source is generated on your own machine, from your own dump, into the ignored folder `asm/src/`, and
is never committed (decision D1, `docs/decisions/source-location.md`). This folder holds only this notice.

*Micro Machines Turbo Tournament 96* and its code are the property of their rights holder. This project is not
affiliated with, sponsored by or endorsed by the rights holder.

**No license is asserted over anything derived from the game.** The generated source exists for study, interoperability
and preservation: to document how the game works, to make its code readable, and to keep it buildable. Nothing here grants
anyone more rights in the original work than they already have, and nothing here is a license to distribute the game or
its code. The assembled output is, by design, identical to the original ROM; distributing it is distributing the game.

What this repository does **not** contain: the game's ROM, any disassembly listing or generated source, any memory
image. Building requires your own dump (see the top-level `README.md`).

The rest of the repository (the tooling under `tools/` and `scripts/`, the build system and the documentation under
`docs/`) is the project's own work and is licensed under MIT (`LICENSE`).
