#!/usr/bin/env bash
# Switch the Claude Code adapter plugin on or off.
#
# Ticket 0887. The adapter ships inert on purpose. On this machine the harness
# repository *is* ~/.claude, so a plugin directory reachable under skills/ is
# auto-discovered on the next session -- while the live settings.json still
# carries its own copy of the same hooks. Both sources firing means every guard
# runs twice, on-start.sh backgrounds its git sync twice, and the log lines
# double. The symlink this script creates is therefore the switch, and the
# switch refuses to close while the live file would double-fire.
#
#   activate            create the link, after checking the live file
#   --revert            remove the link
#   --status            say which state we are in, change nothing
#
# What it deliberately does NOT do: edit the live settings.json. That file is
# the operator's, it is outside the repository by design, and a script that
# silently rewrites a user's live configuration is the wrong shape. It tells
# you what to remove and stops.
set -euo pipefail

HARNESS_DIR="${HARNESS_DIR:-$HOME/.claude}"
LINK="$HARNESS_DIR/skills/claude-code"
TARGET_REL="../adapters/claude-code"
TARGET_ABS="$HARNESS_DIR/adapters/claude-code"
LIVE="$HARNESS_DIR/settings.json"

live_has_hooks() {
    [ -f "$LIVE" ] || return 1
    python3 - "$LIVE" <<'PY'
import json, sys
try:
    live = json.load(open(sys.argv[1]))
except (OSError, ValueError):
    sys.exit(2)                      # unreadable: treat as "cannot rule it out"
sys.exit(0 if live.get("hooks") else 1)
PY
}

status() {
    if [ -L "$LINK" ]; then
        echo "adapter: ACTIVE ($LINK -> $(readlink "$LINK"))"
    elif [ -e "$LINK" ]; then
        echo "adapter: $LINK exists and is not a symlink — refusing to touch it"
        return 1
    else
        echo "adapter: inert (no $LINK)"
    fi
    if live_has_hooks; then
        echo "live settings.json: carries a hooks block"
    else
        echo "live settings.json: no hooks block"
    fi
}

case "${1:-activate}" in
  --status)
    status
    ;;
  --revert)
    if [ -L "$LINK" ]; then
        rm "$LINK"
        echo "adapter: reverted — $LINK removed; the live settings.json hooks are your only source again"
    else
        echo "adapter: already inert, nothing to remove"
    fi
    ;;
  activate)
    [ -d "$TARGET_ABS" ] || { echo "adapter: $TARGET_ABS not found" >&2; exit 1; }
    [ -e "$LINK" ] && { echo "adapter: $LINK already exists — run --status" >&2; exit 1; }
    if live_has_hooks; then
        cat >&2 <<MSG
adapter: refusing to activate — $LIVE still carries a hooks block.

Both sources would fire: every guard twice, on-start.sh's git sync twice.
Remove the "hooks" key from $LIVE (it is your file, outside the repository by
design; this script will not edit it), then run this again. Ticket 0886 is what
turns that hand edit into one command.
MSG
        exit 1
    fi
    ln -s "$TARGET_REL" "$LINK"
    echo "adapter: ACTIVE — $LINK -> $TARGET_REL"
    echo "The hooks now come from the plugin. Start a new session and confirm a guard fires;"
    echo "reading this message is not evidence that it does. Revert with --revert."
    ;;
  *)
    echo "usage: $(basename "$0") [activate|--revert|--status]" >&2; exit 2
    ;;
esac
