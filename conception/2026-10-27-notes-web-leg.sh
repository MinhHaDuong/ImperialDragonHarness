#!/usr/bin/env bash
# Ticket 1277, transport trial, web legs (ChatGPT Work, Claude Code Web).
# Run inside a clone of MinhHaDuong/ImperialDragonHarness in the web environment:
#   bash conception/2026-10-27-notes-web-leg.sh <env-name>
# Push needs a credential the environment already has, or GH_TOKEN set to a
# narrow token. The script never prints a credential. It touches only the
# throwaway ref refs/notes/idh-trial-1277-web and deletes it at the end.
# No -e or pipefail: each check must report FAIL and the script must reach cleanup.
set -u
env_name="${1:-unnamed}"
ref="refs/notes/idh-trial-1277-web"
head="$(git rev-parse origin/main 2>/dev/null || git rev-parse HEAD)"
pass() { printf 'PASS %s\n' "$1"; }
fail() { printf 'FAIL %s: %s\n' "$1" "$2"; }

if [ -n "${GH_TOKEN:-}" ] && command -v gh >/dev/null 2>&1; then
    git config credential.helper '!gh auth git-credential'
fi

# 1. A plain clone carries no notes; an explicit refspec fetches them.
if git fetch -q origin '+refs/notes/gate:refs/notes/gate' 2>/dev/null \
    && git notes --ref=gate list | head -1 | grep -q .; then
    pass "fetch-notes (refs/notes/gate readable)"
else
    fail "fetch-notes" "could not fetch or read refs/notes/gate"
fi

# 2. Publish a note on origin/main's tip under the throwaway ref.
git notes --ref="$ref" add -f -m "trial 1277 web leg: env=$env_name time=$(date -u +%FT%TZ)" "$head" 2>/dev/null
if git push -q origin "$ref:$ref" 2>/dev/null; then
    pass "push-notes"
else
    fail "push-notes" "push of $ref refused or no credential"
fi

# 3. Verify the publication from the remote before the session ends.
remote_sha="$(git ls-remote origin "$ref" 2>/dev/null | cut -f1)"
local_sha="$(git rev-parse -q --verify "$ref" 2>/dev/null)"
if [ -n "$remote_sha" ] && [ "$remote_sha" = "$local_sha" ]; then
    pass "verify-published (remote holds $remote_sha)"
else
    fail "verify-published" "remote=${remote_sha:-none} local=${local_sha:-none}"
fi

# 4. Persistence: say whether an earlier run of this script left a marker here.
marker="$(git rev-parse --git-dir)/idh-trial-1277-web.marker"
if [ -f "$marker" ]; then
    pass "persistence (clone survived since $(cat "$marker"))"
else
    printf 'INFO persistence: first run in this clone; run again in a later session to test\n'
    date -u +%FT%TZ > "$marker"
fi

# Cleanup: delete the throwaway ref remotely and locally.
git push -q origin ":$ref" 2>/dev/null && printf 'INFO cleanup: remote ref deleted\n' \
    || printf 'INFO cleanup: remote ref not deleted (none pushed, or refused)\n'
git update-ref -d "$ref" 2>/dev/null || true
printf 'DONE env=%s git=%s\n' "$env_name" "$(git --version | cut -d' ' -f3)"
