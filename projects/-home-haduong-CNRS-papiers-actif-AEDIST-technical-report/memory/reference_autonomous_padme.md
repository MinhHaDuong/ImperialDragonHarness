---
name: Launch autonomous Claude on Padme
description: How to nohup Claude Code on Padme to work on a ticket autonomously
type: reference
---

## Recipe: autonomous Claude on Padme

```bash
ssh padme "export PATH=\$HOME/.local/bin:\$PATH && \
  source ~/.claude/.env && export ANTHROPIC_API_KEY && \
  cd ~/aedist-technical-report && \
  nohup claude --print --dangerously-skip-permissions \
    --max-budget-usd 5 \
    'Your prompt here — describe the ticket, the task, where to find keys, branch instructions' \
  > ~/autonomous_TASKNAME.log 2>&1 &"
```

**Key details:**
- Claude Code CLI at `~/.local/bin/claude` (not on default PATH)
- Auth: `ANTHROPIC_API_KEY` in `~/.claude/.env` — must `source` and `export`
- OpenRouter key: in `~/aedist-technical-report/.env` — tell Claude to source it
- `--print` for non-interactive, `--dangerously-skip-permissions` for full autonomy
- `--max-budget-usd` to cap spend
- Always nohup, always log to `~/autonomous_TASKNAME.log`
- Monitor: `ssh padme "tail -30 ~/autonomous_TASKNAME.log"`
- Check process: `ssh padme "pgrep -af 'claude.*print.*dangerously'"`

**How to apply:** When user asks to launch autonomous work on Padme for a ticket.
