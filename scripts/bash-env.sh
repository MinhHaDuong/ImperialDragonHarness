#!/bin/bash
# Loaded via BASH_ENV at startup of every Claude Code bash subprocess.
#
# $PWD/.env is project-level and UNTRUSTED. An agent, a cloned repo, or any
# project write can place it. It is never sourced: this loader strict-parses
# KEY=VALUE, assigns values literally, and refuses names that can alter shell,
# process, interpreter, Git, pager, or harness-guard behaviour. Bad lines are
# skipped rather than made fatal. CRLF is tolerated and a 256 KiB cap keeps a
# pathological file from taxing every subprocess.
#
# Credential consumers resolve values from ~/.config/keys at their point of
# use. This loader does not source ~/.claude/.env, does not read provider files,
# and refuses the retired KEYS name in a project .env. A consuming project's
# Python pipeline may still implement its own KEYS mechanism through
# python-dotenv; it is independent of this loader, not an agreeing apply path.
#
# xtrace guard (tickets 0939, 0945). The strict parser exports an
# already-expanded project value with `export "$name=$value"`; `set -x` would
# print that value. Suppress tracing for this loader and restore the caller's
# setting at the end.
case "$-" in
    *x*) _be_had_xtrace=1; set +x ;;
    *)   _be_had_xtrace=0 ;;
esac

# Return success when NAME must never be exported from an untrusted project
# .env. The case block is the authoritative policy enumeration.
_be_is_protected_name() {
    case "$1" in
        *GUARD_*|_be_*) return 0 ;;
        PATH|BASH_ENV|ENV|SHELLOPTS|BASHOPTS|IFS|\
        PS0|PS1|PS2|PS3|PS4|PROMPT_COMMAND|CDPATH|GLOBIGNORE|\
        LD_PRELOAD|LD_LIBRARY_PATH|LD_AUDIT|LD_DEBUG|LD_PROFILE|\
        GCONV_PATH|PYTHONPATH|NODE_OPTIONS|NODE_PATH|PERL5LIB|RUBYOPT|\
        GIT_SSH_COMMAND|GIT_SSH|GIT_ASKPASS|GIT_EXTERNAL_DIFF|LESSOPEN|LESSCLOSE|\
        TZ|TZDIR|LOCALDOMAIN|TERMINFO|BASH_XTRACEFD|HISTFILE|KEYS|\
        BASH_FUNC_*|DYLD_*) return 0 ;;
    esac
    return 1
}

# Skip the project parse when $PWD/.env is the harness's former user-level
# ~/.claude/.env. The file is no longer sourced, and treating it as an
# untrusted project file merely because the checkout lives at ~/.claude would
# be a surprising second interpretation of the same installation file.
if [ -n "${PWD:-}" ] && [ -f "$PWD/.env" ]; then
    # Guard realpath failures so sourcing under an already-active `set -e`
    # still reaches the end of this file.
    _be_proj="$(realpath "$PWD/.env" 2>/dev/null || true)"
    _be_user="$(realpath "$HOME/.claude/.env" 2>/dev/null || true)"
    if [ "$_be_proj" != "$_be_user" ]; then
        _be_cap=262144
        _be_size="$(wc -c < "$PWD/.env" 2>/dev/null || echo 0)"
        if [ "${_be_size:-0}" -gt "$_be_cap" ]; then
            printf 'bash-env: project .env exceeds size cap (%s > %s bytes), skipping\n' \
                "$_be_size" "$_be_cap" >&2
        else
            while IFS= read -r _be_line || [ -n "$_be_line" ]; do
                # `read` strips LF only; remove a surviving Windows CR.
                _be_line="${_be_line%$'\r'}"
                _be_trim="${_be_line#"${_be_line%%[![:space:]]*}"}"
                [ -z "$_be_trim" ] && continue
                [ "${_be_trim:0:1}" = "#" ] && continue
                _be_trim="${_be_trim#export }"
                case "$_be_trim" in
                    [A-Za-z_]*=*) ;;
                    *) continue ;;
                esac
                _be_key="${_be_trim%%=*}"
                case "$_be_key" in
                    *[!A-Za-z0-9_]*) continue ;;
                esac
                _be_val="${_be_trim#*=}"
                # Strip one matching quote pair, literally; never eval values.
                if [ "${#_be_val}" -ge 2 ]; then
                    _be_first="${_be_val:0:1}"
                    _be_last="${_be_val: -1}"
                    if { [ "$_be_first" = '"' ] && [ "$_be_last" = '"' ]; } ||
                       { [ "$_be_first" = "'" ] && [ "$_be_last" = "'" ]; }; then
                        _be_val="${_be_val:1:${#_be_val}-2}"
                    fi
                fi
                if _be_is_protected_name "$_be_key"; then
                    printf 'bash-env: refusing protected name from project .env: %s\n' \
                        "$_be_key" >&2
                    continue
                fi
                export "$_be_key=$_be_val"
            done < "$PWD/.env"
            unset _be_line _be_trim _be_key _be_val _be_first _be_last
        fi
        unset _be_cap _be_size
    fi
    unset _be_proj _be_user
fi

unset -f _be_is_protected_name 2>/dev/null || true

# Must stay last: restore the caller's xtrace setting without returning a
# failing status when xtrace was initially off.
[ "${_be_had_xtrace:-0}" = 1 ] && set -x
unset _be_had_xtrace
