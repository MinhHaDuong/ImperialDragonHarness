#!/usr/bin/env bash
# Reviewer-management dispatcher — pure I/O helper for the /reviewers skill.
# Case-switch dispatch; no plugin architecture.
#
# "Review is CI" (ticket 0205): each seat is a sandboxed CI-style reviewer
# job. `request` runs the 0217 seat-runner once per roster seat (one
# container per seat); `harvest` normalizes every seat's findings to the
# 0205 contract shape; `scorecard` appends a fixed-schema trial line.
#
# Containment is the seat-runner's OS sandbox (0217), NOT this script.
# This script holds no secrets. A seat's credential comes from the environment
# when the BASH_ENV path exported it (0207); when it did not, the variable is
# resolved from the user's keystore at run time (0393, see § seat credential
# resolution). Either way the value lives only in a shell variable and reaches
# the seat-runner through a subshell's environment — never argv, never a file,
# never any log line.
set -euo pipefail
export LC_ALL=C  # every awk/sort float reads and writes `.` decimals under any ambient locale

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="${REVIEWERS_REPO:-$(cd "${SCRIPT_DIR}/../.." && pwd)}"
PANEL="${REVIEWERS_PANEL:-${SCRIPT_DIR}/panel.yml}"
# The 0217 seat-runner. Overridable so the test suite can stub it.
SEAT_RUNNER="${SEAT_RUNNER:-${SCRIPT_DIR}/../../scripts/seat-runner.sh}"
# Where per-seat findings land for harvest to collect (per merge request).
FINDINGS_DIR="${REVIEWERS_FINDINGS_DIR:-${TMPDIR:-/tmp}/reviewers}"
# The frozen benchmark board `audition` replays (ticket 0346). Overridable.
BENCHMARK_BOARD="${REVIEWERS_BOARD:-${SCRIPT_DIR}/benchmark-board.yml}"
# The erg binary used to append trial-ticket log lines. Overridable for tests.
ERG="${ERG:-${SCRIPT_DIR}/../../tickets/erg}"
# The user's credential keystore, consulted when a seat's `credential-env`
# variable is absent from the environment (ticket 0393). Overridable for tests.
KEYSTORE="${REVIEWERS_KEYSTORE:-$HOME/.config/keys}"

usage_text() {
    cat <<'EOF'
Usage: reviewers.sh <subcommand> [args]

Subcommands:
  list                          Show panel members and trial progress
  request <pr> [branch]         Run each seat (0217 seat-runner) over the MR
  harvest <pr>                  Normalize all seats' findings to one file
  scorecard <pr> <seat> <ver>   Append a fixed-schema trial line via erg note
  scores [seat-or-candidate]    Read back trial scorecards and audition blocks
                                as one sortable table (corpus-wide, read-only)
  audition <model> [opts]       Replay a candidate over the frozen benchmark
                                board; score decorrelation vs ground truth.
                                Opts: --endpoint URL --board FILE
                                --trial-ticket T --credential-env NAME --name L
  help                          Print this usage block and exit 0

Reviewing a branch in another repository (a fork of an upstream project, say):
  REVIEWERS_REPO=<path>         the checkout the seats read (default: this harness)
  REVIEWERS_PR_BRANCH=<branch>  skip the forge lookup for the head branch
Without the first, a branch that lives elsewhere fails as an unknown pathspec.

`request` exits non-zero when cli/model seats were attempted and none of them ran.
Per-seat fail-open is unchanged: one seat failing never blocks the others.
EOF
}

# Unknown / no verb: usage to stderr, exit 1. The `help` verb prints the same
# block to stdout and exits 0 (a conventional help contract; ticket 0348).
usage() { usage_text >&2; exit 1; }

# ── roster parsing ───────────────────────────────────────────────────────────
# Emit one pipe-separated record per seat: name kind status endpoint model
# login trial-ticket credential-env. Minimal block parser for the flat
# panel.yml schema; comment and blank lines are ignored, and an explicit
# `reviewers: []` yields nothing. Pipe (not tab) is the delimiter so an empty
# middle field (e.g. a seat with no credential-env) does not shift later fields.
roster_records() {
    awk '
        /^[[:space:]]*#/        { next }
        /^reviewers:[[:space:]]*\[\][[:space:]]*$/ { exit }
        /^[[:space:]]*-[[:space:]]*name:/ {
            if (have) print rec(); have=1; name=val($0); kind=st=ep=mo=lg=tt=ce=""; next
        }
        /^[[:space:]]+kind:/           { kind=val($0) }
        /^[[:space:]]+status:/         { st=val($0) }
        /^[[:space:]]+endpoint:/       { ep=val($0) }
        /^[[:space:]]+model:/          { mo=val($0) }
        /^[[:space:]]+login:/          { lg=val($0) }
        /^[[:space:]]+trial-ticket:/   { tt=val($0) }
        /^[[:space:]]+credential-env:/ { ce=val($0) }
        END { if (have) print rec() }
        function val(line,  v) { sub(/^[^:]*:[[:space:]]*/, "", line); gsub(/^[[:space:]]+|[[:space:]]+$/, "", line); return line }
        function rec() { return name"|"kind"|"st"|"ep"|"mo"|"lg"|"tt"|"ce }
    ' "$PANEL" 2>/dev/null
}

panel_is_empty() { [ -z "$(roster_records)" ]; }

# ── benchmark-board parsing (ticket 0346) ────────────────────────────────────
# Emit one pipe-separated record per board PR: pr title base head panel defects.
# `panel`/`defects` are space-separated anchor lists (scalar YAML values), so the
# minimal block parser never has to descend into nested YAML lists. Pipe is the
# delimiter and `defects` (possibly empty) is last, so an empty middle field
# cannot shift later fields (rules/coding-bash.md).
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

# 4-digit ticket ID from a `.../NNNN-slug.erg` path; empty when unmatched.
# One extractor for every trial-ticket consumer (scorecard, audition).
_ticket_id_from_path() {  # path
    basename "$1" | sed -n 's/^\([0-9]\{4\}\)-.*/\1/p'
}

# Extract one `key=value` field (value runs to the next `|`) from a
# 0205-contract FINDING line. One decoder for harvest AND audition, so a
# contract change cannot silently drift between the two subcommands.
_contract_field() {  # key line
    sed -n "s/.*${1}=\([^|]*\).*/\1/p" <<<"$2"
}

# Extract one space-delimited `key=value` field (value runs to the next space)
# from a scorecard/audition card line. Sibling of `_contract_field`, which
# decodes the pipe-delimited FINDING contract; this one decodes the
# space-delimited trial-log cards that `scores` reads back (ticket 0348).
_card_field() {  # key line
    # First-match, no subprocess: strip up to (and including) the first `key=`,
    # then take the value up to the next space. A greedy sed `.*key=` would bind
    # the LAST occurrence and, if a value repeats the key, silently pick the
    # wrong one — the scorecard parser is likewise first-match (0348 review).
    local rest="${2#*"$1"=}"
    [ "$rest" = "$2" ] && return 0   # key absent → empty
    printf '%s' "${rest%% *}"
}

# Elapsed seconds (one decimal) between two `date +%s.%N` stamps. One
# implementation for request's per-seat timing AND audition's per-PR timing,
# so a change to how wall-clock is measured cannot drift between the two
# call sites (ticket 0353 simplify review).
_elapsed() {  # t0 t1
    awk -v a="$1" -v b="$2" 'BEGIN{printf "%.1f", b - a}'
}

# Nearest-rank percentile (1-based) at percentile $1 of the numeric arguments
# $2..$N. Empty arg list → "0.0". One implementation for audition's per-run
# p50/p95 AND the peer-relative SLOW median, so the two can never drift apart
# (ticket 0353).
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

# Emit every ticket's `--- log ---` section lines across the corpus (tickets/
# and tickets/closed/). The scan latches at the FIRST `--- log ---`, stops at
# the next section boundary, and never re-enters, so a body line quoting
# `--- log ---` cannot fabricate a phantom row (ticket 0348). Shared by `scores`
# (read-back table) and audition's peer-relative SLOW scan (ticket 0353), so
# both read the same log-only surface from one implementation.
_corpus_log_lines() {  # tickets_dir
    local td="$1"
    [ -d "$td" ] || return 0
    # One awk over the whole file list (FNR==1 resets the per-file latch), not
    # one awk fork per ticket — the corpus is hundreds of files and `audition`
    # now scans it on every run (ticket 0353 simplify review). -print0/-0 keep
    # unusual filenames intact; xargs -r skips awk entirely on an empty list.
    find "$td" -name '*.erg' -type f -print0 2>/dev/null | sort -z | \
        xargs -0 -r awk '
            FNR == 1        { inlog = 0; done_log = 0 }
            done_log        { next }
            !inlog && /^--- log ---/ { inlog=1; next }
            inlog && /^--- /         { inlog=0; done_log=1; next }
            inlog
        ' 2>/dev/null
}

# Peer p50 latencies: emit the `latency-p50` seconds (`s` stripped) of every
# OTHER candidate's audition card on the SAME board size, read log-only from the
# ticket corpus. Feeds the peer-relative SLOW gate (ticket 0353).
_audition_peer_p50s() {  # tickets_dir board_size self_label
    local td="$1" bsize="$2" self="$3" line p50 lbl
    _corpus_log_lines "$td" | while IFS= read -r line; do
        case "$line" in *"audition candidate="*) ;; *) continue ;; esac
        [ "$(_card_field board "$line")" = "${bsize}MR" ] || continue
        p50=$(_card_field latency-p50 "$line")
        p50="${p50%s}"
        # Emit only a well-formed numeric p50 — a malformed card must not coerce
        # to 0.0 and silently drag the peer median down (ticket 0353 review).
        case "$p50" in ''|*[!0-9.]*|*.*.*) continue ;; esac
        lbl=$(_card_field candidate "$line")
        [ "$lbl" = "$self" ] && continue
        printf '%s\n' "$p50"
    done
}

# Does candidate finding basename $1 + line $2 match any anchor in list $3?
# Anchor form: basename[:LINE] or basename:* (bare basename == :*).
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

# ── seat credential resolution (ticket 0393) ─────────────────────────────────
# A seat's `credential-env: NAME` names the variable holding its endpoint key.
# The BASH_ENV path (0207) exports it — but only where the cwd's `.env` KEYS=
# line selects that provider, and that selection is DEFAULT-DENY. From a project
# whose selection names a different key, or from any cwd declaring none, NAME is
# simply absent: the seat cannot authenticate, and before 0393 it failed open.
#
# Robustness belongs on the CONSUMER side. The key files under the keystore are
# the author's and are never edited here: they hold bare assignments with no
# `export`, which is exactly why the extraction below sources under `set -a`.
#
# Hygiene, non-negotiable in this block: a resolved value is never printed,
# logged, written to a file, or placed on any argv. Warnings name variables and
# provider FILES only. The value lands in one shell variable (_CRED_VALUE) and
# is exported solely inside the subshell that execs the seat-runner.
_CRED_VALUE=""

# The keystore file defining NAME, or non-zero when none does. Provider file
# names are not secrets, so an ambiguity WARN may name them.
_keystore_file_for() {  # $1 validated variable name
    local name="$1" f restore
    local -a hits=()
    restore="$(shopt -p nullglob)"
    shopt -s nullglob
    for f in "$KEYSTORE"/*.env; do
        grep -Eq "^[[:space:]]*(export[[:space:]]+)?${name}=" "$f" 2>/dev/null && hits+=("$f")
    done
    eval "$restore"
    [ "${#hits[@]}" -gt 0 ] || return 1
    if [ "${#hits[@]}" -gt 1 ]; then
        echo "reviewers: WARN credential ${name} is defined in ${#hits[@]} keystore files; using $(basename "${hits[0]}")" >&2
    fi
    printf '%s\n' "${hits[0]}"
}

# Read ONE variable out of a trusted provider file. Same isolation idiom as
# ~/.claude/scripts/bash-env.sh's selection path, for the same reasons: `env -i` drops
# BASH_ENV (so this `bash -c` cannot re-source the harness env script and
# fork-bomb) and clears the environment (so the lookup can only resolve a name
# the provider file itself defines — no ambient variable is smuggled in). `set
# -a` is what makes an export-less assignment visible at all. The value is
# captured as a string and assigned literally, never eval'd; the file's other
# variables die with the subshell. Exit 3 = unreadable file, 4 = name absent.
_keystore_value() {  # $1 provider file, $2 validated variable name
    env -i bash -c '
        set -a
        . "$1" >/dev/null 2>&1 || exit 3
        [ -z "${!2+x}" ] && exit 4
        printf "%s" "${!2}"
    ' _ "$1" "$2"
}

# Resolve a seat's credential into _CRED_VALUE. Returns 0 when the seat can
# authenticate (either the variable is already exported — _CRED_VALUE stays
# empty and the seat-runner reads it from the inherited environment — or the
# keystore supplied it), non-zero when it cannot.
_resolve_seat_credential() {  # $1 credential-env name
    local name="$1" file val
    _CRED_VALUE=""
    if [[ ! "$name" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
        # Also keeps the name out of the grep regex above as a metacharacter.
        echo "reviewers: WARN credential-env '${name}' is not a valid variable name" >&2
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

# ── PR → branch resolution (forge-specific; overridable for tests) ───────────
pr_branch() {  # $1 pr; honor an explicit override first
    local pr="$1"
    if [ -n "${REVIEWERS_PR_BRANCH:-}" ]; then echo "$REVIEWERS_PR_BRANCH"; return 0; fi
    gh pr view "$pr" --json headRefName --jq '.headRefName'  # harness-extension-point
}

# ── Forge reviewer request (forge-specific; swap for another forge) ──────────
request_forge_reviewer() {  # $1 pr, $2 bot login
    local pr="$1" login="$2"
    gh api --method POST \
        "repos/{owner}/{repo}/pulls/${pr}/requested_reviewers" \
        -f "reviewers[]=${login}" >/dev/null 2>&1  # harness-extension-point
}

subcmd="${1:-}"; shift || true

case "$subcmd" in
    list)
        if panel_is_empty; then echo "no reviewers configured"; exit 0; fi
        printf '%-18s %-12s %-9s %s\n' NAME KIND STATUS TRIAL-TICKET
        while IFS='|' read -r name kind st ep mo lg tt ce; do
            printf '%-18s %-12s %-9s %s\n' "$name" "$kind" "${st:-advisory}" "$tt"
        done < <(roster_records)
        ;;

    request)
        pr="${1:-}"; [ -n "$pr" ] || { echo "error: request requires a merge request identifier" >&2; exit 1; }
        if panel_is_empty; then echo "no reviewers configured"; exit 0; fi
        branch="${2:-$(pr_branch "$pr")}"
        [ -n "$branch" ] || { echo "error: could not resolve branch for MR #${pr}" >&2; exit 1; }
        dest="${FINDINGS_DIR}/${pr}"; mkdir -p "$dest"
        ran=0; unrun=0
        # Counted beside `ran` so the two silences can be told apart: a roster of
        # forge-bot seats alone attempts nothing locally and is not a failure, while
        # every attempted seat failing is no verdict at all (0870).
        attempted=0
        # Per-seat run record for `harvest`'s panel-integrity pass (0393). One
        # line, `ok` or `fail <reason>`; reasons name variables, never values.
        _seat_status() { printf '%s\n' "$2" > "${dest}/${1}.status"; }
        while IFS='|' read -r name kind st ep mo lg tt ce; do
            case "$kind" in
                forge-bot)
                    # Server-side reviewer, requested on demand — nothing
                    # fires without this explicit request (0206: no repo-wide
                    # auto-request lever). Fail-open like every other seat.
                    if [ -z "$lg" ]; then
                        echo "request: WARN forge-bot seat '${name}' has no login — skipped" >&2
                        _seat_status "$name" "fail seat has no forge login"
                        unrun=$((unrun+1))
                        continue
                    fi
                    if request_forge_reviewer "$pr" "$lg"; then
                        echo "request: forge-bot seat '${name}' requested (${lg}) on MR #${pr}" >&2
                        _seat_status "$name" "ok"
                    else
                        echo "request: WARN forge-bot seat '${name}' request failed (fail-open)" >&2
                        _seat_status "$name" "fail forge reviewer request failed"
                        unrun=$((unrun+1))
                    fi
                    ;;
                cli-agent|local-model)
                    # Per-seat fail-open: a seat that errors WARNs and the
                    # others proceed — one seat never blocks the verdict (0205).
                    # Thread the credential-env NAME only when the seat sets it;
                    # a local, unauthenticated endpoint carries no credential.
                    cred_args=()
                    _CRED_VALUE=""
                    if [ -n "$ce" ]; then
                        cred_args=(--credential-env "$ce")
                        # A seat that cannot authenticate is skipped LOUDLY and
                        # recorded: running it would only reproduce the same
                        # failure with a vaguer message, and the whole point of
                        # 0393 is that this outcome must reach the report.
                        if ! _resolve_seat_credential "$ce"; then
                            echo "request: WARN seat '${name}' did NOT review — credential ${ce} unresolved (fail-open; reported by harvest)" >&2
                            _seat_status "$name" "fail credential ${ce} unresolved"
                            unrun=$((unrun+1))
                            continue
                        fi
                    fi
                    # Time the seat, whatever the outcome — a slow-then-failed
                    # seat is still evidence. The elapsed seconds land in a
                    # `.latency` sidecar beside the findings; `scorecard` folds
                    # it into the seat's trial line (ticket 0353). forge-bot
                    # seats run async server-side and get no sidecar — there is
                    # nothing local to time.
                    #
                    # `attempted` counts the seats actually handed to the
                    # seat-runner, so it is incremented HERE and not before the
                    # credential gate above. That boundary is a live arbitration
                    # between two open tickets, recorded rather than decided:
                    # 0870 says a panel that produced no verdict must exit
                    # non-zero, and a seat skipped for an unresolved credential
                    # produced none either; 0393 says an unresolved credential
                    # stays fail-open (0205) and is reported on `harvest`'s
                    # STDOUT as SEAT-FAILED / PANEL-INTEGRITY, which is the
                    # channel the panel's reader actually sees. Counting it here
                    # keeps both tickets' own tests true. The residual case —
                    # a roster whose EVERY seat is credential-skipped exits 0,
                    # loud on harvest's report but silent to a caller gating on
                    # the exit status — is noted in ticket 0393 for the author.
                    attempted=$((attempted+1))
                    t0=$(date +%s.%N)
                    _seat_exec "$ce" --repo "$REPO_ROOT" --branch "$branch" \
                        --endpoint "$ep" --model "$mo" --out "${dest}/${name}.findings" \
                        ${cred_args[@]+"${cred_args[@]}"} \
                        >/dev/null 2>"${dest}/${name}.err" && seat_ok=1 || seat_ok=0
                    t1=$(date +%s.%N)
                    _elapsed "$t0" "$t1" > "${dest}/${name}.latency"
                    if [ "$seat_ok" = 1 ]; then
                        echo "request: seat '${name}' ok → ${dest}/${name}.findings" >&2
                        _seat_status "$name" "ok"
                        ran=$((ran+1))
                    else
                        echo "request: WARN seat '${name}' failed (fail-open; see ${dest}/${name}.err)" >&2
                        _seat_status "$name" "fail seat-runner exited non-zero (see ${name}.err)"
                        unrun=$((unrun+1))
                    fi
                    ;;
                *)
                    echo "request: WARN seat '${name}' has unknown kind '${kind}' — skipped" >&2
                    _seat_status "$name" "fail unknown seat kind '${kind}'"
                    unrun=$((unrun+1))
                    ;;
            esac
        done < <(roster_records)
        echo "request: ${ran} cli/model seat(s) ran for MR #${pr}" >&2
        # `if`, not `[ … ] && echo`: a false test as the branch's last command
        # would become the script's exit status under `set -e` (coding-bash.md).
        if [ "$unrun" -gt 0 ]; then
            echo "request: ${unrun} seat(s) did NOT review MR #${pr} — harvest reports them" >&2
        fi
        # A panel that reviewed nothing must not report success. Per-seat fail-open is
        # right and stays: one seat must never block a verdict. No seat running is not a
        # lenient verdict, it is the absence of one, and a caller that gates on the exit
        # status cannot otherwise tell it from three seats finding nothing to say (0870).
        # Placed AFTER the `unrun` report so a caller that gates on the exit status
        # still gets the per-seat detail on the way out.
        if [ "$attempted" -gt 0 ] && [ "$ran" -eq 0 ]; then
            echo "request: no seat reviewed MR #${pr} — all ${attempted} attempted seat(s) failed;" \
                 "see ${dest}/*.err. This is not an approval." >&2
            exit 1
        fi
        ;;

    harvest)
        pr="${1:-}"; [ -n "$pr" ] || { echo "error: harvest requires a merge request identifier" >&2; exit 1; }
        dest="${FINDINGS_DIR}/${pr}"
        shopt -s nullglob
        # A missing dest is no longer an early exit: the panel-integrity pass
        # below must still run, precisely because "no seat ran" is the case that
        # used to be indistinguishable from "no seat found anything" (0393).
        for f in "$dest"/*.findings; do
            seat="$(basename "$f" .findings)"
            declare -A _seen=()
            while IFS= read -r line; do
                case "$line" in
                    FINDING\|*)
                        sev=$(_contract_field severity "$line")
                        loc=$(_contract_field file "$line")
                        rat=$(sed -n 's/.*rationale=\(.*\)$/\1/p' <<<"$line")
                        if [ -n "$sev" ] && [ -n "$loc" ]; then
                            if [ "$sev" = "verifiable-or-consider" ] || [ "$loc" = "PATH:LINE" ] || [ "$rat" = "ONE SENTENCE" ]; then
                                echo "harvest: DROP template-echo from '${seat}': ${line}" >&2; continue
                            fi
                            key="${sev}|${loc}|${rat}"
                            if [ -n "${_seen[$key]:-}" ]; then
                                echo "harvest: DROP duplicate from '${seat}': ${line}" >&2; continue
                            fi
                            _seen[$key]=1
                            echo "${sev}: ${loc} — ${rat}  [${seat}]"
                        else
                            echo "harvest: WARN unparseable finding from '${seat}': ${line}" >&2
                        fi
                        ;;
                    SUMMARY\|*) : ;;
                    "") : ;;
                    *) echo "harvest: WARN non-contract line from '${seat}': ${line}" >&2 ;;
                esac
            done < "$f"
            unset _seen
        done

        # ── panel integrity (ticket 0393) ────────────────────────────────────
        # A seat that never reviewed must not read as a seat that found nothing.
        # `request` leaves a `.status` record per seat; every seat that did not
        # review is named HERE, on STDOUT — the report stream the panel's reader
        # actually sees. A stderr WARN is exactly what was lost the day the
        # OpenRouter seat failed open mid-gaze, and an empty harvest that exits
        # 0 for both "clean" and "nothing ran" is not a check at all.
        #
        # Fail-open is preserved deliberately: these are visible lines, not a
        # non-zero exit, so one dead seat still never blocks a verdict (0205).
        unreviewed=0
        while IFS='|' read -r sname skind sst sep smo slg stt sce; do
            [ -n "$sname" ] || continue
            status=""
            if [ -f "${dest}/${sname}.status" ]; then
                status="$(head -1 "${dest}/${sname}.status")"
            fi
            case "$status" in
                ok*) continue ;;
                fail*)
                    echo "SEAT-FAILED: ${sname} — ${status#fail }  [this seat did NOT review]"
                    unreviewed=$((unreviewed+1))
                    continue
                    ;;
            esac
            # No run record at all. A forge-bot seat leaves no local findings by
            # design (its review lands server-side), so only the seats that were
            # supposed to write findings here can be judged missing.
            case "$skind" in
                cli-agent|local-model)
                    if [ ! -s "${dest}/${sname}.findings" ]; then
                        echo "SEAT-MISSING: ${sname} — no findings and no run record  [this seat did NOT review]"
                        unreviewed=$((unreviewed+1))
                    fi
                    ;;
            esac
        done < <(roster_records)
        if [ "$unreviewed" -gt 0 ]; then
            echo "PANEL-INTEGRITY: ${unreviewed} seat(s) did not review this merge request — the findings above are NOT a full panel"
        fi
        ;;

    scorecard)
        pr="${1:-}"; seat="${2:-}"; verdict="${3:-}"
        [ -n "$pr" ] && [ -n "$seat" ] && [ -n "$verdict" ] || { echo "error: scorecard requires <pr> <seat> <verdict-summary>" >&2; exit 1; }
        # Resolve the seat's trial ticket from the roster.
        tt=""
        while IFS='|' read -r n k s e m l t ce; do [ "$n" = "$seat" ] && tt="$t"; done < <(roster_records)
        [ -n "$tt" ] || { echo "error: seat '${seat}' not in roster (no trial-ticket)" >&2; exit 1; }
        tid=$(_ticket_id_from_path "$tt")
        # Fixed schema so 0205's integration review is evidence-based, not vibes.
        line="MR #${pr} seat=${seat} verdict: ${verdict}"
        # Fold in the seat's per-MR latency when `request` left a sidecar
        # (ticket 0353). Appended at END so every existing parser is unaffected;
        # absent sidecar → byte-identical to the pre-0353 line.
        latfile="${FINDINGS_DIR}/${pr}/${seat}.latency"
        [ -f "$latfile" ] && line="${line} latency=$(cat "$latfile")s"
        "$ERG" log "$tid" "claude note ${line}"
        ;;

    audition)
        # Replay a CANDIDATE model over the frozen benchmark board (0346) and
        # score its decorrelation value against ground truth. The candidate is
        # NOT a roster seat: audition filters candidates BEFORE the live advisory
        # trial, and never touches panel.yml.
        model="${1:-}"; shift || true
        [ -n "$model" ] || { echo "error: audition requires <model> [--endpoint URL]" >&2; exit 1; }
        endpoint=""; board="$BENCHMARK_BOARD"; cred=""; label=""
        trial="tickets/0207-agnostic-cli-reviewer-seat-one-config-op.erg"
        while [ $# -gt 0 ]; do
            case "$1" in
                --endpoint)       endpoint="$2"; shift 2 ;;
                --board)          board="$2"; shift 2 ;;
                --trial-ticket)   trial="$2"; shift 2 ;;
                --credential-env) cred="$2"; shift 2 ;;
                --name)           label="$2"; shift 2 ;;
                *) echo "error: audition: unknown option '$1'" >&2; exit 1 ;;
            esac
        done
        label="${label:-$model}"
        # Reject control characters (newlines/CRs) AND the card's field delimiters
        # (space, `=`) in the values that flow into the space-delimited scorecard
        # card. A newline would forge a second ticket-log line `erg check` cannot
        # flag; a space or `=` truncates or hijacks the first-match `_card_field`
        # parse — e.g. `--name "Local Qwen 30B"` would read back as `Local`,
        # breaking the peer-median self-exclusion and the `scores` NAME column
        # (ticket 0353 review). Candidate labels are identifiers, not prose.
        case "$model" in *[$'\n\r'\ =]*) echo "error: audition: model must not contain spaces, '=', or newlines" >&2; exit 1 ;; esac
        case "$label" in *[$'\n\r'\ =]*) echo "error: audition: --name must not contain spaces, '=', or newlines" >&2; exit 1 ;; esac
        [ -f "$board" ] || { echo "error: benchmark board not found: ${board}" >&2; exit 1; }
        # Resolve the candidate's credential the same way a seat's is (0393),
        # but fail LOUD here: audition already refuses to report a partial
        # score, and an unauthenticated replay is the emptiest partial there is.
        _CRED_VALUE=""
        if [ -n "$cred" ]; then
            _resolve_seat_credential "$cred" \
                || { echo "error: audition: credential ${cred} unresolved — not in the environment, not defined in ${KEYSTORE}/*.env" >&2; exit 1; }
        fi

        dest="${FINDINGS_DIR}/audition-$$"; mkdir -p "$dest"
        trap 'rm -rf "$dest"' EXIT   # reap the scratch dir on every exit path
        n_pr=0; tot=0; dup=0; uv=0; uh=0; ptok=0; ctok=0; lat="0"
        lat_samples=()
        # Per-PR elapsed is real wall-clock; REVIEWERS_AUDITION_ELAPSED (a
        # space-separated list of seconds, one per board PR, indexed by board
        # position) overrides it so the latency statistics are deterministic
        # under test — the same override philosophy as SEAT_RUNNER/ERG (0353).
        _elapsed_ov=()
        [ -n "${REVIEWERS_AUDITION_ELAPSED:-}" ] && read -ra _elapsed_ov <<<"$REVIEWERS_AUDITION_ELAPSED"
        while IFS='|' read -r pr title base head panel defects; do
            [ -n "$pr" ] || continue
            n_pr=$((n_pr + 1))
            out="${dest}/${pr}.findings"
            # Reuse the exact seat-runner invocation path `request` uses: one
            # sandboxed, read-only replay over the PR's reconstructed diff.
            sr_args=(--repo "$REPO_ROOT" --base "$base" --branch "$head" \
                     --model "$model" --out "$out")
            [ -n "$endpoint" ] && sr_args+=(--endpoint "$endpoint")
            [ -n "$cred" ]     && sr_args+=(--credential-env "$cred")
            t0=$(date +%s.%N)
            # Fail-LOUD (unlike request's per-seat fail-open): a candidate that
            # cannot be replayed — unreachable endpoint, sandbox failure — voids
            # the whole audition rather than reporting a partial, misleading score.
            if ! _seat_exec "$cred" "${sr_args[@]}" >/dev/null 2>"${out}.err"; then
                # The scratch dir (and ${out}.err) is reaped by the EXIT trap, so
                # dump the seat-runner's stderr HERE — a message pointing at the
                # now-deleted file would be unreachable to the operator.
                echo "error: audition: seat-runner failed on board MR #${pr} (candidate=${label}); seat-runner stderr follows:" >&2
                cat "${out}.err" >&2 2>/dev/null || true
                exit 1
            fi
            t1=$(date +%s.%N)
            if [ "${#_elapsed_ov[@]}" -gt 0 ]; then
                e="${_elapsed_ov[$((n_pr - 1))]:-0.0}"
            else
                e=$(_elapsed "$t0" "$t1")
            fi
            lat_samples+=("$e")
            # Existing `latency=` field stays a running SUM across board PRs
            # (unchanged — do not turn it into a mean); the distribution stats
            # are appended separately below (ticket 0353).
            lat=$(awk -v s="$lat" -v e="$e" 'BEGIN{printf "%.1f", s + e}')
            # A seat that exited 0 but wrote nothing contributes zero findings —
            # count the latency (above) and move on rather than crashing on a
            # missing file.
            [ -f "$out" ] || continue
            while IFS= read -r line; do
                case "$line" in
                    FINDING\|*)
                        loc=$(_contract_field file "$line")
                        [ -n "$loc" ] || continue
                        tot=$((tot + 1))
                        case "$(_audition_classify "$loc" "$panel" "$defects")" in
                            duplicate)           dup=$((dup + 1)) ;;
                            unique-verified)     uv=$((uv + 1)) ;;
                            unique-hallucinated) uh=$((uh + 1)) ;;
                        esac
                        ;;
                    SUMMARY\|*)
                        p=$(sed -n 's/.*prompt_tokens=\([0-9]\{1,\}\).*/\1/p' <<<"$line")
                        c=$(sed -n 's/.*completion_tokens=\([0-9]\{1,\}\).*/\1/p' <<<"$line")
                        [ -n "$p" ] && ptok=$((ptok + p))
                        [ -n "$c" ] && ctok=$((ctok + c))
                        ;;
                esac
            done < "$out"
        done < <(board_records "$board")

        [ "$n_pr" -gt 0 ] || { echo "error: benchmark board is empty: ${board}" >&2; exit 1; }

        # overlap% = share of the candidate's findings that merely duplicate the
        # internal panel (redundant; the inverse of decorrelation value).
        overlap=0; [ "$tot" -gt 0 ] && overlap=$(( dup * 100 / tot ))
        # $ per review from token counts, when the seat reported them on SUMMARY;
        # prices are USD per 1M tokens (env-overridable). n/a when no tokens or no
        # price is configured — honest rather than a fabricated $0.
        price_in="${REVIEWERS_PRICE_IN_PER_M:-0}"
        price_out="${REVIEWERS_PRICE_OUT_PER_M:-0}"
        cost="n/a"
        if [ $((ptok + ctok)) -gt 0 ]; then
            cost=$(awk -v p="$ptok" -v c="$ctok" -v pi="$price_in" -v po="$price_out" \
                'BEGIN{ if (pi==0 && po==0) { print "n/a" } else { printf "$%.4f", p/1e6*pi + c/1e6*po } }')
        fi

        # Per-run latency distribution (nearest-rank) over the replayed board.
        p50=$(_percentile 50 ${lat_samples[@]+"${lat_samples[@]}"})
        p95=$(_percentile 95 ${lat_samples[@]+"${lat_samples[@]}"})

        # Peer-relative SLOW gate (ticket 0353). A candidate is compared only
        # against OTHER candidates that replayed the SAME board size — identical
        # work, so the comparison is host- and diff-size-independent. Flag when
        # this p50 exceeds factor × the cross-candidate median p50 (self included
        # in the median sample, so a mean-based bug on 10/10/35 is caught). Fires
        # only with ≥1 peer (a lone candidate has no basis for comparison) and is
        # a STRICT >, so a boundary candidate at exactly factor × median is kept.
        # Flagged → the verdict is eliminate-slow (no advisory trial); the prior
        # candidates' logged lines are never touched (append-only).
        tickets_dir="${REVIEWERS_TICKETS:-${REPO_ROOT}/tickets}"
        factor="${REVIEWERS_SLOW_FACTOR:-3}"
        slow=""
        peer_p50s=()
        mapfile -t peer_p50s < <(_audition_peer_p50s "$tickets_dir" "$n_pr" "$label")
        if [ "${#peer_p50s[@]}" -ge 1 ]; then
            median=$(_percentile 50 "${peer_p50s[@]}" "$p50")
            if awk -v x="$p50" -v m="$median" -v f="$factor" 'BEGIN{exit !(x > f * m)}'; then
                slow=" SLOW"
                echo "audition: candidate '${label}' flagged SLOW — p50 ${p50}s > ${factor}× peer median ${median}s; eliminate-slow (no advisory trial)" >&2
            fi
        fi

        card="audition candidate=${label} model=${model} board=${n_pr}MR findings=${tot} duplicate=${dup} unique-verified=${uv} unique-hallucinated=${uh} overlap=${overlap}% latency=${lat}s cost=${cost} latency-p50=${p50}s latency-p95=${p95}s${slow}"
        echo "$card"

        # Append the scorecard to the candidate's trial ticket (erg verbs:
        # created/note/closed only — audition uses note). Promotion stays manual.
        tid=$(_ticket_id_from_path "$trial")
        [ -n "$tid" ] || { echo "error: audition: could not derive a ticket id from '${trial}' — scorecard not logged" >&2; exit 1; }
        if ! "$ERG" log "$tid" "claude note ${card}" >/dev/null; then
            echo "error: audition: failed to log scorecard to trial ticket ${trial} (id ${tid})" >&2
            exit 1
        fi
        ;;

    scores)
        # Read back the fixed-schema trial cards — scorecard lines and audition
        # blocks — that `scorecard`/`audition` append to trial tickets, and print
        # one sortable comparison table. Read-only: reads the ticket store, never
        # edits a roster or writes an erg-log line (ticket 0348). The search is
        # corpus-wide — every `*.erg` under tickets/ including tickets/closed/, so
        # a retired seat's archived trial ticket is still read back (scorecard/
        # audition resolve their tickets by 4-digit ID, so a card outlives the
        # ticket's move to closed/) — but confined to each file's log section.
        filter="${1:-}"
        tickets_dir="${REVIEWERS_TICKETS:-${REPO_ROOT}/tickets}"
        fmt='%-9s %-20s %-26s %5s %5s %5s %4s %5s %5s %8s %9s %8s %8s %5s\n'
        # shellcheck disable=SC2059  # $fmt is a fixed local format, not user input
        printf "$fmt" KIND NAME MR/BOARD VERIF CONS FIND DUP UVER UHAL OVERLAP LATENCY P95 COST FLAG
        [ -d "$tickets_dir" ] || exit 0
        while IFS= read -r line; do
            [ -n "$line" ] || continue
            case "$line" in
                *"audition candidate="*)
                    name=$(_card_field candidate "$line")
                    board=$(_card_field board "$line")
                    find=$(_card_field findings "$line")
                    dup=$(_card_field duplicate "$line")
                    uv=$(_card_field unique-verified "$line")
                    uh=$(_card_field unique-hallucinated "$line")
                    ov=$(_card_field overlap "$line")
                    lat=$(_card_field latency "$line")
                    p50=$(_card_field latency-p50 "$line")
                    p95=$(_card_field latency-p95 "$line")
                    cost=$(_card_field cost "$line")
                    if [ -z "$name" ] || [ -z "$find" ] || [ -z "$dup" ] || [ -z "$uv" ] || [ -z "$uh" ]; then
                        echo "scores: WARN unparseable audition line: ${line}" >&2; continue
                    fi
                    [ -n "$filter" ] && [ "$filter" != "$name" ] && continue
                    # LATENCY column shows p50 (the gate-relevant stat); older
                    # cards without p50 fall back to the running-sum `latency=`.
                    # The bare ` SLOW` token (ticket 0353) surfaces in FLAG.
                    latshow="${p50:-$lat}"
                    flag="-"; case "$line" in *" SLOW") flag="SLOW" ;; esac
                    # shellcheck disable=SC2059
                    printf "$fmt" audition "$name" "${board:--}" - - "$find" "$dup" "$uv" "$uh" "${ov:--}" "${latshow:--}" "${p95:--}" "${cost:--}" "$flag"
                    ;;
                *"MR "*"seat="*"verdict:"*)
                    # Extract the counts as one anchored `N verifiable, M consider`
                    # unit — the exact shape `scorecard` writes. A first- OR
                    # last-occurrence parse of a lone "N verifiable" is poisoned by
                    # freeform verdict prose on either side ("5 verifiable issues …
                    # — 1 verifiable, 2 consider"); the comma-joined pair almost
                    # never occurs except as the real tally. The count feeds 0205's
                    # promote/drop decision, so a wrong number is a wrong decision
                    # (ticket 0348 review, rounds 1–2).
                    seat="${line#*seat=}"; seat="${seat%% *}"
                    mr="${line#*MR }";     mr="${mr%% *}"
                    lat=$(_card_field latency "$line")   # per-seat latency (0353), if request left one
                    tally=$(grep -oE '[0-9]+ verifiable, [0-9]+ consider' <<<"$line" | head -1 || true)
                    if [ -z "$seat" ] || [ -z "$tally" ]; then
                        echo "scores: WARN unparseable scorecard line: ${line}" >&2; continue
                    fi
                    verif="${tally%% *}"                 # "N verifiable, M consider" → N
                    cons="${tally##*, }"; cons="${cons%% *}"   # → M
                    [ -n "$filter" ] && [ "$filter" != "$seat" ] && continue
                    # shellcheck disable=SC2059
                    printf "$fmt" scorecard "$seat" "${mr:--}" "$verif" "$cons" - - - - - "${lat:--}" - - -
                    ;;
            esac
            # Scan only each ticket's `--- log ---` section, where scorecard/
            # audition append their cards — NOT the body, where a ticket may
            # quote the card schema as documentation (this very ticket does).
            # The scan latches: it starts at the FIRST `--- log ---`, stops at the
            # section boundary that follows, and never re-enters — so a body line
            # quoting `--- log ---` (the %erg template shows one) cannot fabricate
            # a phantom row or spam WARNs (ticket 0348 review, rounds 1–2).
            # No pre-filter grep here: the `case` above has no default arm, so a
            # log line matching neither pattern is already a silent no-op -- a
            # second regex re-stating the same two patterns would only risk
            # drifting out of sync with the case arms (simplify review, PR 634).
        done < <(_corpus_log_lines "$tickets_dir")
        ;;

    help) usage_text ;;

    ""|--help|-h) usage ;;
    *) echo "error: unknown subcommand '${subcmd}'" >&2; usage ;;
esac
