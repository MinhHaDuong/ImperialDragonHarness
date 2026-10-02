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
#       into the anchor field by the scalar block parser in reviewers.sh);
#   (b) every DEFECTS anchor resolves against the entry's OWN diff: the
#       basename appears in `git diff --name-only base...head`, and a
#       line-precise anchor blames (at head) to a commit introduced BY that
#       PR — i.e. ancestor of head but not of base. Scoped to defects, not
#       panel: panel anchors are recovered from gate-verdict comments and
#       legitimately cite pre-existing lines or adjacent files a reviewer
#       may flag; defect anchors are the fabrication surface (ticket 1008's
#       pre-registered anchor rule), so they are held to the strict oracle;
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
BOARD="${REPO_ROOT}/skills/reviewers/benchmark-board.yml"
PASS=0; FAIL=0

fail() { echo "FAIL: $*"; FAIL=$((FAIL+1)); }
pass() { echo "PASS: $*"; PASS=$((PASS+1)); }

[ -f "$BOARD" ] || { echo "FAIL: skills/reviewers/benchmark-board.yml missing"; exit 1; }

# ── parse: one pipe-delimited record per entry ────────────────────────────────
# pr|has_defects_key|has_justification|base|head|panel|defects
# Mirrors the scalar block parser in reviewers.sh board_records(), extended
# with the two bookkeeping fields the data contract needs. Comment lines are
# DATA here (justifications live in them), so they are tracked, not skipped.
records="$(awk '
    /^board:[[:space:]]*\[\][[:space:]]*$/ { exit }
    /^[[:space:]]*#/ {
        if (inblock && !dkey && $0 ~ /none confirmed/) just=1
        next
    }
    /^[[:space:]]*-[[:space:]]*pr:/ {
        if (have) print rec()
        have=1; inblock=1; just=0; dkey=0
        pr=fv($0,"pr"); title=base=head=panel=defects=""; next
    }
    inblock && /^[[:space:]]+base:/    { base=fv($0,"base") }
    inblock && /^[[:space:]]+head:/    { head=fv($0,"head") }
    inblock && /^[[:space:]]+panel:/   { panel=fv($0,"panel") }
    inblock && /^[[:space:]]+defects:/ { defects=fv($0,"defects"); dkey=1 }
    END { if (have) print rec() }
    function fv(line,key,  v) {
        sub("^[[:space:]]*-?[[:space:]]*" key ":[[:space:]]*", "", line)
        gsub(/^[[:space:]]+|[[:space:]]+$/, "", line)
        gsub(/^"|"$/, "", line)
        gsub(/\|/, "/", line)
        return line
    }
    function rec() { return pr"|"dkey"|"just"|"base"|"head"|"panel"|"defects }
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
while IFS='|' read -r pr dkey just base head panel defects; do
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

# ── (b) defects anchors verified against git history ──────────────────────────
# basename present in the entry's own diff; line-precise anchors blame (at
# head) to a commit introduced by the PR itself — ancestor of head, not of base.
while IFS='|' read -r pr dkey just base head panel defects; do
    [ -n "$defects" ] || continue
    files="$(git -C "$REPO_ROOT" diff --name-only "$base...$head" 2>/dev/null || true)"
    if [ -z "$files" ]; then
        fail "(b) entry pr=$pr diff $base...$head is empty or unresolvable"
        continue
    fi
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
        # wildcard anchors only need the file in the diff
        if [ "$line" = "*" ] || [ "$line" = "$a" ]; then continue; fi
        intro="$(git -C "$REPO_ROOT" blame -L "$line,$line" --porcelain "$head" -- "$full" 2>/dev/null \
            | head -1 | sed 's/^\^//' | awk '{print $1}')"
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
    done
done <<<"$records"
if [ "$FAIL" -eq 0 ]; then
    pass "(b) every defects anchor resolves in its own diff and blames inside the PR"
fi

# ── (d) defect-bearing floor (exit criterion 2) ───────────────────────────────
if [ "$n_defect" -ge 10 ]; then
    pass "(d) board carries >=10 defect-bearing entries ($n_defect)"
else
    fail "(d) board carries only $n_defect defect-bearing entries (<10)"
fi

echo "test_benchmark_board: PASS=$PASS FAIL=$FAIL"
[ "$FAIL" -eq 0 ] || exit 1
