#!/usr/bin/env bash
# Harness shell init — sourced from ~/.bashrc through the loader in
# scripts/bashrc-loader.sh (which also covers the case where this file is
# unreachable).
#
# Wraps claude, codex and pi. Before each launch, the projection validator
# (scripts/validate-projections.py, ticket 0983) checks every link the runtime
# depends on and refuses the launch with the `idh install` repair: a broken
# projection would otherwise drop the guard or the instructions silently.
# The claude wrapper also skips permission prompts and names the session
# after the project.
#
# Bypass, explicit and logged: IDH_SKIP_VALIDATE=1 <runtime> ...

# Resolve the checkout from this sourced file instead of a fixed home path.
_IDH_ROOT="$(cd -P -- "$(dirname -- "$(readlink -f -- "${BASH_SOURCE[0]}")")/.." && pwd -P)"
# Exported for every runtime the wrappers launch (claude, codex, pi) and for
# the skills' helper commands and rules/workflow.md's session-start probe.
export IDH_ROOT="$_IDH_ROOT"

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
  local v="$_IDH_ROOT/scripts/validate-projections.py"
  if [ ! -f "$v" ]; then
    echo "idh: refusing to launch $1: $v is unreachable; the loaded harness checkout moved or was removed." >&2
    echo "  repair: reinstall the loader from the current checkout, then open a new shell" >&2
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

# Advisory only: a failed disk probe must never block an otherwise valid launch.
# Stderr, like every other launch notice: a caller capturing the wrapper's
# stdout sees the runtime's output alone (ticket 1337).
_idh_disk_warning() {
  local output
  output=$(python3 "$_IDH_ROOT/scripts/tmp_report.py" --disk-warning 2>&1) || {
    echo "Disk headroom probe unavailable; /tmp and /home headroom is unchecked." >&2
    return 0
  }
  [ -z "$output" ] || printf '%s\n' "$output" >&2
}

# _idh_agent_gh RUNTIME ARGS... — launch RUNTIME on the narrow agent gh
# credential (ticket 1284, after 1196). The variable is set for the child only
# (env prefix, never exported), so the author's interactive shell keeps the
# owner login. Applies when the agent config exists and the caller has not set
# GH_CONFIG_DIR. Launches outside these wrappers (IDE, desktop app, cron) are
# not covered.
_idh_agent_gh() {
  if [ -z "${GH_CONFIG_DIR:-}" ] && [ -n "${HOME:-}" ] && [ -f "$HOME/.config/gh-agent/hosts.yml" ]; then
    GH_CONFIG_DIR="$HOME/.config/gh-agent" command "$@"
  else
    command "$@"
  fi
}

# `function NAME {`, never `NAME() {`: an alias of the same name (e.g.
# alias codex='codex --approve-for-me') is expanded inside `NAME()` and makes
# this file a syntax error. The alias still applies at the prompt, then calls
# the wrapper.
function claude {
  _idh_preflight claude || return
  local name top
  top=$(git -C "$PWD" rev-parse --show-toplevel 2>/dev/null || :)
  name=$(basename "${top:-$PWD}")
  command claude --dangerously-skip-permissions --name "$name" "$@"
}

function codex {
  _idh_preflight codex || return
  _idh_disk_warning
  _idh_agent_gh codex "$@"
}

function pi {
  _idh_preflight pi || return
  _idh_disk_warning
  _idh_agent_gh pi "$@"
}

# Last line on purpose: the ~/.bashrc loader keeps its refusing stubs unless
# this file ran to the end (scripts/bashrc-loader.sh).
_IDH_WRAPPERS=1
