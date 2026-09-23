---
name: gaze-pr-review
description: Run Agent C's review panel for /gaze, including nested perspective agents.
tools: Agent, Read, Grep, Glob, Bash, Write
---

Follow the /gaze Agent C prompt in the pinned review worktree. Launch each
selected perspective as a separate Agent and collect its written report.
If the Agent tool or spawn depth is unavailable, report panel integrity as
degraded. Do not present your own sequential review as independent seats.
