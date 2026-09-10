---
name: feedback-subagent-traces-dilute-every-rate
description: "subagent runs outnumber main sessions nine to one in the trace corpus, so any per-session rate computed over all .jsonl files is diluted about tenfold"
metadata:
  type: feedback
---

# Separate subagent runs from main sessions, or every rate is wrong

Session traces live at `~/.claude/projects/<slug>/<uuid>.jsonl`. Subagent runs
live one level deeper, at `<slug>/<session>/subagents/agent-*.jsonl`, and
**they outnumber main sessions about nine to one** — 5 189 against 564 on
2026-09-10.

A walk with `os.walk` picks up both. Measuring "what fraction of sessions do X"
over the union therefore divides the answer by ten while measuring a different
population: a subagent is launched with a task, not with a morning's
uncertainty, so it was never a candidate for most session-level behaviours.

**Why:** it happened. A measurement of how often a session consults its memory
index read 3.83% over the union and 11.01% over main sessions alone — the
difference between "nobody uses this" and "one session in nine". Diluting the
arm under test with runs that could not exhibit the behaviour is how a real
effect is made to look like noise.

**How to apply:** classify by path depth relative to the projects root — one
component is a main session, more is a subagent — and report the arms
separately rather than summing them. The same call also caught a second
counting error worth the same care: a session that both `Read` and `cat`'d a
file is one session, and summing the two channels inflated the arm by a
quarter.

Instrument: `scripts/census/memory-recall.py`.

See also [[reference_no_recall_channel_fires]], [[feedback_trace_usage_dedupe_by_message_id]].
