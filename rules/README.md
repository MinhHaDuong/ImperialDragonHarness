<!-- last-reviewed: 2026-09-09 -->
# Harness rules — how they load

`~/.claude/rules/**.md` is loaded by the runtime itself, not by a hook. The
mechanism was isolated on 2026-09-09 in the Claude Code bundle (2.1.266): the
rules directory is walked at session start and each `.md` is sorted on one
question — does its frontmatter declare `paths:`?

- **No `paths:` → the body sits in the system prompt of every session, in every
  project**, labelled "user's private global instructions for all projects".
  Such a file needs no entry here: it is already in front of you, and each body
  opens with its own scope line. Describing it again is paying for it twice.
- **`paths:` → conditional.** The body arrives only when the session touches a
  matching file. These are the rules an agent does *not* have by default, so
  they are the ones this index names.

That is the whole index. It is short because the runtime already did the work;
it was 942 words while shipping full copies of what it summarised.

## Conditional rules — absent until a matching file is touched

| File | Loads on | Summary |
|------|----------|---------|
| [coding-python.md](./coding-python.md) | `**/*.py` | Python 3.10+ style, testing markers, Make rules, `uv` workflow. |
| [coding-bash.md](./coding-bash.md) | `**/*.sh` | Bash `set -euo pipefail` discipline: arithmetic-zero abort, unbound associative-array key. |
| [prose/_all.md](./prose/_all.md) | `**/*.tex` `**/*.qmd` `**/*.md` `**/*.txt` | Universal prose rules: LLMism guards, Elements of Style. |
| [doctype/techreport.md](./doctype/techreport.md) | `**/*.tex` | Report conventions: standalone abstract, numbered floats with takeaway captions, label cross-references. |
| [doctype/slides.md](./doctype/slides.md) | `**/*.tex` | Slide conventions: one idea per slide, takeaway titles, fragments not paragraphs. |
| [doctype/book.md](./doctype/book.md) | `**/*.tex` | Book conventions: book-wide terminology, chapter openings/closings, label cross-references. |
| [lang/fr.md](./lang/fr.md) | prose files | French norms: espaces insécables, guillemets « », virgule décimale, casse de phrase. |
| [lang/en.md](./lang/en.md) | prose files | English norms: one spelling variety, serial comma, sentence-case headings. |
| [state.md](./state.md) | `STATE.md` | STATE.md format spec — sections, length cap, pruning rules. |

The path glob is coarse where the axis is not a path: any `.tex` edit brings
all three doctypes and both languages. `scripts/inject_rule_on_edit.py` is the
precise channel — it resolves doctype from `\documentclass` and lang from the
project manifest, and injects the one body that applies. Before 2026-09-09 it
re-served bodies that were already resident (1 069 injections in 101 days);
scoping is what gives it back a job.

Not a rules file, and not loaded by this mechanism: `tickets/AGENTS.md` reaches
a session through `@tickets/AGENTS.md` in the project's own `CLAUDE.md`.

## Resident rules

`workflow.md` `git.md` `knowledge-hints.md` `edm.md` `manuscript-build.md`
`pdf-finishing.md` `prose/cutting.md` `submission-events.md` `systemd-units.md`
— bodies in context already, listed here only so an adapter knows what to ship.

**A runtime without this auto-load gets none of it.** On the Pi and Codex
adapters (tickets 0800, 0802) the resident set must be injected by the adapter
or made genuinely on-demand; `~22 000 tokens` is what that decision moves.

Compliance is verified ex post by the `verify-adherence` skill.

## Review cadence

Each rule body carries a `last-reviewed: YYYY-MM-DD` marker, in the frontmatter
where the file has one, else as an HTML comment on the first line.
`scripts/warn-stale-rules.sh` runs at session start and warns, advisory only,
when one is 30 or more days old. It scans `rules/*.md` and one level of
subdirectory, so `prose/`, `doctype/` and `lang/` are covered.

A file without a marker is skipped, not flagged, so absence buys permanent
silence: a new rule body needs its marker at creation. Two files sat unmarked
and unmonitored for months before the 2026-08-14 review found them.

Read the marker for what it records: deliberate review passes, not edits.
Nothing bumps it when a rule is amended in place, so an old stamp is weak
evidence of rot — on 2026-08-14 the two loudest warnings named the two files
with the most commits since their stamps — and a recent one is worth exactly as
much as the pass that set it. Stamping a file you have not read makes the
marker lie, and nothing downstream can catch that.

Age is only half the drift. `tests/test_rules_resident_budget.py` caps what the
resident set may cost, so a body that grows one incident bullet at a time hits
a gate instead of a reader's patience.
