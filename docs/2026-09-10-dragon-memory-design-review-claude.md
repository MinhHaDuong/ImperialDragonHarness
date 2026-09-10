# Dragon memory design — review (Claude, 2026-09-10)

> **NON-NORMATIVE.** A review, recorded for information. Nothing here is
> decided or adopted. Its verdicts, its proposed wave order and its "drop T7"
> are the reviewer's recommendations on a draft, not harness policy. The norms
> live in `rules/`, `CLAUDE.md` and the tickets — not in `docs/`.

**Author:** Claude. **Recorded:** 2026-09-10, verbatim.
Figures and claims are the reviewer's and were not re-verified at recording
time.

Reviews the design draft
[`2026-09-10-dragon-memory-design.md`](./2026-09-10-dragon-memory-design.md)
(landing in PR #887), answering its §8 questions. Distinct in kind from the
three study reports
([Fable](./2026-09-10-memoire-agent-fable.md),
[Perplexity](./2026-09-10-memoire-agent-perplexity.md),
[ChatGPT](./2026-09-10-memoire-agent-chatgpt.md)), which were solicited
*before* the design and fed it. This one comes after and judges it.

**The reviewer opens by disqualifying itself in part:** the design asked for a
read from a different model family, and this is an in-family review. That
outside read has since arrived —
[`2026-09-10-dragon-memory-design-review-chatgpt.md`](./2026-09-10-dragon-memory-design-review-chatgpt.md)
— so read the two together rather than either alone.

---

Caveat first: the document asks for a read from a different model family. I am not that; I'm the same family as the runtime under study, so treat this as an in-family review and still get the outside one.

**Verdict.** The measurement is the strongest part and §2.4 is right. The principles follow from it. The plan has one missing prerequisite (P2 has no ticket), one mechanism that reintroduces the bias P4 rejects (T4), and one proposal I would drop (T7).

## Answers to §8

**1. §2.4 — no recall channel.** Right, and for a structural reason rather than an empirical one: the documented mechanism is exactly index-resident, bodies on demand. Only the first 200 lines or 25 KB of MEMORY.md load at session start; topic files load on demand. The `description:` guidance instructs the model what to open; it is not a runtime channel. Your probes confirm a documented absence. Two structural blind spots remain: (a) your probes read transcripts, so anything injected at system-prompt level would be invisible — that is where an injection would live if it existed; (b) compaction summaries paraphrase, so exact-string probes miss content that survives a session by that route. Cheap falsifier: a canary. Put a nonce in a body's `description:` (not in its title), open a fresh session, ask the question the description answers, check whether the answer arrives with no Read call. Repeat with a mid-body nonce, ten runs. Also pin the runtime version next to the commit hash — the negative claim is version-bound and auto-memory behaviour has changed across releases.

**2. 5 022 tokens at 11 %.** Reframe the cost. The index is in the system prompt, hence prompt-cached; per-turn cost is a cache read. The real cost is context share (21.7 % of pre-question load) and dilution. The "28×" figure invites the wrong optimisation. On the decision: reject zero-resident. It converts a standing cost into a behavioural dependency, and P6 is your own evidence that behavioural steps here fail silently. You do have a natural control: the five directories with no index at all — do sessions there repeat mistakes more often? Small n, but it is the A/B you say you cannot run. Recommendation: hard-budget the resident tier (order 40–60 lines, ~5 KB, consistent with the 10 KB knee even as analogy) and route the rest through the door. Separately: does the 4.78 M-char figure include the 5 189 subagent runs? If subagents inherit the index at a 3.6 % hit rate, per-agent-type loading is a bigger lever than index size.

**3. Silent-title effect.** Measure triggers, not opens. For each entry define a trigger predicate observable in traces (a tool-call pattern, a path, an error string), then classify sessions where it fired: mistake recurred → entry failed; mistake absent → entry worked, silently or not; trigger never fired → dormant, not inert. Feedback-type entries almost always have a trigger. This partitions the 94 % with no A/B. Static complement: classify titles as self-sufficient rules ("use REST, not GraphQL, for PR edits") vs pointers ("notes on X"); an unopened rule is expected, an unopened pointer is inert. Then demotion is the experiment: demote through the door, log traversals; an entry the agent comes back for has earned residency.

**4. Corpus cap.** Drop T7. Dedup over 950 slugs is 450 k pairs, milliseconds; orphans are T2's job; maintenance cost is a property of the active set /dream iterates, not of the corpus. Replace with a cold tier: entries below threshold leave the maintenance loop (an `archive/` with its own index, still in git), not the disk. P1 stays intact, the ordering constraint in §6 disappears, /dream's cost is bounded. Cap the door index instead — a 900-line full index costs ~2.5 k tokens per traversal.

**5. Durability axis.** Yes. Type = subject, durability = lifetime; per-type TTL conflates them. Make durability the retention axis, type a default prior only. Where possible, replace the clock with a validity condition: most feedback entries are true until tool X changes, so record `valid_while: gh<2.70` (or a dependency version, a file hash) and expire on the condition. Deterministic (P3), and it does not wait 90 days. Enum: permanent / stable (re-validate every N days) / conditional (valid_while) / volatile (do not persist).

**6. Composite score.** Not as a weighted sum. A signal with a known inverted bias inside a weighted sum does harm proportional to its weight, and you have no weights. Use the signals asymmetrically: opens are a reliable positive signal and an unreliable negative one, so observed use is a veto on demotion (recently opened → never demoted), never a reason to demote. Retention then becomes lexicographic — which is the "staged hybrid" of §3: validity/durability gate → resident vs door by declared durability → size as tiebreak. Note also that "per token" barely applies to the resident tier: the tax is the title line (60–100 chars, near-uniform), not the body. Normalising by body size penalises long bodies that cost nothing; divide by the line if at all.

## Outside §8

1. **P2 has no ticket.** Every demotion (T4's flag, the resident budget) has nowhere to go until the door exists. Add a T-door before Wave 1: resident/full split, the 60-char line, the traversal defined. Everything that demotes depends on it.
2. **T4 reintroduces LFU.** "Unconfirmed for 90 days" — confirmed by what? If a /dream NOOP counts, everything is confirmed every run and yield stays zero. If only opens count, "unconfirmed" = "never opened" = the 94 % set, and decay is the use-count eviction P4 rejects. Define confirmation as positive re-validation (trigger fired, lesson held), or replace the time criterion with Q5's validity conditions.
3. **Admission is where the growth is.** +110 entries in 13 runs; 726 writes against 974 reads. The literature result you cite says eviction pressure raises quality; the cheapest form is an admission budget per /dream run (each ADD names what it displaces or merges into) plus a write-time hard cap on the resident index only.
4. **Make the door a search, not only a list.** A one-line pointer to `memory-search <query>` (SQLite FTS5 over titles, descriptions, bodies) makes the corpus reachable by content at O(1) resident cost, dissolves "unindexed = unreachable", and stays plain-file, portable, standard.
5. **Provenance records where, not who.** Add `source: user-stated | agent-observed | agent-inferred`. Agent-inferred entries (tool output, README text, dependency docs) are the poisoning surface; never auto-promote them to the harness tier without a human diff. Your promotion-by-PR is the right gate — make it explicit in T1.
6. **Tombstones as 35 files** serve a real purpose (do-not-relearn) at a walk cost. One `tombstones.md` (slug, date, reason) does the same.
7. **§3's benchmark ranking** (hybrid ≈0.911) comes from a task where access signals exist. On a 94 %-zero corpus, every access-dependent stage of that ranking is degenerate; only the deterministic stages transfer. Say so next to the 10 KB caveat.

**Wave order proposed:** T-door (new) → T1, T2, T3 → resident budget + admission budget (split from T7) → T5 → T4 rewritten on validity conditions → T6 as lexicographic policy → no corpus cap.
