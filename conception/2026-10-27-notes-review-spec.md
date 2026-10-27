# Git-native review storage: design spec (ticket 1277, tracker 1252)

Status: proposed, for cross-family review and author acceptance. Answers the five questions of 1277.
Inputs: the author's note `2026-10-27-git-notes-review-design.md` (cited "note §"), the transport trial
`2026-10-27-notes-transport-trial.md` ("trial case N"), the prior-art survey `2026-10-27-notes-review-prior-art.md`
("prior art §N"), 1252's advisor ruling ("ruling"), `scripts/merge-gate.py`.
Legend: **[M]** measured in the trial; **[M']** measured in this session (git 2.43, temp repo + bare remote, script
not kept, rerunnable in a minute; GitHub as remote and doudou's git 2.53 untested); **[I]** inferred, not run.

Roles stay as note §2: hunt writes the request, gaze writes plan, reports (on behalf of seats) and summary, verify-gate
writes verdicts. Reviewers never need git rights (note §2.3). Every write goes through one helper,
`scripts/review_notes.py` (ruling point 1); no skill or prompt spells a refspec or `git notes`.

## Decision summary

| Q | Decision | Rejected |
|---|----------|----------|
| 1 Rebase | Entries hang on a **review anchor** (fixed OID derived from `review_id`), not on branch commits; each entry records `head`, `base`, `range_patch_id`; coverage carries to a rebased head when whitespace-sensitive patch-ids match; reviewed heads kept by `refs/review-heads/*` | `notes.rewriteRef`, `git notes copy`, Change-Id trailer |
| 2 Transport | `review_notes.py setup` writes two fetch refspecs and a merge strategy; writes = fetch, `notes merge -s cat_sort_uniq`, push, retry; `publish` verifies against the remote | per-session prompt text, forced fetch into the live ref, push refspec config |
| 3 Layout | **One ref** `refs/notes/review`, `kind:` field (ruling stands), one note per review, **one JSON line per entry**, blank lines skipped | one ref per kind (appraise, note §3.1); one ref/commit per entry (git-bug), kept as the fallback store |
| 4 Request | `what` = verbatim `git request-pull` output; round n>1 adds `delta` = `git range-diff`; findings have stable ids; open findings derived from the whole history | latest-summary-only view as truth |
| 5 Ids | `review_id`, `request_id`, `run_id`, `seat_id` minted by the helper; `gate_session_id` unchanged; refs/notes/gate untouched | numbering by round counters (collide across hosts) |

## 1. Rebase survival

**Problem.** Notes key on an object id; raid rebases before every gate (rules/git.md). Without config a rebase loses
every note on the new SHAs [M, trial case 4a]. `notes.rewriteRef` carries them, but only in the clone that rebases,
must be set in each clone, is not fetched, and leaves orphans (11 of 14 entries) [M, case 4b]; a web session rebasing
without it drops the link silently [M/I, case 4]. `git notes copy` works [M, case 4c] but pairs old/new commits by
order, which a squash or drop breaks [I]. None of the surveyed tools solves this (prior art, Verdict: appraise silent, amlog says
rewriteRef, Gerrit writes after submit).

**Decision: do not key review entries on branch commits.**
- *Anchor.* Each review owns one note, attached to `anchor(review_id) = git hash-object --stdin <<< "idh-review <review_id>"`.
  The anchor needs no stored object: `notes append`/`show` on a 40-hex OID absent from the object store work, and a
  second clone reads the note after fetching the ref [M', bare remote, git 2.43 only]. A rebase, amend, squash or force-push moves nothing.
- *Head binding.* Every entry states `head`, `base` (OID), `base_ref`, `merge_base` and
  `range_patch_id = git diff <merge_base>..<head> | git patch-id --verbatim`. `--stable` alone is unsafe: it ignores
  whitespace, so two heads differing only in Python indentation (a behaviour change) shared one id, and `--verbatim`
  is refused together with `--stable` [M', gaze]. Rule for verify-gate and merge: a review entry covers head H iff
  `entry.head == H`, or `entry.range_patch_id` is non-empty and equals the verbatim patch-id of H's range (an empty
  diff yields an empty id and never matches). Scratch check of the rule [M']: the indentation-only pair gave distinct
  verbatim ids (35ba1bf6 vs c29e8292, same `--stable` id 548af34e); a clean rebase of a two-commit branch onto a base
  that changed the same file kept the verbatim id (373b2d5e). Rejected second conditions: identical blobs per changed
  path fail that clean rebase (the base's edit changes the blob), and `range-diff` flags it `!` (hunk headers move).
  A match on a new base carries the review of the *diff*, not of the merge result; CI is the only backstop for
  semantic interaction with the moved base.
- *Conservative, with frequent false misses.* The patch-id hashes context lines: a base edit within 3 lines of a
  branch hunk changes the id although the branch did not change (aa860f55 to 8cc7c3f0 [M', gaze]), and so does a
  conflict-resolving rebase. A miss never carries coverage wrongly; it costs a delta review (§4) on the range-diff,
  expected after most rebases onto a busy base.
- *Keeping the examined commits* (note §6.5): when an entry names a head, the helper pushes
  `refs/review-heads/<review_id>/<request_id>` → that head (never forced by the helper; immutable by convention only,
  since the remote accepted a `+` push and `gc --prune=now` then removed the old commit [M', bare remote, git 2.43];
  §6(a) checks them). Range-diff of later rounds and
  audit need those objects after the branch is force-pushed or deleted.
- *Display:* `git log --notes` no longer shows reviews on the commit; `review_notes.py show` replaces it. Accepted cost.

**Orphans and pruning.** By construction there are none: a review's note dies only when deleted on purpose.
`git notes --ref=review prune` is **forbidden** (helper refuses; housekeeping skills must not call it): its dry run
listed every anchor as prunable, since anchors are not objects [M']. `git gc --prune=now` left the notes intact [M'].
Retention of `refs/review-heads/*` is an author decision (§10); default: kept.

**Rejected.** rewriteRef: per-clone config in four environments, silent loss in any one, orphans [M]. Copy: fragile
pairing [I], and someone must remember to run it. Change-Id trailer (prior art Verdict): needs a commit-msg hook in
every environment and rewrites the commits under review [I]. Notes on the head *plus* a copy on rebase: two sources
of truth.

## 2. Transport

**Facts.** Neither clone nor fetch, nor fetching the branch, brings notes [M, case 1]; a blobless clone with a refspec
recovers the full history [M, case 5]. Two writers on one ref: the second push is rejected non-fast-forward [M, case 3].
Replacing the default push refspec makes pushes notes-only, and a forced `+refs/notes/*` fetch clobbers local
unpushed entries (prior art §8) [S].

**Per-clone config, written only by `review_notes.py setup`** (idempotent; every helper operation calls it first, so
a fresh clone self-heals; the session-start bootstrap also calls it):
```
git config --add remote.<r>.fetch '+refs/notes/review:refs/notes/origin/review'   # tracking ref, never the live one
git config --add remote.<r>.fetch 'refs/review-heads/*:refs/review-heads/*'         # immutable, no '+'
git config notes.review.mergeStrategy cat_sort_uniq
```
No `remote.<r>.push` entry (pushes are explicit, in the helper). No `notes.rewriteRef` (§1 makes it unnecessary).
With no remote, setup is a no-op and everything stays local (1252 exit criteria: temp repo, no remote).

**Concurrent-append protocol (`sync`).** fetch → if the tracking ref descends from the local ref, fast-forward;
else `git notes --ref=review merge -s cat_sort_uniq refs/notes/origin/review` → `git push <r>
refs/notes/review:refs/notes/review` → on rejection loop (at most 5 attempts, jittered backoff). Appends to
different reviews merge cleanly [M']; appends to the same review merge by line union. cat_sort_uniq destroyed
multi-line entries in the trial [M, case 3B]; with **each entry on one line** and a unique `id` in each line,
union-sort-dedup loses nothing and is idempotent [I: follows from the strategy's definition; C3 must test it].
`git notes append` separates entries with a blank line (`{t2}\n\n{t3}`) and a fast-forward keeps them; only a
merge drops them [M', gaze]. Decision: the helper keeps `append` and **readers skip blank lines**; a blank line is
never an entry, and the merge's sort-dedup reduces blanks to one, harmlessly. Rewriting the whole blob
(`notes add -f`) was rejected: it makes each append a read-modify-write of the note.
This replaces merge-gate's re-append recovery, which needs regenerable text and caps at 2 attempts [M, case 3].
The helper never force-pushes the notes ref.

**Verified publication (note §6.3).** `publish <entry-id>...` = `sync`, then refetch and require that the remote
ref OID equals the local one (`git ls-remote`) and that every named entry id is readable from the refetched
tracking ref; it prints one of `done-unpublished | published | retrievable` and exits non-zero below
`retrievable`. A web session's closing step is `publish`; a non-zero exit is reported as an incomplete delivery,
and the entries stay in the local ref and in an `export` file for relay.

**Web environments (legs pending, author's accounts).** The web-leg script exercises fetch, push and remote
verification. Decision rule per outcome:
- A. fetch and push of notes work → same as doudou/padme, nothing else.
- B. fetch works, push of `refs/notes/*` refused but branch push works → the environment is a reader and a seat,
  never a publisher; its entries leave through `export` (JSONL) in its returned report and a durable host runs
  `import` + `publish`; `publisher` records the relaying host, `author` the web session.
- C. even fetch of notes fails → the handing host passes `export <review_id>` as an input file; same relay back.
- D. the author wants a B/C environment to *publish* unattended → switch the store to the fallback branch store
  (§3), a one-module change inside the helper (ruling point 2); no skill changes.
Claude Code Web may restrict pushes to its session branch [I, unverified]; that is outcome B or C, handled above.

## 3. Storage layout and entry format

**Decision: one ref, `refs/notes/review`, a `kind` field per entry, one note per review (on its anchor).**
- Contention is per ref tip whatever the split; with merge-based sync (§2) a rejected push costs one fetch+merge,
  not a lost entry, so one ref per kind buys nothing and multiplies refspecs, setup and verification by four
  (ruling point 1; trial "Does anything argue against one ref?": nothing refuses it [M]).
- Per-kind refs (note §3.1, appraise) were chosen there against overwriting several runs on one commit; append +
  `run_id` satisfies that requirement (note §3.1 last line, §8.3 first case). The four families become
  `kind ∈ {request, plan, report, answer, verdict, link}`.
- One commit or ref per entry (git-bug, git-dit; prior art §4) removes races outright but is a bespoke layout with
  enumeration cost and many refs. Kept as the **fallback store**: branch `idh-review-store`, one file
  `<review_id>/<ts>-<id>.json` per entry, conflict-free rebase on retry [I, not run]. Chosen only on outcome D.
- refs/notes/gate stays apart: mechanical evidence on the candidate merge commit, not reports (ruling point 1).

**Entry format.** One JSON object per non-blank line (§2), UTF-8, keys in the writer's fixed order with `ts` first (so the
strategy's sort is chronological), no raw newline (json escapes it; the writer refuses control characters as
merge-gate's `single_line` does). Required in every entry:
`ts` (UTC, ms), `id` (entry id: `<ts compact>-<host>-<8 hex>`, unique), `v` (schema, 1), `kind`, `review_id`,
`request_id`, `author` (who produced the content: role, runtime, observed model/family, never a requested one, note
§5.2), `publisher` (process that wrote: skill, host, git user), `head`, `base`, `base_ref`, `merge_base`,
`range_patch_id`, `links` (entry ids this one answers, supersedes or cites; may be empty).
Kind-specific: `request`: `what`, `why`, `intent`, `tickets`, `delta` (n>1), `responses` [{finding_id, disposition}].
`plan`: `run_id`, manifest (seats, missions, budgets). `report`: `run_id`, `seat_id`, `status ran|failed|skipped`,
`text`, `findings` [{finding_id, ...}]. `answer` (gaze summary, note §2.3 field list): `run_id`, `result
REVIEWED|FINDINGS|ESCALATE`, `seats panel|self-only`, `coverage` {scope full|delta, verified, carried, out},
`report_ids` (pins report versions), `unresolved`, `attribution` (lines), telemetry. `verdict`: `gate_session_id`,
`round`, `verdict APPROVED|REROLL|ESCALATE|NEEDS-AUTHOR`, `evidence` (entry ids), `gate_candidate` (OID).
`link`: forge PR number or other external id. An entry is never edited; a correction is a new entry linking it.
"Latest summary" is a derived view (note §3.2).

## 4. The request's What; incremental review

- `what` = verbatim `git request-pull <base> <url> <head>`; `<url>` is the remote URL, or the repo path with no remote.
  hunt pushes the branch (or the review-head ref) first, since request-pull checks the head exists at the URL [I].
  `why` and `intent` are hunt's text (note §2.1); a narrow intent is stated, never widened by default.
- Round n>1: hunt writes a new `request` on the new head with `links` to the previous request and answer,
  `delta = git range-diff <prev_merge_base>..<prev_head> <merge_base>..<head>` (needs §1's review-heads), and
  `responses` naming each prior finding by id with its disposition (note §4).
- `finding_id = <run_id>/<seat_id>/<n>`, minted by gaze at publication. The open set is computed by the helper over
  the review's whole history (latest disposition per id, latest by `(ts, id)` compared lexicographically; `id`
  embeds the host and a random suffix, so two hosts writing in the same millisecond resolve the same way
  everywhere), so a finding not mentioned in the last round stays open
  (note §4, §8.3 second case).
- `answer.coverage.scope = delta` never counts as full: a head is fully covered only by a full answer on that head
  or on an equal `range_patch_id`, chained with delta answers whose `carried` names it (note §4: incremental is not
  automatically full).

## 5. Identifiers

| Id | Minted by | Form | Relation |
|----|-----------|------|----------|
| `review_id` | helper `open` (hunt) | `rv-<yyyymmdd>-<branch slug>-<4 hex>` | the merge-request stand-in (D1); `forge.py resolve branch:<name>` finds it via the latest open `request` naming that branch; anchor of the note |
| `request_id` | hunt, each submission | `rq-<ts compact>-<4 hex>` | names `refs/review-heads/<review_id>/<request_id>` |
| `run_id` | gaze, each execution | `gz-<ts compact>-<4 hex>`; reuse the gaze manifest's run id if present | several runs on one head stay distinct (§8.3) |
| `seat_id` | gaze manifest | `<run_id>:<seat name>` | same seat name as attribution's `seat=` |
| `gate_session_id` | verify-gate | unchanged UUID (`session=`) | `round` counted from `verdict` entries of the **review_id**, all sessions: a new session never resets the two-round budget (note §8.3) |

Random suffixes, not counters: two hosts may mint at once. refs/notes/gate is unchanged: a `verdict` entry cites
the gate candidate OID; merge still checks the gate record there. Attribution lines (`reviewer:`, `seat:`,
`finding:`; one format home, `attribution_record.py`) are carried verbatim in `answer.attribution`; with no forge,
D3's merge message takes them from there. With a forge, the forge route is unchanged in 1252 (no notes written);
a review that later gains a PR records it in a `link` entry, and the PR number never replaces `review_id`.

## 6. Protection and integrity

Measured: the only GitHub ruleset targets the default branch; with the narrow token, forced non-fast-forward
update and deletion of a notes ref succeeded [M, case 6]. Notes refs are unprotected; unsigned (prior art Verdict).
Posture as merge-gate: a record is a traceable statement, not proof. Options, priced (agent hours at harness rates):
- (a) **Adopt now.** Detection: the helper never forces; it keeps the last-seen remote tip (tracking-ref reflog) and
  refuses to fast-forward over a remote tip that does not descend from it, merging instead, so durable clones
  re-publish lost entries and report the rewrite. Ancestry alone misses a descendant commit that drops or replaces
  entries, so each sync also requires the set of entry ids to only grow (last-seen set kept locally); a shrink is
  reported and the missing entries re-published. Review-heads get the same check: each
  `refs/review-heads/<review_id>/<request_id>` must equal the `head` of its `request` entry, and the no-`+` fetch
  refspec (§2) rejects a moved remote ref instead of following it; the helper reports the move and re-pushes from a
  clone that still holds the object. Detects: rewritten, truncated or moved refs, seen by any durable clone that
  synced before. Cannot detect a rewrite made before any other clone synced, nor restore an object no clone kept.
  ~1.5 h in C3, $0.
- (b) Ruleset on `refs/notes/*`: rulesets target branches and tags [I]; 0.25 author-hour to confirm, likely nil.
- (c) Signed notes commits (helper builds them with `commit-tree -S`, SSH signing): ~3-4 agent-hours + one
  author-hour per environment for keys; web sessions have no key, so their entries stay unsigned. Proves who moved the
  ref, not who wrote the content.
- (d) Per-entry `ssh-keygen -Y sign` field: same key problem, ~4 agent-hours.
- Fallback store (§3) would gain branch rulesets (non-ff, deletion) [I]. Recommendation: (a) now; (c) with the
  cross-environment ticket if the author wants attestation.

## 7. Helper interface C3 builds (`scripts/review_notes.py`; names only)

`setup`, `open`, `request`, `add` (plan, report, answer, verdict, link), `sync`, `publish`, `show`, `history`,
`find` (branch → review_id), `findings` (open set), `coverage` (does head H carry the review: equal, patch-id, delta,
none), `keep-head`, `export`, `import`. Note §6.2's `review run` is gaze itself, not the helper.

## 8. Changes to the children

- 1273 (C3): builds §7 with the anchor layout, JSONL entries, cat_sort_uniq sync and review-heads; gaze resolves
  `branch:<name>` via `find`; tests: note §8.3 cases plus same-review concurrent append from two clones.
- 1274 (C4): verify-gate reads through `coverage`/`findings`, appends `verdict` with `gate_session_id`, counts
  rounds per `review_id`, and admits a rebased head only on equal non-empty verbatim `range_patch_id` (§1).
- 1276 (C6): the end-to-end test adds a rebase between gaze and gate, a second clone with no refspec (setup
  self-heals), and a concurrent append.
- 1275 (C5), for completeness: the D3 merge message takes attribution from the latest `answer` entry.

## 9. Validation (note §8.3) mapped

Several runs on one head: distinct `run_id`, append-only. Findings survive fixes: §4 open set. Narrow intent: §4.
Missing/failed seats: `report.status`, `answer.seats`. Gate budget: §5. Failed publication keeps reports: §2
`publish` + local ref + `export`. Resume without blind rerun: `plan`/`report` entries per seat. Rebase and cleanup:
§1 anchors and review-heads, prune forbidden. Full no-forge path: 1276. Historic evidence: refs/notes/gate untouched.

## 10. For the author to decide

1. Accept that reviews hang on a review anchor, not on the examined commits (note's Synthèse says "attachées aux
   commits examinés"; D2 said "notes on the reviewed head"). The head stays named in every entry. Reversible inside
   the helper, but it is the note's founding choice, so it is yours.
2. Retention of `refs/review-heads/*` after merge: keep forever (default), or let roar delete the just-merged review's.
3. Web legs: run them (script `conception/2026-10-27-notes-web-leg.sh`); outcome D is a store switch.
4. Attestation: option (c) or not.
5. rules/git.md wording once C5 lands (ruling point 4, unchanged).
