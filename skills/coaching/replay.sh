#!/usr/bin/env bash
# Cold, read-only replay of the frozen coaching board. Ground-truth matching,
# credential resolution, and seat invocation are preserved from reviewers.sh.
set -euo pipefail
export LC_ALL=C
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="${COACHING_REPO:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
SEAT_RUNNER="${SEAT_RUNNER:-$SCRIPT_DIR/seat-runner.sh}"
BOARD_DEFAULT="$SCRIPT_DIR/benchmark-board.yml"
KEYSTORE="$HOME/.config/keys"
MAX_KEYSTORE_BYTES=262144

board_records() {  # $1 board file
    awk '
        /^[[:space:]]*#/ { next }
        /^board:[[:space:]]*\[\][[:space:]]*$/ { exit }
        /^[[:space:]]*-[[:space:]]*pr:/ {
            if (have) print rec(); have=1
            pr=fv($0,"pr"); title=base=head=panel=defects=""; next
        }
        /^[[:space:]]+title:/   { title=fv($0,"title") }
        /^[[:space:]]+base:/    { base=fv($0,"base") }
        /^[[:space:]]+head:/    { head=fv($0,"head") }
        /^[[:space:]]+panel:/   { panel=fv($0,"panel") }
        /^[[:space:]]+defects:/ { defects=fv($0,"defects") }
        END { if (have) print rec() }
        function fv(line,key,  v) {
            sub("^[[:space:]]*-?[[:space:]]*" key ":[[:space:]]*", "", line)
            gsub(/^[[:space:]]+|[[:space:]]+$/, "", line)
            gsub(/^"|"$/, "", line)
            gsub(/\|/, "/", line)   # never let a value carry the record delimiter
            return line
        }
        function rec() { return pr"|"title"|"base"|"head"|"panel"|"defects }
    ' "$1" 2>/dev/null
}

_contract_field() {  # key line
    sed -n "s/.*${1}=\([^|]*\).*/\1/p" <<<"$2"
}

_elapsed() {  # t0 t1
    awk -v a="$1" -v b="$2" 'BEGIN{printf "%.1f", b - a}'
}

# Nearest-rank percentile (1-based) at percentile $1 of the numeric arguments
# $2..$N. Empty arg list → "0.0". Used for cold replay's per-PR p50/p95.
_percentile() {  # pct v1 v2 ...
    local pct="$1"; shift
    [ "$#" -gt 0 ] || { printf '0.0'; return 0; }
    # LC_ALL=C so `sort -g` and awk read `.` decimals regardless of the ambient
    # locale (a fr_FR locale would otherwise mis-parse "10.5" on the comma).
    printf '%s\n' "$@" | LC_ALL=C sort -g | LC_ALL=C awk -v p="$pct" '
        { a[NR]=$0 }
        END {
            x = (p / 100.0) * NR
            r = int(x); if (r < x) r++      # ceil → nearest-rank
            if (r < 1) r = 1; if (r > NR) r = NR
            printf "%.1f", a[r]
        }'
}

_audition_match() {  # cfile cline anchor-string
    local cf="$1" cl="$2" a af al
    local -a arr=()
    read -ra arr <<<"$3"
    for a in ${arr[@]+"${arr[@]}"}; do
        case "$a" in
            *:*) af="${a%%:*}"; al="${a##*:}" ;;
            *)   af="$a"; al="*" ;;
        esac
        [ "$cf" = "$af" ] || continue
        { [ "$al" = "*" ] || [ "$al" = "$cl" ]; } && return 0
    done
    return 1
}

# Classify one finding location against a PR's ground truth. Echoes exactly one
# of: duplicate | unique-verified | unique-hallucinated.
_audition_classify() {  # location panel-anchors defect-anchors
    local loc="$1" panel="$2" defects="$3" bn cf cl
    bn="${loc##*/}"                       # drop directory → basename[:line]
    case "$bn" in
        *:*) cf="${bn%%:*}"; cl="${bn##*:}" ;;
        *)   cf="$bn"; cl="" ;;
    esac
    if _audition_match "$cf" "$cl" "$panel";   then echo duplicate; return; fi
    if _audition_match "$cf" "$cl" "$defects"; then echo unique-verified; return; fi
    echo unique-hallucinated
}

_CRED_VALUE=""

# A provider must be a bounded regular file before anything reads it. The byte
# count uses the POSIX utility path (`command -p`), not the caller's PATH: a
# planted `wc` must not be able to waive the guard it implements. A bash
# `read -N` guard looks more self-contained but silently discards NUL bytes and
# therefore is not a byte count.
_keystore_file_is_safe() {  # $1 provider file
    local file="$1" bytes
    [ -f "$file" ] && [ -r "$file" ] || return 1
    bytes="$(command -p wc -c < "$file")" || return 1
    case "$bytes" in ''|*[!0-9]*) return 1 ;; esac
    [ "$bytes" -le "$MAX_KEYSTORE_BYTES" ]
}

# The keystore file defining NAME, or non-zero when none does. Provider file
# names are not secrets, so an ambiguity WARN may name them.
_keystore_file_for() {  # $1 validated variable name
    local name="$1" f restore line found
    local -a hits=()
    restore="$(shopt -p nullglob)"
    shopt -s nullglob
    for f in "$KEYSTORE"/*.env; do
        _keystore_file_is_safe "$f" || continue
        found=""
        while IFS= read -r line || [ -n "$line" ]; do
            if [[ "$line" =~ ^[[:space:]]*(export[[:space:]]+)?${name}= ]]; then
                found=1
                break
            fi
        done < "$f"
        [ -n "$found" ] && hits+=("$f")
    done
    eval "$restore"
    [ "${#hits[@]}" -gt 0 ] || return 1
    if [ "${#hits[@]}" -gt 1 ]; then
        echo "reviewers: WARN credential ${name} is defined in ${#hits[@]} keystore files; using $(basename "${hits[0]}")" >&2
    fi
    printf '%s\n' "${hits[0]}"
}

# Read ONE variable out of a trusted provider file. Same isolation idiom as
# $IDH_ROOT/scripts/bash-env.sh's selection path, for the same reasons: `env -i` drops
# BASH_ENV (so this `bash -c` cannot re-source the harness env script and
# fork-bomb) and clears the environment (so the lookup can only resolve a name
# the provider file itself defines — no ambient variable is smuggled in). `set
# -a` is what makes an export-less assignment visible at all. The EXTRACTED
# VALUE is captured as a string and printed literally, never eval'd; the file's
# other variables die with the subshell. Sourcing the provider file, on the
# other hand, executes its entire content — `.` is not a parser, it is the
# shell — so a provider file is trusted code, exactly as $IDH_ROOT/scripts/
# bash-env.sh trusts the same files for the same reason. Reaching that
# execution requires prior write access to the keystore, which is the trust
# boundary this design already assumes; the isolation above bounds what such
# code can reach, it does not stop it running. The regular-file and 256 KiB
# checks deliberately repeat after discovery to narrow the scan/source race.
# Exit 3 = unsafe/unreadable file, 4 = name absent, 5 = non-scalar value.
_keystore_value() {  # $1 provider file, $2 validated variable name
    local file="$1" name="$2" marked rc=0 value
    _keystore_file_is_safe "$file" || return 3
    marked="$(command -p env -i bash -c '
        set -a
        [ -r "$1" ] || exit 3
        __idh_emit_credential() {
            [ -z "${!1+x}" ] && exit 4
            declaration="$(declare -p "$1" 2>/dev/null)" || exit 4
            case "$declaration" in
                "declare -a "*|"declare -A "*) exit 5 ;;
            esac
            # Prefix proves completion; suffix preserves a trailing LF.
            printf "v%sx" "${!1}"
            exit 0
        }
        # A sourced provider may end in a failed command or call exit. Extract
        # on shell exit so either path can use a value already defined above.
        trap '\''__idh_emit_credential "$2"'\'' EXIT
        . "$1" >/dev/null 2>&1 || :
    ' _ "$file" "$name")" || rc=$?
    [ "$rc" -eq 0 ] || return "$rc"
    # No marker means the sourced provider exited before extraction completed.
    case "$marked" in v*x) ;; *) return 3 ;; esac
    value="${marked#v}"
    value="${value%x}"
    value="${value%$'\r'}"
    [ -n "$value" ] || return 4
    case "$value" in *$'\n'*|*$'\r'*) return 5 ;; esac
    printf '%s' "$value"
}

# Resolve a seat's credential into _CRED_VALUE. Returns 0 when the seat can
# authenticate (either the variable is already exported — _CRED_VALUE stays
# empty and the seat-runner reads it from the inherited environment — or the
# keystore supplied it), non-zero when it cannot.
_resolve_seat_credential() {  # $1 credential-env name
    local name="$1" file val
    _CRED_VALUE=""
    if [[ ! "$name" =~ ^[A-Z][A-Z0-9_]*$ ]] \
       || [[ ! "$name" =~ (^|_)(API_KEY|KEY|TOKEN|PASSWORD|SECRET)($|_) ]]; then
        # This is a credential resolver, not a general variable extractor.
        # Uppercase credential-shaped names also stay literal in the scan regex.
        echo "reviewers: WARN credential-env '${name}' is not an allowed credential name" >&2
        return 1
    fi
    [ -n "${!name:-}" ] && return 0
    if ! file="$(_keystore_file_for "$name")"; then
        echo "reviewers: WARN credential ${name} is neither in the environment nor defined in ${KEYSTORE}/*.env" >&2
        return 1
    fi
    if ! val="$(_keystore_value "$file" "$name")" || [ -z "$val" ]; then
        echo "reviewers: WARN credential ${name} could not be read from $(basename "$file")" >&2
        return 1
    fi
    _CRED_VALUE="$val"
    echo "reviewers: credential ${name} resolved from the keystore ($(basename "$file"))" >&2
    return 0
}

# Run the seat-runner with a keystore-resolved credential exported ONLY for that
# process. The export happens in a subshell, so the secret never enters this
# script's own environment (no other child — `gh`, `erg` — inherits it) and
# never appears on any argv (`env NAME=value cmd` would leak it to `ps -ef`).
# With no resolved value the seat-runner is invoked directly and reads the
# variable from the inherited environment exactly as before.
_seat_exec() {  # $1 credential-env name (may be empty); rest: seat-runner argv
    local cname="$1"; shift
    if [ -n "$cname" ] && [ -n "$_CRED_VALUE" ]; then
        ( export "${cname}=${_CRED_VALUE}"; exec "$SEAT_RUNNER" "$@" )
    else
        "$SEAT_RUNNER" "$@"
    fi
}

usage() {
    echo 'Usage: replay.sh <model> [--endpoint URL] [--board FILE] [--repo DIR] [--credential-env NAME] [--name LABEL]' >&2
    exit 2
}

model="${1:-}"; [ -n "$model" ] || usage; shift
endpoint=""; board="$BOARD_DEFAULT"; cred=""; label=""
while [ "$#" -gt 0 ]; do
    [ "$#" -ge 2 ] || usage
    case "$1" in
        --endpoint) endpoint="$2" ;;
        --board) board="$2" ;;
        --repo) REPO_ROOT="$2" ;;
        --credential-env) cred="$2" ;;
        --name) label="$2" ;;
        *) usage ;;
    esac
    shift 2
done
label="${label:-$model}"
case "$model" in *[$'\n\r'\ =]*) echo 'error: model must be a single identifier' >&2; exit 1;; esac
case "$label" in *[$'\n\r'\ =]*) echo 'error: name must be a single identifier' >&2; exit 1;; esac
[ -f "$board" ] || { echo "error: board not found: $board" >&2; exit 1; }
[ -d "$REPO_ROOT" ] || { echo "error: repository not found: $REPO_ROOT" >&2; exit 1; }
_CRED_VALUE=""
if [ -n "$cred" ]; then
    _resolve_seat_credential "$cred" || { echo "error: replay credential $cred unresolved" >&2; exit 1; }
fi

# Validate the whole board before invoking a runner. Pipe-delimited records are
# the same flat board format consumed by the old dispatcher.
mapfile -t records < <(board_records "$board")
[ "${#records[@]}" -gt 0 ] || { echo 'error: board is empty' >&2; exit 1; }
declare -A seen=()
for record in "${records[@]}"; do
    IFS='|' read -r pr title base head panel defects <<< "$record"
    if [[ ! "$pr" =~ ^[0-9]+$ ]] || [ -z "$base" ] || [ -z "$head" ] || [ -n "${seen[$pr]:-}" ]; then
        echo "error: incomplete or duplicate board entry: ${pr:-unknown}" >&2; exit 1
    fi
    seen[$pr]=1
done

dest="$(mktemp -d)"; trap 'rm -rf "$dest"' EXIT
n_pr=0; tot=0; dup=0; uv=0; uh=0; ptok=0; ctok=0; lat='0.0'; lat_samples=()
_elapsed_ov=()
[ -n "${REVIEWERS_AUDITION_ELAPSED:-}" ] && read -ra _elapsed_ov <<< "$REVIEWERS_AUDITION_ELAPSED"
for record in "${records[@]}"; do
    IFS='|' read -r pr title base head panel defects <<< "$record"
    n_pr=$((n_pr + 1))
    out="$dest/$pr.findings"
    sr_args=(--repo "$REPO_ROOT" --base "$base" --branch "$head" --model "$model" --out "$out")
    [ -n "$endpoint" ] && sr_args+=(--endpoint "$endpoint")
    [ -n "$cred" ] && sr_args+=(--credential-env "$cred")
    t0="$(date +%s.%N)"
    if ! _seat_exec "$cred" "${sr_args[@]}" >/dev/null 2>"$out.err"; then
        echo "error: replay runner failed on board MR #$pr; stderr follows:" >&2
        cat "$out.err" >&2
        exit 1
    fi
    t1="$(date +%s.%N)"
    [ -s "$out" ] || { echo "error: replay runner produced no result for board MR #$pr" >&2; exit 1; }
    e="$(_elapsed "$t0" "$t1")"
    if [ "${#_elapsed_ov[@]}" -gt 0 ]; then e="${_elapsed_ov[$((n_pr - 1))]:-0.0}"; fi
    lat_samples+=("$e")
    lat="$(awk -v s="$lat" -v e="$e" 'BEGIN{printf "%.1f", s + e}')"
    summary=0; findings=0; declared=''
    while IFS= read -r line; do
        case "$line" in
            FINDING\|*)
                loc="$(_contract_field file "$line")"
                [ -n "$loc" ] || { echo "error: malformed finding on board MR #$pr" >&2; exit 1; }
                findings=$((findings + 1)); tot=$((tot + 1))
                case "$(_audition_classify "$loc" "$panel" "$defects")" in
                    duplicate) dup=$((dup + 1));;
                    unique-verified) uv=$((uv + 1));;
                    unique-hallucinated) uh=$((uh + 1));;
                esac
                ;;
            SUMMARY\|*)
                summary=$((summary + 1))
                declared="$(_contract_field findings "$line")"
                p="$(sed -n 's/.*prompt_tokens=\([0-9]\{1,\}\).*/\1/p' <<< "$line")"
                c="$(sed -n 's/.*completion_tokens=\([0-9]\{1,\}\).*/\1/p' <<< "$line")"
                [ -n "$p" ] && ptok=$((ptok + p))
                [ -n "$c" ] && ctok=$((ctok + c))
                ;;
        esac
    done < "$out"
    if [ "$summary" -ne 1 ] || [[ ! "$declared" =~ ^[0-9]+$ ]]; then
        echo "error: incomplete summary on board MR #$pr" >&2; exit 1
    fi
    # Compare decimal strings so an oversized count cannot turn an integer
    # comparison error inside `if` into an apparent clean replay. Leading
    # zeroes were accepted by the former numeric comparison and remain valid.
    declared_norm="$(sed 's/^0*//' <<< "$declared")"
    declared_norm="${declared_norm:-0}"
    if [[ "$declared_norm" != "$findings" ]]; then
        echo "error: incomplete summary on board MR #$pr" >&2; exit 1
    fi
done

overlap=0; [ "$tot" -gt 0 ] && overlap=$((dup * 100 / tot))
price_in="${REVIEWERS_PRICE_IN_PER_M:-0}"; price_out="${REVIEWERS_PRICE_OUT_PER_M:-0}"
cost='n/a'
if [ $((ptok + ctok)) -gt 0 ]; then
    cost="$(awk -v p="$ptok" -v c="$ctok" -v pi="$price_in" -v po="$price_out" 'BEGIN{if(pi==0 && po==0){print "n/a"}else{printf "$%.4f", p/1e6*pi+c/1e6*po}}')"
fi
p50="$(_percentile 50 "${lat_samples[@]}")"
p95="$(_percentile 95 "${lat_samples[@]}")"
printf 'replay candidate=%s model=%s board=%sMR findings=%s duplicate=%s unique-verified=%s unique-hallucinated=%s overlap=%s%% latency=%ss cost=%s latency-p50=%ss latency-p95=%ss\n' "$label" "$model" "$n_pr" "$tot" "$dup" "$uv" "$uh" "$overlap" "$lat" "$cost" "$p50" "$p95"
