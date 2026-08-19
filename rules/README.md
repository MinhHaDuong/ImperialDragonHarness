# Harness rules — index

Lightweight pointer table injected at session start. Read individual
files on demand when their scope signal applies to your task.

| File | Scope | Summary |
|------|-------|---------|
| [workflow.md](./workflow.md) | always | Session start gate, escalation protocol, when to ask the author, subagent and compaction rules. |
| [git.md](./git.md) | always | Branch discipline, commit-message standards, worktree lifecycle, merge-request workflow; prose-in-place exception for paper repos. |
| [state.md](./state.md) | skill-list: `/lair` | STATE.md format spec — sections, length cap, pruning rules. |
| `tickets/AGENTS.md` (project-level) | skill-list: `ticket-*`, `hunt` | Ticket format rules injected via `@tickets/AGENTS.md` in project CLAUDE.md — no global rules file needed. |
| [knowledge-hints.md](./knowledge-hints.md) | a project declares or maintains domain knowledge an agent cannot search for (canon, controlled vocabulary, map of a field) | `<repo>/.knowledge.toml` + `scripts/knowledge_hints.py`: one catalog line resident at session start, pointer + caveat on a declared term. Inject the pointer, never the payload; write the summary context-free. |
| [edm.md](./edm.md) | skill-list: `zotero-import`, `index-source` | EDM discipline — Zotero is the system of record; `docs/` and `.bib` are git-ignored staging, synced and purged on archival. |
| [coding-python.md](./coding-python.md) | edit of `*.py` (alias: `format/python`) | Python 3.10+ style, testing markers, Make rules, `uv` workflow. |
| [coding-bash.md](./coding-bash.md) | edit of `*.sh` (alias: `format/bash`) | Bash `set -euo pipefail` discipline: arithmetic-zero abort, unbound associative-array key. |
| [manuscript-build.md](./manuscript-build.md) | a manuscript build (LaTeX/tectonic, Quarto/pandoc) is set up or changed | An unresolved `\cite`/`\ref` is a link error, not a warning: gate the build on the log, vendor the check, `.DELETE_ON_ERROR`. |
| [pdf-finishing.md](./pdf-finishing.md) | finishing pass of any PDF deliverable (submission, deposit, personal page) | Automate pagination (titlesec, widow penalties, dash-ratio widths); scripted pdftotext checklist; variants as archived transform layers. |
| [submission-events.md](./submission-events.md) | a manuscript's submission state changes (submitted, resubmitted, accepted, published) | Propagate the event to the external registers: homepage `Ha-Duong.bib` (rebuild + deploy) and CNRS secretariat `Feuille de route <year>.odt` (+ PDF). |
| [prose/_all.md](./prose/_all.md) | edit of any prose file (`*.tex` `*.qmd` `*.md` `*.txt`) | Universal prose rules: LLMism guards, Elements of Style. |
| [prose/cutting.md](./prose/cutting.md) | a pass cutting prose to a word/page budget | Remove whole passages before condensing; displaced ≠ deleted; a cut plan starts with the whole-removal pass. |
| [doctype/techreport.md](./doctype/techreport.md) | edit of a `techreport` file (`\documentclass{report}` or manifest) | Report conventions: standalone abstract, numbered floats with takeaway captions, label cross-references. |
| [doctype/slides.md](./doctype/slides.md) | edit of a `slides` file (`\documentclass{beamer}` or manifest) | Slide conventions: one idea per slide, takeaway titles, fragments not paragraphs. |
| [doctype/book.md](./doctype/book.md) | edit of a `book` file (`\documentclass{book}` or manifest) | Book conventions: book-wide terminology, chapter openings/closings, label cross-references. |
| [lang/fr.md](./lang/fr.md) | edit of a `lang = "fr"` file (manifest) | French norms: espaces insécables, guillemets « », virgule décimale, casse de phrase. |
| [lang/en.md](./lang/en.md) | edit of a `lang = "en"` file (manifest) | English norms: one spelling variety, serial comma, sentence-case headings. |

Compliance is verified ex post by the `verify-adherence` skill — this
index is the single source of truth on when each rule file applies.

## Review cadence

Each rule body carries a `last-reviewed: YYYY-MM-DD` marker, as an HTML comment
on the first line or as a frontmatter key where the file has frontmatter.
`scripts/warn-stale-rules.sh` runs at session start and warns, advisory only,
when one is 30 or more days old. It scans `rules/*.md` and one level of
subdirectory, so the `prose/`, `doctype/` and `lang/` bodies are covered. This
`README.md` is the index rather than a rule body and carries no marker.

A file without a marker is skipped, not flagged, so absence buys permanent
silence: a new rule body needs its marker at creation. Two files sat unmarked
and unmonitored for months before the 2026-08-14 review found them.

Read the marker for what it records: deliberate review passes, not edits.
Nothing bumps it when a rule is amended in place, so an old stamp is weak
evidence of rot — on 2026-08-14 the two loudest warnings named the two files
with the most commits since their stamps — and a recent one is worth exactly as
much as the pass that set it. Stamping a file you have not read makes the
marker lie, and nothing downstream can catch that.

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
