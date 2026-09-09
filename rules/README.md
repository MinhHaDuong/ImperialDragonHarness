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
| [authoring-skills.md](./authoring-skills.md) | `**/SKILL.md`, `**/skills/**/*.md` | Writing a skill: name capabilities not tools, discoverability-first `description:`, quoted frontmatter, declared concurrency, naming. |
| [edm.md](./edm.md) | `**/*.bib`, `**/*.ris`, `**/docs/**` | EDM discipline — Zotero is the system of record; `docs/` and `.bib` are git-ignored staging. Also named by `/zotero-import` and `/index-source`. |
| [knowledge-hints.md](./knowledge-hints.md) | `**/.knowledge.toml`, `**/knowledge_hints.py` | `<repo>/.knowledge.toml` + `scripts/knowledge_hints.py`: one catalog line resident at session start, pointer + caveat on a declared term. Inject the pointer, never the payload. |
| [manuscript-build.md](./manuscript-build.md) | `**/Makefile`, `**/_quarto.y(a)ml`, `**/*.latexmkrc` | An unresolved `\cite`/`\ref` is a link error, not a warning: gate the build on the log, vendor the check, `.DELETE_ON_ERROR`. |
| [systemd-units.md](./systemd-units.md) | `**/*.service`, `**/*.timer`, `**/systemd/**` | What PID 1 reads at boot lives on the root filesystem: install units as real copies, never symlinks into a late-mounted volume; `is-enabled` lies after a `daemon-reload`. |
| [state.md](./state.md) | `STATE.md` | STATE.md format spec — sections, length cap, pruning rules. |

Not a rules file, and not loaded by this mechanism: `tickets/AGENTS.md` reaches
a session through `@tickets/AGENTS.md` in the project's own `CLAUDE.md`.

## Per-file rule injection (axis model)

`paths:` is coarse where the axis is not a path: any `.tex` edit brings all
three doctypes and both languages. `scripts/inject_rule_on_edit.py` (PreToolUse
`Edit|Write`) is the precise channel — on the first edit of a file along each
axis it injects the one body that applies, then stays silent (deduped per
`session_id` + rule). Before the bodies were scoped it re-served what was
already resident, 1 069 times in 101 days; scoping is what gives it back a job.

| Axis | Resolved from | Rule path |
|------|---------------|-----------|
| **format** | filename extension (project-agnostic) | `format/<value>.md` (legacy alias: `coding-<value>.md`) |
| **doctype** | `\documentclass` sniff for `.tex`; else project manifest | `doctype/<value>.md` |
| **lang** | project manifest (`lang` per glob, else `default_lang`) | `lang/<value>.md` |
| **prose** | implied for prose formats | `prose/_all.md` |

Missing rule files are skipped silently, so content grows by adding files — no
code change. Doc-type and language are not derivable from a filename: they come
from an optional per-project manifest `<repo>/.claude/rules-map.toml`, which
holds path→axis *mappings* only, never rule text. Format, precedence and a
worked manifest live in the hook's own docstring; the same resolver is the
single source for prose/code review routing (`scripts/prose_predicate.py`).

## Resident rules

`workflow.md` `git.md` `claude-code.md` — the whole resident set, plus this
index. Bodies in context already, listed here only so an adapter knows what to
ship, and `claude-code.md` is the one an adapter on another runtime skips.

Three former rule bodies left in 2026-09-09 because their trigger is a *task*,
which no `paths:` glob reaches: they are the skills `/pdf-finish`,
`/cut-prose` and `/submission-event`. A skill's description stays resident in
the catalog and its body loads on invocation — the same pointer-and-payload
split as `paths:`, for triggers a filename cannot express.

`claude-code.md` is the runtime-specific one: an adapter on another runtime
loads every other resident file and skips it.

**A runtime without this auto-load gets none of it.** On the Pi and Codex
adapters, the resident set must be injected by the adapter
or made genuinely on-demand; `~8 800 tokens` is what that decision moves.

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
