# Harness rules — index

Lightweight pointer table injected at session start. Read individual
files on demand when their scope signal applies to your task.

| File | Scope | Summary |
|------|-------|---------|
| [workflow.md](./workflow.md) | always | Session start gate, escalation protocol, when to ask the author, subagent and compaction rules. |
| [git.md](./git.md) | always | Branch discipline, commit-message standards, worktree lifecycle, merge-request workflow; prose-in-place exception for paper repos. |
| [state.md](./state.md) | skill-list: `/lair` | STATE.md format spec — sections, length cap, pruning rules. |
| `tickets/AGENTS.md` (project-level) | skill-list: `ticket-*`, `hunt` | Ticket format rules injected via `@tickets/AGENTS.md` in project CLAUDE.md — no global rules file needed. |
| [coding-python.md](./coding-python.md) | edit of `*.py` (alias: `format/python`) | Python 3.10+ style, testing markers, Make rules, `uv` workflow. |
| [coding-bash.md](./coding-bash.md) | edit of `*.sh` (alias: `format/bash`) | Bash `set -euo pipefail` discipline: arithmetic-zero abort, unbound associative-array key. |
| [prose/_all.md](./prose/_all.md) | edit of any prose file (`*.tex` `*.qmd` `*.md` `*.txt`) | Universal prose rules: LLMism guards, Elements of Style. |

Compliance is verified ex post by the `verify-adherence` skill — this
index is the single source of truth on when each rule file applies.

## Per-file rule injection (axis model)

`scripts/inject_rule_on_edit.py` (PreToolUse `Edit|Write` hook) injects the full
body of every matching **global** rule the first time you edit a file along each
axis in a session — then stays silent (deduped per `session_id` + rule). Rules
stay global and shared; only the *mapping* can be project-local. A file resolves
along four orthogonal axes, and the injected set is their union:

| Axis | Resolved from | Rule path |
|------|---------------|-----------|
| **format** | filename extension (project-agnostic) | `format/<value>.md` (legacy alias: `coding-<value>.md`) |
| **doctype** | `\documentclass` sniff for `.tex`; else project manifest | `doctype/<value>.md` |
| **lang** | project manifest (`lang` per glob, else `default_lang`) | `lang/<value>.md` |
| **prose** | implied for prose formats | `prose/_all.md` |

Missing rule files are skipped silently, so content grows by adding files — no
code change. Doc-type and language (not derivable from the filename) come from an
optional per-project manifest `<repo>/.claude/rules-map.toml`:

```toml
default_lang = "fr"
[[map]]
glob = "slides/manuscript/**/*.tex"
doctype = "techreport"
lang = "fr"
```

The manifest holds path→axis *mappings* only, never rule text — the rulebook
itself stays here, shared across every project.
