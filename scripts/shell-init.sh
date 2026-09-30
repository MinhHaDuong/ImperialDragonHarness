#!/usr/bin/env bash
# Harness shell init — sourced from ~/.bashrc through the loader in
# scripts/bashrc-loader.sh (which also covers the case where this file is
# unreachable).
#
# Wraps claude, codex and pi. Before each launch, the projection validator
# (scripts/validate-projections.py, ticket 0983) checks every link the runtime
# depends on and refuses the launch with the culprit and its repair: a
# dangling link would otherwise drop the guard or the instructions silently.
# The claude wrapper also skips permission prompts and names the session
# after the project.
#
# Bypass, explicit and logged: IDH_SKIP_VALIDATE=1 <runtime> ...

# _idh_bypass_log RUNTIME [NOTE] — record an explicit bypass, and say so.
# $PWD is printf %q escaped (every control character, not only newlines), so
# a directory name can neither forge a log line nor inject terminal escapes;
# a failed write is reported as such, never as "logged".
_idh_bypass_log() {
  local dir="${XDG_STATE_HOME:-$HOME/.local/state}/idh" cwd how
  printf -v cwd '%q' "$PWD"
  if mkdir -p "$dir" 2>/dev/null &&
    printf '%s %s bypass cwd=%s%s\n' "$(date -u +%Y-%m-%dT%H:%MZ)" "$1" "$cwd" "${2:+ ($2)}" \
      >>"$dir/validate-bypass.log" 2>/dev/null; then
    how="logged to $dir/validate-bypass.log"
  else
    how="could not log to $dir/validate-bypass.log"
  fi
  echo "idh: IDH_SKIP_VALIDATE=1, launching $1 without the projection check ($how)" >&2
}

# _idh_preflight RUNTIME — 0 when the launch may proceed.
_idh_preflight() {
  if [ "${IDH_SKIP_VALIDATE:-}" = 1 ]; then
    _idh_bypass_log "$1"
    return 0
  fi
  if [ -z "${HOME:-}" ]; then
    echo "idh: refusing to launch $1: HOME is unset, so no projection can be checked. Set HOME, or launch anyway (logged): IDH_SKIP_VALIDATE=1 $1 ..." >&2
    return 1
  fi
  local v="$HOME/.idh/scripts/validate-projections.py"
  if [ ! -f "$v" ]; then
    # ~/.idh vanished after this shell sourced the wrappers.
    echo "idh: refusing to launch $1: $v is unreachable, so $HOME/.idh no longer resolves to the harness checkout." >&2
    printf '  repair: restore the checkout at %q, then relaunch\n' "$HOME/.idh" >&2
    echo "  To launch anyway (logged): IDH_SKIP_VALIDATE=1 $1 ..." >&2
    return 1
  fi
  if ! command -v python3 >/dev/null 2>&1; then
    echo "idh: refusing to launch $1: python3 is not on PATH, so the projection check cannot run." >&2
    echo "  repair: install python3 (e.g. sudo apt install python3), or fix PATH=$PATH" >&2
    echo "  To launch anyway (logged): IDH_SKIP_VALIDATE=1 $1 ..." >&2
    return 1
  fi
  python3 "$v" "$1"
}

# `function NAME {`, never `NAME() {`: an alias of the same name (e.g.
# alias codex='codex --approve-for-me') is expanded inside `NAME()` and makes
# this file a syntax error. The alias still applies at the prompt, then calls
# the wrapper.
function claude {
  _idh_preflight claude || return
  local name top
  top=$(git -C "$PWD" rev-parse --show-toplevel 2>/dev/null)
  name=$(basename "${top:-$PWD}")
  command claude --dangerously-skip-permissions --name "$name" "$@"
}

function codex {
  _idh_preflight codex || return
  command codex "$@"
}

function pi {
  _idh_preflight pi || return
  command pi "$@"
}

# Last line on purpose: the ~/.bashrc loader keeps its refusing stubs unless
# this file ran to the end (scripts/bashrc-loader.sh).
_IDH_WRAPPERS=1
