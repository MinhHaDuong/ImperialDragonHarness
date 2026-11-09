kind: review-attribution
pr: 2349 · merged 2026-11-09 · project: harness
writer: step=plan · runtime=claude · model=anthropic/claude-sonnet-5-5 · effort=not-stated · route=subagent · independence=not-stated
writer: step=execute · runtime=claude · model=anthropic/claude-sonnet-5-5 · effort=not-stated · route=subagent · independence=not-stated
reviewer: step=review · seat=read · runtime=claude-code · model=anthropic/claude-sonnet-5-5 · effort=not-stated · route=subagent · independence=not-stated · status: ran
reviewer: step=review · seat=redteam · runtime=codex · model=openai/gpt-6.1-sol · effort=not-stated · route=gpt-6.1-sol · independence=not-stated · status: ran
  finding: verifiable · scripts/raid_land.py:88 · adopted: yes
  finding: verifiable · scripts/raid_land.py:334 · adopted: yes
  finding: verifiable · scripts/raid_land.py:91 · adopted: yes
reviewer: step=review · seat=probe · runtime=claude-code · model=anthropic/claude-opus-5-5 · effort=not-stated · route=self · independence=not-stated · status: ran
  finding: verifiable · scripts/raid_land.py:88 · adopted: yes
  finding: verifiable · scripts/raid_land.py:91 · adopted: yes
reviewer: step=review · seat=redteam · runtime=codex · model=openai/gpt-6.1-sol · effort=not-stated · route=unconfirmed · independence=not-stated · status: ran
  finding: verifiable · scripts/raid_land.py:93 · adopted: yes
reviewer: step=review · seat=probe · runtime=claude-code · model=anthropic/claude-opus-5-5 · effort=not-stated · route=self · independence=not-stated · status: ran
  finding: verifiable · scripts/raid_land.py:93 · adopted: yes
  finding: consider · scripts/raid_land.py:140 · adopted: yes
reviewer: step=review · seat=redteam · runtime=codex · model=openai/gpt-6.1-sol · effort=not-stated · route=gpt-6.1-sol · independence=not-stated · status: ran
reviewer: step=review · seat=probe · runtime=claude-code · model=anthropic/claude-opus-5-5 · effort=not-stated · route=self · independence=not-stated · status: ran
  finding: consider · scripts/raid_land.py:88 · adopted: no
