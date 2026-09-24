# docs/

Reference materials and review records for the Imperial Dragon Harness.

**Dragon memory design — the authoritative document is
[`2026-09-10-dragon-memory-design.md`](./2026-09-10-dragon-memory-design.md),
currently v7.** Everything else in that family is a frozen record: the
predecessor v6, the reviews, the provider study notes and the measurement
notes. Drafts v0 through v5 were retired from the tree; see *Superseded
drafts* below.

## References

| File | What |
|------|------|
| `Forsythe-2026-10principles.md` | Forsythe's 10 Claude Code Principles (converted from ODT) |
| `DevMoses-2026-5levels.md` | 5-level harness maturity framework |
| `VISION-original.md` | Original harness vision document |
| `2026-03-19-memo-harness-extraction.md` | Extraction memo: splitting generic from project-specific config |
| `2026-04-03-harness-best-practices-research.md` | Evidence-based research report (8 papers, 3 official docs) |
| `2026-09-11-memory-systems-comparison.md` | Architectural comparison with MemU, Letta, Mem0 and Graphiti; review amendments and licence-aware reuse |
| `2026-09-11-memory-implementation-plan.md` | V6 implementation train: dependencies, pilot milestone, rollout and deferred experiments |
| `2026-09-24-rules-coherence-audit.md` | Harness ↔ project directive coherence audit of eleven repos: findings, in-flight PR check, ranked preconisations (tracker 0956) |
| `2026-09-10-dragon-memory-design.md` | **Authoritative** design for the harness memory system — always the current version, v7 today |
| `2026-09-10-dragon-memory-design-v6.md` | Frozen v6 — the predecessor the open memory tickets (0908–0925) were written against |
| `2026-09-10-dragon-memory-design-nomenclature.md` | Settled nomenclature for the memory system — the vocabulary v7 and the open tickets use |
| `2026-09-10-dragon-memory-design-review-fable-acceptance.md` | **Non-normative** acceptance review of v6 — accept with four §12.1 conditions, all closed by v7 |
| `2026-09-10-portable-agent-memory-calibration.md` | Calibration note for the memory tier: what the literature fixes, what it declines to fix, and the local measurement to run |
| `2026-09-10-memoire-agent-fable.md` | **Non-normative study report** by Fable — agent memory: state of the art and a proposal for IDH, suggested and not adopted (French) |
| `2026-09-10-memoire-agent-perplexity.md` | **Non-normative study report** by Perplexity on the same question, solicited independently (French) |
| `2026-09-10-memoire-agent-chatgpt.md` | **Non-normative study report** by ChatGPT on the same question, solicited independently (French) |
| `2026-09-10-dragon-memory-design-review-claude.md` | **Non-normative review** by Claude of the memory design draft — answers its section 8; in-family, read alongside the ChatGPT review |
| `2026-09-10-dragon-memory-design-review-chatgpt.md` | **Non-normative review** by ChatGPT of the same draft — the out-of-family read it asked for; substantial revisions before sign-off (French) |
| `2026-09-10-dragon-memory-design-review-fable-design.md` | **Non-normative review** by a Fable panel of v3 — design-scoped; finds that the index cut removes awareness rather than only reachability |
| `2026-09-10-valid-while-coverage-ledger.md` | Measurement record — what a `valid_while` predicate grammar can express and evaluate over real memory bodies |
| `2026-09-10-dragon-memory-design-review-fable.md` | **Non-normative review** by a Fable panel of v1 — the first with repository access; refutes v1's central amendment and finds the recall channel in the runtime |

## Reviews

| Directory | What |
|-----------|------|
| `20260404-review/` | 5-perspective harness audit with synthesis and ticket plan |

## Superseded drafts

Drafts v0 through v5 of the dragon memory design were removed from the tree on
2026-09-16: they were superseded by v6 and v7 and nothing outside `docs/`
referenced them. Git history is the project's long-term memory, so read them
back from there rather than from the working tree:

```bash
git log --diff-filter=D --oneline -- 'docs/2026-09-10-dragon-memory-design-v*.md'
git show <sha>^:docs/2026-09-10-dragon-memory-design-v3.md
```

Frozen records — v6 and the review documents — still link to those drafts by
relative path. Those links are left as written: the records are historical and
editing them would falsify what the reviewers read. Follow them through git
history instead.
