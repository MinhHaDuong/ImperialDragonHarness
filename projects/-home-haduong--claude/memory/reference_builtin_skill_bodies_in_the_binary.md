---
name: reference_builtin_skill_bodies_in_the_binary
description: Built-in skill bodies ship as zstd frames inside the Claude Code ELF; how to extract them, and the pointer-to-payload ratio they demonstrate.
metadata:
  type: reference
---

The runtime is one ~207 MB ELF at
`~/.local/share/claude/versions/<version>`; no skill files sit on disk. Bodies
and their reference trees are **zstd frames** inside it, exported from a bun
bytecode chunk as `SKILL_MD` and `SKILL_FILES` (paths like
`/$bunfs/root/SKILL-<hash>.md.zst`). Descriptions are separate: plain JSON/JS
string literals, sometimes **concatenated from several fragments** —
`claude-api`'s is a reference line, a `TRIGGER` block and a `SKIP` block, and a
decoder that stops at the first string gets a third of it.

Extraction, Python 3.14 (`compression.zstd` is stdlib there; `zstandard` is not
installed): scan for the magic `28 b5 2f fd`, feed each hit to a
`ZstdDecompressor`, and keep the frames where `.eof` is set. About 136 of ~3 972
magic hits decompress — the rest are false positives. `zstd.decompress` on a
slice fails where the streaming decompressor succeeds, because the frame
boundary is unknown.

What it is worth knowing for: the **pointer-to-payload ratio**. `claude-api`
costs ~360 resident tokens and carries a reference tree whose *Model Migration
Guide* alone is 246 KB; `dataviz` costs ~480 for ~43 KB of palette, validator
and mark specs. Roughly 1:100 — and the resident half is written as a *routing
rule* (when to load, when not, with a `grep` that decides), not as a
description. Harness skills invert this deliberately: the ones a user invokes
by name carry 60-100 char descriptions, and only the task-triggered ones
(`index-source`, `biblio-saturation`, `submission-event`) spend 300-450.

The binary also carries skills absent from any local catalog — `workshop`,
`whiteboard`, `prototype`, `verify`, `plan`, `design-sync` — so an inventory
read from it is the runtime's, not this account's.

Related: [[reference_claude_code_goal_command]] (same technique, different
target), [[feedback_derived_token_figures_must_be_swept]].
