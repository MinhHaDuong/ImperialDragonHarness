#!/usr/bin/env bash
# Switch the Claude Code adapter plugin on or off.
#
# Ticket 0887. The adapter ships inert on purpose. The harness and runtime profile are independent. A plugin directory
# registered under the runtime's skills/ is
# auto-discovered on the next session. When the live settings.json ALSO
# carries a copy of the same hooks, both sources fire: every guard runs
# twice, on-start.sh backgrounds its git sync twice, and the log lines
# double. The symlink this script creates is therefore the switch, and the
# switch refuses to close while the live file would double-fire.
#
# Run from a git worktree, activate and revert both refuse: the link already
# exists (activate) or does not point at THIS checkout's adapter (revert's
# managed-link check), so a worktree session can neither move nor remove the
# reference checkout's switch.
#
#   activate            create the link, after checking the live file
#   --revert            remove the link
#   --status            say which state we are in, change nothing
#
# What it deliberately does NOT do: edit the live settings.json. That file is
# the operator's, it is outside the repository by design, and a script that
# silently rewrites a user's live configuration is the wrong shape.
#
# Since the activation (ticket 0887) the canonical settings.shared.json
# carries no hooks at all: the plugin is the single hook source. Reverting
# therefore leaves the guards off until a hooks block is restored to the live
# settings -- the block lives in git history, in the commit that removed it.
# --revert allows that rollback and says so loudly instead of refusing
# forever against a precondition the endgame removed.
set -euo pipefail

ROOT=$(cd -- "$(dirname -- "$(readlink -f -- "${BASH_SOURCE[0]}")")/.." && pwd -P)
HARNESS_DIR="${HARNESS_DIR:-$ROOT}"
LINK="$HOME/.claude/skills/claude-code"
TARGET_REL="$HARNESS_DIR/adapters/claude-code"
TARGET_ABS="$HARNESS_DIR/adapters/claude-code"
# Configuration belongs to the runtime profile.
LIVE="$HOME/.claude/settings.json"

inspect_live_hooks() {
    if [ ! -e "$LIVE" ]; then
        [ -L "$LIVE" ] && return 2
        return 1
    fi
    [ -f "$LIVE" ] || return 2
    python3 - "$LIVE" <<'PY'
import json, sys

try:
    with open(sys.argv[1]) as stream:
        value = json.load(stream)
except (OSError, ValueError):
    sys.exit(2)
if not isinstance(value, dict):
    sys.exit(2)
hooks = value.get("hooks")
if hooks is None or hooks == {}:
    sys.exit(1)
if not isinstance(hooks, dict):
    sys.exit(2)
sys.exit(0)
PY
}

load_live_hooks_state() {
    if inspect_live_hooks; then
        LIVE_HOOKS_STATE=present
    else
        case $? in
          1) LIVE_HOOKS_STATE=absent ;;
          *) LIVE_HOOKS_STATE=unknown ;;
        esac
    fi
}

adapter_payload_ready() {
    [ -d "$TARGET_ABS" ] &&
        [ -f "$TARGET_ABS/.claude-plugin/plugin.json" ] &&
        [ -f "$TARGET_ABS/hooks/hooks.json" ] &&
        [ -f "$TARGET_ABS/bin/idh-hook" ] &&
        [ -x "$TARGET_ABS/bin/idh-hook" ]
}

load_link_state() {
    if [ -L "$LINK" ]; then
        resolved_link=$(readlink -f "$LINK" 2>/dev/null || true)
        resolved_target=$(readlink -f "$TARGET_ABS" 2>/dev/null || true)
        if [ -n "$resolved_link" ] &&
           [ "$resolved_link" = "$resolved_target" ] &&
           adapter_payload_ready; then
            LINK_STATE=managed
        else
            LINK_STATE=unmanaged
        fi
    elif [ -e "$LINK" ]; then
        LINK_STATE=unmanaged
    else
        LINK_STATE=absent
    fi
}

status() {
    load_link_state
    if [ "$LINK_STATE" = managed ]; then
        echo "adapter: ACTIVE ($LINK -> $(readlink "$LINK"))"
    elif [ "$LINK_STATE" = unmanaged ]; then
        echo "adapter: UNKNOWN — $LINK is not the managed adapter link; refusing to touch it"
        return 1
    else
        echo "adapter: inert (no $LINK)"
    fi
    load_live_hooks_state
    case "$LIVE_HOOKS_STATE" in
      present) echo "live settings.json: carries a hooks block" ;;
      absent)  echo "live settings.json: no hooks block" ;;
      unknown)
        echo "live settings.json: UNKNOWN — unreadable, invalid JSON, or not an object"
        return 1
        ;;
    esac
}

case "${1:-activate}" in
  --status)
    status
    ;;
  --revert)
    load_link_state
    if [ "$LINK_STATE" = managed ]; then
        rm "$LINK"
        load_live_hooks_state
        case "$LIVE_HOOKS_STATE" in
          present)
            echo "adapter: reverted — $LINK removed; the live settings hooks take over"
            ;;
          absent)
            echo "adapter: reverted — $LINK removed; NO HOOKS WILL FIRE NOW." >&2
            echo "  The canonical settings.shared.json carries no hooks (the plugin was" >&2
            echo "  the single source); restore a hooks block to $LIVE if you want" >&2
            echo "  settings-borne hooks — the block lives in git history, in the" >&2
            echo "  commit that removed it. Otherwise every guard stays off." >&2
            ;;
          unknown)
            echo "adapter: reverted — $LINK removed; could not read $LIVE," >&2
            echo "  so whether any hooks still fire is unknown. Check the file." >&2
            ;;
        esac
    elif [ "$LINK_STATE" = unmanaged ]; then
        echo "adapter: $LINK is not the managed adapter link — refusing to touch it" >&2
        exit 1
    else
        echo "adapter: already inert, nothing to remove"
    fi
    ;;
  activate)
    adapter_payload_ready || {
        echo "adapter: adapter payload is incomplete under $TARGET_ABS — refusing" >&2
        exit 1
    }
    load_link_state
    [ "$LINK_STATE" = absent ] || {
        echo "adapter: $LINK already exists and is not available — refusing; run --status" >&2
        exit 1
    }
    load_live_hooks_state
    case "$LIVE_HOOKS_STATE" in
      present)
        cat >&2 <<MSG
adapter: refusing to activate — $LIVE still carries a hooks block.

Both sources would fire: every guard twice, on-start.sh's git sync twice.
Remove the "hooks" key from $LIVE (it is your file, outside the repository by
design; this script will not edit it), then run this again.
MSG
        exit 1
        ;;
      unknown)
        echo "adapter: refusing to activate — cannot determine whether $LIVE carries hooks" >&2
        echo "Make it a readable JSON object, then run this again." >&2
        exit 1
        ;;
      absent) ;;
    esac
    mkdir -p -- "$(dirname -- "$LINK")"
    ln -s "$TARGET_REL" "$LINK"
    echo "adapter: ACTIVE — $LINK -> $TARGET_REL"
    echo "The hooks now come from the plugin. Start a new session and confirm a guard fires;"
    echo "reading this message is not evidence that it does. Revert with --revert."
    ;;
  *)
    echo "usage: $(basename "$0") [activate|--revert|--status]" >&2; exit 2
    ;;
esac
