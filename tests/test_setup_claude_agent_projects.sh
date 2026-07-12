#!/usr/bin/env bash
# Tests for scripts/setup-claude-agent.sh --list: the project-dir derivation
# must read scripts/projects.json (the canonical registry), expand a leading
# ~ to $HOME, keep paths with spaces intact, and exclude the harness itself
# (it gets read-only ACL treatment, not group ownership).
set -euo pipefail

cd "$(dirname "$0")/.."
SCRIPT="$PWD/scripts/setup-claude-agent.sh"
fail=0

# Build a throwaway HOME + fixture registry, run `--list`, capture stdout.
_derive() {
    local home="$1" registry="$2"
    HOME="$home" PROJECTS_JSON="$registry" bash "$SCRIPT" --list
}

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
FAKE_HOME="$TMP/home"
mkdir -p "$FAKE_HOME"
REG="$TMP/projects.json"
cat > "$REG" <<'JSON'
[
  { "name": "harness", "path": "~/.claude" },
  { "name": "plain", "path": "~/CNRS/code/plain" },
  { "name": "spaced", "path": "~/CNRS/papiers/actif/Fuzzy Corpus" }
]
JSON

mapfile -t OUT < <(_derive "$FAKE_HOME" "$REG")

# --- harness (~/.claude) is excluded --------------------------------------
if printf '%s\n' "${OUT[@]}" | grep -qx "$FAKE_HOME/.claude"; then
    echo "FAIL: harness path should be excluded from the group-ownership list"
    fail=1
else
    echo "PASS: harness path excluded"
fi

# --- leading ~ expanded to \$HOME -----------------------------------------
if printf '%s\n' "${OUT[@]}" | grep -qx "$FAKE_HOME/CNRS/code/plain"; then
    echo "PASS: leading ~ expanded to \$HOME"
else
    echo "FAIL: expected expanded path $FAKE_HOME/CNRS/code/plain in output:"
    printf '  %s\n' "${OUT[@]}"
    fail=1
fi
# no unexpanded tilde survives
if printf '%s\n' "${OUT[@]}" | grep -q '~'; then
    echo "FAIL: an unexpanded ~ leaked into the output"
    fail=1
else
    echo "PASS: no unexpanded ~ in output"
fi

# --- path with a space stays a single intact element ----------------------
found_spaced=0
for p in "${OUT[@]}"; do
    if [[ "$p" == "$FAKE_HOME/CNRS/papiers/actif/Fuzzy Corpus" ]]; then
        found_spaced=1
    fi
done
if (( found_spaced )); then
    echo "PASS: spaced path preserved as one element"
else
    echo "FAIL: spaced path was split or lost; output was:"
    printf '  [%s]\n' "${OUT[@]}"
    fail=1
fi

# --- exactly the two non-harness entries, no more, no fewer ---------------
if (( ${#OUT[@]} == 2 )); then
    echo "PASS: derived exactly the 2 non-harness project dirs"
else
    echo "FAIL: expected 2 derived dirs, got ${#OUT[@]}"
    fail=1
fi

if (( fail )); then
    exit 1
fi
echo "PASS: setup-claude-agent.sh --list derives expanded, intact project dirs"
