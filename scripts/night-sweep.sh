#!/bin/bash
# Autonomous night-sweep agent: surveys one project per hour and does the
# highest-priority available task. Runs 22:00–06:00 via systemd user timer.
#
# Auth: OAuth via ~/.claude/.credentials.json (Max account).
# Logs: ~/.claude/logs/night-sweep/ — text headers + stream-json from claude.
#       Extract cost: grep '"type":"result"' <logfile> | jq '.total_cost_usd'
set -euo pipefail

HARNESS_DIR="$HOME/.claude"
PROJECTS_ROOT="$HOME"

export PATH="$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin"

# Git author identity for commits by the agent
export GIT_AUTHOR_NAME="claude-agent"
export GIT_AUTHOR_EMAIL="claude-agent@localhost"
export GIT_COMMITTER_NAME="claude-agent"
export GIT_COMMITTER_EMAIL="claude-agent@localhost"

# ERR trap: write a tombstone on any unexpected failure
trap 'echo "=== night-sweep ABORT rc=$? line $LINENO $(date -u +%FT%TZ) ===" >&2' ERR

# ── Lock: skip if a previous run hasn't finished ─────────────────────────────
# fd 200 is released on exit, unlocking automatically
LOCKFILE="${RUNTIME_DIRECTORY:-${XDG_RUNTIME_DIR:-$HOME/.cache}}/night-sweep.lock"
exec 200>"$LOCKFILE"
flock -n 200 || { echo "$(date -u +%FT%TZ): another sweep still running, skipping." >&2; exit 0; }

# ── Logging ──────────────────────────────────────────────────────────────────
LOGDIR="$HARNESS_DIR/logs/night-sweep"
mkdir -p "$LOGDIR"
LOGFILE="$LOGDIR/$(date -u +%Y%m%dT%H%M%SZ).log"
exec > >(tee -a "$LOGFILE") 2>&1
# Close fd 1 on exit so tee gets EOF and flushes; wait ensures no truncation
trap 'exec 1>&- 2>&-; wait 2>/dev/null || true' EXIT

# Keep the last 60 log files (≈ one week of nightly runs)
find "$LOGDIR" -name "*.log" -type f | sort -r | tail -n +61 | xargs -r rm -f 2>/dev/null || true

echo "=== night-sweep start $(date -u +%FT%TZ) ==="

# ── Project rotation (sequential counter, even coverage) ─────────────────────
PROJECTS=(
    "$PROJECTS_ROOT/aedist-technical-report"
    "$PROJECTS_ROOT/cadens"
    "$PROJECTS_ROOT/Climate_finance"
    "$PROJECTS_ROOT/fuzzy-corpus"
)

COUNTER_FILE="$LOGDIR/.run-counter"
COUNT=$(cat "$COUNTER_FILE" 2>/dev/null || echo 0)
IDX=$(( COUNT % ${#PROJECTS[@]} ))
echo $(( COUNT + 1 )) > "$COUNTER_FILE"

# Guard against array shrink under set -u
(( IDX < ${#PROJECTS[@]} )) || { echo "ERROR: slot $IDX out of range (${#PROJECTS[@]} projects)"; exit 1; }

export PROJECT="${PROJECTS[$IDX]}"
echo "Run $COUNT  →  project slot $IDX: $PROJECT"

if [[ ! -d "$PROJECT/.git" ]]; then
    echo "ERROR: $PROJECT is not a git repository. Aborting."
    exit 1
fi

cd "$PROJECT"

# ── State directory bootstrap ────────────────────────────────────────────────
mkdir -p "$PROJECT/.claude/sweep-state"

# ── Run Claude ────────────────────────────────────────────────────────────────
# --permission-mode bypassPermissions  non-interactive unattended mode
# --output-format stream-json          structured output; cost in .usage field
# --no-session-persistence             no writes to harness session store
# --settings                           destructive-bash + no-push guards
# --add-dir                            load CLAUDE.md from harness and project
# CLAUDE_NIGHT_SWEEP=1 tells on-start.sh to skip the worktree isolation message
# timeout 55m: kill hung agent before next timer firing (timer is hourly)
# Override SKILL env var to use a different entry point (e.g. /smoke)
SKILL="${SKILL:-/beat}"
timeout 55m claude \
    --print \
    --verbose \
    --output-format stream-json \
    --permission-mode bypassPermissions \
    --no-session-persistence \
    --max-budget-usd 1.00 \
    --model sonnet \
    --settings "$HARNESS_DIR/scripts/night-sweep-settings.json" \
    --add-dir "$HARNESS_DIR" \
    --add-dir . \
    -p "$SKILL"

echo "=== night-sweep done $(date -u +%FT%TZ) ==="
