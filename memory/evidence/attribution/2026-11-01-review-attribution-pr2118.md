kind: review-attribution
pr: 2118 · merged 2026-11-01 · project: harness
writer: step=plan · runtime=claude · model=anthropic/claude-sonnet-5-5 · effort=not-stated · route=not-stated · independence=not-stated
writer: step=execute · runtime=claude · model=anthropic/claude-sonnet-5-5 · effort=not-stated · route=not-stated · independence=not-stated
reviewer: step=review · seat=xfam · runtime=claude-code · model=anthropic/gpt-6-luna · effort=not-stated · route=subagent · independence=not-stated · status: failed
reviewer: step=review · seat=tests-probes · runtime=claude-code · model=anthropic/claude-sonnet-5-5 · effort=not-stated · route=self · independence=not-stated · status: ran
reviewer: step=review · seat=adversarial · runtime=codex · model=openai/gpt-6.1-sol · effort=not-stated · route=gpt-6.1-sol · independence=not-stated · status: failed
reviewer: step=review · seat=redteam · runtime=codex · model=openai/gpt-6.1-sol · effort=not-stated · route=unconfirmed · independence=not-stated · status: ran
  finding: consider · scripts/gaze_seat.py:326 · adopted: no
reviewer: step=review · seat=redteam · runtime=codex · model=openai/gpt-6.1-sol · effort=not-stated · route=gpt-6.1-sol · independence=not-stated · status: ran
