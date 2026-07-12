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

# --- a missing registry fails loudly, not silently empty ------------------
# set -e does NOT observe jq failing inside `< <(...)` process substitution,
# so a missing/malformed registry once yielded an empty list and exit 0 —
# the ownership loop then ran zero iterations while the script reported "Done".
if missing_out="$(HOME="$FAKE_HOME" PROJECTS_JSON="$TMP/does-not-exist.json" bash "$SCRIPT" --list 2>/dev/null)"; then
    missing_rc=0
else
    missing_rc=$?
fi
if (( missing_rc != 0 )) && [ -z "$missing_out" ]; then
    echo "PASS: missing registry exits non-zero with no derived dirs"
else
    echo "FAIL: missing registry should exit non-zero (got rc=$missing_rc, out=[$missing_out])"
    fail=1
fi

# --- a malformed-JSON registry also fails loudly --------------------------
BAD_REG="$TMP/malformed.json"
printf 'not valid json {[' > "$BAD_REG"
if malformed_out="$(HOME="$FAKE_HOME" PROJECTS_JSON="$BAD_REG" bash "$SCRIPT" --list 2>/dev/null)"; then
    malformed_rc=0
else
    malformed_rc=$?
fi
if (( malformed_rc != 0 )) && [ -z "$malformed_out" ]; then
    echo "PASS: malformed registry exits non-zero with no derived dirs"
else
    echo "FAIL: malformed registry should exit non-zero (got rc=$malformed_rc, out=[$malformed_out])"
    fail=1
fi

# --- a valid but empty registry [] is legitimate, not an error ------------
EMPTY_REG="$TMP/empty.json"
printf '[]' > "$EMPTY_REG"
if empty_out="$(HOME="$FAKE_HOME" PROJECTS_JSON="$EMPTY_REG" bash "$SCRIPT" --list 2>/dev/null)"; then
    empty_rc=0
else
    empty_rc=$?
fi
if (( empty_rc == 0 )) && [ -z "$empty_out" ]; then
    echo "PASS: empty registry [] exits 0 with no derived dirs"
else
    echo "FAIL: empty registry [] should exit 0 with empty output (got rc=$empty_rc, out=[$empty_out])"
    fail=1
fi

# --- the MUTATING entry point (no --list) aborts on a bad registry --------
# Round-2 gate finding on PR #500: the fix inside derive_project_dirs was
# swallowed again at the call site `mapfile -t PROJECTS < <(derive_project_dirs)`
# — the child's exit 1 never reaches the parent, PROJECTS goes empty, and the
# ownership step no-ops behind a clean "Done." Run the real path with a stub
# sudo first on PATH (never touch the system; on CI sudo is passwordless, so an
# unstubbed run would REALLY mutate) and assert: non-zero exit, the derive
# error on stderr, and zero sudo invocations.
STUBDIR="$TMP/bin"
mkdir -p "$STUBDIR"
SUDO_LOG="$TMP/sudo-calls.log"
: > "$SUDO_LOG"
cat > "$STUBDIR/sudo" <<STUB
#!/usr/bin/env bash
echo "\$*" >> "$SUDO_LOG"
exit 99
STUB
chmod +x "$STUBDIR/sudo"

set +e
mutate_err="$(PATH="$STUBDIR:$PATH" HOME="$FAKE_HOME" \
    PROJECTS_JSON="$TMP/does-not-exist.json" bash "$SCRIPT" 2>&1 >/dev/null)"
mutate_rc=$?
set -e
mutate_ok=1
(( mutate_rc != 0 )) || { echo "  mutating path exited 0 on a bad registry"; mutate_ok=0; }
grep -q "failed to read registry" <<< "$mutate_err" \
    || { echo "  no derive error on stderr: [$mutate_err]"; mutate_ok=0; }
[ ! -s "$SUDO_LOG" ] \
    || { echo "  sudo was invoked despite the bad registry:"; cat "$SUDO_LOG"; mutate_ok=0; }
if (( mutate_ok )); then
    echo "PASS: mutating entry point aborts on a bad registry before any sudo"
else
    echo "FAIL: bad registry must abort the mutating path before any sudo"
    fail=1
fi

if (( fail )); then
    exit 1
fi
echo "PASS: setup-claude-agent.sh --list derives expanded, intact project dirs"
