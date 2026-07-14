#!/bin/bash
# Loaded via BASH_ENV — sourced at startup of every Claude Code bash subprocess.
# Exports .env secrets into the process environment without inlining them in argv
# (inlining in argv leaks secrets to ps -ef, which is visible to all local users).
#
# BASH_ENV is honored by non-interactive bash (i.e. "bash -c ..."), which is
# exactly what Claude Code uses for Bash tool calls.
#
# Two .env sources with DIFFERENT trust levels:
#
#   * $HOME/.claude/.env — user-owned, TRUSTED. Sourced as shell code (full
#     expansion), exactly as before. Only the user writes this file.
#
#   * $PWD/.env — project-level, UNTRUSTED. An agent, a cloned repo, or any
#     project write can place it. It is NEVER sourced: it is strict-parsed
#     KEY=VALUE, values are assigned LITERALLY (no eval / $() / backticks), and
#     any guard-namespaced key — any key whose name contains GUARD_, covering
#     both GUARD_* and the leading-underscore _GUARD_* override pair — is
#     REFUSED. This structurally closes the escape-hatch provenance hole
#     (ticket 0323, residual 2): a sourced project .env could otherwise forge a
#     per-process guard nonce (e.g. GUARD_ALLOW_PRIMARY_EDIT) or the worktree-
#     path override (_GUARD_WORKTREE_ROOT / _GUARD_PRIMARY_ROOT), or execute
#     arbitrary shell via BASH_ENV.
#
# The script runs on every bash subprocess, so it stays fast and never aborts on
# a missing or malformed .env — bad lines in the project file are skipped, never
# fatal.
#
# Provider-secret scoping (KEYS=). A project declares which credential providers
# it needs by setting KEYS=<name,name,...> in its project .env (parsed by the
# untrusted strict-parse above, so KEYS itself is a plain value). For each
# declared, VALIDATED provider <name>, and ONLY those, this script sources the
# user-owned $HOME/.config/keys/<name>.env. Default-deny: no KEYS line loads no
# provider secrets. Provider names must match ^[a-z0-9-]+$ — anything else (path
# traversal like ../../x, a slash, uppercase, empty) is ignored with a warning.
# The per-provider files are user-owned and TRUSTED, so they are sourced as shell
# code (contrast the untrusted project .env). A missing provider file warns but is
# non-fatal.
#
# Guarantee and its limit. Two properties hold even against a hostile project
# .env: it never sources a path outside ~/.config/keys/ (name validation), and it
# never executes the project .env (strict-parsed, never sourced) — so a hostile
# .env can neither run code nor exfiltrate a secret through the .env itself. But
# the provider SET is self-declared by that untrusted file, which can name any
# provider to load its secret into the environment. This is cooperative scoping
# that shrinks default secret exposure, NOT access control against a hostile
# project .env.

# --- trusted user-level .env: source as before (full expansion) ---
set -a  # mark all subsequent assignments for export
[ -f "$HOME/.claude/.env" ] && source "$HOME/.claude/.env"
set +a

# --- untrusted project-level .env: strict KEY=VALUE parse, never executed ---
# Claude Code sets PWD to the project dir for each subprocess. Skip if it
# resolves to the same file as the trusted user-level one (already loaded).
if [ -n "${PWD:-}" ] && [ -f "$PWD/.env" ]; then
    _be_proj="$(realpath "$PWD/.env" 2>/dev/null)"
    _be_user="$(realpath "$HOME/.claude/.env" 2>/dev/null)"
    if [ "$_be_proj" != "$_be_user" ]; then
        while IFS= read -r _be_line || [ -n "$_be_line" ]; do
            # strip leading whitespace for blank/comment detection
            _be_trim="${_be_line#"${_be_line%%[![:space:]]*}"}"
            [ -z "$_be_trim" ] && continue          # blank line
            [ "${_be_trim:0:1}" = "#" ] && continue # comment
            _be_trim="${_be_trim#export }"          # optional `export ` prefix
            # require KEY=VALUE with a valid identifier key
            case "$_be_trim" in
                [A-Za-z_]*=*) ;;
                *) continue ;;
            esac
            _be_key="${_be_trim%%=*}"
            case "$_be_key" in
                *[!A-Za-z0-9_]*) continue ;;        # key has an invalid char
            esac
            _be_val="${_be_trim#*=}"                # everything after the FIRST =
            # strip ONE matching pair of surrounding quotes (literal, no escapes)
            if [ "${#_be_val}" -ge 2 ]; then
                _be_first="${_be_val:0:1}"
                _be_last="${_be_val: -1}"
                if { [ "$_be_first" = '"' ] && [ "$_be_last" = '"' ]; } ||
                   { [ "$_be_first" = "'" ] && [ "$_be_last" = "'" ]; }; then
                    _be_val="${_be_val:1:${#_be_val}-2}"
                fi
            fi
            # structural refusal: an untrusted file cannot set guard vars.
            # Match every guard-namespaced key — both the GUARD_* form and the
            # leading-underscore _GUARD_* override pair (_GUARD_WORKTREE_ROOT /
            # _GUARD_PRIMARY_ROOT) that pretooluse-worktree-path-guard.sh honors
            # as an unconditional worktree-path override. Substring match, since
            # no legitimate project key contains the harness-internal GUARD_ token.
            if [[ "$_be_key" == *GUARD_* ]]; then
                printf 'bash-env: refusing guard-namespaced key from project .env: %s\n' \
                    "$_be_key" >&2
                continue
            fi
            # assign the value LITERALLY — never expanded, never executed
            export "$_be_key=$_be_val"
        done < "$PWD/.env"
        unset _be_line _be_trim _be_key _be_val _be_first _be_last
    fi
    unset _be_proj _be_user
fi

# --- least-privilege provider secrets: source only the declared KEYS providers ---
# $KEYS (if any) was set by the project strict-parse above. Split it on commas and
# source $HOME/.config/keys/<name>.env for each validated provider name only.
if [ -n "${KEYS:-}" ]; then
    # Disable globbing while splitting so a stray '*' in KEYS cannot expand to
    # filenames; restore the caller's setting afterwards.
    case "$-" in
        *f*) _be_had_noglob=1 ;;
        *)   _be_had_noglob=0 ;;
    esac
    set -f
    _be_ifs="$IFS"
    IFS=','
    for _be_prov in ${KEYS}; do
        IFS="$_be_ifs"
        # trim surrounding whitespace
        _be_prov="${_be_prov#"${_be_prov%%[![:space:]]*}"}"
        _be_prov="${_be_prov%"${_be_prov##*[![:space:]]}"}"
        [ -z "$_be_prov" ] && { IFS=','; continue; }
        # validate: lowercase, digits and dashes only — blocks path traversal
        if [[ ! "$_be_prov" =~ ^[a-z0-9-]+$ ]]; then
            printf 'bash-env: ignoring invalid KEYS provider name: %s\n' "$_be_prov" >&2
            IFS=','
            continue
        fi
        _be_keyfile="$HOME/.config/keys/$_be_prov.env"
        if [ -f "$_be_keyfile" ]; then
            # Enable allexport ONLY around the source, so exactly the variables
            # the trusted provider file assigns get exported — the loop
            # bookkeeping (IFS, the _be_* temporaries) is assigned outside
            # allexport and stays unexported.
            set -a
            source "$_be_keyfile"
            set +a
        else
            printf 'bash-env: KEYS provider not found: %s\n' "$_be_prov" >&2
        fi
        IFS=','
    done
    IFS="$_be_ifs"
    [ "$_be_had_noglob" = 1 ] || set +f
    unset _be_ifs _be_prov _be_keyfile _be_had_noglob
fi
