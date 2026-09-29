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
    local rt="$1" st="${XDG_STATE_HOME:-$HOME/.local/state}/idh" hint; shift
    if [ "${IDH_SKIP_VALIDATE:-}" = 1 ]; then
      mkdir -p "$st" 2>/dev/null
      printf '%s %s bypass cwd=%s (harness unreachable)\n' "$(date -u +%Y-%m-%dT%H:%MZ)" "$rt" "$PWD" >>"$st/validate-bypass.log" 2>/dev/null
      echo "idh: IDH_SKIP_VALIDATE=1, launching $rt with NO harness (logged to $st/validate-bypass.log)" >&2
      command "$rt" "$@"
      return
    fi
    hint=$(cat "$st/last-good-root" 2>/dev/null)
    echo "idh: refusing to launch $rt: $HOME/.idh/scripts/shell-init.sh is unreachable, so $HOME/.idh does not resolve to the harness checkout." >&2
    echo "  repair: ln -sfn ${hint:-/path/to/harness-checkout} $HOME/.idh   (then open a new shell)" >&2
    echo "  To launch anyway (logged): IDH_SKIP_VALIDATE=1 $rt ..." >&2
    return 1
  }
  claude() { _idh_unreachable claude "$@"; }
  codex() { _idh_unreachable codex "$@"; }
  pi() { _idh_unreachable pi "$@"; }
fi
