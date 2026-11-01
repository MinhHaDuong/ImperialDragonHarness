#!/usr/bin/env bash
# usage: run.sh <runtime pi|codex> <task 1|2> <arm none|rule> <rep>
set -euo pipefail
D=$(cd "$(dirname "$0")" && pwd); rt=$1 t=$2 arm=$3 rep=$4
name=$rt-t$t-$arm-r$rep; scratch=$(mktemp -d /tmp/ab1414.XXXXXX); cd "$scratch"
task=$(cat "$D/prompts/task$t.txt"); rule="$D/prompts/rule$t.md"
case $rt in
pi)
  args=(--print --no-session -nt -ne -ns -nc -np)
  [ "$arm" = rule ] && args+=(--append-system-prompt "$rule")
  pi "${args[@]}" "$task" </dev/null > "$D/out/$name.txt" 2> "$D/out/$name.err" ;;
codex)
  p=$task; [ "$arm" = rule ] && p="The following project rules apply to this task.

$(cat "$rule")

---
Task: $task"
  codex exec --skip-git-repo-check --ephemeral -s read-only -C "$scratch" -o "$D/out/$name.txt" "$p" </dev/null > "$D/out/$name.log" 2>&1 ;;
esac
rm -rf "$scratch"
