# Gaze — the plan

Loaded from `skills/gaze/SKILL.md` § 2. The one home of gaze's planning
guidance; no other file restates it.

**The cheapest method that settles the what wins.** The intent sets the
focus (the what) and the risk (the why). Gaze plans a method that answers
that question and nothing wider; the `review plan:` line records what it
covered, and no label claims more.

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
- **History.** Earlier gaze answers of this merge request's review
  (`review_notes.py answers --unit pr:<n>`; a PR gazed before notes evidence:
  its gaze result comments): what they covered, on which head, and what
  changed since.

#### Methods, cheapest first

| Method | Plan item | When it settles the what |
|---|---|---|
| Check | a script run in the review worktree, against old and new code (`git show <ref>:<path>`); model `script`, family `none` | the what is a behaviour a test or a script can show |
| One seat | one code-reviewer or prose-reviewer, one perspective | a narrow what, one concern |
| Panel | several seats in parallel, one perspective each | a what spanning concerns, or a large diff split by directory |
| Other family | a seat from another model family on its headless door (`decorrelation.md`, "The launch line"), or an external reviewer routed by `skills/reviewers/SKILL.md` | a preference (`decorrelation.md` § Family is a preference, not a gate), except on the machinery paths above where the plan includes one: worth it on a high-risk row when the host consents to the spend (the `# spend:` line) and the deadline allows; without it a same-family seat takes the perspective, never called independent |

Plan at least one item that is not `self`: a run where only `self` reports
is `seats: self-only` (SKILL.md § 4), valid but the weakest record. When the
subagent door cannot launch (nesting limit, no delegation tool), plan a
same-family seat on the headless door (`"$IDH_ROOT/scripts/gaze_seat.py"`, which needs no
nesting) before it may fall back to `seats: self-only`; self-only stays only
for "no door launched", that is, every door tried and none started.

**Machinery diffs take an other-family seat** (author ruling 2026-11-01;
evidence: PR #2149, where the coder's self-only gaze missed a blocking
`git cherry` whitespace-amend defect that an OpenAI red-team seat found). When
the changed files include, under `"$IDH_ROOT/scripts/"`, `review_notes.py`,
`merge-gate.py`, `raid_land.py`, `seat_clock.py`, `panel-manifest-check.py`, or
any `gate_*.py` or `gaze_*.py`, or anything under `skills/gaze/`, `skills/merge/`
or `skills/verify-gate/`, the plan includes at least one seat
whose family differs from the producer's (a red team by default), subject to the
spend consent of the `# spend:` line. When no other-family door is reachable or
consented, the plan's `# method:` line says so and a same-family seat takes the
perspective; the result stays valid and is never called independent. No gate
refuses it.

`plan-write` refuses a plan whose every item is self unless
`--no-door "<doors tried>"` names them; the flag becomes a header line that
the plan check reports as a deviation. A planned seat that files no report
(timed out, refused, `NOT-RUN:`) fails the plan check like any missing item.
`gaze_close.py` refuses a `seats: panel` result that no non-self report backs.
Elsewhere a seat of another family is a routing preference, not a requirement
(`skills/route/references/decorrelation.md`): plan one when the host consents
to its spend and the risk, deadline and budget make it worth it.

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

Write it with `python3 "$IDH_ROOT/scripts/seat_clock.py" plan-write <panel>
--intent T --method T --budget <n>m --spend T --item NAME MODEL FAMILY
REASON` (`--item` repeats, once per plan item) before launching anything. The helper
builds `<panel>/manifest.txt` and runs `panel-manifest-check.py` on it; a plan
the checker cannot parse exits 2 and writes nothing. Never write the file by
hand: free text there makes every sentence a seat with no report. Header lines
carry the intent, the method, the budget in minutes, which fits the
15-minute deadline less the closing (at most 13), and the spend: the line
`python3 "$IDH_ROOT/scripts/gaze_seat.py" consent` prints, which names the
providers the author consented to spend on (one host-local key, set once; none
by default). Consent follows the provider that bills the seat, not the family
the plan writes. Each plan item is `name<TAB>model<TAB>family<TAB>reason`, the
reason naming the seat's door (`headless <runtime>`, or `subagent`). An item
is self when its name or its model is `self`: gaze's own read. Every
item, a check included, writes `<panel>/<name>.md`. The item name is the seat's
one name for good: the roster, the `seat:` line, the attribution `seat=` field and
`finding:` lines use it, and `gaze_close.py` builds the identity lines from it
(ticket 1303). It carries no round or ticket suffix (`correctness`, never
`correctness-r1`), so records of one seat join across reviews; the reason names
the door as `headless <runtime>` (the runtime of the seat's line) or `subagent`.

#### Worked cases

##### Small intent: verify one fix

Arguments `1700 verify the fix for finding 2 because it was blocking` on a
twelve-line change to one script. One seat reads the fix and its test.

```text
# intent: verify the fix for finding 2 because it was blocking
# method: one seat on the twelve changed lines and their test
# budget: 10m
# spend: cross-family none consented (cross_family_spend unset in <config path>)
correctness	small-model	anthropic	a few lines of logic; the test is the evidence
```

##### Behaviour claim: a check, no seat

Arguments `1701 verify the parser now rejects an empty key because the ticket's
exit criterion says so`. Running the new test against the old code settles it.

```text
# intent: verify the parser rejects an empty key because of exit criterion 2
# method: run the new test on the base and on the head
# budget: 5m
# spend: cross-family none consented (cross_family_spend unset in <config path>)
regression	script	none	fails on the base, passes on the head
```

##### No intent, high risk: the whole merge request

Arguments `1702` on a 300-line change to a merge gate script. The default what
is the whole merge request against its ticket's exit criteria; a gate is a
high-risk row, and the host consents to OpenAI, so the red team comes from
another family.

```text
# intent: the whole merge request against its ticket's exit criteria
# method: panel; red team from another family: high risk, consented, worth the spend
# budget: 13m
# spend: cross-family consented for OpenAI (<config path>)
correctness	mid-model	anthropic	headless; logic of the gate against the exit criteria
scope	small-model	anthropic	headless; only what the ticket asks
redteam	other-model	openai	headless codex; gate bypass, another family preferred on a high-risk row
```
