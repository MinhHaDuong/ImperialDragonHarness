# >>> Imperial Dragon Harness loader >>>  (tickets 0983, 0987)
#
# `idh install` writes this block into ~/.bashrc and later replaces exactly
# the lines from the >>> marker to the <<< marker; do not source it from the
# checkout, and keep your own lines outside the markers.
# It must work when the checkout is unreachable or broken, which is exactly
# when a stale absolute source path would leave claude, codex and pi
# running unwrapped, their guards gone without a word.
#
# Fail-closed by construction: refusing stubs are defined FIRST; sourcing
# scripts/shell-init.sh replaces them with the validating wrappers and sets
# _IDH_WRAPPERS=1 on its last line. A shell-init.sh that is missing, empty,
# unreadable, broken or a pre-0983 copy leaves (or restores) the stubs.
# Bypass, explicit and logged:  IDH_SKIP_VALIDATE=1 claude ...
_idh_checkout_root() {
  local bin real source
  bin=$(type -P idh 2>/dev/null || :)
  if [ -n "$bin" ]; then
    real=$(readlink -f -- "$bin" 2>/dev/null || :)
    if [ -n "$real" ] && [ -f "$real" ]; then
      cd -P -- "$(dirname -- "$real")/.." 2>/dev/null && pwd -P
      return
    fi
  fi
  # Also support sourcing this template directly in tests or recovery shells.
  source=$(readlink -f -- "${BASH_SOURCE[0]}" 2>/dev/null || :)
  if [ -n "$source" ] && [ "$(basename -- "$(dirname -- "$source")")" = scripts ]; then
    cd -P -- "$(dirname -- "$source")/.." 2>/dev/null && pwd -P
    return
  fi
  return 1
}

_idh_refuse() {
  local rt="$1" st="${XDG_STATE_HOME:-$HOME/.local/state}/idh" cwd how; shift
  printf -v cwd '%q' "$PWD"
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
  local root init
  root=$(_idh_checkout_root 2>/dev/null || :)
  init="${root:+$root/scripts/shell-init.sh}"
  if [ -r "$init" ]; then
    echo "idh: refusing to launch $rt: $init loaded but did not define the harness wrappers (empty, broken or an old copy)." >&2
    printf '  repair: bash -n %q   (shows a syntax error), then bring that checkout current and open a new shell\n' "$init" >&2
  elif [ -e "$init" ]; then
    echo "idh: refusing to launch $rt: $init exists but is unreadable." >&2
    printf '  repair: chmod u+r %q   (then open a new shell)\n' "$init" >&2
  else
    echo "idh: refusing to launch $rt: the IDH checkout cannot be resolved from the idh executable on PATH." >&2
    echo "  repair: run <checkout>/bin/idh install from the current checkout, then open a new shell" >&2
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
_idh_root=$(_idh_checkout_root 2>/dev/null || :)
[ -n "$_idh_root" ] && [ -r "$_idh_root/scripts/shell-init.sh" ] && source "$_idh_root/scripts/shell-init.sh"
unset _idh_root
[ "${_IDH_WRAPPERS:-}" = 1 ] || _idh_stubs
# <<< Imperial Dragon Harness loader <<<
