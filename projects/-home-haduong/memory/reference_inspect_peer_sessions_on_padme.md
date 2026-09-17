---
name: reference_inspect_peer_sessions_on_padme
description: "How to see what other Claude and Codex clients on padme are doing, and the two traps met while closing them (2026-09-17)"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 86cc53ac-e558-4443-affc-ce2276333c00
  modified: 2026-09-17T15:40:10.725Z
---

Claude Code peers on the same machine are listed by `ListAgents` and reachable by `SendMessage`; Codex clients are not, so they are read from the outside: `readlink /proc/<pid>/cwd` for the repo, and the session log `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`, where `session_meta` carries `cwd`, `response_item` messages with `role: assistant` carry the agent's replies, and the last one says whether the session finished or stalled. A client whose work is done still runs until someone types: `kill -TERM <pid>` then `kill -HUP` on its bash closes it without losing the transcript.

**Why:** three Codex sessions sat idle for hours after finishing; the author's question "finished or out of tokens?" is answered by the last assistant message, not by `ps`.

**How to apply:** never `pkill -f <pattern>` from the session doing the killing when the pattern appears in its own command line (it killed my own shell twice, exit 144); use `pgrep -f '[h]ttp.server'` style patterns. `pts/N` numbers are reused within minutes, so identify a terminal by pid, never by its pts. Related: [[reference_padme_display]], [[feedback_tour_des_chantiers_advisor_role]].
