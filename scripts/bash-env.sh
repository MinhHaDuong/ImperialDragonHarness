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
#     any protected export NAME is REFUSED. Protected names cover BOTH (1) every
#     guard-namespaced key — any name containing GUARD_, covering GUARD_* and the
#     leading-underscore _GUARD_* override pair — AND (2) the shell/process/
#     interpreter-critical set (PATH, LD_PRELOAD/LD_LIBRARY_PATH/LD_AUDIT,
#     BASH_ENV, ENV, GCONV_PATH, PYTHONPATH, NODE_OPTIONS/NODE_PATH, PERL5LIB,
#     RUBYOPT, IFS, the prompt/CDPATH/GLOBIGNORE parse vars, the git exec vectors
#     GIT_SSH_COMMAND/GIT_SSH/GIT_ASKPASS/GIT_EXTERNAL_DIFF, the LESSOPEN/LESSCLOSE
#     pager hooks, and the BASH_FUNC_* / DYLD_* prefix families). This structurally
#     closes two holes: the escape-hatch
#     provenance hole (ticket 0323, residual 2) — a sourced project .env could
#     forge a per-process guard nonce (e.g. GUARD_ALLOW_PRIMARY_EDIT) or the
#     worktree-path override (_GUARD_WORKTREE_ROOT / _GUARD_PRIMARY_ROOT) or run
#     arbitrary shell via BASH_ENV — and the critical-name/RCE injection hole
#     (ticket 0345): because the untrusted file controls both name and value, an
#     un-denied critical name is a direct code-execution vector (GCONV_PATH iconv
#     module load, LD_PRELOAD, BASH_ENV re-source, PATH/interpreter clobber) in
#     every subprocess. The refusal is one shared predicate, _be_is_protected_name,
#     applied identically here and at the KEYS-selection export below, so the two
#     denylists cannot drift.
#
# The script runs on every bash subprocess, so it stays fast and never aborts on
# a missing or malformed .env — bad lines in the project file are skipped, never
# fatal, and it stays safe under an already-active `set -e` in the sourcing shell
# (the realpath dedup below is guarded with `|| true`). The strict parse tolerates
# CRLF (a trailing \r is dropped, for Windows-edited files) and is bounded: a
# project .env past a generous byte cap is skipped whole, so a pathological or
# adversarial one cannot tax every subprocess.
#
# Provider-secret scoping (KEYS=). A project declares which credential providers
# it needs by setting KEYS=<entry,entry,...> in its project .env (parsed by the
# untrusted strict-parse above, so KEYS itself is a plain value). Default-deny: no
# KEYS line loads no provider secrets. Each comma-separated entry takes one of
# three forms:
#
#   * provider          — source the whole user-owned
#     $HOME/.config/keys/<provider>.env (all its variables enter the environment).
#
#   * provider:VAR      — from <provider>.env, export ONLY VAR, under the name VAR.
#
#   * provider:SRC=DST  — from <provider>.env, export ONLY SRC, renamed to DST.
#     No other variable from that file enters the environment.
#
# The last two forms exist because a provider file may hold several keysets (e.g.
# openrouter.env: OPENROUTER_API_KEY_AEDIST, OPENROUTER_API_KEY_KIEU, EXPIRED_*);
# sourcing it whole over-shares. Selection is EXPLICIT and VERBOSE — there is no
# naming convention or suffix-stripping — and it happens at the EXPORT BOUNDARY:
# for a provider:... entry the file is sourced in an ISOLATED subshell run with a
# CLEARED environment (`env -i`), only the requested SRC value is extracted, and
# DST is exported in the parent with that value assigned LITERALLY (command
# substitution captures the string; it is never eval'd), so a value with spaces or
# a $(...) literal is captured literally and never re-evaluated. Trailing newlines
# are stripped by command-substitution capture; credential values carry none.
# SRC's siblings die with the subshell — only DST lands in the real env. The cleared environment is
# load-bearing: it drops BASH_ENV (so the extraction `bash -c` cannot re-source
# this script and fork-bomb under production BASH_ENV=bash-env.sh) and prevents the
# SRC lookup from resolving against any ambient exported var — only the provider
# file's own definitions are visible. Least-privilege lives here, not in the
# filesystem (one file per provider).
#
# Provider names must match ^[a-z0-9-]+$ — anything else (path traversal
# like ../../x, a slash, uppercase, empty) is ignored with a warning.
# SRC/DST must each match ^[A-Za-z_][A-Za-z0-9_]*$; a malformed entry
# warns `ignoring invalid KEYS entry: <entry>` and is skipped. The EXPORT
# NAME (DST, or SRC in the no-rename form) is additionally refused when it
# names a shell/process/interpreter-critical variable — PATH, BASH_ENV, ENV,
# SHELLOPTS, BASHOPTS, IFS, PS1..PS4, PROMPT_COMMAND, CDPATH, GLOBIGNORE,
# LD_PRELOAD, LD_LIBRARY_PATH, LD_AUDIT, GCONV_PATH, PYTHONPATH, NODE_OPTIONS,
# NODE_PATH, PERL5LIB, RUBYOPT, the git exec vectors GIT_SSH_COMMAND, GIT_SSH,
# GIT_ASKPASS, GIT_EXTERNAL_DIFF, the LESSOPEN / LESSCLOSE pager hooks, or the
# BASH_FUNC_* / DYLD_* prefix families —
# via the shared _be_is_protected_name predicate (ticket 0345), alongside the
# existing GUARD_* / _be_* refusal; such an entry warns `refusing KEYS export to
# protected name: <name>` and is skipped, so an untrusted .env cannot overwrite a
# process-critical variable in every subprocess. A named
# SRC absent from the file warns `KEYS var not found: <provider>:<SRC>` and
# is skipped. The per-provider files are user-owned and TRUSTED, so a bare
# `provider` entry sources them as shell code (contrast the untrusted project
# .env). A missing provider file warns but is non-fatal.
#
# Guarantee and its limit. Two properties hold even against a hostile project
# .env: it never sources a path outside ~/.config/keys/ (name validation), and it
# never executes the project .env (strict-parsed, never sourced) — so a hostile
# .env can neither run code nor exfiltrate a secret through the .env itself. But
# the provider SET is self-declared by that untrusted file, which can name any
# provider to load its secret into the environment. This is cooperative scoping
# that shrinks default secret exposure, NOT access control against a hostile
# project .env.

# --- shared protected-name predicate (tickets 0343 + 0345) -------------------
# Returns success (0) when NAME must never be set by the untrusted project .env,
# whether through the strict-parse KEY=VALUE loop or a KEYS= selection export.
# Both export paths call this ONE predicate so their denylists cannot drift.
# It refuses, as an auditable single `case`:
#   * any guard-namespaced key — the GUARD_* form and the leading-underscore
#     _GUARD_* worktree-path override pair (substring match), plus this script's
#     own _be_* bookkeeping (whose live value the strict-parse loop would corrupt);
#   * the shell/process/interpreter-critical set: PATH / LD_PRELOAD / LD_LIBRARY_PATH
#     / LD_AUDIT (code execution), BASH_ENV / ENV (bash re-source), SHELLOPTS /
#     BASHOPTS / IFS / PS1..PS4 / PROMPT_COMMAND / CDPATH / GLOBIGNORE (parse and
#     word-split hijack), GCONV_PATH (glibc iconv-module RCE), the interpreter
#     hijacks PYTHONPATH / NODE_OPTIONS / NODE_PATH / PERL5LIB / RUBYOPT, the git
#     command-execution vectors GIT_SSH_COMMAND / GIT_SSH / GIT_ASKPASS /
#     GIT_EXTERNAL_DIFF (the harness runs git constantly, so a project .env that
#     set one would run its command in every git call) and the pager hooks
#     LESSOPEN / LESSCLOSE (a `|cmd %s` input pipe runs on every `git log` / `less`),
#     and the BASH_FUNC_* exported-function and DYLD_* (macOS LD_* analogue) prefix
#     families.
_be_is_protected_name() {
    case "$1" in
        *GUARD_*|_be_*) return 0 ;;
        PATH|BASH_ENV|ENV|SHELLOPTS|BASHOPTS|IFS|\
        PS1|PS2|PS3|PS4|PROMPT_COMMAND|CDPATH|GLOBIGNORE|\
        LD_PRELOAD|LD_LIBRARY_PATH|LD_AUDIT|\
        GCONV_PATH|PYTHONPATH|NODE_OPTIONS|NODE_PATH|PERL5LIB|RUBYOPT|\
        GIT_SSH_COMMAND|GIT_SSH|GIT_ASKPASS|GIT_EXTERNAL_DIFF|LESSOPEN|LESSCLOSE|\
        BASH_FUNC_*|DYLD_*) return 0 ;;
    esac
    return 1
}

# --- trusted user-level .env: source as before (full expansion) ---
set -a  # mark all subsequent assignments for export
[ -f "$HOME/.claude/.env" ] && source "$HOME/.claude/.env"
set +a

# --- untrusted project-level .env: strict KEY=VALUE parse, never executed ---
# Claude Code sets PWD to the project dir for each subprocess. Skip if it
# resolves to the same file as the trusted user-level one (already loaded).
if [ -n "${PWD:-}" ] && [ -f "$PWD/.env" ]; then
    # `|| true` so a realpath failure (e.g. ~/.claude/.env absent, so its parent
    # dir is missing) cannot abort this script under an active `set -e` in the
    # sourcing shell. An empty result still compares unequal, so dedup is intact:
    # when the two files resolve to the same path the project parse is skipped;
    # when either is absent the paths differ and the project file is parsed.
    _be_proj="$(realpath "$PWD/.env" 2>/dev/null || true)"
    _be_user="$(realpath "$HOME/.claude/.env" 2>/dev/null || true)"
    if [ "$_be_proj" != "$_be_user" ]; then
      # This script is sourced on EVERY bash subprocess, so a pathological or
      # adversarial project .env must not tax each one. Past a generous byte cap
      # (256 KiB — no legitimate .env approaches it) skip the file entirely
      # rather than partially parse and risk a desynced read.
      _be_cap=262144
      _be_size="$(wc -c < "$PWD/.env" 2>/dev/null || echo 0)"
      if [ "${_be_size:-0}" -gt "$_be_cap" ]; then
        printf 'bash-env: project .env exceeds size cap (%s > %s bytes), skipping\n' \
            "$_be_size" "$_be_cap" >&2
      else
        while IFS= read -r _be_line || [ -n "$_be_line" ]; do
            # tolerate CRLF: a Windows-edited .env ends lines with \r\n and `read`
            # strips only \n, so drop a surviving trailing CR before parsing (this
            # also cleans a trailing \r on the KEYS= provider list).
            _be_line="${_be_line%$'\r'}"
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
            # ticket 0345: an untrusted project .env controls both name and value,
            # so refuse any shell/process/interpreter-critical export NAME (else
            # GCONV_PATH / LD_PRELOAD / BASH_ENV → RCE, PATH / PYTHONPATH /
            # NODE_OPTIONS → interpreter clobber, in EVERY subprocess). Shares the
            # _be_is_protected_name predicate with the KEYS-selection path below,
            # so the two denylists cannot drift. Default-deny, skip + warn.
            if _be_is_protected_name "$_be_key"; then
                printf 'bash-env: refusing protected name from project .env: %s\n' \
                    "$_be_key" >&2
                continue
            fi
            # assign the value LITERALLY — never expanded, never executed
            export "$_be_key=$_be_val"
        done < "$PWD/.env"
        unset _be_line _be_trim _be_key _be_val _be_first _be_last
      fi
      unset _be_cap _be_size
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
    for _be_entry in ${KEYS}; do
        IFS="$_be_ifs"
        # trim surrounding whitespace
        _be_entry="${_be_entry#"${_be_entry%%[![:space:]]*}"}"
        _be_entry="${_be_entry%"${_be_entry##*[![:space:]]}"}"
        [ -z "$_be_entry" ] && { IFS=','; continue; }
        # An entry is a bare `provider` or a selection `provider:VAR` /
        # `provider:SRC=DST`. A colon means selection mode.
        case "$_be_entry" in
            *:*) _be_sel_mode=1
                 _be_prov="${_be_entry%%:*}"
                 _be_sel="${_be_entry#*:}" ;;
            *)   _be_sel_mode=0
                 _be_prov="$_be_entry"
                 _be_sel="" ;;
        esac
        # validate provider: lowercase, digits and dashes only — blocks traversal
        if [[ ! "$_be_prov" =~ ^[a-z0-9-]+$ ]]; then
            printf 'bash-env: ignoring invalid KEYS entry: %s\n' "$_be_entry" >&2
            IFS=','
            continue
        fi
        if [ "$_be_sel_mode" = 1 ]; then
            # split selector into SRC and DST (DST defaults to SRC when no `=`).
            # A second `=` lands inside DST and fails the identifier check below,
            # so `SRC=DST=extra` and `provider:` (empty selector) are rejected.
            case "$_be_sel" in
                *=*) _be_src="${_be_sel%%=*}"; _be_dst="${_be_sel#*=}" ;;
                *)   _be_src="$_be_sel";       _be_dst="$_be_sel" ;;
            esac
            if [[ ! "$_be_src" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || \
               [[ ! "$_be_dst" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
                printf 'bash-env: ignoring invalid KEYS entry: %s\n' "$_be_entry" >&2
                IFS=','
                continue
            fi
            # structural refusal (mirrors the project-.env line-138 guard): the
            # untrusted project .env supplies SRC/DST, so it must not name a
            # guard-namespaced target (GUARD_* / the _GUARD_* worktree-path
            # override pair honored by pretooluse-worktree-path-guard.sh) nor
            # this script's own _be_* bookkeeping, which is live in the sourcing
            # shell and would be corrupted mid-loop. Default-deny, skip + warn.
            if [[ "$_be_dst" == *GUARD_* ]] || [[ "$_be_dst" == _be_* ]] || \
               [[ "$_be_src" == *GUARD_* ]]; then
                printf 'bash-env: ignoring invalid KEYS entry: %s\n' "$_be_entry" >&2
                IFS=','
                continue
            fi
            # shell/process/interpreter-critical export-name refusal: the export
            # NAME is DST (== SRC in the no-rename form), chosen by the untrusted
            # project .env. Refuse names that would subvert every subprocess if a
            # hostile .env aimed a value at them — PATH/LD_* (code execution),
            # BASH_ENV/ENV (re-source arbitrary shell), IFS/prompt/CDPATH/GLOBIGNORE
            # (parse and word-splitting hijack), GCONV_PATH (glibc iconv RCE), the
            # PYTHONPATH/NODE_OPTIONS/NODE_PATH/PERL5LIB/RUBYOPT interpreter hijacks,
            # the BASH_FUNC_* exported-function channel, and the DYLD_* macOS
            # analogue of LD_*. Shares the _be_is_protected_name predicate with the
            # strict-parse loop above (ticket 0345), so the two denylists cannot
            # drift. Default-deny, skip + warn.
            if _be_is_protected_name "$_be_dst"; then
                printf 'bash-env: refusing KEYS export to protected name: %s\n' \
                    "$_be_dst" >&2
                IFS=','
                continue
            fi
        fi
        _be_keyfile="$HOME/.config/keys/$_be_prov.env"
        if [ ! -f "$_be_keyfile" ]; then
            printf 'bash-env: KEYS provider not found: %s\n' "$_be_prov" >&2
            IFS=','
            continue
        fi
        if [ "$_be_sel_mode" = 0 ]; then
            # bare provider: whole-file source. Enable allexport ONLY around the
            # source, so exactly the variables the trusted provider file assigns
            # get exported — the loop bookkeeping (IFS, the _be_* temporaries) is
            # assigned outside allexport and stays unexported.
            set -a
            source "$_be_keyfile"
            set +a
        else
            # selection: source the file in an ISOLATED subshell with a CLEARED
            # environment (env -i), extract ONLY the requested SRC value, and
            # export DST in this shell. `env -i` is load-bearing on two counts:
            #   (1) it drops BASH_ENV, so the `bash -c` does NOT re-source this
            #       script — in production BASH_ENV=bash-env.sh, so a plain
            #       `bash -c` here would re-read $PWD/.env, re-hit this selection
            #       entry, and re-spawn `bash -c` without bound (fork bomb).
            #   (2) the subshell starts with NO inherited variables, so `${!2}`
            #       (the SRC lookup) can only resolve names the provider file
            #       itself defines — an ambient exported var cannot be smuggled
            #       into DST. A SRC absent from the file exits 4 regardless of env.
            # The value is captured as a string via command substitution and
            # assigned LITERALLY (never eval'd), never re-evaluated; command
            # substitution strips trailing newlines (credential values carry
            # none). SRC's siblings die with the subshell — only DST reaches
            # the real env. The `if` wrapper keeps the substitution's exit status
            # from tripping an active `set -e` in the sourcing shell. The inner
            # `.`/`printf`/`[`/`set` are bash builtins, so the empty PATH under
            # env -i does not matter; `. "$1"` uses an absolute path.
            if _be_val="$(env -i bash -c '
                    set -a
                    . "$1" >/dev/null 2>&1 || exit 3
                    [ -z "${!2+x}" ] && exit 4
                    printf "%s" "${!2}"
                ' _ "$_be_keyfile" "$_be_src")"; then
                export "$_be_dst=$_be_val"
            else
                _be_rc=$?
                if [ "$_be_rc" = 4 ]; then
                    printf 'bash-env: KEYS var not found: %s:%s\n' "$_be_prov" "$_be_src" >&2
                elif [ "$_be_rc" = 3 ]; then
                    # File is present (existence checked above) but sourcing or
                    # extraction failed — a distinct condition from a missing file.
                    printf 'bash-env: KEYS could not read %s:%s (provider file present but source failed)\n' \
                        "$_be_prov" "$_be_src" >&2
                else
                    printf 'bash-env: KEYS provider not found: %s\n' "$_be_prov" >&2
                fi
            fi
        fi
        IFS=','
    done
    IFS="$_be_ifs"
    [ "$_be_had_noglob" = 1 ] || set +f
    unset _be_ifs _be_entry _be_prov _be_sel _be_sel_mode _be_src _be_dst \
          _be_val _be_rc _be_keyfile _be_had_noglob
fi

# Drop the shared predicate so it does not leak into every subprocess's shell.
unset -f _be_is_protected_name 2>/dev/null || true
