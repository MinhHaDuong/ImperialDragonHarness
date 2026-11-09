# Research project practices: a reference

Reference, read on demand. It is not a rule and nothing loads it
automatically. It records what the author's research repositories already do,
so a new project can borrow a practice without rediscovering it. The audit
behind it, with its limits and a triaged list of deviations, is in
[2026-10-23-research-project-practices-audit.md](./2026-10-23-research-project-practices-audit.md).

## What this is not

- **Not a directory layout.** No surveyed repository has directories named
  Data, Analysis, Figures and Tables, Article. `climate-finance-het` splits by
  pipeline phase, `archiveCIRED` by index layer, `corpus-access-bench` by
  campaign. A shared tree is not imposed here.
- **Not a mapping to ODEM.** ODEM (Ontology, Data, Evidence, Models) is the
  author's frame for an inquiry, defined in
  `~/CNRS/projets/actifs/ODUM/conception/` (design note v2.0 of 2026-09-22).
  The practices below do not depend on it, and no directory is meant to mirror
  O, D, E or M. Two consequences of the frame do reach repository practice,
  see § ODEM.

## Practices that recur

Each item names where it was seen. Items marked (verified) were checked
against the files by the author of this note; the others rest on a survey
agent's reading and are labelled as such in the audit.

1. **The handoff between analysis and writing is tracked.** Whatever a
   document embeds is in git, so a writing build needs no analysis data.
   `climate-finance-het` does it by allowlist: `.gitignore` ignores
   `deliverables/_shared/figures/*` and re-admits each embedded figure, and
   `tests/test_deliverable_artifacts.py` diffs the list against the real
   include closure in both directions (verified: 11 of 13 figures on disk are
   tracked, the 2 ignored ones are embedded nowhere). `cired.digital` copies
   chosen figures by hand into `slides/slides-assets` (reported).
2. **A deliverable is a self-contained project that declares what it
   consumes.** `climate-finance-het`: one Quarto project per
   `deliverables/<x>/`, with `paths.mk` listing each document's `*_INCLUDES`
   and `*_FIGS` (verified). `polycentric_activity`: one `article-*` directory
   with its own Makefile (reported).
3. **A check compares the declaration to what is used.** An allowlist entry
   that nothing needs is rejected, so exceptions cannot rot into silent skips.
4. **Compute, plot and prose are separate steps.** A script that computes does
   not draw; a script that draws does not write prose
   (`climate-finance-het/.claude/rules/architecture.md`, rule 4).
5. **One make target writes one file, and the recipe asserts it.** File
   targets depend on their script; the recipe ends with `@test -f $@`
   (`cired.digital`, `archiveCIRED`; same idea as `rules/manuscript-build.md`).
6. **Parameters and seeds live in a configuration file**, not in code
   (`climate-finance-het/config/analysis.yaml`, `maiba/config/maiba.yaml`).
7. **Decisions leave a trail that is only appended to.** Tickets
   (`tickets/*.erg`), or a journal when tickets are too heavy
   (`klem-closure-python/JOURNAL.md`, UTC-stamped, corrections as new entries).
8. **A guard is proven by a positive control.** The test asserts on
   `git ls-files`, not on the ignore file, and first checks a case known to
   fire (`corpus-access-bench/tests/test_instrument_sealed.py`, reported). The
   same idea is in `rules/workflow.md`, "A null result is not a finding until
   a positive control has fired".
9. **The network stays out of the fast check.** Network targets are excluded
   from `make check` with a comment on each, and slow tests carry pytest
   markers (`archiveCIRED`, reported).
10. **Sealed or private material never enters git; a hash manifest of it
    may.** `corpus-access-bench` tracks `MANIFEST.sha256` of the sealed
    instrument and ignores the instrument (reported).
11. **A regression is a byte comparison against a delivered artifact.**
    `cired.digital`: `make test` regenerates four figures and `cmp`s them to
    those of the delivered report (reported).
12. **Project management and code live apart when the project is partly
    confidential.** `cired.digital`: a parent directory holds accounting,
    discussions, deliverables and secrets, outside git; the code repository is
    open (reported).
13. **Data flows one way**, from the machine that computes to the one that
    writes, never back (`climate-finance-het/.claude/rules/data-location.md`,
    verified).
14. **A research notebook as a wiki** exists in two repositories,
    `sen-causal-reading` and `climate-finance-het`, with a per-claim
    provenance field and a queue of items still to be moved into the
    permanent text (reported; the second states it borrowed the pattern from
    the first).

## ODEM

Two points of the design note bear on how a repository is kept.

- **A result is relative to a version of the ontology, a sample of the data,
  a procedure and stated assumptions** (note § 2.2). In practice a figure or
  table should be traceable to the definitions and the dataset it came from.
  `JETP-observer` does this for its ledger and asks that the vocabulary be
  versioned in time, so an as-of query can rebuild the ontology in force
  (reported, from its acceptance review of 2026-09-23). No other surveyed
  repository does it.
- **A redefinition does not silently carry old results over.** Earlier results
  stay archived under the earlier definition (note § 2.2).

Naming: in the ODEM frame "Evidence" means computed results. A project that
uses the word for something else, such as sources, collides with it;
`JETP-observer` rejected the name for that reason.

## Open questions

- **`docs/`: staging or documentation?** `rules/zotero.md` says `docs/` is
  git-ignored in full. `climate-finance-het` tracks 153 files there (92 `.md`,
  41 `.csv`, 7 `.json`, verified), `aedist` and `JETP-observer` track their
  notes and design documents. Most repositories ignore the PDFs and track the
  notes. The rule may be too coarse; see the audit.
- **Stage names.** `climate-finance-het` names its stages "Phase 1 to 4" in
  its own rules, against `rules/prose/workpackages.md` (plain-language names).
- **Where ODEM objects live in a repository** is undecided and deliberately
  left so.

## Related rules

- `rules/prose/workpackages.md`: handoff artifacts tracked, prose edited in
  place, plain-language names.
- `rules/manuscript-build.md`: assert the product, not the exit code.
- `rules/zotero.md`: Zotero is the system of record; `docs/` staging.
- `rules/coding-python.md`: uv, lock, `RUN` prefix in Makefiles.
