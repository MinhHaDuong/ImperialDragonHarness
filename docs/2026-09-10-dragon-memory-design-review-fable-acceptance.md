> **NON-NORMATIVE.** A review, recorded for information. Nothing here is
> decided or adopted. Its verdict, its named conditions and its ranked
> showstoppers are the panel's recommendations, not harness policy. The norms
> live in `rules/`, `CLAUDE.md` and the tickets — not in `docs/`.

**Panel:** Fable, one seat. **Recorded:** 2026-09-11.

Fifth review, and the first at **acceptance** level: not "is the design
right" but "can implementation start on it without a new decision". Reviews
[v6](./2026-09-10-dragon-memory-design.md) at `origin/main` `8e54245e`. The
earlier reviews — [Claude](./2026-09-10-dragon-memory-design-review-claude.md)
and [ChatGPT](./2026-09-10-dragon-memory-design-review-chatgpt.md) on v0,
[Fable](./2026-09-10-dragon-memory-design-review-fable.md) on v1 (figures),
[Fable](./2026-09-10-dragon-memory-design-review-fable-design.md) on v3 (design,
§5–§6 and the ticket seams) — are taken as settled where v6 acts on them and
are not re-raised. §12 has not been reviewed before: the v3 panel judged the
*tickets'* exit criteria, several of which it found to be null traps, and v6 is
the first version with an acceptance table of its own. That table is where this
review spends its time. Scope is showstoppers only; wording, structure,
deferred calibration and stated exclusions are out of scope by instruction.

---

# Dragon memory design v6 — acceptance review (Fable panel, 2026-09-11)

## Verdict

**Accept with named conditions.** The architecture is settled enough to build
on: the four adopted choices (single ownership contract, one library, optimistic
concurrency, licence-aware reuse) are internally consistent, and I found no pair
of sections that an implementer could not reconcile without a new decision and
no §16.3 first-increment step that depends on something §13 defers — §13.1
orders schema and identity (step 2) before the library (step 5), and §16.3
lets the increment be built and tested on temporary trees, which is necessary
because none of the 1,050 bodies on the tree carries a UUID, lifecycle or
routing field today. What is not yet acceptable is §12.1 as the *gate* the
design says it is. Its opening sentence — "each gate includes a fixture that
fails when the relevant mechanism is removed" — is true of most rows and false
of a few, and two stated invariants have no row at all. The four findings below
are all of that kind: gate-definition gaps, each settled by adding or
restating a row in §12.1, none requiring a change to the architecture. They are
conditions because §12.2 makes the deterministic contracts "hard acceptance
gates": a hard gate that cannot fail is a claim of coverage that will be
believed, and that is the one thing an acceptance suite must not do.

## Showstoppers

Ranked by the cost of the failure each would let through undetected.

### 1. The no-execution invariant on predicates has no gate

**Where.** §7.1 ("It must not execute arbitrary memory-authored shell code";
"At entry, reject malformed predicates and unknown grammar operators"), against
§12.1, which has no row for it. Category (b).

**The failure it permits.** Memory bodies are model-authored, and under §3.3
they travel: a project's `shared-snapshot/` is a committed replica of bodies
authored in *other* projects, refreshed by dreaming. A body carrying a
predicate is therefore untrusted input from outside the consuming repository.
Nothing in §12 distinguishes an evaluator that returns *unknown* for an
operator it does not recognise from one that hands the predicate to a shell,
a template engine or `eval` to find out. Both pass every row in the table: row
10 ("False and unknown applicability") only checks that a false predicate
excludes and an unknown one keeps its label; a predicate that executed and
*then* returned false or unknown is indistinguishable from one that was never
executed. The grammar itself is deferred (§13.2, "bounded portable grammar to
specify") — that is allowed and not the finding. The invariant is not deferred,
and the first increment (§16.3) already evaluates at least the explicit-scope
subset at load, in every session, on every consumer.

**What would settle it.** One row: *predicate carrying an unknown operator, a
path outside the declared root, or a string that would have a side effect if
interpreted* → rejected at entry, *unknown* at evaluation, and a sentinel
(a file the payload would create if interpreted) verifiably untouched. The
sentinel is the positive control that separates "did not execute" from "did
not look". Cheap, deterministic, and it should exist before any
`shared-snapshot/` is ever committed.

### 2. "Canonical store protected from native writes" names a result and no mechanism

**Where.** §11.1 ("its independent memory must not write into that store"),
§11.2 (the adapter "documents how canonical bodies are isolated from native
writers" — documents, not enforces), and §12.1 row *Native loading plus adapter
enabled*. Category (a): a fixture whose pass is indistinguishable from the
mechanism never having been exercised.

**The failure it permits.** As phrased, the fixture needs a live runtime with
native memory enabled and a session in which the runtime *chooses* to write.
That choice is model behaviour; it cannot be forced, so a green run means
either "protected" or "nothing tried". Verified on the tree: on the owner's
machine this repository *is* `~/.claude` (STATE.md, 0887 entry), so today the
canonical directories `memory/` and `projects/<slug>/memory/` are exactly the
runtime's native auto-memory path; no hook in `settings.shared.json`
intercepts writes into them (the `Write|Edit` matchers run the worktree-path
guard and rule injection only); and a native edit that keeps frontmatter
well-formed is invisible to §10.3's malformed-file report *and* to row 6's
revision check, because it lands uncommitted in the working tree and is swept
into the next commit as if a session had authored it — the write-path gap the
v3 panel recorded as F5, reappearing on the other side of the ownership
contract. The design's own migration (§13.1 step 3) moves project bodies out
of this path, but nothing says the new root must be disjoint from every
runtime's native root, and §11.2 leaves isolation to per-adapter prose.

**What would settle it.** Make the protection structural and the fixture
deterministic: (i) the canonical memory root and each supported runtime's
native memory root are disjoint paths, asserted by a test that reads the
adapter's declared native root; (ii) whatever the runtime *does* load is a
generated view carrying a generated-file marker, and the fixture writes a
foreign line into that view, runs a load, and asserts the canonical store is
byte-identical and the foreign line is reported and discarded. No model in the
loop, and a removed mechanism fails it. Until the store leaves `~/.claude`, the
row should be recorded as *known red*, not as a gate.

### 3. The G/C revision overlay has no delivery fixture for a changed revision of the same UUID

**Where.** §6.1 ("New or semantically changed revisions belong to the
supplement, rather than inheriting an obsolete content score"), §6.2 ("if a new
revision replaces an old orientation revision, expose the current revision at
most once. Never fall back to obsolete advice merely because its replacement
did not fit"), §10.2 ("Orientation uses bodies whose revisions still match G;
accepted new or changed revisions in C feed the recent supplement"). Category
(b).

**The failure it permits.** State: body U is ranked in publication G at
revision r1; on the consuming branch U is now accepted at r2 (same UUID, still
`active`, text corrected); the recent supplement is already full. §12.1 has
three rows near this and none on it. Row *Retracted body still present in
stale orientation* covers a lifecycle change, not a revision change. Row
*Replacement is unavailable or below budget* is written for supersession — a
*different* UUID replacing this one — and its "superseded advice" wording does
not read onto an active body whose text moved. Row *New write during dreaming*
checks membership in the unprocessed *set* after publication, not what is
delivered. A loader that walks the published order and renders U from G's
text (the obvious implementation of "walks the published order") passes all
three while injecting the sentence the author just corrected — and under §6.2
the correction is queued behind the supplement's 500-token cut, so the reader
sees the old advice and not the new. This is the drift §14 says v6 removed
("A generated index cannot drift → revision-aware publication plus
current-state filtering"); it is the one invariant the whole G/C construction
exists for, and it has no row.

**What would settle it.** One row with two sub-cases: *same UUID, revision in
C differs from G* → the G text is never rendered; the C revision appears in the
supplement if it fits, else the UUID appears nowhere and the backlog report
names it. The removed mechanism (revision comparison at load) fails it. Rows 3
and 4 could be widened instead, but "replacement" and "superseded" are terms
of art in §4.3 and §9.1 and should not be stretched to cover an active body.

### 4. Absence-shaped rows, and "reported / disclosed" clauses without a surface

**Where.** §12.1 rows *Rediscovery in several projects* and *Pending editorial
review*, and the result clauses "unavailability is reported", "divergence
reported", "reduced capability is explicit", "no false completeness claim",
"retained cumulative injection is measured", "uncontrollable exposure
disclosed" (rows 4, 13, 14, 15, 16, 18). Category (a).

**The failure it permits.** *Rediscovery in several projects → candidate
consideration only; no automatic scope change or synthesis* has no mechanism
whose removal makes it fail: the operation it constrains is editorial judgment
(§9.1, "Generalisation requires an explicit judgment"), and a pass that does
nothing, or a dreaming step not yet built, passes it. It is the same shape the
v3 panel flagged in 0912's "no file-count cap introduced" ("an absence claim,
drop or ratchet it"), and it guards exactly the v4 behaviour §14 says was
removed — promotion that tombstoned project copies on a match count. A gate
that cannot fail cannot protect that decision. *Pending editorial review →
compilation still succeeds* has the same shape: no compiler anyone would write
waits on a review, and the fixture does not say what artefact represents
"pending". The "reported / disclosed" clauses are a milder case: they are
falsifiable only if the report is a named structured field the fixture asserts
on; as prose they are satisfied by a log line nobody reads, and §12.1 does not
say which. §16.3 ("Return structured results to adapters") makes the fix
natural but does not connect it to the table.

**What would settle it.** Restate the two absence rows as compiler invariants
with a removable mechanism: *the deterministic compiler never creates, modifies
or moves a canonical body* (fixture: hash the body set before and after
`reckon`/`seal`; a compiler that writes a synthesis or a scope change fails),
and *the compiler reads accepted (committed) bodies only* (fixture: an
uncommitted body and an unmerged branch present; the manifest's processed set
excludes both). For the report clauses, name the field per row and give each
a positive control — a fixture in which the condition holds and the field must
be non-empty. The design already states this discipline for itself in §10.3
("Positive controls must distinguish an empty store from a broken walker"); it
only needs applying to its own table.

## Verified / not verified

**Verified against the tree at `origin/main` `8e54245e`.**

- §5.1's "existing memory admission exclusions" are the *What NOT to remember*
  list in `skills/memory/SKILL.md`. (That file also still carries the caps
  and TTL table §8 retires; ticket 0913 owns that, and it is a design-vs-tree
  gap, not a §-vs-§ contradiction.)
- §5.2's knowledge-hint subsystem: `rules/knowledge-hints.md` and
  `scripts/knowledge_hints.py` provide the `.knowledge.toml` catalogue, `terms`
  triggers, `caveat` field and the two channels (`catalog`, `prompt`) as
  described; the `UserPromptSubmit` hook wires the prompt channel.
- §5.1's "ticket bodies already carry decision records": `tickets/AGENTS.md`,
  *Decision records vs. artifacts*.
- §14's three companion documents exist (`portable-agent-memory-calibration`,
  `valid-while-coverage-ledger`, `2026-09-11-memory-systems-comparison`); the
  cited source revision `2e1adaa6` is a commit on main.
- §16 is new in v6 (absent from frozen v5); the §12.1 diff v5→v6 adds the
  three concurrency rows and rewrites the native-loading row into the form
  finding 2 addresses.
- Corpus state relevant to §16.3: 1,050 bodies under `memory/` and
  `projects/*/memory/`, none with a `uuid`, `lifecycle`, `status`, `scope`,
  `source`, `routing`, `generalizes` or `superseded-by` frontmatter field; 47
  `MEMORY.md` files tracked.
- Finding 2's premises: `STATE.md` (0887 entry) states the repo is `~/.claude`
  on the owner's machine; `skills/dream/SKILL.md` addresses projects under
  `~/.claude/projects/`; `scripts/on-start.sh` injects `memory/MEMORY.md`;
  `settings.shared.json` has no `PreCompact` hook and no `PreToolUse` guard on
  memory paths; the v3 panel's F5 (uncommitted native writes swept into dream
  commits) and ticket 0247 (dream runs in the primary checkout) describe the
  current write path.
- Finding 1's premise that no evaluator exists yet: no `valid_while` or
  predicate code under `scripts/`, `tests/` or `skills/`; no link validator
  either (§3.2's is future work, which is fine).

**Taken on the document's word.**

- That Codex and Pi expose boundaries comparable to the Claude Code hooks (row
  2, row 19); no adapter for either is on the tree.
- The state of the draft PR carrying the revised 0908–0919 train: `gh` is not
  installed in this container and I did not query the forge. Nothing here
  depends on it; the tickets on main were read only for scope.
- The three research citations in §14; not opened, and §14 claims nothing
  from them beyond a prior.

**Considered and not reported**, so the reader can check the negative.
§10.1's atomic generation switch against §3.2's fixed tracked filenames looks
like a (c) but is not: the manifest carries the view hashes, so a reader can
verify it holds one generation and treat a mismatch as §10.3 damage — an
implementation choice, not a new decision. §9.2's "isolated checkout" against
0247's same-checkout practice is a tree fact the design explicitly says the
tickets must be re-read against. Row 19's "at supported boundaries" is
conditional on the adapter's declared coverage, which §13.2 requires to be
declared and verified per runtime; it becomes vacuous only if an adapter
declares none, and §10.2 mandates at least session start. Row 7 has a real
failing mechanism (any per-addition edit to a tracked shared file) provided the
fixture performs an actual merge. Cyclic supersession (§9.1) has no row but
is caught by the "resolvable relations" clause of row 12 read generously; I
would add it to the same row rather than list it here.
