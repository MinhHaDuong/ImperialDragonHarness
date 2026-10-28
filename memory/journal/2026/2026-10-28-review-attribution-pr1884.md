kind: review-attribution
pr: 1884 · merged 2026-10-28 · project: ImperialDragonHarness
writer: step=plan · runtime=claude · model=anthropic/claude-sonnet-5-5 · effort=not-stated · route=sonnet · independence=not-stated
writer: step=execute · runtime=claude · model=anthropic/claude-sonnet-5-5 · effort=not-stated · route=sonnet · independence=not-stated
reviewer: step=review · seat=self · runtime=claude-code · model=anthropic/claude-sonnet-5-5 · effort=not-stated · route=self · independence=not-stated · status: ran
reviewer: step=review · seat=correctness · runtime=codex · model=openai/gpt-6.1-sol · effort=not-stated · route=gpt-6.1-sol · independence=not-stated · status: ran
  finding: consider · tests/test_raid_sitrep.py:217 · adopted: no
  finding: consider · scripts/raid_log.py:42 · adopted: no
reviewer: step=review · seat=docs · runtime=claude-code · model=anthropic/claude-opus-5-5 · effort=not-stated · route=self · independence=not-stated · status: ran
  finding: consider · skills/raid/references/sitrep.md:7 · adopted: no
  finding: consider · tickets/1310-raid-log-carries-a-raid-id-so-concurrent.erg:25 · adopted: no
reviewer: step=review · seat=correctness · runtime=codex · model=openai/gpt-6.1-sol · effort=not-stated · route=gpt-6.1-sol · independence=not-stated · status: ran
