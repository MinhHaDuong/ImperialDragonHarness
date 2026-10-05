#!/usr/bin/env bash
# Data-integrity tests for the frozen benchmark board (ticket 1008).
#
# The board is ground truth for the audition benchmark; a silent edit here
# corrupts every scorecard computed from it. These checks guard the DATA
# against dropped keys, fabricated or drifted anchors, duplicate entries and
# an unlabeled board — using the git history itself as the oracle, never the
# YAML's own claims:
#   (a) every entry carries a `defects:` key; an explicitly-empty set must
#       carry a `none confirmed` justification comment inside its block
#       (on its own line, above the key — inline comments would be parsed
#       into the anchor field by the scalar block parser in
#       skills/coaching/replay.sh);
#   (b) every DEFECTS anchor resolves against the entry's OWN diff: the
#       basename appears in `git diff --name-only base...head`, and a
#       line-precise anchor blames (at head) to a commit introduced BY that
#       PR — i.e. ancestor of head but not of base. Scoped to defects, not
#       panel: panel anchors are recovered from gate-verdict comments and
#       legitimately cite pre-existing lines or adjacent files a reviewer
#       may flag; defect anchors are the fabrication surface (ticket 1008's
#       pre-registered anchor rule), so they are held to the strict oracle.
#       (b) also enforces the anchor GRAMMAR on both anchor sets — allowed
#       forms are `basename:LINE` and `basename:*`; a bare basename without
#       the colon is out-of-grammar and fails — and verifies the CONFIRMING
#       FIX recorded per populated entry as `# confirmed: <full-fix-sha>`
#       comment lines inside the block (parser-skipped, agnostic-clean):
#       (i) every populated entry carries at least one confirmed-fix SHA;
#       (ii) each fix commit exists and is on main history;
#       (iii) it postdates the PR (the entry head is an ancestor of the fix);
#       (iv) for every defect anchor, at least one confirmed fix REMOVED a
#            line in the anchor basename whose blame at the fix parent
#            points inside the PR (ancestor of head, not of base); for
#            line-precise anchors the removed pre-image content must match
#            the anchored head line content when the file is otherwise
#            unchanged between head and the fix parent — wildcards and
#            changed files use the basename-level check only.
#   (c) `pr` values are unique (pr is the only entry key; a duplicate would
#       overwrite a findings file, forging another candidate's verdict);
#   (d) at least 10 entries carry a non-empty defects set (exit criterion 2:
#       without labeled defect-bearing games the statistics policy is idle
#       and UVER is pinned at 0 by construction).
#
# (d) is the floor paired with (b): the count alone is satisfiable by
# fabrication; the pair is not.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BOARD="${REPO_ROOT}/skills/coaching/benchmark-board.yml"
PASS=0; FAIL=0

fail() { echo "FAIL: $*"; FAIL=$((FAIL+1)); }
pass() { echo "PASS: $*"; PASS=$((PASS+1)); }

[ -f "$BOARD" ] || { echo "FAIL: skills/coaching/benchmark-board.yml missing"; exit 1; }

# ── parse: one pipe-delimited record per entry ────────────────────────────────
# pr|has_defects_key|has_justification|base|head|panel|defects|confirmed
# Mirrors the scalar block parser in skills/coaching/replay.sh board_records(), extended
# with the bookkeeping fields the data contract needs. Comment lines are
# DATA here (justifications and confirmed-fix SHAs live in them), so they
# are tracked, not skipped.
records="$(awk '
    /^board:[[:space:]]*\[\][[:space:]]*$/ { exit }
    /^[[:space:]]*#/ {
        if (inblock && !dkey && $0 ~ /none confirmed/) just=1
        if (inblock && $0 ~ /^[[:space:]]*#[[:space:]]*confirmed:/) {
            s=$0
            sub(/^[[:space:]]*#[[:space:]]*confirmed:[[:space:]]*/, "", s)
            gsub(/[[:space:]]/, "", s)
            conf = (conf == "" ? s : conf "," s)
        }
        next
    }
    /^[[:space:]]*-[[:space:]]*pr:/ {
        if (have) print rec()
        have=1; inblock=1; just=0; dkey=0
        pr=fv($0,"pr"); title=base=head=panel=defects=conf=""; next
    }
    inblock && /^[[:space:]]+base:/    { base=fv($0,"base") }
    inblock && /^[[:space:]]+head:/    { head=fv($0,"head") }
    inblock && /^[[:space:]]+panel:/   { panel=fv($0,"panel") }
    inblock && /^[[:space:]]+defects:/ { defects=fv($0,"defects"); dkey=1 }
    END { if (have) print rec() }
    function fv(line,key,  v) {
        sub("^[[:space:]]*-?[[:space:]]*" key ":[[:space:]]*", "", line)
        gsub(/^[[:space:]]+|[[:space:]]+$/, "", line)
        gsub(/^\"|\"$/, "", line)
        gsub(/\|/, "/", line)
        return line
    }
    function rec() { return pr"|"dkey"|"just"|"base"|"head"|"panel"|"defects"|"conf }
' "$BOARD")"

[ -n "$records" ] || { echo "FAIL: benchmark board parses to zero entries"; exit 1; }
n_entries=$(printf '%s\n' "$records" | wc -l)

# ── (c) pr values unique ─────────────────────────────────────────────────────
dups="$(printf '%s\n' "$records" | awk -F'|' '{print $1}' | sort | uniq -d)"
if [ -z "$dups" ]; then
    pass "(c) board pr values are unique ($n_entries entries)"
else
    fail "(c) board pr values duplicated: $(printf '%s ' $dups)"
fi

# ── (a) defects key present; empty set carries a none-confirmed justification ─
n_empty=0; n_defect=0
while IFS='|' read -r pr dkey just base head panel defects conf; do
    if [ "$dkey" != 1 ]; then
        fail "(a) entry pr=$pr has no defects key"
        continue
    fi
    if [ -z "$defects" ]; then
        n_empty=$((n_empty+1))
        if [ "$just" != 1 ]; then
            fail "(a) entry pr=$pr has empty defects without a none-confirmed justification comment"
        fi
    else
        n_defect=$((n_defect+1))
    fi
done <<<"$records"
if [ "$FAIL" -eq 0 ]; then
    pass "(a) every entry carries a defects key; empty sets justified ($n_empty empty, $n_defect populated)"
fi

# ── helpers for (b) ──────────────────────────────────────────────────────────
# Removed pre-image lines of the fix diff for one file, as "lineno<TAB>content".
_fix_removed_lines() {  # fix full → stdout
    git -C "$REPO_ROOT" diff "$1^" "$1" -- "$2" 2>/dev/null | awk '
        /^@@/ { inhunk=1; split($2, h, ","); n = substr(h[1], 2); next }
        !inhunk { next }                      # --- a/ / +++ b/ file headers
        /^-/  { print n "\t" substr($0, 2); n++; next }
        /^\\/ { next }                          # "\ No newline" markers
        /^\+/ { next }
        /^ /  { n++; next }
    '
}

# Intro commit (SHA) of one pre-image line at the fix parent.
_blame_intro() {  # fix lineno full → stdout
    { git -C "$REPO_ROOT" blame -L "$2,$2" --porcelain "$1^" -- "$3" 2>/dev/null \
        | head -1 | sed 's/^\^//' | awk '{print $1}'; } || true
}

# Does one fix commit confirm one defect anchor? (see (iv) in the header)
# Exit 0 when yes. Wildcards use the basename-level check only; line-precise
# anchors additionally require a removed line whose pre-image content matches
# the anchored head line content when the file is otherwise unchanged between
# head and the fix parent (blob-equal); a changed file degrades to basename.
_confirming_fix_ok() {  # fix base head anchor full
    local fix="$1" base="$2" head="$3" anchor="$4" full="$5"
    local suffix="${anchor#*:}"
    local want=""
    if [ "$suffix" != "*" ] \
       && [ "$(git -C "$REPO_ROOT" rev-parse -q --verify "$head:$full" 2>/dev/null)" \
          = "$(git -C "$REPO_ROOT" rev-parse -q --verify "$fix^:$full" 2>/dev/null)" ]; then
        want="$(git -C "$REPO_ROOT" show "$head:$full" 2>/dev/null \
            | awk -v n="$suffix" 'NR==n { printf "%s", $0; exit }')"
    fi
    local ln content intro
    while IFS=$'\t' read -r ln content; do
        intro="$(_blame_intro "$fix" "$ln" "$full")"
        [ -n "$intro" ] || continue
        git -C "$REPO_ROOT" merge-base --is-ancestor "$intro" "$head" 2>/dev/null || continue
        git -C "$REPO_ROOT" merge-base --is-ancestor "$intro" "$base" 2>/dev/null && continue
        # removed line introduced by the PR: basename-level confirmation
        [ -z "$want" ] && return 0
        [ "$content" = "$want" ] && return 0
    done < <(_fix_removed_lines "$fix" "$full")
    return 1
}

# ── (b) anchor grammar, resolution, and confirming-fix verification ───────────
n_conf=0
while IFS='|' read -r pr dkey just base head panel defects conf; do
    # grammar: colon required, wildcard explicit (applies to both anchor sets;
    # no shipped anchor is a bare basename, so strict is safe).
    for a in $panel $defects; do
        case "$a" in
            *:*) ;;
            *)  fail "(b) pr=$pr anchor '$a' is out of grammar: colon required (basename:LINE or basename:*)"; continue ;;
        esac
        case "${a#*:}" in
            \*) ;;
            ''|*[!0-9]*) fail "(b) pr=$pr anchor '$a' is out of grammar: suffix must be a line number or *" ;;
        esac
    done
    [ -n "$defects" ] || continue
    files="$(git -C "$REPO_ROOT" diff --name-only "$base...$head" 2>/dev/null || true)"
    if [ -z "$files" ]; then
        fail "(b) entry pr=$pr diff $base...$head is empty or unresolvable"
        continue
    fi
    # (i) populated entries carry at least one confirmed-fix SHA
    fixes=()
    if [ -n "$conf" ]; then
        readarray -t fixes < <(tr ',' '\n' <<<"$conf")
    elif [ -n "$defects" ]; then
        fail "(b) pr=$pr: populated defects but no '# confirmed: <sha>' line in its block"
    fi
    for fix in "${fixes[@]}"; do
        # (ii) exists and is on main history
        if ! git -C "$REPO_ROOT" rev-parse -q --verify "$fix^{commit}" >/dev/null 2>&1; then
            fail "(b) pr=$pr confirmed fix $fix does not exist"
            continue
        fi
        if git -C "$REPO_ROOT" merge-base --is-ancestor "$fix" origin/main 2>/dev/null \
           || git -C "$REPO_ROOT" merge-base --is-ancestor "$fix" HEAD 2>/dev/null; then
            n_conf=$((n_conf+1))
        else
            fail "(b) pr=$pr confirmed fix $fix is not on main history"
        fi
        # (iii) postdates the PR merge: head is an ancestor of the fix
        git -C "$REPO_ROOT" merge-base --is-ancestor "$head" "$fix" 2>/dev/null \
            || fail "(b) pr=$pr confirmed fix $fix does not postdate the entry head $head"
    done
    for a in $defects; do
        name="${a%%:*}"
        line="${a#*:}"
        full=""
        while IFS= read -r f; do
            [ "$(basename "$f")" = "$name" ] && { full="$f"; break; }
        done <<<"$files"
        if [ -z "$full" ]; then
            fail "(b) pr=$pr anchor $a: basename not in diff base...$head"
            continue
        fi
        # line-precise anchors resolve and blame inside the PR; wildcards
        # only need the file in the diff
        if [ "$line" != "*" ]; then
            case "$line" in
                *[!0-9]*|'') continue ;;   # already failed the grammar check above
            esac
            intro="$( { git -C "$REPO_ROOT" blame -L "$line,$line" --porcelain "$head" -- "$full" 2>/dev/null \
                | head -1 | sed 's/^\^//' | awk '{print $1}'; } || true )"
            if [ -z "$intro" ]; then
                fail "(b) pr=$pr anchor $a: line $line absent from $name at head $head"
                continue
            fi
            if git -C "$REPO_ROOT" merge-base --is-ancestor "$intro" "$head" 2>/dev/null \
               && ! git -C "$REPO_ROOT" merge-base --is-ancestor "$intro" "$base" 2>/dev/null; then
                :
            else
                fail "(b) pr=$pr anchor $a: line $line blames to $intro, outside the PR (base..head)"
            fi
        fi
        # (iv) at least one confirmed fix removed an anchor-file line
        # introduced by this PR (content-matched for line-precise anchors
        # when the file is unchanged; see _confirming_fix_ok).
        confirmed=""
        if [ "${#fixes[@]}" -gt 0 ]; then
            for fix in "${fixes[@]}"; do
                if _confirming_fix_ok "$fix" "$base" "$head" "$a" "$full"; then confirmed=1; break; fi
            done
        fi
        if [ -n "$confirmed" ]; then :; else
            fail "(b) pr=$pr anchor $a: no confirmed fix removed a $name line introduced by this PR"
        fi
    done
done <<<"$records"
if [ "$FAIL" -eq 0 ]; then
    pass "(b) anchor grammar valid; every defects anchor resolves in its own diff and blames inside the PR"
    pass "(b) every populated entry carries confirmed fixes on main history that postdate it and removed PR-introduced lines ($n_conf fixes)"
fi

# ── (d) defect-bearing floor (exit criterion 2) ───────────────────────────────
if [ "$n_defect" -ge 10 ]; then
    pass "(d) board carries >=10 defect-bearing entries ($n_defect)"
else
    fail "(d) board carries only $n_defect defect-bearing entries (<10)"
fi

echo "test_benchmark_board: PASS=$PASS FAIL=$FAIL"
[ "$FAIL" -eq 0 ] || exit 1
