---
name: host-file-writes-avoid-heredoc
description: avoid heredoc for host file edits sent through chat — leading spaces and first-line splitting cause silent corruption
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 9993d6d0-9b52-45c8-a2f9-af09c65ce564
---

When writing files on the host via chat-pasted commands, heredocs are fragile: the terminal/chat interface can indent content (adding leading spaces) or split the first line after `<<'EOF'` into a filename argument instead of stdin. Both corrupted `/etc/profile.d/dev-cache.sh` on 2026-06-08.

**Why:** The `tee -a /path << 'EOF'` pattern looks clean but the first content line gets mangled if there's any whitespace between the heredoc marker and the content. Leading spaces in the chat block become literal leading spaces in the file.

**How to apply:** For host file edits sent through chat, use one of these instead:
- `printf 'line1\nline2\n' | sudo tee /path` (explicit, no heredoc)
- `sudo tee /path > /dev/null` with content on truly separate unindented lines
- A Python one-liner: `python3 -c "open('/path','w').write('...')"`
