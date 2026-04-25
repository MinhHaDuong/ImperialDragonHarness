#!/bin/bash
# One-shot setup: create claude-agent user, dev-projects group, system service.
# Run as haduong with sudo password:  bash ~/.claude/scripts/setup-claude-agent.sh
set -euo pipefail

HARNESS="$HOME/.claude"
PROJECTS=(
    "$HOME/aedist-technical-report"
    "$HOME/cadens"
    "$HOME/Climate_finance"
    "$HOME/fuzzy-corpus"
)

echo "── 1. User + group ──────────────────────────────────────────────────────"
sudo groupadd -f dev-projects
id claude-agent &>/dev/null || sudo useradd -r -s /usr/sbin/nologin -M -g dev-projects claude-agent
sudo usermod -aG dev-projects haduong      # haduong joins the group
sudo usermod -aG dev-projects claude-agent # redundant but explicit

echo "── 2. Project dirs: group dev-projects, g+rwX, setgid ──────────────────"
for d in "${PROJECTS[@]}"; do
    sudo chown -R haduong:dev-projects "$d"
    sudo chmod -R g+rwX "$d"
    sudo find "$d" -type d -exec chmod g+s {} +   # batch: one process for all dirs
done

echo "── 3. API key env file (ANTHROPIC_API_KEY only) ─────────────────────────"
sudo mkdir -p /etc/claude-agent
grep 'ANTHROPIC_API_KEY' "$HARNESS/.env" | sudo tee /etc/claude-agent/env >/dev/null
sudo chown claude-agent /etc/claude-agent/env   # no separate group needed
sudo chmod 400 /etc/claude-agent/env

echo "── 4. Log dir ───────────────────────────────────────────────────────────"
mkdir -p "$HARNESS/logs/night-sweep"
# ACL: claude-agent can write logs (no sudo needed — haduong owns the dir)
setfacl -m u:claude-agent:rwx "$HARNESS/logs"
setfacl -m d:u:claude-agent:rwx "$HARNESS/logs"   # default ACL for new subdirs
setfacl -m u:claude-agent:rwx "$HARNESS/logs/night-sweep"
setfacl -m d:u:claude-agent:rwx "$HARNESS/logs/night-sweep"

echo "── 5. Harness read-only access for claude-agent ─────────────────────────"
# Traverse + read on ~/.claude/ and all subdirs/files …
setfacl -R -m u:claude-agent:rX "$HARNESS"
# … but NOT the .env (other providers' keys live there)
setfacl -m u:claude-agent:--- "$HARNESS/.env"

echo "── 6. Install system service + timer ────────────────────────────────────"
sudo cp "$HARNESS/scripts/claude-night-sweep.service" /etc/systemd/system/
sudo cp "$HARNESS/scripts/claude-night-sweep.timer"   /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now claude-night-sweep.timer

echo "── 7. Disable the old user-level timer ──────────────────────────────────"
systemctl --user disable --now claude-night-sweep.timer 2>/dev/null || true

echo ""
echo "Done. Verify with:"
echo "  systemctl list-timers claude-night-sweep.timer"
echo "  sudo systemctl start claude-night-sweep.service   # test run"
echo "  sudo journalctl -u claude-night-sweep.service -f  # watch logs"
