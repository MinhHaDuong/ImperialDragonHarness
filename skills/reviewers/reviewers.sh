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
# This script holds no secrets; seat credentials load via BASH_ENV (0207).
set -euo pipefail

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
        ran=0
        while IFS='|' read -r name kind st ep mo lg tt ce; do
            case "$kind" in
                forge-bot)
                    # Server-side reviewer, requested on demand — nothing
                    # fires without this explicit request (0206: no repo-wide
                    # auto-request lever). Fail-open like every other seat.
                    if [ -z "$lg" ]; then
                        echo "request: WARN forge-bot seat '${name}' has no login — skipped" >&2
                        continue
                    fi
                    if request_forge_reviewer "$pr" "$lg"; then
                        echo "request: forge-bot seat '${name}' requested (${lg}) on MR #${pr}" >&2
                    else
                        echo "request: WARN forge-bot seat '${name}' request failed (fail-open)" >&2
                    fi
                    ;;
                cli-agent|local-model)
                    # Per-seat fail-open: a seat that errors WARNs and the
                    # others proceed — one seat never blocks the verdict (0205).
                    # Thread the credential-env NAME only when the seat sets it;
                    # a local, unauthenticated endpoint carries no credential.
                    cred_args=()
                    [ -n "$ce" ] && cred_args=(--credential-env "$ce")
                    if "$SEAT_RUNNER" --repo "$REPO_ROOT" --branch "$branch" \
                        --endpoint "$ep" --model "$mo" --out "${dest}/${name}.findings" \
                        ${cred_args[@]+"${cred_args[@]}"} \
                        >/dev/null 2>"${dest}/${name}.err"; then
                        echo "request: seat '${name}' ok → ${dest}/${name}.findings" >&2
                        ran=$((ran+1))
                    else
                        echo "request: WARN seat '${name}' failed (fail-open; see ${dest}/${name}.err)" >&2
                    fi
                    ;;
                *)
                    echo "request: WARN seat '${name}' has unknown kind '${kind}' — skipped" >&2
                    ;;
            esac
        done < <(roster_records)
        echo "request: ${ran} cli/model seat(s) ran for MR #${pr}" >&2
        ;;

    harvest)
        pr="${1:-}"; [ -n "$pr" ] || { echo "error: harvest requires a merge request identifier" >&2; exit 1; }
        dest="${FINDINGS_DIR}/${pr}"
        # No seats ran / empty panel → empty normalized output, exit 0.
        [ -d "$dest" ] || exit 0
        shopt -s nullglob
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
        # Reject control characters (newlines/CRs) in the values that flow into
        # the erg-log scorecard card: an embedded newline would forge a second,
        # well-formed ticket-log line that `erg check` cannot flag.
        case "$model" in *[$'\n\r']*) echo "error: audition: model must not contain newlines or carriage returns" >&2; exit 1 ;; esac
        case "$label" in *[$'\n\r']*) echo "error: audition: --name must not contain newlines or carriage returns" >&2; exit 1 ;; esac
        [ -f "$board" ] || { echo "error: benchmark board not found: ${board}" >&2; exit 1; }

        dest="${FINDINGS_DIR}/audition-$$"; mkdir -p "$dest"
        trap 'rm -rf "$dest"' EXIT   # reap the scratch dir on every exit path
        n_pr=0; tot=0; dup=0; uv=0; uh=0; ptok=0; ctok=0; lat="0"
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
            if ! "$SEAT_RUNNER" "${sr_args[@]}" >/dev/null 2>"${out}.err"; then
                # The scratch dir (and ${out}.err) is reaped by the EXIT trap, so
                # dump the seat-runner's stderr HERE — a message pointing at the
                # now-deleted file would be unreachable to the operator.
                echo "error: audition: seat-runner failed on board MR #${pr} (candidate=${label}); seat-runner stderr follows:" >&2
                cat "${out}.err" >&2 2>/dev/null || true
                exit 1
            fi
            t1=$(date +%s.%N)
            lat=$(awk -v s="$lat" -v a="$t0" -v b="$t1" 'BEGIN{printf "%.1f", s + (b - a)}')
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

        card="audition candidate=${label} model=${model} board=${n_pr}MR findings=${tot} duplicate=${dup} unique-verified=${uv} unique-hallucinated=${uh} overlap=${overlap}% latency=${lat}s cost=${cost}"
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
        fmt='%-9s %-20s %-26s %5s %5s %5s %4s %5s %5s %8s %9s %8s\n'
        # shellcheck disable=SC2059  # $fmt is a fixed local format, not user input
        printf "$fmt" KIND NAME MR/BOARD VERIF CONS FIND DUP UVER UHAL OVERLAP LATENCY COST
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
                    cost=$(_card_field cost "$line")
                    if [ -z "$name" ] || [ -z "$find" ] || [ -z "$dup" ] || [ -z "$uv" ] || [ -z "$uh" ]; then
                        echo "scores: WARN unparseable audition line: ${line}" >&2; continue
                    fi
                    [ -n "$filter" ] && [ "$filter" != "$name" ] && continue
                    # shellcheck disable=SC2059
                    printf "$fmt" audition "$name" "${board:--}" - - "$find" "$dup" "$uv" "$uh" "${ov:--}" "${lat:--}" "${cost:--}"
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
                    tally=$(grep -oE '[0-9]+ verifiable, [0-9]+ consider' <<<"$line" | head -1 || true)
                    if [ -z "$seat" ] || [ -z "$tally" ]; then
                        echo "scores: WARN unparseable scorecard line: ${line}" >&2; continue
                    fi
                    verif="${tally%% *}"                 # "N verifiable, M consider" → N
                    cons="${tally##*, }"; cons="${cons%% *}"   # → M
                    [ -n "$filter" ] && [ "$filter" != "$seat" ] && continue
                    # shellcheck disable=SC2059
                    printf "$fmt" scorecard "$seat" "${mr:--}" "$verif" "$cons" - - - - - - -
                    ;;
            esac
            # Scan only each ticket's `--- log ---` section, where scorecard/
            # audition append their cards — NOT the body, where a ticket may
            # quote the card schema as documentation (this very ticket does).
            # The scan latches: it starts at the FIRST `--- log ---`, stops at the
            # section boundary that follows, and never re-enters — so a body line
            # quoting `--- log ---` (the %erg template shows one) cannot fabricate
            # a phantom row or spam WARNs (ticket 0348 review, rounds 1–2).
        done < <(
            # No pre-filter grep here: the `case` above has no default arm, so a
            # log line matching neither pattern is already a silent no-op -- a
            # second regex re-stating the same two patterns would only risk
            # drifting out of sync with the case arms (simplify review, PR 634).
            find "$tickets_dir" -name '*.erg' -type f 2>/dev/null | sort | while IFS= read -r f; do
                awk '
                    done_log        { next }
                    !inlog && /^--- log ---/ { inlog=1; next }
                    inlog && /^--- /         { inlog=0; done_log=1; next }
                    inlog
                ' "$f" 2>/dev/null
            done
        )
        ;;

    help) usage_text ;;

    ""|--help|-h) usage ;;
    *) echo "error: unknown subcommand '${subcmd}'" >&2; usage ;;
esac
