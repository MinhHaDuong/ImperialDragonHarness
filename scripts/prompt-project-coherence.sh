#!/bin/bash
set -euo pipefail
# SessionStart context: ask the model to reconcile local directives with the
# user-level harness when a project actually has local rules or skills.

project=${1:-}
[[ -d "$project" ]] || exit 0
project=$(cd "$project" && pwd -P)
harness=$(cd "$(dirname "$0")/.." && pwd -P)
[[ "$project" != "$harness" ]] || exit 0
# A linked worktree is the same harness project even though its path differs.
harness_git=$(git -C "$harness" rev-parse --path-format=absolute --git-common-dir 2>/dev/null || true)
project_git=$(git -C "$project" rev-parse --path-format=absolute --git-common-dir 2>/dev/null || true)
[[ -z "$harness_git" || "$project_git" != "$harness_git" ]] || exit 0

sources=()
for file in "$project/CLAUDE.md" "$project/AGENTS.md" \
            "$project/.claude/CLAUDE.md"; do
    [[ -f "$file" ]] && sources+=("${file#"$project"/}")
done

if [[ -d "$project/.claude/rules" ]] &&
   find "$project/.claude/rules" -type f -name '*.md' -print -quit | grep -q .; then
    sources+=(".claude/rules/")
fi
for directory in "$project/.claude/skills" "$project/.agents/skills"; do
    [[ -d "$directory" ]] || continue
    if find "$directory" -type f -name 'SKILL.md' -print -quit | grep -q .; then
        sources+=("${directory#"$project"/}/")
    fi
done

((${#sources[@]})) || exit 0
source_list=$(printf '%s, ' "${sources[@]}")
printf 'PROJECT DIRECTIVE COHERENCE: Local sources: %s. A startup coherence pass is due after worktree entry. Its scope is applicable project rules and skill descriptions against the loaded harness rules and skills: conflicting instructions, repeated procedures, and stale references. Full skill bodies are needed only where descriptions overlap. The result is concrete findings with file paths and the governing instruction, or "no actionable overlap found".\n' "${source_list%, }"
