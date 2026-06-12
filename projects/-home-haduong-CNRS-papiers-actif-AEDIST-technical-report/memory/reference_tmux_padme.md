---
name: launch-interactive-claude-on-padme-via-tmux
description: How to start a named tmux session on padme for interactive Claude Code work (companion to nohup recipe)
metadata: 
  node_type: memory
  type: reference
  originSessionId: 7dae5ef0-afaf-42b7-a81b-8409f7419ece
---

## Recipe: interactive Claude on Padme via tmux

Companion to [[reference_autonomous_padme]] — that one is `nohup --print` for unattended runs; this one is interactive tmux for live driving.

### Start a new session

```bash
ssh padme
tmux new -s claudeN          # claude1, claude2, ... pick a free name
# inside the tmux window:
export PATH=$HOME/.local/bin:$PATH
source ~/.claude/.env && export ANTHROPIC_API_KEY
cd ~/aedist-technical-report
claude
# detach: Ctrl-b d
```

### One-liner from local shell (creates detached, ready to attach)

```bash
ssh padme "tmux new -d -s claudeN 'export PATH=\$HOME/.local/bin:\$PATH; source ~/.claude/.env && export ANTHROPIC_API_KEY; cd ~/aedist-technical-report; exec bash'"
ssh padme -t tmux attach -t claudeN
```

### Reattach

```bash
ssh padme -t tmux attach -t claudeN
```

### List / kill

```bash
ssh padme tmux ls
ssh padme tmux kill-session -t claudeN
```

**Key details:**
- Claude binary: `~/.local/bin/claude` (symlink to `~/.local/share/claude/versions/<v>`)
- Auth: `ANTHROPIC_API_KEY` in `~/.claude/.env` — `source` + `export` in the tmux shell
- OpenRouter key: `~/aedist-technical-report/.env` (sourced by repo tooling)
- Naming convention observed in practice: `claude1`, `claude2`, ... one tmux session per concurrent interactive agent
- `ssh -t` is required for attach (TTY)

**When to use tmux vs nohup:**
- tmux — you want to watch / interact / approve permissions live
- nohup `--print --dangerously-skip-permissions` — fire-and-forget autonomous run with budget cap
