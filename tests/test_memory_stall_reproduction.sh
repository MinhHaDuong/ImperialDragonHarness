#!/usr/bin/env bash
# Ticket 0988 — disposable-HOME reproduction of the padme memory stall.
#
# The padme case (2026-09-24..29): sessions wrote memory uncommitted into the
# harness checkout, incoming commits touched the same paths, and the nightly
# checkout update refused every night with no visible signal. This suite proves
# the exit criteria against the repo side of that nightly update,
# scripts/sync-local-main.sh — the script padme's claude-harness-pull unit runs
# for checkout update (closed ticket 0987's table); the unit itself is
# machine-local and not reproducible from here.
#
# Arms:
#   1. positive control — old-style uncommitted memory writes in a host clone
#      (3 new notes, 1 edited note, 2 index lines) plus an origin advance over
#      the same paths: today's script refuses and leaves every byte in place;
#   2. visible reporting — the refusal surfaces at session start
#      (scripts/on-start.sh re-echoes the sync report);
#   3. treatment — capture at roar commits entries on a wrap-up branch through
#      origin instead of dirtying the host: the same host fast-forwards the
#      next night, and the note set is byte-identical across the reproduction
#      (public plaintext, private .age ciphertext decryptable with the
#      per-project key, no plaintext in the tree).
#
# Skips the private-capture assertions visibly when age is not installed; the
# pull arms always run.
set -euo pipefail

cd "$(dirname "$0")/.."
REPO="$PWD"
CAPTURE="$REPO/scripts/memory-capture.sh"
SYNC="$REPO/scripts/sync-local-main.sh"
ONSTART="$REPO/scripts/on-start.sh"

fail=0
SANDBOX=$(mktemp -d)
trap 'rm -rf "$SANDBOX"' EXIT

# Disposable HOME: capture keys, settings and shell-config reads must never
# touch the real user state (the capture helper writes its per-project key
# under $HOME/.config/keys/memory).
export HOME="$SANDBOX/home"
mkdir -p "$HOME"
export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_SYSTEM=/dev/null
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t

if command -v age >/dev/null 2>&1; then
    HAVE_AGE=1
else
    HAVE_AGE=0
    echo "SKIP: age not installed — private-capture assertions will not run"
fi

_pass() { echo "PASS: $1"; }
_fail() { echo "FAIL: $1"; fail=1; }

# Byte fingerprint of every file under memory/, sorted by path. The note-set
# comparison across the reproduction: no note lost, none duplicated, none
# altered. Empty lines (paths without leading ./) are dropped by the caller.
snapshot() {
    (cd "$1" && find memory -type f -print | sort | while IFS= read -r f; do
        printf '%s  %s\n' "$(sha256sum "$f" | cut -d' ' -f1)" "$f"
    done)
}

# Seed origin: a project with a live memory surface (index, a theme, two
# journal entries) and a lagging host clone of it.
# Args: <name> → sets $ORIGIN, $HOST, $SEED_SHA
_setup() {
    local name="$1"
    ORIGIN="$SANDBOX/$name-origin.git"
    HOST="$SANDBOX/$name-host"
    local seed="$SANDBOX/$name-seed"
    git init --quiet --bare --initial-branch=main "$ORIGIN"
    git init --quiet --initial-branch=main "$seed"
    (
        cd "$seed"
        mkdir -p memory/journal/2026 memory/topics
        printf '# Project memory\n\n## Topics\n\n- [Theme](topics/theme.md)\n' > memory/MEMORY.md
        printf '# Theme\n\nConsolidated knowledge.\n' > memory/topics/theme.md
        printf 'Seed entry one.\n' > memory/journal/2026/2026-10-01-seed.md
        printf 'Seed entry two, edited by the host session.\n' > memory/journal/2026/2026-10-01-edit-me.md
        git add memory
        git commit --quiet -m "seed memory surface"
        git push --quiet "$ORIGIN" main
    )
    git clone --quiet "$ORIGIN" "$HOST"
    SEED_SHA=$(git -C "$HOST" rev-parse HEAD)
}

# ---------------------------------------------------------------------------
# Arm 1 + 2: the padme stall, today's script as positive control
# ---------------------------------------------------------------------------
_setup padme

# The host's sessions wrote memory since the last pull, uncommitted — the
# exact padme shape: three new notes, one edited note, two index lines.
mkdir -p "$HOST/memory/journal/2026"
printf 'Host session note A.\n' > "$HOST/memory/journal/2026/2026-10-02-note-a.md"
printf 'Host session note B.\n' > "$HOST/memory/journal/2026/2026-10-02-note-b.md"
printf 'Host session note C.\n' > "$HOST/memory/journal/2026/2026-10-02-note-c.md"
printf 'Seed entry two, edited by the host session. Locally edited.\n' \
    > "$HOST/memory/journal/2026/2026-10-01-edit-me.md"
printf -- '- [note a](journal/2026/2026-10-02-note-a.md)\n- [note b](journal/2026/2026-10-02-note-b.md)\n' \
    >> "$HOST/memory/MEMORY.md"

NOTES_BEFORE=$(snapshot "$HOST")

# The origin advances over the same paths (another host's merged capture PR).
(
    cd "$SANDBOX"
    git clone --quiet "$ORIGIN" padme-peer
    cd padme-peer
    printf 'Peer session note A.\n' > memory/journal/2026/2026-10-02-note-a.md
    printf 'Peer session note B.\n' > memory/journal/2026/2026-10-02-note-b.md
    printf 'Peer session note C.\n' > memory/journal/2026/2026-10-02-note-c.md
    printf 'Seed entry two, edited upstream by the peer.\n' > memory/journal/2026/2026-10-01-edit-me.md
    printf -- '- [peer note](journal/2026/2026-10-02-note-a.md)\n' >> memory/MEMORY.md
    git add memory
    git commit --quiet -m "peer capture merge touches the same memory paths"
    git push --quiet origin main
)

CONTROL_OUT=$("$SYNC" "$HOST")
if printf '%s\n' "$CONTROL_OUT" | grep -q "could not fast-forward" \
   && printf '%s\n' "$CONTROL_OUT" | grep -q "left untouched"; then
    _pass "positive control: today's script refuses the dirty-memory host"
else
    _fail "positive control: sync did not report a refusal — got: $CONTROL_OUT"
fi

# No note lost or duplicated across the refusal: the checkout ends as found.
NOTES_AFTER=$(snapshot "$HOST")
if [ "$NOTES_BEFORE" = "$NOTES_AFTER" ]; then
    _pass "refused sync left the uncommitted note set byte-identical"
else
    _fail "refused sync altered the note set"
fi

# Arm 2 — the refusal is reported where the author sees it: session start.
# on-start.sh's background eager sync writes its report to
# <git-common-dir>/sync-local-main.last; the next session start echoes it back
# when it needed attention (ticket 0277). Plant the control arm's refusal as
# that report and run a real session start against the host.
printf '%s\n' "$CONTROL_OUT" > "$HOST/.git/sync-local-main.last"
START_OUT=$(CLAUDE_PROJECT_DIR="$HOST" bash "$ONSTART")
if printf '%s\n' "$START_OUT" | grep -q "Local-main sync (previous session start)" \
   && printf '%s\n' "$START_OUT" | grep -q "left untouched"; then
    _pass "session start surfaces the unresolvable pull"
else
    _fail "session start did not surface the refusal — got: $START_OUT"
fi

# ---------------------------------------------------------------------------
# Arm 3: capture at roar — the same host fast-forwards the next night
# ---------------------------------------------------------------------------
if [ ! -x "$CAPTURE" ]; then
    _fail "treatment: capture helper $CAPTURE is missing"
elif [ "$HAVE_AGE" = 1 ]; then
    _setup roar
    DATE=$(date +%Y-%m-%d)
    YEAR=$(date +%Y)
    PUBLIC_ENTRY="memory/journal/$YEAR/$DATE-treatment-public.md"
    PRIVATE_ENTRY="memory/journal/$YEAR/$DATE-treatment-private.age"

    # The wrap-up branch/worktree roar uses: capture never touches the host
    # checkout, so nothing lands uncommitted in the pulled tree.
    WT="$SANDBOX/roar-wrapup"
    git -C "$HOST" worktree add --quiet -b wrap-up "$WT"

    printf 'Treatment public note: committed at roar on the wrap-up branch.\n' \
        | "$CAPTURE" "$WT" public treatment-public
    PRIVATE_TEXT='Treatment private note: uncleared, ciphertext from birth.'
    printf '%s\n' "$PRIVATE_TEXT" | "$CAPTURE" "$WT" private treatment-private

    # The committed note set — what the session wrote, before integration.
    NOTES_WRITTEN=$(snapshot "$WT")
    if printf '%s\n' "$NOTES_WRITTEN" | grep -q "treatment-private.age" \
       && [ ! -e "$WT/$PRIVATE_ENTRY.plain" ]; then
        _pass "private entry committed as .age ciphertext"
    else
        _fail "private entry did not land as .age ciphertext"
    fi
    if grep -rFq "$PRIVATE_TEXT" "$WT" --exclude='*.age'; then
        _fail "private plaintext leaked into the wrap-up tree"
    else
        _pass "private plaintext never in the wrap-up tree"
    fi

    # One branch, one bundled PR: commit the bundle, push, merge through origin.
    git -C "$WT" add memory
    git -C "$WT" commit --quiet -m "roar wrap-up: capture journal entries (0988)"
    git -C "$WT" push --quiet origin wrap-up
    (
        cd "$SANDBOX"
        git clone --quiet "$ORIGIN" roar-forge
        cd roar-forge
        git fetch --quiet origin wrap-up
        git merge --quiet --no-ff -m "Merge pull request #N from wrap-up" FETCH_HEAD
        git push --quiet origin main
    )

    # The next night's pull on the same host: clean tree, capture integrated.
    TREAT_OUT=$("$SYNC" "$HOST")
    if printf '%s\n' "$TREAT_OUT" | grep -q "fast-forwarded"; then
        _pass "treatment: the host fast-forwards the next night"
    else
        _fail "treatment: sync did not fast-forward — got: $TREAT_OUT"
    fi

    # Byte comparison across the reproduction: what was committed is what the
    # host now carries — nothing lost, duplicated or altered.
    NOTES_PULLED=$(snapshot "$HOST")
    if [ "$NOTES_WRITTEN" = "$NOTES_PULLED" ]; then
        _pass "note set byte-identical across the reproduction"
    else
        _fail "note set differs across the reproduction"
    fi

    # The pulled ciphertext is readable with the per-project key.
    KEY=$(find "$HOME/.config/keys/memory" -name '*.age' -type f | head -1)
    if [ -n "$KEY" ] && [ "$(age -d -i "$KEY" "$HOST/$PRIVATE_ENTRY")" = "$PRIVATE_TEXT" ]; then
        _pass "pulled private entry decrypts with the per-project key"
    else
        _fail "pulled private entry does not decrypt with the per-project key"
    fi
    if grep -rFq "$PRIVATE_TEXT" "$HOST" --exclude='*.age'; then
        _fail "private plaintext leaked into the pulled host tree"
    else
        _pass "private plaintext never in the pulled host tree"
    fi
    if [ -z "$(git -C "$HOST" status --porcelain)" ]; then
        _pass "host checkout clean after the pull (memory never uncommitted)"
    else
        _fail "host checkout dirty after the pull"
    fi
else
    echo "SKIP: treatment arm needs age (private capture); not installed"
fi

if [ "$fail" -eq 0 ]; then
    echo "ALL PASS: memory stall reproduction (0988)"
fi
exit $fail
