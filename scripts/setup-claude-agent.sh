#!/bin/bash
# One-shot setup: create claude-agent user, dev-projects group, system service.
# Run as haduong with sudo password:  bash ~/.claude/scripts/setup-claude-agent.sh
set -euo pipefail

HARNESS="$HOME/.claude"
# Canonical project registry — the single source of truth also read by
# beat.py, the nightbeat survey, and scry. Override for tests.
REGISTRY="${PROJECTS_JSON:-$HARNESS/scripts/projects.json}"

# Derive the project directories that get dev-projects group ownership.
# Reads the registry, expands a leading ~ to $HOME (as the Python consumers do
# via expanduser), and excludes the harness itself: ~/.claude receives
# read-only ACL access in steps 4-5, so granting it group write here would
# contradict that design and expose the config tree. Every other registry
# entry is a project the overnight agent works on and needs write access to.
derive_project_dirs() {
    local name path tsv
    # Capture jq's output into a variable BEFORE the loop so its exit status is
    # observable under `set -e`. A `< <(jq …)` process substitution hides jq's
    # failure — `set -e` only reacts to a pipeline's status under `pipefail`,
    # and process substitution is neither — so a missing or malformed registry
    # would silently yield an empty list and exit 0, and the ownership loop
    # would run zero iterations while the script still printed "Done." A valid
    # but empty registry (`[]`) yields empty output with jq exit 0, which is a
    # legitimate degenerate state and must NOT abort.
    tsv="$(jq -r '.[] | [.name, .path] | @tsv' "$REGISTRY")" \
        || { echo "derive_project_dirs: failed to read registry $REGISTRY" >&2; exit 1; }
    # Empty registry (`[]`) → empty $tsv. A here-string of "" still feeds one
    # blank line, so guard it to avoid emitting a spurious empty project dir.
    [ -z "$tsv" ] && return 0
    while IFS=$'\t' read -r name path; do
        path="${path/#\~/$HOME}"          # expand leading ~ only
        [ "$path" = "$HARNESS" ] && continue
        printf '%s\n' "$path"
    done <<< "$tsv"
}

# `--list` prints the derived dirs and exits — the testable, side-effect-free
# entry point. Everything below it mutates the system and needs sudo.
if [ "${1:-}" = "--list" ]; then
    derive_project_dirs
    exit 0
fi

mapfile -t PROJECTS < <(derive_project_dirs)

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
