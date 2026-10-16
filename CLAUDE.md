# Micro Machines Turbo Tournament 96 decomp — Project Architect 3.0
Matching decompilation of Micro Machines Turbo Tournament 96 (Mega Drive, Europe v1.1)

Roles: planner · router · expert · coder · retriever · critic. Rules: the `project-architect` skill.
Standing facts and tools: `HOW_WE_WORK.md`. Live plan: `phase-ends/current/PHASE_PLAN.md`
(changed only via `tools/plan_edit.py`). Constitution: `PROJECT_CONTEXT.md` (never edited).
Roadmap: `GENERATION_PLAN.md`. Full rule texts: `rules/INDEX.md`. Techniques: `cookbook/INDEX.md` (grep it).

Every agent, always: never push; no AI trailers; never write memories; never `/compact`, `/model`, `/effort`;
never Read `phase-ends/*/logs/`, `research/`, PhaseEnds or `tool-results/*.txt` whole: grep/tail or dispatch
a retriever; commands that may print >40 lines run via `tools/run.sh`; commit via `tools/commit_task.sh`;
a one-time fetch is a fetch, not a tool.

Fail-safes: never push · the milestone gate is the arbiter
