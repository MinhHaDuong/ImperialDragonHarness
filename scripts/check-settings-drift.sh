#!/bin/bash
# Compare the live ~/.claude/settings.json against the tracked canonical
# settings.shared.json, ignoring the volatile keys the CLI rewrites
# (model, effortLevel). Reports drift on stdout; never blocks (exit 0),
# except exit 2 on missing canonical file.
#
# Bootstrap: if the live file is absent (fresh machine), create it from
# the canonical copy.
set -euo pipefail

HARNESS_DIR="${HARNESS_DIR:-$HOME/.claude}"
SHARED="$HARNESS_DIR/settings.shared.json"
LIVE="$HARNESS_DIR/settings.json"

if [ ! -f "$SHARED" ]; then
    echo "check-settings-drift: canonical $SHARED missing" >&2
    exit 2
fi

if [ ! -f "$LIVE" ]; then
    cp "$SHARED" "$LIVE"
    echo "check-settings-drift: bootstrapped $LIVE from settings.shared.json"
    exit 0
fi

python3 - "$SHARED" "$LIVE" <<'EOF'
import json, sys

VOLATILE = {"model", "effortLevel"}

shared = json.load(open(sys.argv[1]))
live = json.load(open(sys.argv[2]))
for k in VOLATILE:
    shared.pop(k, None)
    live.pop(k, None)

drift = []
for k in sorted(set(shared) | set(live)):
    if shared.get(k) != live.get(k):
        drift.append(k)

if drift:
    print("check-settings-drift: live settings.json differs from "
          f"settings.shared.json on shared keys: {', '.join(drift)}. "
          "If intentional, fold the change into settings.shared.json "
          "via a PR; otherwise re-align the live file.")
else:
    print("check-settings-drift: OK")
EOF
