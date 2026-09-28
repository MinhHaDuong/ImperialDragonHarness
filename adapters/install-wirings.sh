#!/usr/bin/env bash
# Install or remove the pilot's adapter wirings (ticket 0810).
#
# Two wirings exist after the three slices (0809): the Codex PreToolUse hook
# and the Pi tool_call extension. Both install as a symlink to the canonical
# file in this repository, so the body stays single-source and live.
#
# Semantics (the same doctrine as bin/idh):
#   - a target that does not exist is created;
#   - a target that already resolves to the canonical file is success, not a
#     collision ("already discoverable");
#   - a target that is anything else — an unmanaged file, a symlink pointing
#     elsewhere — is REFUSED. Activation never overwrites the only
#     recoverable copy of a live configuration; the operator decides.
#   - removal takes back exactly what install created: the symlink and every
#     directory the removal left empty, up to and including the runtime home
#     directories. Unmanaged files survive untouched.
#
# Usage:
#   adapters/install-wirings.sh install [IDH_ROOT]   # default: this repo
#   adapters/install-wirings.sh uninstall
#   adapters/install-wirings.sh status
#
# Everything is relative to $HOME, so a test can drive it against a fixture
# home with HOME=/path/to/fixture.
set -euo pipefail

IDH_ROOT="${2:-$(cd -P "$(dirname "$0")/.." && pwd -P)}"
CANONICAL_HOOKS="$IDH_ROOT/adapters/codex/hooks.json"
CANONICAL_EXT="$IDH_ROOT/adapters/pi/extensions/idh-guard.ts"
MODE="${1:-status}"

CODEX_TARGET="$HOME/.codex/hooks.json"
PI_TARGET="$HOME/.pi/agent/extensions/idh-guard.ts"

ensure_parent() { mkdir -p "$(dirname "$1")"; }

place() {
  local canonical="$1" target="$2"
  if [[ -e "$target" || -L "$target" ]]; then
    if [[ -L "$target" && "$(readlink "$target")" == "$canonical" ]]; then
      echo "already discoverable: $target -> $canonical"
      return 0
    fi
    echo "REFUSED: $target exists and is not managed by this install" >&2
    return 1
  fi
  ensure_parent "$target"
  ln -s "$canonical" "$target"
  echo "installed: $target -> $canonical"
}

remove() {
  local target="$1"
  if [[ ! -e "$target" && ! -L "$target" ]]; then
    echo "absent: $target"
    return 0
  fi
  if [[ -L "$target" && "$(readlink "$target")" == "$3" ]]; then
    rm "$target"
    echo "removed: $target"
    # Take back every directory the removal left empty, never a non-empty one.
    local dir
    dir="$(dirname "$target")"
    while [[ -z "$(ls -A "$dir" 2>/dev/null)" && "$dir" != "$HOME" && "$dir" != "/" ]]; do
      rmdir "$dir"
      dir="$(dirname "$dir")"
    done
    return 0
  fi
  echo "REFUSED: $target is not managed by this install" >&2
  return 1
}

# Every target is attempted; refusals are collected so one unmanaged
# target never hides the state of the others, and the exit code reports
# whether anything refused.
run_all() {
  local rc=0 fn="$1"; shift
  for target_spec in "$@"; do
    "$fn" $target_spec || rc=1
  done
  return "$rc"
}

case "$MODE" in
  install)
    run_all place "$CANONICAL_HOOKS $CODEX_TARGET" "$CANONICAL_EXT $PI_TARGET"
    ;;
  uninstall)
    run_all remove "$CODEX_TARGET x $CANONICAL_HOOKS" "$PI_TARGET x $CANONICAL_EXT"
    ;;
  status)
    for pair in "codex:$CODEX_TARGET" "pi:$PI_TARGET"; do
      runtime="${pair%%:*}"; target="${pair#*:}"
      if [[ -L "$target" ]]; then
        echo "$runtime: $target -> $(readlink "$target")"
      elif [[ -e "$target" ]]; then
        echo "$runtime: $target exists, unmanaged"
      else
        echo "$runtime: not installed"
      fi
    done
    ;;
  *)
    echo "unknown mode: $MODE" >&2
    exit 2
    ;;
esac
