# Imperial Dragon Harness loader for ~/.bashrc (ticket 0983).
#
# Copy this block VERBATIM into ~/.bashrc; do not source it from the checkout.
# It must work when the checkout is unreachable, which is exactly when a
# `source ~/.idh/...` line would skip silently and leave claude, codex and pi
# running unwrapped, their guards gone without a word.
#
# Reachable: source the wrappers (scripts/shell-init.sh), which validate the
# projections before every launch. Unreachable: define stubs that refuse to
# launch, name the culprit and the repair. Bypass, explicit and logged:
#   IDH_SKIP_VALIDATE=1 claude ...
if [ -f "$HOME/.idh/scripts/shell-init.sh" ]; then
  source "$HOME/.idh/scripts/shell-init.sh"
else
  _idh_unreachable() {
    local rt="$1" st="${XDG_STATE_HOME:-$HOME/.local/state}/idh" cwd="${PWD//$'\n'/\\n}" how; shift
    if [ "${IDH_SKIP_VALIDATE:-}" = 1 ]; then
      if mkdir -p "$st" 2>/dev/null &&
        printf '%s %s bypass cwd=%s (harness unreachable)\n' "$(date -u +%Y-%m-%dT%H:%MZ)" "$rt" "$cwd" \
          >>"$st/validate-bypass.log" 2>/dev/null; then
        how="logged to $st/validate-bypass.log"
      else
        how="could not log to $st/validate-bypass.log"
      fi
      echo "idh: IDH_SKIP_VALIDATE=1, launching $rt with NO harness ($how)" >&2
      command "$rt" "$@"
      return
    fi
    # The checkout sits at ~/.claude until the 0986 cutover, which updates
    # this repair (and asks for the installed copy to be refreshed).
    echo "idh: refusing to launch $rt: $HOME/.idh/scripts/shell-init.sh is unreachable, so $HOME/.idh does not resolve to the harness checkout." >&2
    printf '  repair: ln -sfn %q %q   (then open a new shell)\n' "$HOME/.claude" "$HOME/.idh" >&2
    echo "  To launch anyway (logged): IDH_SKIP_VALIDATE=1 $rt ..." >&2
    return 1
  }
  # `function NAME {`, never `NAME() {`: a user alias of the same name (say
  # alias codex='codex --flag') would be expanded inside `NAME()` and turn the
  # whole if-block into a syntax error. The alias still applies at the prompt.
  function claude { _idh_unreachable claude "$@"; }
  function codex { _idh_unreachable codex "$@"; }
  function pi { _idh_unreachable pi "$@"; }
fi
