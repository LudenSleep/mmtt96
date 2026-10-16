---
name: edit-escapes-with-edit-tool
description: Edit backslash-bearing source with the Edit tool; Bash heredocs collapse double backslashes to one
---

# Edit Escapes With Edit Tool

Captured 2026-10-12 from .run/pe14/wf.md.

## When to use
a change contains backslash escapes

## Steps
# Edit escape-bearing Python with the Edit tool, not a heredoc
When: a change to a Python (or any) source contains backslash escapes (regexes, `\` in strings).
Why: a Bash heredoc collapsed a double backslash to a single one even with a quoted delimiter in this harness, corrupting the file silently.
How: use the Edit tool (exact string replace) for such edits; if a script must be written, write it with the Write tool, then run it.
