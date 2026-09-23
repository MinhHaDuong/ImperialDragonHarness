#!/usr/bin/env bash
# Pre-flight UNKNOWN is transient; CONFLICTING and exhausted UNKNOWN refuse.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
mkdir -p "$WORK/bin"
cat > "$WORK/bin/gh" <<'STUB'
#!/usr/bin/env bash
set -euo pipefail
case "$1 $2" in
  "pr view")
    if [[ "$*" == *"--json mergeable --jq"* ]]; then
      n=$(cat "$POLL_COUNT")
      echo $((n+1)) > "$POLL_COUNT"
      if [[ "$MODE" == transient ]]; then echo MERGEABLE; else echo "$MODE"; fi
    elif [[ "$*" == *"--json state --jq"* ]]; then
      echo MERGED
    else
      initial=$MODE
      [[ "$initial" == transient ]] && initial=UNKNOWN
      jq -n --arg head "$BRANCH" --arg mergeable "$initial" \
        '{number:42,headRefName:$head,baseRefName:"main",mergeable:$mergeable,statusCheckRollup:[],body:"Ticket: none",isDraft:false,title:"Test"}'
    fi ;;
  "pr merge") echo "$*" >> "$MERGE_LOG" ;;
  *) echo "unexpected gh call: $*" >&2; exit 2 ;;
esac
STUB
chmod +x "$WORK/bin/gh"
git init -q "$WORK/repo"
git -C "$WORK/repo" config user.email test@example.com
git -C "$WORK/repo" config user.name Test
git -C "$WORK/repo" config commit.gpgsign false
git -C "$WORK/repo" commit -q --allow-empty -m init
git -C "$WORK/repo" branch -M main
git -C "$WORK/repo" switch -q -c pr-test
BRANCH=pr-test
export BRANCH

run_case() {
  local mode=$1 output rc=0
  echo 0 > "$WORK/polls"
  : > "$WORK/merges"
  output=$(cd "$WORK/repo" && PATH="$WORK/bin:$PATH" MODE="$mode" \
    POLL_COUNT="$WORK/polls" MERGE_LOG="$WORK/merges" \
    ERG_PR_MERGE_POLL_INTERVAL=0 ERG_PR_MERGE_POLL_TRIES=3 \
    ERG_PR_MERGE_SYNC=/bin/true bash "$ROOT/skills/merge/erg-pr-merge" 42 2>&1) || rc=$?
  printf '%s\n' "$output" > "$WORK/$mode.out"
  echo "$rc" > "$WORK/$mode.rc"
}

run_case transient
[[ $(cat "$WORK/transient.rc") -eq 0 ]] || { cat "$WORK/transient.out"; echo 'FAIL: transient UNKNOWN refused'; exit 1; }
[[ $(cat "$WORK/polls") -eq 1 ]] || { echo 'FAIL: transient UNKNOWN did not settle in one poll'; exit 1; }
[[ $(wc -l < "$WORK/merges") -eq 1 ]] || { echo 'FAIL: transient UNKNOWN did not reach merge'; exit 1; }

run_case UNKNOWN
[[ $(cat "$WORK/UNKNOWN.rc") -eq 1 ]] || { echo 'FAIL: persistent UNKNOWN did not refuse'; exit 1; }
[[ $(cat "$WORK/polls") -eq 3 ]] || { echo 'FAIL: persistent UNKNOWN exceeded or skipped poll budget'; exit 1; }
grep -q 'mergeability is UNKNOWN — resolve conflicts or try again in a moment' "$WORK/UNKNOWN.out"
[[ ! -s "$WORK/merges" ]] || { echo 'FAIL: persistent UNKNOWN reached merge'; exit 1; }

run_case CONFLICTING
[[ $(cat "$WORK/CONFLICTING.rc") -eq 1 ]] || { echo 'FAIL: CONFLICTING did not refuse'; exit 1; }
[[ $(cat "$WORK/polls") -eq 0 ]] || { echo 'FAIL: CONFLICTING consumed poll budget'; exit 1; }
grep -q 'mergeability is CONFLICTING — resolve conflicts or try again in a moment' "$WORK/CONFLICTING.out"
[[ ! -s "$WORK/merges" ]] || { echo 'FAIL: CONFLICTING reached merge'; exit 1; }
echo 'PASS: pre-flight mergeability settles UNKNOWN only and refuses unsafe states'
