> **NON-NORMATIVE.** A review, recorded for information. Nothing here is
> decided or adopted. Its verdict, its revert-and-correct table and its ranked
> findings are the panel's recommendations, not harness policy. The norms live
> in `rules/`, `CLAUDE.md` and the tickets — not in `docs/`.

**Panel:** Fable, three executors, led by Fable. **Recorded:** 2026-09-10,
verbatim from the panel's own file.

Reviews [v1](./2026-09-10-dragon-memory-design-v1.md), frozen. v2 acted on this
review; the current version is
[v3](./2026-09-10-dragon-memory-design.md), which then replaced v2's retention
policy with a settled architecture. Third of three reviews and the first with repository access — the
earlier two ([Claude](./2026-09-10-dragon-memory-design-review-claude.md),
[ChatGPT](./2026-09-10-dragon-memory-design-review-chatgpt.md)) read v0 without
a checkout and took its figures on trust.

---

# Dragon memory design v1 — second-round review (Fable panel, 2026-09-10)

**Reviewed:** `docs/2026-09-10-dragon-memory-design.md` at `origin/main`
`6647953` (v1, the nine amendments of PR #891, commit `76079eb`).
**Frozen v0:** `docs/2026-09-10-dragon-memory-design-v0.md` — verified
byte-identical, after its 8-line notice, to the text both round-one reviews
read (`6d61d349`), and unchanged between the two reviews (`03f4bb2..6d61d349`
touches nothing in the file).
**Method:** every figure checked against a git ref (`origin/main` extracted
with `git archive` to `/tmp/fable-ref-snapshot-v1`, plus `b79c2ad` and
`6187ad8` where the document's baseline required it), never against a working
directory. Three Fable executors: (A) corpus and cost figures, (B) the
duplicate-pair inference, (C) the runtime recall channel and the trace
instrument. Non-normative, like the document it reviews.

---

## 1. Verdict

v1 is **not ready to act on as written**, though most of its program survives.
Two things block it. First, the one substantive amendment — that the 35
duplicate slug pairs are retrieval failures and therefore the strongest local
evidence for the door, which is why T8 jumps to wave 0 ahead of T3 — is false
on the ref: zero of the lexical pairs are same-project, the door as P2 defines
it is per-tier and could not have shown any writer the entry it duplicated, and
the flagship `gh_pr_edit` lesson was actually closed by `rules/git.md` on
2026-09-04, not by any memory tier. T8 is still the right first ticket, but for
a reason the document does not state: `tests/test_resident_census.py` already
caps every project index at 14 500 chars, the largest sits at 14 061, and the
only move that gate permits today is deleting index lines, which §2.4 itself
says makes entries unreachable. Second, §2.4 is now the wrong shape: a
description-driven recall channel *exists* in runtime 2.1.267 (`relevant_memories`
attachments, up to five bodies per turn), compiled behind a flag that is
observably closed on this machine and that, when open, *hides* the MEMORY.md
index. The design's cost model (index is the tax, bodies are free) is therefore
a flag setting, not an architecture, and the document must say so. Beneath
those two: the amended 21.7% is arithmetically 21.1%; T4 and T5 rest on
premises the ref contradicts; §9 closes a question by an unsourced appeal to
the owner and then contradicts its own wave order in its fallback. Fix those,
re-justify T8, pin the runtime version and flag state, and the program is
approvable — T1, T2 and T3 are approvable now, with T3's target halved.

## 2. Findings, ranked by what a wrong answer would cost

### F1. The duplicates-imply-door inference is false, and it is the amendment the wave order rests on

**Claim (v1 §2.5, §6 wave 0, commit message):** one lesson under three names is
three sessions that failed to find the two entries already there; that is a
retrieval failure and "the strongest local evidence for P2's door"; hence T8
precedes T3.

**Evidence (executor B, `origin/main`):**
- The pass is *cross-project by construction* (the document says so). A
  session sees only its own project's `MEMORY.md` plus the 367-char harness
  tier. Of the pairs reproduced (43 at Jaccard ≥ 0.5 with the type prefix
  dropped, 38–41 under stricter variants), **same-project pairs the writer's
  own resident index could have surfaced: 0**. Cross-project pairs where no
  visible index listed the earlier entry: 17. Lexical false positives (different
  lessons, e.g. `dropna_before_merge` / `rebase_before_merge`): 22. Same-day
  one-incident pairs: 2. Promoted stubs under an identical name: 2.
- `git log -S<slug> -- memory/MEMORY.md` is empty for every paired slug except
  the two promoted ones: none of the duplicated lessons was ever in the tier
  every session sees.
- The `gh_pr_edit` family is seven bodies in seven project directories,
  2026-05-11 → 2026-09-04, none promoted. The workaround entered `rules/git.md`
  in `d206d38` on 2026-09-04 — the same day as the seventh copy — and no copy has
  appeared since. The channel that closed the loop was the resident *rules*
  channel, not memory.
- P2's door is "the resident index carries one line naming the full index" —
  a per-tier pointer. A chemin-de-voix session with a door still could not
  see git-erg's entry. The door does not address the failure the pairs record.
- A separate same-project pass finds 6 pairs, 5 of them different lessons and
  1 a genuine refinement — so corpus-wide, the retrieval failure the amendment
  describes has about one instance.

**Consequences:** the paragraph "But read the duplicates as a symptom…" and the
sentence "This is why the door precedes T3" should be reverted. The pairs are
evidence for T1 (tombstone on promotion), T3 (dedup, at roughly half the
claimed yield — 17–21 real pairs, not ~38) and for what the document never
names: that cross-project transfer in this harness runs through `rules/`, and
the promotion tier that was supposed to carry it has promoted four entries in
four months. T8 keeps its place for the reason in F3.

**What would change my mind:** a set of same-project pairs of meaningful size
where the earlier body was listed in that project's index at the later body's
write time. Executor B looked and found one.

### F2. A recall channel exists in the runtime, gated off; §2.4 should say "gated", not "not detected", and the design should say what happens when the gate opens

**Claim (v1 §2.4):** no verbatim injection detected; anything in the system
prompt or a compaction summary would be invisible to the probes; the
distinction does not change the design.

**Evidence (executor C, bundle 2.1.267 at
`~/.local/share/claude/versions/2.1.267`, `strings` dump; this session's own
system prompt):**
- Three body-selection paths exist in the code: (1) *pinned bodies* —
  `metadata.pinned`, at most 4, injected in full into the system prompt;
  (2) *per-turn recall* — a selector (LLM or BM25 index at
  `<memory dir>/.bm25-index.json`) picks up to 5 bodies matching the last
  user prompt, truncated to 200 lines / 4 096 bytes each, appended as a
  `relevant_memories` attachment; (3) `memory_list/read/write` tools over
  remote stores. Path (2)'s gate is `EF()` — remote flag `tengu_moth_copse` or
  env `CLAUDE_MEMORY_STORES` — and that same condition *hides* the MEMORY.md
  index. Index-resident and recall are mutually exclusive by design.
- The raw-`MEMORY.md` branch also has a sibling: a *synthesised* index of the
  200 most-recently-modified bodies rendered as `- [name](path): description`,
  behind `tengu_stone_shell`. On that branch `description:` is what the model
  sees, and recency, not the index file, decides membership.
- Gate state here is observable, not inferred: this session's system prompt
  carries the raw `MEMORY.md` under the "user's auto-memory" label, reachable
  only with both flags false. Corroborated by 0 `.bm25-index.json` files, 0
  `pinned:` keys in 992 bodies, no `CLAUDE_MEMORY_STORES`.
- The amendment's "would be invisible" is half wrong: traces do not record the
  system prompt, but they do record attachments, and a `relevant_memories`
  attachment would appear there. Count over the corpus: 0 (the 11 string hits
  are tool outputs from the executor's own grep — which doubles as the
  detector's positive control). Pinned and synthesised-index markers: 0.
- Truncation: MEMORY.md is cut at 200 lines / 25 000 chars with a warning
  appended. The 200-line cap in `skills/dream/SKILL.md:119` is the runtime's
  line cap; the character cap, which the document never mentions, is 25 000.

**Consequences:** (i) §2.4 should read "a description-driven recall channel
exists in 2.1.267 and is gated off on this machine; when it is on, the index is
not loaded". That is a stronger, checkable statement than "not detected". (ii)
"The distinction does not change the design" is wrong: under the open gate
every design quantity inverts — bodies become the per-turn tax (5 × ≤ 4 KB),
`description:` becomes the retrieval key, and a bounded resident index buys
nothing. P1/P2/P4 should state which regime they assume and what the adapter
does in the other. (iii) Pin the runtime version and the flag reading next to
the baseline SHA, as the in-family review asked and the amendments did not do.
(iv) `metadata.pinned` is a runtime-provided resident tier of four bodies; T8
should say whether it uses or ignores it.

**What would change my mind:** nothing about existence — the code is there.
The cheapest falsification of the gate reading, not run because it launches a
session: `CLAUDE_MEMORY_STORES=<config> claude -p "<prompt matching one body's
description>"`, then grep the new trace for `"type":"relevant_memories"`.

### F3. The resident budget already exists and is about to bind; that, not the duplicates, is why the door is wave 0

**Claim (v1 T8 exit criteria):** "the resident index respects a character
budget".

**Evidence (ref):** `tests/test_resident_census.py` on `origin/main` —
`BUDGETS["memory"] = 14500` and `test_no_project_memory_index_exceeds_the_budget`.
Largest index (climate-finance-het) 14 061 chars by `git ls-tree -r -l
origin/main -- projects | grep MEMORY.md`. Headroom 439 chars; index lines
average ~100 chars, so roughly four `/dream` ADDs in that project turn CI red.
The gate has no demotion path: the only legal moves are shortening titles or
deleting lines, and §2.4 (which survives this review in substance) says a
deleted line is an unreachable entry.

**Consequences:** T8's budget criterion is already met by #883; its real exit
criterion is the demotion path — "an index over budget can be brought under it
without any entry becoming unreachable, and a test proves it". State the
budget T8 targets: the existing 14 500, the in-family review's ~5 KB, or the
10 KB knee the document itself calls an analogy. The urgency argument for
wave 0 is one sentence and it is missing.

### F4. T4 and T5 rest on premises the ref contradicts

**T5 claim:** "28 prefixes where the design has 4 … Any per-type policy is
meaningless until this is normalised."
**Evidence:** `grep -rh '^\s*type:' projects/*/memory/*.md` at the ref gives
exactly four values — feedback 704, project 160, reference 64, user 15. The
28 (29 with tombstones) prefixes are *filenames*: 22 stray files out of ~980.
The real normalisation gaps are the 47 bodies with no type field at all and
two frontmatter shapes (`type:` top-level versus `metadata.type`). Defect 7 is
mis-stated and T5's exit criterion ("28 → 4") targets the wrong field. The
out-of-family review asked for exactly this check (I3) before T5; the amendments
did not run it.

**T4 claim:** "the 191 aged entries are flagged; per-type thresholds read from
the memory skill's TTL table."
**Evidence:** `skills/memory/SKILL.md` TTL table: 14 days for "X needed / X
blocked", 60 for benchmarks, 90 for remote machine config, and **"No TTL:
feedback"**. Feedback is 74% of the corpus. A pass that follows that table
cannot flag the 191; the two halves of T4's exit criterion contradict each
other. Further, `skills/dream/SKILL.md:254–270` designs the decay pass as
"stale harness-level entries" only; §2.5's row "designed: flag unconfirmed
entries / measured: covers promoted entries only" describes a design choice as
a gap, and "a mechanism described as the harness's forgetting policy has a
yield of zero over 191 eligible" counts as eligible what the design never
made eligible. The in-family review's "confirmed by what?" is also still
unanswered: `last_confirmed` is what `/dream` writes, so a NOOP run confirms.
What the document does not mention and round one could not see: the memory
skill's own admission caps — 5 feedback entries, 3 project-state — are the
designed admission control, ignored by a factor of ~15 in every large index.

### F5. Figures: one wrong in the amended text, one measured on a working tree, several off by one ref

All from executor A unless noted; commands in §5.
- **21.7% is 21.1%.** 14 061 / 66 611 = 0.2111, and 5 022 / 23 790 = 0.2111.
  The amendment that discusses this share at length restates the wrong value.
  Neither round-one reviewer could have caught it.
- **212 529 chars of harness-project bodies reproduces at no ref** (197 451 at
  `b79c2ad`, 198 763 at `6187ad8`, 208 886 at `origin/main`). The document
  carries the same working-tree measurement the commissioning session was
  warned against.
- **Promoted entries: 4, not 3**, at every ref after #885 (the backfill marks
  `reference_branch_cleanup_incidents`); "3 of 960" mixes a pre-#885 numerator
  with a post-#885 denominator. **Unpromoted candidates at ≥2 alias-collapsed
  projects: 1** (`user_profile`), not 3 (executor B).
- **Live orphan copies of promoted entries: 4 or 5** depending on whether the
  harness's own project directory counts. The cause is worth more than the
  count: the skill writes a `# PROMOTED` stub and `provenance.live_bodies`
  recognises only `# DELETED`. T1 is a marker fix, not a design ticket.
- **949 live bodies reproduces at no ref**: 954 files / 948 distinct slugs at
  `b79c2ad` and `6187ad8`. The provenance populations resolve from the data:
  651 = records at `b79c2ad` including 12 dead; 308 = live project-tier slugs
  uncovered, +1 harness body = 309 backfilled; 960 = 651 + 309; 960 − 12 dead
  = 948 live. The amendment flags this and asks the author to resolve it; it
  was resolvable in ten minutes from the ref.
- **35 pairs / 49 slugs is not reproducible** — 38–43 depending on prefix and
  alias handling — and the repo holds no Jaccard code, so Annex B's "every
  figure regenerates from two instruments" fails for the figure the amendment
  leans on hardest.
- The document's figures match `6187ad8` (main just after #885), not
  `b79c2ad`; say so. Everything else checked out — see §5.

### F6. §9 closes a question by authority, without a source, and its fallback contradicts its own argument

**Claim:** "The harness owner treats context pressure as established … the
argument for reducing the resident tier is the context budget."
**Evidence:** no rule, memory note, ticket or STATE line on the ref records
that position (`grep -ri 'context pressure'` over `rules/ memory/ STATE.md
tickets/`: nothing; the nearest is `workflow.md`'s micro-turn "context tax",
which concerns accumulated context, of which the preamble is the small share
the §2.1 amendment just argued it is). The amending session ran on a
1M-context model, which makes "context pressure" three different claims —
window capacity, attention dilution, per-turn cache-read cost — of which only
the third is measured anywhere. The out-of-family review's replay test (M4)
and the in-family natural control (the five index-less bodies) are the two
cheap benefit measurements on the table; §9 declines both by fiat. A document
that "exists to be attacked" should not close its own hardest question by
citing its owner's belief.
**Internal contradictions introduced:** §9 says "defer T6 and T7 until T8 and
T4 have run" but Annex A lists T8 in no dependency column (T6: T4, T5; T7: T4,
T6); §2.5 says the door precedes T3, and §9's fallback runs T1–T3 without the
door.

### F7. The review record overclaims what was amended, and the status line is not earned

- §9: amendments "take … separating durability from type". No line of the
  v0→v1 diff touches P5, T5, defect 6 or §8 Q5.
- §6: "Both external reviews raised this" — one is in-family and says so.
- v0 notice: "corrects two arithmetic errors" — one corrected (writes/reads),
  one flagged and left (populations).
- §2.3 amendment: "The window's length is not stated … and must be." It is
  2026-06-01 → 2026-09-10, 101 days (executor C, first-line timestamps; the
  instrument has no date filter). The re-run gives maintenance 133/248, working
  35/321, subagent 186/5 218, 51 distinct bodies — the document's figures plus
  the sessions since.
- Status "reviewed and amended" sits over three "must be stated" notes that
  state nothing. v1 is a draft with reviewer comments inlined.

### F8. Points both reviews raised that v1 did not take and should have

Prompt caching (in-family Q2, out-of-family M3): the index is in the system
prompt, so its per-turn cost is a cache read; "28×" and "19 900 tokens per
open" invite the wrong optimisation. Index sizes retroactively applied versus
reconstructed per session (M3) — not stated. T3's "3 → ~38" as an exit
criterion (I1): kept, and now doubly wrong (F1, F5). Subagent index
inheritance (Q2): does the 4.78 M-char figure include 5 189 subagent runs?
Still unstated. The cwd-slug fragmentation executor B found (one repo under
`AEDIST` / `aedist`, or three `climate-finance` slugs) inflates every
"cross-project" count; `.project-aliases.json` collapses part of it and no
ticket names the rest.

## 3. Verdict on the nine amendments as a group

They made the document more honest in four places and wrong in the one place it
claimed to add value. The commit message calls the duplicates-to-door
inference "the substantive one" and notes that "neither review connected it to
the duplicates"; neither did because it does not hold (F1). The rest are hedges
that flag rather than fix, and one that repeats an arithmetic error.

| # | amendment | verdict |
|---|---|---|
| 1 | Duplicates as retrieval failures → door → T8 wave 0 ahead of T3 | **Revert the inference and the "door precedes T3" sentence.** Keep T8 in wave 0, re-justified from F3; rewrite its exit criteria around the demotion path. |
| 2 | §2.1 "share at its maximum" | Keep the dilution point; **fix 21.7% → 21.1%**; add that the resident cost is cache-read priced per turn, which is the number urgency actually turns on. |
| 3 | §2.3 two limits (window, subagent overlap) | Keep; **fill in** 101 days and the per-arm attribution rule, both now measured. |
| 4 | §2.4 "no channel detected" | **Replace** with "channel exists, gated off in 2.1.267 on this machine; when on, the index is not loaded"; drop "the distinction does not change the design" — it changes the cost model (F2); pin version and flag. |
| 5 | Promotion criterion measures recurrence, not generality | Mostly harmless, but it attacks the document's own §1 summary: `skills/dream/SKILL.md` already uses ≥2 projects as the mechanical candidacy gate behind a cost gate and a context-independence gate. Reword to say the skill already does this; drop "how often the author repeats a mistake" — the `gh_pr_edit` family is one tool defect met in seven repos, not seven repetitions of a mistake. |
| 6 | Writes/reads corrected | Keep. Correct. |
| 7 | Provenance populations flagged | **Replace the flag with the reconciliation** (F5): 651 incl. 12 dead → 639 live covered; 309 backfilled; 960 − 12 = 948 live. |
| 8 | §9 decision requested and fallback | Keep the decision request; **remove or source** the owner-belief closure of Q3; fix the fallback (T1–T3 without the door contradicts amendment 1 — which, once reverted, resolves itself); add T8 to the dependency column of whatever demotes. |
| 9 | Status/header, review record | Downgrade to "draft, second amendment pending"; strip "separating durability from type" and "both external" from the record; "two arithmetic errors" → one. |

Net: revert 1, correct 2, 4, 7, 8 and 9, keep 3, 5 and 6. The document is
better for the hedges and worse for the thesis.

## 4. What round one could not see

Round one had no repository. These are the findings that needed one:

1. **The recall channel is in the binary** (F2). Both reviews reasoned from
   the probes' blind spots; the code answers the question the probes cannot,
   and the answer is "exists, gated, and mutually exclusive with the index".
2. **The budget gate is live and four entries from red** (F3). Both reviews
   said the door has no ticket; neither could know a gate already forces it.
3. **The type vocabulary is already four values** (F4). The out-of-family
   review asked; only a grep on the ref could answer.
4. **Decay covers the harness tier by design, feedback has no TTL by design,
   and the per-type admission caps are 5 and 3** (F4). §2.5's
   designed-versus-measured table misreads the design in two rows and omits
   the row where the design is most violated.
5. **The cross-project carrier in practice is `rules/`, not the promotion
   tier** (F1, `gh_pr_edit` timeline). This is the one fact in this review that
   should change the *design*, not just the document: the harness already has a
   working "promote a lesson so every session sees it" mechanism, and it is a
   rule edit through a PR. Promotion to `memory/` (four entries in four months,
   one candidate waiting) is the tier that does not work; the plan should ask
   whether T1/T3 are repairing a road nobody drives.
6. **The document contains a working-tree measurement of its own** (F5,
   212 529) — the exact trap the commissioning session sprang on the document
   and warned this review against.
7. **T1's defect is a marker mismatch** (`# PROMOTED` vs `# DELETED`), a
   one-line fix rather than a design ticket.

## 5. Verification ledger

All refs: `origin/main` = `6647953401d4e5e25c80d9779327acbf95892e51` unless
stated; `6187ad8` = main immediately after #885 merged; `b79c2ad` = the
document's stated baseline (which predates #875 and #885 — neither is its
ancestor). Snapshot: `git archive origin/main | tar -x -C /tmp/fable-ref-snapshot-v1`.

| figure | doc | measured | ref | command (abridged) | verdict |
|---|---|---|---|---|---|
| v0 = reviewed text | claimed | identical after 8-line notice | `6d61d349` | `git show 6d61d349:docs/…design.md`, `diff` with v0 | matches |
| design unchanged between reviews | — | no diff | `03f4bb2..6d61d349` | `git diff --stat 03f4bb2 6d61d349 -- docs/…design.md` | matches |
| rules chars | 35 926 | 35 926 (35 978 on main, +52 from #888) | `6187ad8` | `python3 scripts/resident_census.py <root>` | matches |
| import / hook / skills / agents | 9 646 / 367 / 6 261 / 350 | same | `6187ad8`, main | census | matches |
| largest index | 14 061 | 14 061 (climate-finance-het) | all | `git ls-tree -r -l origin/main -- projects \| grep MEMORY.md` | matches |
| total | 66 611 | 66 611 (66 663 on main) | `6187ad8` | census | matches |
| **memory share** | **21.7%** | **21.1%** | any | 14 061 / 66 611; 5 022 / 23 790 | **wrong** |
| memory dirs | 47 | 47 (46 with index) | all | walk | matches |
| live bodies | 949 | 954 files / 948 slugs | `b79c2ad`, `6187ad8` | `provenance.live_bodies` rule (`# DELETED` head) | off by 1–5 |
| tombstones | 35 | 35 | all | head starts `# DELETED` | matches (3.5–3.7%) |
| index entries | ~905 | 901–906 | all | `- [` lines | matches |
| unlisted / no-index dir / dead records | 13 / 5 / 12 | 13 / 5 / 12 | all | walk vs index vs `.provenance.json` | matches |
| harness project index | 10 368 | 10 368 | `6187ad8` | `git ls-tree -r -l 6187ad8 -- projects/-home-haduong--claude/memory/MEMORY.md` | matches |
| **harness project bodies** | **212 529** | 197 451 / 198 763 / 208 886 | `b79c2ad` / `6187ad8` / main | sum of body lengths | **no ref reproduces it** |
| promoted | 3 | 3 at `b79c2ad`, **4** after | both | `memory/.provenance.json` promoted flag; `memory/MEMORY.md` | off by one post-#885 |
| coverage before / after #885 | 651 / 960 | 651 / 960 (965 on main) | `b79c2ad` / `6187ad8` | `git show <ref>:memory/.provenance.json` | matches |
| decay flagged / > 90 days | 0 / 191 | 0 / 191 by `last_confirmed` (225 by `first_seen`; 107 at `b79c2ad`) | `6187ad8` | reproduced decay logic | matches post-#885 |
| live orphan copies | 4 | 4 (5 incl. harness's own project dir) | all | `# PROMOTED` stubs counted live | matches / off by one |
| prefixes / singletons | 28 / 24 | 28 / 22 (29 / 23 with tombstones) | main | `sed -E 's/[_-].*//' \| sort \| uniq -c` | matches / off by two |
| `metadata.type` values | (defect 7 implies 28) | **4**: feedback 704, project 160, reference 64, user 15; 47 untyped | main | `grep -rh '^\s*type:' projects/*/memory/*.md` | contradicts T5's premise |
| largest index lines / cap | 141 / 200 | 141 / 200 (`dream/SKILL.md:119`; runtime cap 200 lines, 25 000 chars) | all | `wc -l`; bundle strings | matches |
| resident memory budget | not mentioned | 14 500 per index | main | `tests/test_resident_census.py` `BUDGETS` | new fact |
| #875 totals | 198 636 → 111 021 | 198 290 → 110 834 chars | `b79c2ad` → `6187ad8` | census memory entries summed | off by 346 / 187 (PR-body base) |
| #875 largest | 26 531 → 14 061 | same | same | ls-tree | matches |
| 308 uncovered | 308 | 308 project-tier + 1 harness = 309 backfilled | `b79c2ad` → `6187ad8` | `backfilled: true` count | matches |
| 35 pairs / 49 slugs | 35 / 49 | 43 / 59 (prefix dropped); 41 alias-collapsed; 38 excl. stubs | main | `/tmp/jac.py`, Jaccard ≥ 0.5 on `[_-]` tokens | not reproduced; no code in repo |
| candidates ≥ 2 projects | 3 | 1 (`user_profile`) | main | `.provenance.json` projects, alias-collapsed | off by two |
| trace arms | 132/246, 35/318, 23/273, 185/5189; 50 bodies | 133/248, 35/321, 23/275, 186/5218; 51 | traces (not git) | `scripts/census/memory-recall.py --out /tmp/…` (17 s) | matches plus drift |
| trace window | unstated | 2026-06-01 → 2026-09-10 | traces | first-line timestamps | new fact |
| `relevant_memories` / pinned / synthesised-index attachments | 0 injections | 0 / 0 / 0 (positive control: 10 hits from the grep itself) | traces | grep over JSONL | matches, now with a control |
| recall channel in runtime | "nothing fires" | exists behind `EF()` (`tengu_moth_copse` / `CLAUDE_MEMORY_STORES`); closed here | 2.1.267 | `strings` on the Bun binary; this session's system prompt label | claim must be re-worded |
| 852 of 902 at zero | 852 / 902 | not measurable from a ref (trace-derived); store `access_count` 263 nonzero / 702 zero of 965 | main | `.provenance.json` | could not verify |
| T8 raised by both reviews | claimed | yes: in-family "P2 has no ticket", out-of-family B2 | docs | read | matches (one is in-family) |
| "context pressure established" | claimed | no source on the ref | main | `grep -ri 'context pressure' rules memory STATE.md tickets` | unsourced |

Worktree state: `git status --porcelain` empty at start and at finish; no git
mutation performed; scratch under `/tmp/fable-*` only.
