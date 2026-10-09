# Ticket 0375 — project-local rule inventory (trial run, 2026-10-09)

Sweep scope: every `.claude/rules/*.md` under `~/CNRS/papiers/**` and
`~/CNRS/projets/actifs/*` (worktrees excluded). The ticket's
`~/Climate_finance` now lives at `~/CNRS/projets/actifs/climate-finance-het`.

Result: **22 files in 2 repos** — climate-finance-het (18), aedist (4). No
paper repo under `~/CNRS/papiers/` carries a `.claude/rules/` directory; two
repos (`livre-milliards-climat`, `polycentric_activity`) carry only a
`rules-map.toml`, outside this sweep's rule-text scope.

Layers: **P** universal prose (`prose/_all.md`), **D** doctype, **L** lang,
**T** prose-test doctrine (new `rules/prose-adherence-tests.md`), **H** already
harness-level (trim locally, no promotion), **X** project-local (argument,
corpus, venue, voice, toolchain), **O** out of writing scope (code/workflow;
listed, not promoted — author's call below).

No **L** rule was found in either repo.

## Writing rules — verdicts

| Source | Rule | Layer | Action |
|---|---|---|---|
| cfh writing.md | Core argument, periodization, corpus size | X | keep (argument/corpus) |
| cfh writing.md | Self-check questions, "not a policy paper" | X | keep (argument/venue) |
| cfh writing.md | Voice and style, things to avoid | X | keep (voice) |
| cfh writing.md | Falsifiable claim names its falsifier ex ante | D | **promoted** → doctype/article.md; trim |
| cfh writing.md | Conclusion introduces no new facts | D | **promoted** → doctype/article.md; trim |
| cfh writing.md | Continuum not two camps; ΔBIC ≠ bimodality; KMeans IDs | X | keep (analysis-specific) |
| cfh writing.md | Quarto `{{< meta >}}` outside inline math | X | keep (toolchain trap, one project) |
| cfh writing.md | Citation practices | X | keep (corpus/field) |
| cfh writing.md | Ghost mode / no AI tells | H | trim to pointer: prose/_all.md LLMism guards + `/review-pr-prose` |
| cfh writing.md | CI test polarity rule + editorial brief | T | **promoted**; trim to pointer |
| cfh writing.md | Pure prose tickets skip TDD | T | **promoted**; trim |
| cfh writing.md | Sweep, not a guard (+ guard-shaping notes) | T | **promoted** (doctrine only; the incident narrative stays local or in memory) |
| cfh writing.md | Testing (`make check-fast`, clean build) | X | keep |
| cfh writing.md | When to ask the author | H | trim (workflow.md escalation) |
| cfh oeconomia-style.md | Oeconomia house style | X | keep (venue) |
| cfh review-checklist.md | Doc propagation list | X | keep |
| cfh deliverables.md | Deliverable layout, DOC_VARS, paths.mk | X | keep |
| aedist writing.md | No heading above a one-paragraph subsection | D | **promoted** → doctype/article.md; trim |
| aedist writing.md | Absence claims: "to our knowledge" | P | **promoted** → prose/_all.md; trim (keep in Related Work gap line as local pointer) |
| aedist writing.md | Forward-reference, don't link outward | X | keep (judgment: could be D) |
| aedist writing.md | Never hardcode cross-reference numbers | D | already harness-level in doctype/techreport.md and book.md; not re-added to article.md (2 000-char axis budget) — author's call; keep the local test + house LaTeX conventions |
| aedist writing.md | House conventions for `main.tex` (labels, `§\ref`, annex counters, backmatter order, `\fpath`, em-dash glyph, `\newunicodechar`, `tectonic -r 2`) | X | keep (toolchain/venue) |
| aedist writing.md | Related Work citation budget and paragraph mix | X | keep (author preference; `/related-work-note` already carries a budget field) |
| aedist writing.md | Gap paragraph at end | X | keep (judgment: could be D) |
| aedist writing.md | Cite closely related projects unconditionally | X | keep (corpus) |
| aedist writing.md | No in-repo documents in the bibliography | D | **promoted** → doctype/article.md; trim |
| aedist writing.md | Figures are script artifacts, no inline pgfplots | X | keep (judgment: manuscript-build.md candidate) |
| aedist writing.md | ≤3 macros inline (tectonic bundle trap) | X | keep |
| aedist writing.md | Manuscript numbers via generated macros | P | **promoted** (principle) → prose/_all.md; keep local mechanics |
| aedist writing.md | CI test polarity rule + loose anchors + conditional negatives | T | **promoted**; trim to pointer |
| aedist workflow.md | Derive prose from generated artifacts, not agent enumeration | P | **promoted** (merged with the macros rule above); trim |

## Non-writing rules — classified, not promoted

| Source | Rule | Layer | Note |
|---|---|---|---|
| cfh architecture, data-location, openalex-corpus, null-model, jetp-observatory, keystore, script-io, state-roadmap | pipeline, data, corpus, site, credentials | X | project-local |
| cfh coding.md | `uv run`, Make truth | H | duplicates rules/coding-python.md; trim candidates |
| cfh coding.md | Test tiers, data traps (null DOIs, NaN truthy, human judgments) | O | coding-python candidates |
| cfh git.md | branch naming, agent identity, submission branches, `--delete-branch` | X/H | branch naming duplicates harness; rest local |
| cfh ticket-filing.md | fast path, ID-collision scan | O | tickets/AGENTS.md candidate |
| cfh worktree-setup.md, rules-editing.md | worktree file copy; edit rules from a worktree | X/H | rules-editing duplicates workflow.md § Worktree paths |
| cfh workflow.md | science lane vs tooling lane | O | elaborates the harness severity floor |
| aedist workflow.md | test one before blasting; audit before instrumenting | O | workflow candidates (resident budget) |
| aedist workflow.md | prefer skills over commands | O | authoring-skills.md candidate |
| aedist experiment-design.md | genericity, pinned reps, no_think, metrics dict, MoE repeat=3 | X | project-local (MoE non-determinism could become memory) |
| aedist json-output.md | JSON files end with one newline | O | coding-python candidate |

## Counts

- Files swept: 22 (2 repos); 0 in paper repos.
- Writing rules: 31 rows — P 3, D 5 (4 promoted, 1 already in techreport/book), L 0, T 4, H 2, X 17.
  (P counts the absence claim plus the two sources of the generated-numbers rule.)
- Promoted: 11 rule rows, collapsed into 2 prose lines, 4 article lines,
  1 new 8-bullet file. Left local: 17 X; 2 H trims.
- Non-writing rows: 11 (not promoted; 6 flagged as other-rule candidates).

## Proposed trims per project file (separate per-repo PRs, author's call)

- **climate-finance-het `writing.md`:** replace § Ghost mode with a one-line
  pointer to `/review-pr-prose`; replace § CI test polarity rule with a pointer
  to the harness rule plus the local test path and the 0338/0590 evidence
  link; drop the first two bullets of § Claims; drop § When to ask the author.
- **climate-finance-het `rules-editing.md`:** delete (harness worktree rule).
- **climate-finance-het `coding.md`:** drop the `uv run` bullet's generic half.
- **aedist `writing.md`:** drop the absence-claim, one-paragraph-heading and
  no-in-repo-bibliography rules; shorten the hardcoded-crossref rule to the
  local test and house conventions; replace § CI test polarity rule with a
  pointer, keeping the local anchor examples.
- **aedist `workflow.md`:** shorten § Derive prose from generated artifacts to
  the local test and the 0452 evidence.

## Judgment calls for the author

1. The test-polarity doctrine went to a new conditional file, not
   `prose/_all.md`: its trigger is a test or brief edit, not a prose edit, and
   `_all.md` has a 6 000-char budget. Accept the new file or fold it elsewhere.
2. The new file's `paths:` globs assume test files named `*prose*`/`*manuscript*`;
   other names miss it.
3. The generated-numbers rule is now universal and binds every project. The
   cross-reference rule was not added to article.md (budget); articles get it
   only if you raise the 2 000-char axis budget or move it to prose/_all.md.
4. Non-writing candidates (O rows) are out of this ticket's axis scope; file
   follow-ups or drop.
5. Forward-reference, gap paragraph and figures-as-artifacts were left local;
   any could be promoted to doctype or manuscript-build.md.
