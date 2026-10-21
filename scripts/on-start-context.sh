#!/bin/bash
set -euo pipefail
# Session-start context printer: stdout becomes conversation context, and the
# script has no side effects (repository upkeep is on-start-sync.sh). Claude
# Code, Codex and Pi all run it. Lines keyed on CLAUDE_PROJECT_DIR, which only
# Claude Code's hook runner sets, stay silent elsewhere: they describe Claude's
# .claude/ loading, and no runtime-given project root means no guessing one.
# Do not use CLAUDE_ENV_FILE here: it inlines KEY=VALUE in argv, visible in ps.

# Empty outside Claude Code; the Claude-only blocks test it.
_proj=${CLAUDE_PROJECT_DIR:-}

# Worktree instruction: Claude Code only, skipped in automated night sweeps.
if [[ -n "$_proj" && -z "${CLAUDE_NIGHT_SWEEP:-}" ]]; then
    echo "Worktree isolation is enabled for this project: code, data and configuration are worked in the conversation's own worktree, created with plain git and entered by cd before anything else (rules/claude-code.md § Entering the session); manuscript prose in a paper repo is edited in place in the author's checkout (rules/prose/workpackages.md). A session opening on /hunt triages the ticket first (skills/hunt/SKILL.md)."
fi

_host=$(uname -n)
echo "Running on host: ${_host%%.*}"

# Show low disk headroom before the rest of the startup context is assembled.
# This is advisory: failure to inspect storage is visible, but never blocks.
_disk_output=$(python3 "$(dirname "$0")/tmp_report.py" --disk-warning 2>&1) || {
    echo "Disk headroom probe unavailable; check /tmp and /home manually."
    _disk_output=""
}
if [ -n "$_disk_output" ]; then
    printf '%s\n' "$_disk_output"
fi

_script_dir="$(cd "$(dirname "$0")" && pwd)"

# Ask for a project-level coherence pass only when the project has its own
# directives. The helper prints a short instruction; it does not try to infer
# semantic conflicts from matching words or delay startup with a model call.
if [ -n "$_proj" ]; then
    "$_script_dir/prompt-project-coherence.sh" "$_proj" || true
fi

# Remind when the harness loader is missing from the shell config. A bare
# `source` line would skip silently if the checkout broke; the loader's refusing
# stubs do not. `_idh_refuse` and `_idh_unreachable` are the two marker names
# an installed block carries.
if ! grep -qE "_idh_refuse|_idh_unreachable" "$HOME/.bashrc" "$HOME/.zshrc" 2>/dev/null; then
    echo "SETUP REMINDER: the harness loader is not in your shell config. Run ${_script_dir%/scripts}/bin/idh install (it writes $_script_dir/bashrc-loader.sh into ~/.bashrc; remove any bare shell-init.sh source line)."
fi

# Live ticket counts, computed now so STATE.md need not store them. The project
# is the working directory when there is no project root. Local erg only, no
# forge call; silent when the project has no tickets/ or erg, or when erg fails.
_tmo="timeout 10"
if [ -x "${_proj:-.}/tickets/erg" ]; then
    _ready=$(cd "${_proj:-.}" && $_tmo tickets/erg ready tickets/ 2>/dev/null \
        | sed -nE -e 's/^Ready tickets \(([0-9]+)\):?$/\1/p' \
                  -e 's/^No ready tickets found\.$/0/p') || _ready=""
    _open=$(cd "${_proj:-.}" && $_tmo tickets/erg list tickets/ 2>/dev/null \
        | sed -nE -e 's/^Open tickets \(([0-9]+)\):?$/\1/p' \
                  -e 's/^No open tickets found\.$/0/p') || _open=""
    if [ -n "$_ready" ] && [ -n "$_open" ]; then
        echo "Live ticket counts at session start: ${_open} open, ${_ready} ready (\`tickets/erg ready tickets/\` lists the ready ones; STATE.md stores no counts)."
    fi
fi

# Surface the previous session start's local-main sync report when it needed
# attention (dirty overlap, divergence, refusal). A clean fast-forward — and a
# routine offline "fetch failed — skipped" — stays silent: only the outcomes
# that need a human decision reach the conversation.
if [ -n "$_proj" ]; then
    # --git-common-dir is relative to -C on older git; anchor it.
    _gcd=$(git -C "$_proj" rev-parse --git-common-dir 2>/dev/null) || _gcd=""
    case "$_gcd" in /*|"") ;; *) _gcd="$_proj/$_gcd" ;; esac
    _sync_report="${_gcd:+$_gcd/sync-local-main.last}"
    if [ -n "$_sync_report" ] && [ -f "$_sync_report" ] \
       && grep -qE 'untouched|diverged|refused' "$_sync_report" 2>/dev/null; then
        echo "Local-main sync (previous session start): $(cat "$_sync_report")"
    fi
fi
