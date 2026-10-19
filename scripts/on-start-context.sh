#!/bin/bash
set -euo pipefail
# Session-start context printer: stdout becomes conversation context. It has no
# side effects; the repository-mutating half is on-start-sync.sh. Claude Code runs
# it at every SessionStart; another runtime may call it too (ticket 1122), so the Claude-specific
# lines below are guarded by _claude and stay silent elsewhere.
#
# NOTE: a project's non-secret .env settings reach bash subprocesses via BASH_ENV
# (settings.json → env.BASH_ENV → scripts/bash-env.sh), which strict-parses them
# and loads no credential: consumers read ~/.config/keys at point of use (0945).
# Do NOT use CLAUDE_ENV_FILE either: it inlines KEY=VALUE in argv, leaking to ps -ef.

# Claude Code's hook runner sets CLAUDE_PROJECT_DIR; its absence means another
# runtime (or a bare shell) called this script.
_claude=${CLAUDE_PROJECT_DIR:+1}

# Decision (ticket 1122): the blocks below keyed on CLAUDE_PROJECT_DIR alone
# stay Claude-only, with no working-directory fallback. The coherence prompt and
# resident census describe Claude's .claude/ loading and "worktree entry"; the
# memory index is already reached from AGENTS.md ("read memory/MEMORY.md at
# task start") in Codex and Pi; the sync report has no producer without the
# post-cutoff sync, and that sync plus `core.hooksPath` mutate repository state,
# which needs a runtime-given project root, not a guessed working directory.
# Codex and Pi get the runtime-neutral lines: host, disk, loader, ticket counts.

# Worktree instruction (it cites rules/claude-code.md) — Claude Code only, and
# skipped in automated night-sweep runs
if [[ -n "$_claude" && -z "${CLAUDE_NIGHT_SWEEP:-}" ]]; then
    echo "Worktree isolation is enabled for this project: code, data and configuration are worked in the conversation's own worktree, created with plain git and entered by cd before anything else (rules/claude-code.md § Entering the session); manuscript prose in a paper repo is edited in place in the author's checkout (rules/git.md § Prose workpackages). A session opening on /hunt triages the ticket first (skills/hunt/SKILL.md)."
fi

echo "Running on host: $(hostname -s)"

# Show low disk headroom before the rest of the startup context is assembled.
# This is advisory: failure to inspect storage is visible, but never blocks.
_disk_output=$(python3 "$(dirname "$0")/tmp_report.py" --disk-warning 2>&1) || {
    echo "Disk headroom probe unavailable; check /tmp and /home manually."
    _disk_output=""
}
if [ -n "$_disk_output" ]; then
    printf '%s\n' "$_disk_output"
fi

# Surface the effort setting for the session's self-presentation line
# (rules/workflow.md § Session Start): the model knows its own name but has
# no other channel to the effortLevel setting. Read the live user settings,
# not a checkout copy. The file is Claude Code's, so only Claude Code reads it.
if [ -n "$_claude" ]; then
    _effort=$(jq -r '.effortLevel // empty' "$HOME/.claude/settings.json" 2>/dev/null) || _effort=""
    echo "Session effort level (settings.json effortLevel): ${_effort:-unknown}"
fi

_script_dir="$(cd "$(dirname "$0")" && pwd)"

# Ask for a project-level coherence pass only when the project has its own
# directives. The helper prints a short instruction; it does not try to infer
# semantic conflicts from matching words or delay startup with a model call.
if [ -n "${CLAUDE_PROJECT_DIR:-}" ]; then
    "$_script_dir/prompt-project-coherence.sh" "$CLAUDE_PROJECT_DIR" || true
fi

# Check the harness loader (ticket 0983) is in the user's shell config: its
# refusing stubs stay in place unless shell-init.sh loads fully, so a missing
# or broken checkout cannot leave the runtimes unwrapped. A bare `source`
# line would skip silently. `_idh_refuse` marks the current block;
# `_idh_unreachable` marks the round-1 block still installed until the
# post-merge refresh (tests/test_projection_validator.py pins both).
if ! grep -qlE "_idh_refuse|_idh_unreachable" "$HOME/.bashrc" "$HOME/.zshrc" 2>/dev/null; then
    echo "SETUP REMINDER: the harness loader is not in your shell config. Run ${_script_dir%/scripts}/bin/idh install (it writes $_script_dir/bashrc-loader.sh into ~/.bashrc; remove any bare shell-init.sh source line)."
fi

# The harness-rules index is NOT cat-ed here: the runtime already loads every
# `~/.claude/rules/**.md` into the system prompt (mechanism isolated
# 2026-09-09, see rules/README.md), so cat-ing the index served a second copy
# of a file that was already resident. An adapter on a runtime without that
# auto-load is what must inject it — that is the adapter's job, not this
# hook's (tickets 0800, 0802).

# Inject the harness memory index only into sessions whose project is this
# harness repository (or one of its worktrees). Until the v8 pilot (ticket
# 0920) this cat-ed the index into every Claude Code session, including
# unrelated projects — cross-project pooling that v8's project-local scope
# retires here; another project's memory belongs to its own AGENTS.md.
# Still budgeted by the resident census (hook channel).
if [ -n "${CLAUDE_PROJECT_DIR:-}" ]; then
    _mem_gcd=$(git -C "$CLAUDE_PROJECT_DIR" rev-parse --path-format=absolute --git-common-dir 2>/dev/null) || _mem_gcd=""
    _mem_harness=$(git -C "$_script_dir/.." rev-parse --path-format=absolute --git-common-dir 2>/dev/null) || _mem_harness=""
    if [ -n "$_mem_gcd" ] && [ "$_mem_gcd" = "$_mem_harness" ]; then
        cat "$_script_dir/../memory/MEMORY.md" 2>/dev/null || true
    fi
fi

# Live ticket counts, computed now (ticket 1121): STATE.md stores no derived
# number, so the session sees the counts without a committed copy that every
# ticket close makes stale. Runtime-neutral: the project is the working
# directory when CLAUDE_PROJECT_DIR is unset. Local erg only, no forge call;
# silent when the project has no tickets/ or erg, or when erg fails.
_proj=${CLAUDE_PROJECT_DIR:-$PWD}
if [ -d "$_proj/tickets" ] && [ -x "$_proj/tickets/erg" ]; then
    _ready=$(cd "$_proj" && timeout 10 tickets/erg ready tickets/ 2>/dev/null \
        | sed -nE -e 's/^Ready tickets \(([0-9]+)\):?$/\1/p' \
                  -e 's/^No ready tickets found\.$/0/p') || _ready=""
    _open=$(cd "$_proj" && timeout 10 tickets/erg list tickets/ 2>/dev/null \
        | sed -nE -e 's/^Open tickets \(([0-9]+)\):?$/\1/p' \
                  -e 's/^No open tickets found\.$/0/p') || _open=""
    if [ -n "$_ready" ] && [ -n "$_open" ]; then
        echo "Live ticket counts at session start: ${_open} open, ${_ready} ready (\`tickets/erg ready tickets/\` lists the ready ones; STATE.md stores no counts)."
    fi
fi

# Surface the previous session start's local-main sync report when it needed
# attention (dirty overlap, divergence, refusal). A clean fast-forward — and a
# routine offline "fetch failed — skipped" — stays silent: only the outcomes
# that need a human decision reach the conversation. (ticket 0277)
if [ -n "${CLAUDE_PROJECT_DIR:-}" ]; then
    _gcd=$(git -C "$CLAUDE_PROJECT_DIR" rev-parse --path-format=absolute --git-common-dir 2>/dev/null) || _gcd=""
    _sync_report="${_gcd:+$_gcd/sync-local-main.last}"
    if [ -n "$_sync_report" ] && [ -f "$_sync_report" ] \
       && grep -qE 'untouched|diverged|refused' "$_sync_report" 2>/dev/null; then
        echo "Local-main sync (previous session start): $(cat "$_sync_report")"
    fi
fi
