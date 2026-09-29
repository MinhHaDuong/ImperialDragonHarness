# Imperial Dragon Harness loader for ~/.bashrc (ticket 0983).
#
# Copy this block VERBATIM into ~/.bashrc; do not source it from the checkout.
# It must work when the checkout is unreachable or broken, which is exactly
# when a bare `source ~/.idh/...` line would leave claude, codex and pi
# running unwrapped, their guards gone without a word.
#
# Fail-closed by construction: refusing stubs are defined FIRST; sourcing
# scripts/shell-init.sh replaces them with the validating wrappers and sets
# _IDH_WRAPPERS=1 on its last line. A shell-init.sh that is missing, empty,
# unreadable, broken or a pre-0983 copy leaves (or restores) the stubs.
# Bypass, explicit and logged:  IDH_SKIP_VALIDATE=1 claude ...
_idh_refuse() {
  local rt="$1" st="${XDG_STATE_HOME:-$HOME/.local/state}/idh" cwd="${PWD//$'\n'/\\n}" how; shift
  if [ "${IDH_SKIP_VALIDATE:-}" = 1 ]; then
    if mkdir -p "$st" 2>/dev/null &&
      printf '%s %s bypass cwd=%s (harness not loaded)\n' "$(date -u +%Y-%m-%dT%H:%MZ)" "$rt" "$cwd" \
        >>"$st/validate-bypass.log" 2>/dev/null; then
      how="logged to $st/validate-bypass.log"
    else
      how="could not log to $st/validate-bypass.log"
    fi
    echo "idh: IDH_SKIP_VALIDATE=1, launching $rt with NO harness ($how)" >&2
    command "$rt" "$@"
    return
  fi
  local init="$HOME/.idh/scripts/shell-init.sh"
  if [ -r "$init" ]; then
    echo "idh: refusing to launch $rt: $init loaded but did not define the harness wrappers (empty, broken or an old copy)." >&2
    printf '  repair: bash -n %q   (shows a syntax error), then bring a current copy: git -C %q pull --ff-only; open a new shell\n' "$init" "$HOME/.idh" >&2
  else
    # The checkout sits at ~/.claude until the 0986 cutover, which updates
    # this repair (and asks for the installed copy to be refreshed).
    echo "idh: refusing to launch $rt: $init is unreachable, so $HOME/.idh does not resolve to the harness checkout." >&2
    printf '  repair: ln -sfn %q %q   (then open a new shell)\n' "$HOME/.claude" "$HOME/.idh" >&2
  fi
  echo "  To launch anyway (logged): IDH_SKIP_VALIDATE=1 $rt ..." >&2
  return 1
}
# `function NAME {`, never `NAME() {`: a user alias of the same name (say
# alias codex='codex --flag') would be expanded inside `NAME()` and turn this
# block into a syntax error. The alias still applies at the prompt.
_idh_stubs() {
  function claude { _idh_refuse claude "$@"; }
  function codex { _idh_refuse codex "$@"; }
  function pi { _idh_refuse pi "$@"; }
}
_idh_stubs
unset _IDH_WRAPPERS
[ -r "$HOME/.idh/scripts/shell-init.sh" ] && source "$HOME/.idh/scripts/shell-init.sh"
[ "${_IDH_WRAPPERS:-}" = 1 ] || _idh_stubs
