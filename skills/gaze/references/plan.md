# Gaze — the plan

Loaded from `skills/gaze/SKILL.md` § 2. The one home of gaze's planning
guidance; no other file restates it.

**The cheapest method that settles the what wins.** The intent bounds the
scope (the what) and sets the risk (the why). Gaze plans a method that
answers that question and nothing wider.

#### Inputs

- **Nature.** Run `cd "$review_tree" && python3 "$IDH_ROOT/scripts/prose_predicate.py" <changed files>`:
  `prose` when a changed file resolves to a doctype, `code` otherwise. It
  reads the disk, so it runs in the review worktree; a refusal (exit 2) is a
  routing error to fix, never `code`. Process prose (notes, tickets) stays
  code. On prose, run
  `cd "$review_tree" && python3 "$IDH_ROOT/scripts/prose_predicate.py" --axes <changed files>`
  and carry its lines verbatim into each prose seat's prompt: told nothing, a
  reviewer guesses the rulebook (it read `rules/doctype/book.md` on a
  `techreport`, MR 136).
- **Size.** The changed lines inside the what, not the whole merge request.
- **Location.** The risk rows of `skills/route/references/decorrelation.md`:
  rules, gates, credentials and deletion are high risk.
- **History.** Earlier gaze result comments on this merge request: what
  they covered, on which head, and what changed since.

#### Methods, cheapest first

| Method | Plan item | When it settles the what |
|---|---|---|
| Check | a script run in the review worktree, against old and new code (`git show <ref>:<path>`); model `script`, family `none` | the what is a behaviour a test or a script can show |
| One seat | one code-reviewer or prose-reviewer, one perspective | a narrow what, one concern |
| Panel | several seats in parallel, one perspective each | a what spanning concerns, or a large diff split by directory |
| Other family | a seat from another model family (`decorrelation.md`, "The launch line"), or an external reviewer routed by `skills/reviewers/SKILL.md` | a high-risk what: worth its cost, by judgement |

Plan at least one item that is not `self`: a run where only `self` reports
is `seats: self-only` (SKILL.md § 4), which callers discard. Plan `self`
alone only when nothing else can launch.

Choose each seat's model through the `route` skill (`skills/route/SKILL.md`),
weaker or stronger as the what needs.

Code perspectives: correctness, consistency, scope, red team, doc
propagation, simplify, rules. **Simplify** looks for needless complexity,
duplication, a mechanism to reuse, and lines that defend against a scenario no
real actor produces: for each, the scenario, who would produce it and what the
defence costs (lines, branches, tests). It is report-only, its findings tagged
`must-fix` or `consider`. It is a code perspective: on prose the prose seats
judge cuts, and a manuscript change travels through
`rules/prose/workpackages.md`. **Rules** judges the change against the written rules: review,
not the mechanical tier. Prose seats: `references/prose-panel.md`.

Not planned: mechanical adherence (the `-m adherence` tests, verify-adherence's
mechanical tier). The merge gate's record runs it before every merge
(`lint`), and hunt's self-gate before the merge request. Lints, such
as the AI-tells list of `config/ai-tells.yml` on prose, are checks, never
seats.

#### The plan file

Write it as `<panel>/manifest.txt` before launching anything, and pass it
through `python3 "$IDH_ROOT/scripts/panel-manifest-check.py"`. Header lines
carry the intent, the method and the budget in minutes, which fits the
15-minute deadline less the closing (at most 13); each plan item is
`name<TAB>model<TAB>family<TAB>reason`. Every item, a check included, writes
`<panel>/<name>.md`.

#### Worked cases

##### Small intent: verify one fix

Arguments `1700 verify the fix for finding 2 because it was blocking` on a
twelve-line change to one script. One seat reads the fix and its test.

```text
# intent: verify the fix for finding 2 because it was blocking
# method: one seat on the twelve changed lines and their test
# budget: 10m
correctness	small-model	anthropic	a few lines of logic; the test is the evidence
```

##### Behaviour claim: a check, no seat

Arguments `1701 verify the parser now rejects an empty key because the ticket's
exit criterion says so`. Running the new test against the old code settles it.

```text
# intent: verify the parser rejects an empty key because of exit criterion 2
# method: run the new test on the base and on the head
# budget: 5m
regression	script	none	fails on the base, passes on the head
```

##### No intent, high risk: the whole merge request

Arguments `1702` on a 300-line change to a merge gate script. The default what
is the whole merge request against its ticket's exit criteria; a gate is a
high-risk row, so one seat comes from another family.

```text
# intent: the whole merge request against its ticket's exit criteria
# method: panel; red team from another family because a gate is high risk
# budget: 20m
correctness	mid-model	anthropic	logic of the gate against the exit criteria
scope	small-model	anthropic	only what the ticket asks
redteam	other-model	openai	gate bypass; another family for a high-risk row
```
