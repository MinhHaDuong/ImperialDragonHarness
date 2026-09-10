> **NON-NORMATIVE.** A review, recorded for information. Nothing here is decided
> or adopted. Its verdict, its ranked findings and its proposed ticket seams are
> the panel's recommendations, not harness policy.

**Panel:** Fable, four seats, led by Fable. **Recorded:** 2026-09-10, verbatim.

Fourth review, and the first scoped to **design** rather than verification: the
owner asked for no figure auditing this round, the previous Fable panel having
done it. Reviews [v3](./2026-09-10-dragon-memory-design-v3.md), frozen; the
current version is [v4](./2026-09-10-dragon-memory-design.md), which acts on it.
Its `valid_while` coverage experiment is recorded separately as
[the coverage ledger](./2026-09-10-valid-while-coverage-ledger.md).

Earlier reviews: [Claude](./2026-09-10-dragon-memory-design-review-claude.md)
and [ChatGPT](./2026-09-10-dragon-memory-design-review-chatgpt.md) on v0,
[Fable](./2026-09-10-dragon-memory-design-review-fable.md) on v1.

---

# Dragon memory design v3 — design review (Fable panel, 2026-09-10)

**Subject:** `docs/2026-09-10-dragon-memory-design.md` v3, §5 and §6, and
tickets 0908–0912, at `origin/main` in worktree `memory-design-v3`.
**Scope:** design only. No figure was audited, no probe re-run; the previous
panel's verification ledger stands. Where a mechanism claim below rests on the
tree, the lead re-checked it by grep before accepting it.
**Panel:** four Fable seats — failure modes and index safety; retention
economics and the score; `valid_while` against a 54-body sample; plan
boundedness — synthesised by a Fable lead. Non-normative.

---

## 1. Verdict

The central move is sound and should be built on: the store is the bodies, the
index is a generated view, nothing is deleted, expiry only unranks. It
dissolves four of v2's defects for real and it makes retention reproducible
from the store alone. What is not earned is the sentence that follows it —
"demotion stops being an operation with a failure mode" — because the index was
defined in §2.3 as buying *unprompted awareness*, and §5 then judges the cut by
*reachability*. Those are different properties; the cut keeps the second and
removes the first, and for a guard-class memory (a rule that stops an action
before it is taken) being below the cut is functionally deletion, since the
agent never forms the hypothesis that sends it to the grep. Three decisions
belong before anyone writes code. **(1)** The generated index's relation to git:
a regenerated, whole-file, score-ordered `MEMORY.md` that stays tracked puts a
merge conflict on every memory-adding PR and contradicts the design's own rule
that derived views are never committed; either untrack it and regenerate at
session start, or decide that only the pass writes it — 0910 records neither.
**(2)** A writer-declared pinned/durable class (P5, in the body, not in an
authored list) that ranks above the cut with a test that no pinned body ever
falls below N, plus the harness hook budget (500 chars, 369 used) raised before
0912 promotes 17–21 entries into a tier that can show five. **(3)** P3 as
specified: on a stratified sample of 54 real bodies the closed grammar
expresses 26%, evaluates 17% from the slug's path, and is the exact truth
condition for 7%; for the feedback majority "no predicate" is "valid forever",
which is defect 4 under a new name. Keep `valid_while` as the minority's
instrument, add negation and a slug-to-checkout resolver, and stop claiming it
replaces the TTL table — writer-declared durability plus `supersedes` is what
replaces it.

The plan's count is roughly right and its seams are wrong: 0911 and 0912 each
bundle three sign-off units, 0912 depends on all three siblings rather than on
0908 alone, and no ticket retires the machinery §6 declares dead or ships the
one resident line P2 rests on.

---

## 2. Findings, ranked by what a wrong answer would cost

### F1. A generated index that stays tracked reintroduces the conflict the file grain exists to avoid

**Claim.** "Two sessions adding two memories never conflict" (§5, flat files);
derived indexes are "rebuilt on demand, never committed … exactly the status
this design gives `MEMORY.md`" (§5, database corollary).

**Why it fails.** 47 `MEMORY.md` files are tracked (`git ls-files`). Today a
session appends one line; under 0910 the generator rewrites the whole top-N in
score order and the cut line moves whenever any body is added anywhere in the
directory. Two branches that each regenerate produce files differing
throughout, so every memory-adding PR conflicts on the index, and the sanctioned
resolution — regenerate, never hand-merge a generated file (`rules/git.md`) — is
exactly what a merge gate cannot do. The alternative reading, that only the
periodic pass writes the index (§5 "periodically, and not per session"), makes
every new memory invisible until the next pass. The runtime's own auto-memory
instruction tells every session to add an index line, and 0910's invariant
("if hand-edited, regeneration overwrites it") discards those lines silently.
0910 chooses none of this.

**Cost.** Highest: the daily write path either stalls on conflicts or silently
loses the authored line.

**What would change my mind.** A decision recorded in 0910: untrack the view
(gitignored, regenerated by the SessionStart hook before the runtime reads it —
with one probe that the hook runs early enough), or an order-stable rendering
(sorted by slug, cut as a per-line filter) with a measured conflict rate over a
week of sibling PRs.

### F2. Below the cut is deletion for the memories the harness most needs resident

**Claim.** "An entry is never dropped … Demotion stops being an operation with a
failure mode" (§5); P2's one resident line makes the store reachable.

**Why it fails.** §2.3 defines the one thing residency buys as unprompted
awareness. The cut removes it and keeps reachability, which is a different
property. An agent greps a directory after forming the hypothesis that a
relevant memory exists; the listing is what supplied the hypothesis. The corpus
already holds the control: 17 genuine cross-project duplicates, every earlier
body greppable in 49 ms, none found — unprompted discovery of an unlisted body
measures at about zero against 11% for a listed one. The overflow line carries
a count, not a subject: it informs a maintainer and cannot prompt a session.

For a guard memory — `feedback_boolean_probe_must_not_expand_the_value`, the
stash rule, the `checkout -- path` trap — the agent by definition does not know
it is about to err, so it never searches. And 0910's starter score, recency,
unranks these first: a guard that has worked for months has no reads (the
skill itself says a title that did its work is never opened) and no recency.
0910's test "a body below N is still reachable" passes while this happens.

**Cost.** Second: the class of memory the harness was built to keep is the
class the score demotes first, and the plan's only test for it is green.

**Fix that does not reintroduce the authored index.** A `pinned:` or durability
field in the body is P5, not an authored list. Pinned entries rank above the
cut and count against the budget; when the pinned set exceeds the budget the
memory skill's own overflow move applies — promote to `rules/`, the channel
§2.5 shows actually closes loops. 0910 needs a second test: no pinned body
ever falls below N.

**What would change my mind.** A measured grep-into-memory rate in sessions
carrying the P2 line, against the unlisted-body control, above a few percent.

### F3. The harness cut is the effective deletion point, and it is 500 characters wide

**Claim.** "The harness index is capped like the others, and it matters more
there" (§5).

**Why it fails.** `tests/test_resident_census.py:45` sets `BUDGETS["hook"]`
to 500; `memory/MEMORY.md` is 369 chars for four entries. 0912 promises 17–21
promotions on its first run — four times the tier's capacity. Below the harness
cut a promoted lesson is resident nowhere: its project copies are tombstoned
(0908) and it has lost the two or more project indexes it had. Past the fifth
slot, promotion strictly reduces reach. The design's own open question — what
does promotion do that a `rules/` line does not (§2.5) — has an answer at the
cut: nothing. 0910 names only `BUDGETS["memory"]`; the harness budget lives in
the `hook` channel and no ticket touches it.

**Cost.** Cross-project lessons become the least-resident class on the first
consolidation run.

**What would change my mind.** The hook budget raised and a stated rule for the
harness overflow (the `rules/` migration queue) before 0912 lands.

### F4. `valid_while` covers a quarter of the corpus, and the default for the rest is defect 4

**Claim.** P3 replaces the TTL table; "most contradictions should not survive"
because `valid_while` retires the entry that became false; revival is the
argument for keeping everything.

**Why it fails.** Sample of 54 live bodies (20 harness project, 15 git-erg, 15
AEDIST paper, 4 harness tier; ledger at
`/tmp/valid_while_ledger-2c1a7649.md`):

| | expressible | evaluable from the slug's path | predicate *is* the truth condition |
|---|---|---|---|
| all 54 | 14 (26%) | 9 (17%) | 4 (7%) |
| feedback (36) | 5 (14%) | | |
| user (2) | 0 | | |
| project (9) | 6 (67%) | | |
| reference (7) | 3 (43%) | | |

The 40 inexpressible: 13 behavioural (a tool's, runtime's or model's habit), 13
owner facts or preferences, 8 unconditional incident lessons, 2 negation-shaped
("true while X is absent from CI.yml"), 1 cross-host, 1 forge-side, 2 dated
snapshots. Feedback is 74% of the corpus and 14% of it carries a predicate, so
the predicate-less majority is "valid forever" — the complaint §4 makes about
the TTL table, reproduced under a mechanism whose name says otherwise.

Four further points. *Evaluability, not expressibility, binds:* 5 of the 14
expressible predicates name a checkout that is not at the slug's path on this
host (git-erg moved under `CNRS/code/`, no alias; the AEDIST slug's directory
holds no repo), so under fail-open they are "valid plus lint" indefinitely, and
the lint cannot be cleared by an edit. *Write-time "must evaluate true" needs a
resolver the writer lacks:* the writer is in a worktree of the memory's repo,
the scorer runs in the harness; predicates on harness paths name `~/.claude/…`,
which `check-agnostic.sh` flags in `projects/`. *Form (c) is nearly empty and
half of it points the wrong way:* nine bodies corpus-wide pin a version, six as
lower bounds ("since 2.1.266"), which "below a version" cannot state; the
upper-bound cases (`gh pr edit` broken) have an unknowable bound at write time,
so fail-closed accepts any large guess; `erg version` prints a sha, not a
number. *Revival is real for about 5%:* two sampled bodies would expire
correctly today (`scripts/beat.py` absent; rtk past 0.42.1) — those are the
revival candidates, and they are not an argument for the design.

Event-rot is the dominant killer today and has no form: of the 40 tombstones on
the tree, roughly half read "milestone consumed", "gate passed", "ticket
closed", "talk delivered", and a third "absorbed into rules/…". Under P1 these
persist, stay valid, and, being project-state written last, win a recency cut.

**Cost.** 0911 executed as written ships a mechanism that declares validity for
a quarter of the store and leaves the majority where §4 found it, with the TTL
table's name removed from the problem.

**What would change my mind.** Negation as a fourth form (cheap, still closed;
covers ~20 more corpus-wide); a first-class slug-to-checkout alias map the
scorer consults; a harness-root token in the grammar; and a stated default for
predicate-less entries that is a writer-declared durability tier plus
`supersedes`, not "forever". Drop the revival argument from the rationale.

### F5. The write path as it actually runs is not covered by "originals are in git"

**Claim.** A bad merge or tombstone is recoverable because the originals are in
git history (§5; `skills/dream/SKILL.md`).

**Why it fails.** The runtime writes memory straight into the primary checkout,
uncommitted — this session's opening status showed two modified indexes and
five untracked bodies there. `/dream` runs in that same checkout by decision
(ticket 0247). A body created or edited between the pass's read and its
tombstone or merge write is overwritten with no committed ancestor: the one
loss P1 promises never happens, on the freshest feedback. `commit.py` sweeps
whatever survives into the dream commit, which hides the case. Two adjacent
gaps: two passes racing have no run-level lock (the branch name
`dream-consolidate-<date>` collides on the same day and `commit.py` stages the
whole directory, so each commit carries the other's half-done tombstones); and
`memory/.provenance.json` is one 258 KB document edited by every run and merged
across branches by three-way text merge — the design's SQLite blob one level
down, whose `promoted`/`last_confirmed` fields drive the next promotion and
whose corruption the coverage gate cannot see.

**Cost.** Silent and unrecoverable, on the highest-value bodies.

**What would change my mind.** 0912 refuses to start on a dirty memory
directory or commits the dirty state as its own baseline first; a run-level
flock; per-body provenance in frontmatter (P5) with the JSON demoted to a
regenerable ignored cache — the pattern §5 already prescribes.

### F6. The score's inputs cannot carry a score, and "recency" is undefined

**Claim.** P4: with a grep on the other side, a mis-rank only hides a line;
0910 may start with recency and gain 0911's inputs later.

**Why it fails.** Zero bodies carry a date in frontmatter. `.provenance.json`
has `first_seen`/`last_confirmed` batch-stamped by dream runs (78 entries share
one timestamp; 543 of 972 have first equal to last), so ordering on them is run
order plus slug alphabet. File mtime, the runtime's choice, is destroyed by
every clone and daily pull. Git last-commit recency is reset corpus-wide by
0911's own normalisation sweep. Git first-commit is the only stable recency,
and it is the one that demotes the oldest guards (F2). 0910 says "recency"
without choosing. Reproducibility is conflated with quality: 0910's only test is
idempotence, which a constant order passes, and no ticket carries a quality
criterion. Recency does beat random here — the direction of the read-rate by
age survives the exposure confound — but the loss is concentrated in pointer
entries that exist nowhere else.

**Cost.** Medium: a ranking nobody can say is working, over inputs that make
two clones disagree.

**What would change my mind.** A named recency source (git first-commit or
provenance, stated); pinned tiers with creation-recency within tier and no
weights; a miss-rate instrument — any `Read` of a body not in that day's index
is a ranking miss, and `usage`'s slug extraction plus an index snapshot
measures it — with the positive control of deliberately unranking one followed
body and watching it fire.

### F7. The plan omits the retirements and P2's door, and inverts store and view in one reader

**Claim.** §6: "Dead, and worth naming so nobody revives them: the decay pass
and its TTL table, the corpus cap, the orphan collector, and the full-catalogue
file." 0909: "deliberately not children".

**Why it fails.** Naming them prevents adding them; it deletes nothing. The
decay pass (`provenance.py:303`, `SKILL.md:254-272`, `confirm` at :244, tests in
`test_dream.py:455-551`), the TTL table (`memory/SKILL.md:49-57`), the 200-line
cap (`dream/SKILL.md:119`), and the paragraph "the index is the only door …
never shorten this index by unlisting an entry" (`dream/SKILL.md:126-132`) all
stay live, and the last contradicts 0910 outright. P2's one resident line
saying the store can be searched and how — the premise of every "still
reachable" claim — is in no ticket. `read-index.py:50-57` reads entries from
`MEMORY.md`, so after 0910 the dream classifier sees only the top N: the view
becomes the store's source for the pass. The authored "## Key insights" block
(15 of 46 indexes; generated by `dream/SKILL.md:157`, rendered at :106-111) has
no source under a generated view, and 0910 is silent on it.

**Cost.** 0910's central criterion cannot be met as filed, and its executor
faces three mid-run decisions.

### F8. Second-order costs of keeping everything, at the horizons where they bite

- **False positives are re-judged forever (immediate, cheap).** 0912 has no
  rejection ledger; the ~22 lexical false positives are re-proposed to the model
  and the reviewer on every pass. The quadratic compare is not the expensive
  part; the human queue is, and a queue of repeats produces rubber-stamping —
  the poisoning entry the review step exists to close. Record rejected pairs by
  content-hash pair.
- **The grep door at 3–5× (measurable now).** `grep -li worktree` hits 215 of
  949 bodies; `gh pr` 96. A door returning 215 paths is larger than the index it
  replaces; at 3× it needs its own ranking, where P4's "only hides a line" no
  longer holds because nothing is behind it.
- **Rule-shadowed entries (modest, growing).** A third of tombstones read
  "absorbed into rules/"; 42 live bodies cite a rules file; the grammar has no
  "pattern absent" form, so a lesson that graduates to a rule stays
  double-resident. Cross-project mind-change: `supersedes` is declared by the
  new writer, who in seven `gh_pr_edit` copies never knew the old slug.
- **The alarm is a record (non-issue on horizon; mislabelled).** 0912 action 7
  records count and duration; no threshold, no reader, no surface. It measures
  the compare, which is cheap; the items above are what scale. At the observed
  rate 10× is about three years off.
- **Non-issues:** tombstones (40, skipped by `_bodies_in`, so absent from the
  pair set; a `# PROMOTED … Now at:` stub found by grep is a redirect); git
  size (278 of 2 807 commits touch memory, 38 MiB pack, 4.3 MB bodies — a
  decade of headroom); crash mid-regeneration (a regenerable view; a stale line
  points at a stub the reader still opens) provided the next *pass* regenerates.

### F9. Lower-cost observations

- A gate flip to the runtime's mtime-synthesised index lists tombstone stubs
  (`.md`, fresh mtimes, no frontmatter) and blinds the census test, which
  measures the file rather than what is loaded. Store survives; budget and
  overflow line do not. Low while the flag is closed.
- Rejected promotion PR: tombstones and harness body travel in one branch, so
  rejection is atomic *only* while 0912 keeps one PR per run; a reviewer
  dropping one of five promotions orphans its tombstone. One test closes it:
  every `# PROMOTED … Now at: X` has a live X.
- The embedding database, hash cache, equivalence test and local-model
  condition occupy ~600 words of §5 and no ticket. §2.5 says lexical suffices.
  Either amend §5 or 0909 fails its own "§6 matches what shipped" criterion.

---

## 3. Verdict on the five tickets as a plan

The count is nearly right; the seams and the dependency line are wrong.

**Traceability gaps (load-bearing in §5, absent from all five):** P2's resident
search line; retirement of decay/TTL/200-line cap/"never unlist"; the
`read-index.py` inversion; the Key-insights decision; P5's stated-by-owner /
observed / inferred provenance field (no such field exists in
`provenance.py`); the embedding cache and its equivalence test; the semantic
report over the ranked set; a threshold and reader for the alarm; the harness
hook budget; the rejection ledger; a run lock and dirty-tree refusal.

**Sizing.** 0908: one unit, fine (add the new marker to the coverage test's
positive control; assert on the five named slugs, not "drops by exactly five",
which races with any session writing memory before merge). 0910: named three
files, touches about eight plus 46 regenerated indexes; two units (generator
plus tests; retirement of contradicting prose and caps) and three undecided
inputs (git status of the view, recency source, Key insights). 0911: a
954-file migration (47 no frontmatter, 208 top-level `type:`, 746
`metadata.type`) bundled with a grammar, a resolver, write-path integration
where no write path exists as code (`memory/SKILL.md` is prose, and the
runtime's auto-memory writes bypass it), `supersedes` in a generator 0910 has
not shipped, and scorer integration — three units. 0912: eight actions, at
least five units (pool and group; near-miss and provenance reports;
model-judged merge; PR-routed harness review; tombstoning with `supersedes`),
and it depends on 0910 (regeneration), 0911 (`supersedes` on merged bodies)
and 0908 — the tracker's "only 0912 has a real prerequisite (0908)" is wrong
in both directions.

**Proposed wave order.** W1, independent: 0908; 0911a frontmatter migration
(a data PR reviewable by count); **0913, new: retire the dead machinery and
ship P2's line** — delete `decay`/`confirm` and their tests, the TTL table, the
200-line cap and the "never unlist" paragraph; move or restate the harness
index budget; add the one resident line naming the search, with a test that it
is resident and under budget. Depends on nothing; 0910 depends on it. W2: 0910
with the three decisions recorded in its body and a pinned-never-below-N test
beside the idempotence test. W3: 0911b grammar (with negation) plus resolver
(alias map, harness-root token) plus scorer plus `supersedes`; 0911c write-path
check only if a write path exists as code, else enforce at scoring and say so.
W4: 0912a deterministic pool, lexical grouping, near-miss report, rejection
ledger, count and duration with a threshold that fails a test, dirty-tree
refusal and run lock. W5: 0912b model merge, PR-routed review, tombstoning.
Delete from the plan, or park as deferred in §5: the embedding database and
cache.

**Exit-criteria defects.** 0910 "no entry becomes unreachable" is a null trap —
and by §2.4's own logic an unlisted body is unreachable until P2's line ships;
the positive control is an over-budget fixture with a known slug below the
cut, body present, overflow count equal to live minus N, and the documented
search finding it by `name:`. 0910 "N derives from a budget" needs the fixture
to exceed the budget or an empty directory passes. 0911 "47 untyped typed" is a
count-of-zero shape; ship a lint test with a deliberately untyped fixture. 0912
"17–21 genuine pairs" is judged, not gated — promote the Test section's fixture
pair and named false positive into the criterion; "same footing" is
unmeasurable as phrased, use the straddling fixture; "no file-count cap
introduced" is an absence claim, drop or ratchet it; "duration recorded" is
not an alarm without a threshold.

---

## 4. One sentence for the owner

Reachable is not resident: the cut deletes awareness, which is the only thing
the index buys, so declare in each body which memories must stay above it, keep
the generated index out of git, and treat `valid_while` as the instrument for
the quarter of the store it can actually describe.

---

## Passing note on figures (not audited)

§5 says the harness tier is "369 characters for five entries"; `memory/MEMORY.md`
lists four. Immaterial to the design.
