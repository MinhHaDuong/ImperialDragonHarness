# Pi acceptance leg interrupted by provider credit depletion

Context: memory-v8 acceptance trial (ticket 0918), the Pi runtime leg
(pi 0.87.1, provider huggingface, model moonshotai/Kimi-K2.6 per the
session header), one headless session in a disposable clone on 2026-10-02,
started 11:01:18Z.

Observation: the session read memory/MEMORY.md and the worktree-guards
topic before any write (read tool calls at 11:01:54Z, git rev-parse of both
blob revisions in the same turn), then worked through the trial steps
slowly — the retired read-index helper invocation (exit 2) at 11:05:29Z,
the occupied-slug capture refusal at 11:06:49Z, the routine relocated-clone
test at 11:07:27Z. While preparing its captures (reading
scripts/memory-capture.sh source at 11:13:40Z), the session ended with
"You have depleted your monthly included credits" from the provider and
pi exited 1. No journal entry and no capture-decision report was produced;
the session record in the disposable --session-dir is the only evidence
channel.

Consequence: the pi cells of the trial record interrupted outcomes, not
captures: three capture opportunities occurred in the session but yielded
neither an entry nor a recorded no-capture verdict. The interruption is an
external provider limit, not an observed capture decision by the runtime;
whether the credits reset and the leg can be re-run later is not
established here.

Evidence: /tmp/mem0918/pi/sessions/*.jsonl (33 events, timestamps above),
the empty capture log and exit=1 status, and the provider message quoted in
/tmp/mem0918/pi/stream.jsonl. The clone was disposable; nothing was
committed from it.
