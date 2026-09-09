#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
HARNESS_DIR=$(cd "$SCRIPT_DIR/.." && pwd)
# Keep this in sync with the service's fixed %h/.local/bin ExecStart.
USER_BIN=$HOME/.local/bin
USER_UNITS=${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user

mkdir -p "$USER_BIN" "$USER_UNITS"
ln -sfn "$HARNESS_DIR/bin/mammoth-audit" "$USER_BIN/idh-mammoth-audit"
install -m 0644 "$HARNESS_DIR/systemd/idh-mammoth-audit.service" "$USER_UNITS/"
install -m 0644 "$HARNESS_DIR/systemd/idh-mammoth-audit.timer" "$USER_UNITS/"
systemctl --user daemon-reload
systemctl --user enable --now idh-mammoth-audit.timer
systemctl --user list-timers idh-mammoth-audit.timer --no-pager
