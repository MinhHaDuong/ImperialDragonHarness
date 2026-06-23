---
name: feedback_no_tool_for_single_use
description: "For a single-use operation, run the command — don't build a tested reusable tool around it"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: fddacf5c-0539-4890-8018-5cd62c316c57
---

For a one-time operation, the command IS the deliverable. Do not inflate it into a script + tests + ticket + review.

**Why:** On 2026-06-18 I turned a single `rm -rf .venv && ln -sfn /data/envs/venv/oeconomia .venv` (reclaim 2 GB) into ticket 0145 + a 50-line guarded bash script + 7 integration tests + TDD + an independent review + two PRs. The user pushed back: "Ça fait beaucoup de cérémonies pour un rm suivi de ln non ?" then "C'est à usage unique." We scrapped the tool (PR #804 closed) and they ran the one-liner by hand. The ceremony came partly from my own ticket framing ("idempotent tested script") — I escalated a one-liner into a tooling project.

**How to apply:** Before building tooling, ask "is this single-use?" If yes: run the command (or hand it to the user when sandboxed), skip the script/tests/reusable-tool. Reusability — same op across many worktrees/machines, or recurring — is what justifies a tool; a one-time move does not. Safety guards (e.g. an lsof check) are only worth it if the tool will be re-run blindly; for a one-shot, the human checks the precondition once. Sibling of [[feedback_simplest_fix]] and [[feedback_no_long_running]]: prefer the smallest action that works within what exists.
