kind: review-attribution
pr: 2085 · merged 2026-10-31 · project: ImperialDragonHarness
writer: step=execute · runtime=claude-code · model=anthropic/claude-opus-5-5 · effort=not-stated · route=landing · independence=not-stated
reviewer: step=review · seat=correctness · runtime=claude-code · model=anthropic/sonnet · effort=not-stated · route=sonnet · independence=not-stated · status: ran
  finding: consider · skills/gaze/references/plan.md:129 · adopted: yes
  finding: consider · tests/test_seat_clock.py:188 · adopted: yes
reviewer: step=review · seat=redteam · runtime=codex · model=openai/gpt-6.1-sol · effort=not-stated · route=gpt-6.1-sol · independence=not-stated · status: ran
reviewer: step=review · seat=delta · runtime=claude-code · model=anthropic/sonnet · effort=not-stated · route=subagent · independence=not-stated · status: ran
  finding: consider · skills/route/references/decorrelation.md:32 · adopted: no
reviewer: step=review · seat=redteam · runtime=codex · model=openai/gpt-6.1-sol · effort=not-stated · route=gpt-6.1-sol · independence=not-stated · status: ran
