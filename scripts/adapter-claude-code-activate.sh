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
CANONICAL="$HARNESS_DIR/settings.shared.json"

inspect_live_hooks() {
    mode=$1
    if [ ! -e "$LIVE" ]; then
        [ -L "$LIVE" ] && return 2
        return 1
    fi
    [ -f "$LIVE" ] || return 2
    python3 - "$LIVE" "$CANONICAL" "$mode" <<'PY'
import json, sys

def load_object(path):
    try:
        with open(path) as stream:
            value = json.load(stream)
    except (OSError, ValueError):
        return None
    return value if isinstance(value, dict) else None

live = load_object(sys.argv[1])
if live is None:
    sys.exit(2)
hooks = live.get("hooks")
if hooks is None or hooks == {}:
    sys.exit(1)
if not isinstance(hooks, dict):
    sys.exit(2)

if sys.argv[3] == "any":
    sys.exit(0)

canonical = load_object(sys.argv[2])
if canonical is None or not isinstance(canonical.get("hooks"), dict):
    sys.exit(2)
for event, wanted_blocks in canonical["hooks"].items():
    actual_blocks = hooks.get(event)
    if not isinstance(wanted_blocks, list) or not isinstance(actual_blocks, list):
        sys.exit(1)
    remaining = list(actual_blocks)
    for wanted in wanted_blocks:
        try:
            remaining.remove(wanted)
        except ValueError:
            sys.exit(1)
sys.exit(0)
PY
}

load_live_hooks_state() {
    if inspect_live_hooks "$1"; then
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
    load_live_hooks_state any
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
        load_live_hooks_state canonical
        case "$LIVE_HOOKS_STATE" in
          present)
            rm "$LINK"
            echo "adapter: reverted — $LINK removed; the live hooks block is restored"
            ;;
          absent)
            echo "adapter: refusing to revert — restore the canonical hooks in $LIVE first" >&2
            exit 1
            ;;
          unknown)
            echo "adapter: refusing to revert — cannot verify the canonical hooks in $LIVE" >&2
            echo "Make $LIVE and $CANONICAL readable JSON objects, then run this again." >&2
            exit 1
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
    load_live_hooks_state any
    case "$LIVE_HOOKS_STATE" in
      present)
        cat >&2 <<MSG
adapter: refusing to activate — $LIVE still carries a hooks block.

Both sources would fire: every guard twice, on-start.sh's git sync twice.
Remove the "hooks" key from $LIVE (it is your file, outside the repository by
design; this script will not edit it), then run this again. Ticket 0886 is what
turns that hand edit into one command.
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
    ln -s "$TARGET_REL" "$LINK"
    echo "adapter: ACTIVE — $LINK -> $TARGET_REL"
    echo "The hooks now come from the plugin. Start a new session and confirm a guard fires;"
    echo "reading this message is not evidence that it does. Revert with --revert."
    ;;
  *)
    echo "usage: $(basename "$0") [activate|--revert|--status]" >&2; exit 2
    ;;
esac
