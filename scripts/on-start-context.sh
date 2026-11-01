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
    echo "Worktree isolation is enabled for this project: code, data and configuration are worked in the conversation's own worktree, created with plain git and entered by cd before anything else (rules/workflow.md § Session start); manuscript prose in a paper repo is edited in place in the author's checkout (rules/prose/workpackages.md). A session opening on /hunt plans the ticket first (skills/hunt/SKILL.md)."
fi

# Standing authorization for model-service transmissions (author, 2026-10-23;
# provenance in memory/journal/2026/). Printed on every runtime and in every
# project: the hook reaches Claude, Codex and Pi alike, where the resident rules
# have no room left and reach Claude only. Whether a runtime's managed approval
# reviewer reads session context is not established.
echo "Model-service transmissions are authorized by the user: sending the documents a requested task needs to Claude (Anthropic), Codex (OpenAI) or OpenRouter, through their authenticated routes, needs no renewed confirmation. Explicit local-only and confidentiality restrictions still apply; material kept encrypted or local needs separate clearance; credentials never enter prompts; no unrelated publication, messages to people or spend beyond what the task agreed. Runtime-managed approval controls stay in force: a refusal is reported, never bypassed."

_host=$(uname -n)
echo "Running on host: ${_host%%.*}"

# Show low disk headroom before the rest of the startup context is assembled.
# This is advisory: failure to inspect storage is visible, but never blocks.
_disk_output=$(python3 "$(dirname "$0")/tmp_report.py" --disk-warning 2>&1) || {
    echo "Disk headroom probe unavailable; /tmp and /home headroom is unchecked."
    _disk_output=""
}
if [ -n "$_disk_output" ]; then
    printf '%s\n' "$_disk_output"
fi

# Editor autosave (author ruling 2026-11-01, rules/git.md § Branch and commit):
# agents edit files the author may have open in the primary checkout, and an
# unsaved buffer is invisible to them. Silent when VS Code's user settings are
# absent or set an autosave mode other than off, and in night sweeps (no
# author). A grep, not a JSON parse: settings.json is JSONC; whole-line `//`
# comments are dropped first so a commented-out setting reads as off (trailing
# and /* */ comments, and language-scoped settings, still read as on). Linux stable VS
# Code path only: macOS, Insiders, VSCodium and Remote-SSH stay silent.
_vsc="${XDG_CONFIG_HOME:-$HOME/.config}/Code/User/settings.json"
if [ -f "$_vsc" ] && [ -z "${CLAUDE_NIGHT_SWEEP:-}" ] &&
    ! grep -qE '"files\.autoSave"[[:space:]]*:[[:space:]]*"(afterDelay|onFocusChange|onWindowChange)"' \
        <<<"$(grep -vE '^[[:space:]]*//' "$_vsc")"; then
    echo "VS Code autosave is off on this host: an agent editing a file the author has open cannot see unsaved changes. Setting \"files.autoSave\": \"afterDelay\" in $_vsc closes that gap. The session offers once to set it for the author, waits for the answer, and edits that file only on a yes."
fi

_script_dir="$(cd "$(dirname "$0")" && pwd)"

# Resident-text budget for the project's own directives (0971): the zero-LLM
# census prints one declarative line when the project is over budget or declares
# a catch-all `paths:`. The harness and its linked worktrees are skipped: their
# resident text is gated by the harness tests. The guard fails closed: it runs
# the census only when the harness git-common-dir is readable and differs from
# the project's, so an error never reads as "not the harness".
if [ -n "$_proj" ] && [ -d "$_proj" ]; then
    _harness=$(cd "$_script_dir/.." && pwd -P) || _harness=""
    _pdir=$(cd "$_proj" && pwd -P 2>/dev/null) || _pdir=""
    _hgit=$(git -C "$_harness" rev-parse --path-format=absolute --git-common-dir 2>/dev/null || true)
    _pgit=$(git -C "$_pdir" rev-parse --path-format=absolute --git-common-dir 2>/dev/null || true)
    if [ -n "$_pdir" ] && [ -n "$_harness" ] && [ "$_pdir" != "$_harness" ] && [ -n "$_hgit" ] && [ "$_pgit" != "$_hgit" ]; then
        python3 "$_script_dir/resident_census.py" --project "$_pdir" --warn 2>/dev/null || true
    fi
fi

# Remind when the harness loader is missing from the shell config. A bare
# `source` line would skip silently if the checkout broke; the loader's refusing
# stubs do not. `_idh_refuse` and `_idh_unreachable` are the two marker names
# an installed block carries.
if ! grep -qE "_idh_refuse|_idh_unreachable" "$HOME/.bashrc" "$HOME/.zshrc" 2>/dev/null; then
    echo "Setup gap: the harness loader is not in the shell config. ${_script_dir%/scripts}/bin/idh install writes $_script_dir/bashrc-loader.sh into ~/.bashrc and fixes it; a bare shell-init.sh source line is to be removed."
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
