---
name: feedback-gaze-resolve-pr-number-before-invoking
description: /gaze hard-refuses without a PR number by design; the caller (main loop), not the skill, must resolve it from conversation context first
metadata:
  type: feedback
---

`/gaze`'s phase-1 directive (`skills/gaze/SKILL.md:14-17`) STOPs and returns
ESCALATE if `$ARGUMENTS` has no PR number, and explicitly forbids inferring
one from the environment (worktree name, git status, ticket files, task
list). This is intentional, not overzealous: it's the hardening that followed
ticket 0193 — a bare `context: fork` invocation once guessed its target from
ambient state and drifted onto the wrong branch, pushing a stray branch and
opening a rogue PR (#243). See [[feedback_fork_skills_bare_context]].

**Why:** the fork has no conversation to draw on, so any inference it makes
is a guess over ambient filesystem state — exactly the failure mode that bit
before. The guard is correctly scoped to the fork's cold start, not to the
caller.

**How to apply:** when the user invokes `/gaze` without a number but the
conversation unambiguously implies one (a PR just opened this session, "the
PR for branch X" already discussed, etc.), resolve the PR number in the main
loop BEFORE calling the skill — pass `/gaze <N>` explicitly. Don't relay the
skill's hard refusal back to the user as if no fix were possible, and don't
loosen the fork's own no-inference rule to fix this — that reopens the
0193 surface. If the conversation genuinely doesn't pin down a PR, ask the
user for the number rather than guessing.
