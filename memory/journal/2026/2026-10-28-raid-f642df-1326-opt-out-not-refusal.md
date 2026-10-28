# Raid f642df, ticket 1326: the lost cross-family seat was an opt-out, not a refusal

Date: 2026-10-28 · PR #1925 (merged 56c1133a) · ticket 1326 (closed)

## Context
Ticket 1326 assumed a gaze run from a subagent could not launch a codex seat
(raid f7fa41, PR #1915 merged with same-family review only). Candidates named:
subagent permission layer, nesting depth, seat sandbox.

## Events
- Reproduction by a coder subagent: `gaze_seat.py launch --runtime codex` reported
  in 8 s at depth 1 and 10 s at depth 2 (nested Agent), exit 0, launcher header
  `door=headless`, no permission, nesting or sandbox refusal.
- Notes for review `rv-20261028-pr-1915-f0c6`: five answers, none planned a
  cross-family seat; each plan carried a `no cross-family seat:` reason written by
  the gaze run itself (e.g. "host not consenting") while the host consents to
  OpenAI and Mistral.
- PR #1925 adds `--require-cross-family <producer family>` to `review_notes.py`
  gate/verdict; self, subagent and unconfirmed seats never count; a headless seat
  without the launcher header is `route=unconfirmed`. Gaze took 3 rounds (two
  reproduced blocking findings from the OpenAI redteam seat); the headless
  claude-code correctness seat failed with an empty log in rounds 1 and 2.
- Verify-gate APPROVED round 1; the branch's own check admitted the PR's review
  with `--require-cross-family anthropic` and refused it with `openai`.
- Worktree collision: hunt's `t$ID-$PPID` path equalled the raid orchestrator's
  session worktree (`t1326-3606107`); the coder switched that clean tree to the PR
  branch and `raid_land.py --cleanup` removed it. No work lost (all committed).

## Outcome
Merged. Ticket filed for the worktree-name collision.
