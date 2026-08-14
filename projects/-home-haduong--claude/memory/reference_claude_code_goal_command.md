---
name: reference_claude_code_goal_command
description: "/goal is a real but flag-hidden Claude Code command — a session-scoped Stop hook that blocks stopping until a 4000-char condition holds; absent from --help and from the skills list"
metadata:
  type: reference
---

`/goal <condition>` exists in Claude Code (confirmed in the 2.1.232 binary,
2026-08-14) but is **hidden behind a feature flag**, so it appears in neither
`claude --help` nor the session's available-skills listing. Searching those two
places and concluding it does not exist is the wrong inference — grep the
binary instead.

Extracted definition:

```js
{type:"local-jsx", name:"goal",
 description:"Set a goal Claude checks before stopping",
 argumentHint:"[<condition> | clear]"}
{type:"local", name:"goal", supportsNonInteractive:true,
 isHidden:()=>!On(), isEnabled:()=>On()||Sl()}
```

Mechanism: it registers a **session-scoped Stop hook** whose prompt is the
condition, and sets `activeGoal = {condition, iterations, setAt, tokensAtStart}`.
The hook blocks stopping until the condition holds, then auto-clears. The
injected directive tells the model to treat the condition as its directive and
not to pause to ask the user.

Four constraints that decide whether it fits a design:

- **4000-character cap** on the condition (`UNr=4000`).
- **Session-scoped.** It does not survive across sessions, so a per-cycle
  scheduled-session architecture cannot hold a goal across cycles — adopting it
  means one long session instead of many short ones.
- **The condition is judged by a prompt hook** — the model assessing its own
  work. It can carry done-ness; it cannot carry independent verification.
- Requires a **trusted workspace**, and refuses when `disableAllHooks` or
  `allowManagedHooksOnly` is set.

`supportsNonInteractive: true`, so it does work headless.

**Why:** it is a *continuation* primitive, not an orchestrator — it defines
when to stop, not how to work. That makes it the right replacement for
procedural scaffolding whose real job was "keep going" and "here is done", and
the wrong replacement for anything that must actually be verified. See
[[feedback_tests_pinning_prompt_prose]].
