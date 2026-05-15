---
name: feedback-bash-background-sigterm
description: Bash tool kills background processes launched with & on return — use run_in_background=true instead
metadata:
  node_type: memory
  type: feedback
  originSessionId: 81fc99a1-8472-468c-bcbd-7194e0d2166b
---

`cmd &` inside a regular Bash tool call does NOT truly detach the process. The tool sends SIGTERM to its subprocess group on return (exit code 143 = 128+15). Long-running scripts die silently at exactly the tool's timeout boundary.

**Why:** Diagnosed 2026-05-13 when clean_corpus.py kept dying at ~5025 files (consistently the same wall-clock time regardless of concurrency). The kill is time-based, not file-based.

**How to apply:** For any long-running background process, use `run_in_background=true` in the Bash tool call parameters — this truly detaches the subprocess from the tool's lifecycle. Never rely on `&` appended to the command to keep a process alive past the tool call.
