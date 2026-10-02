#!/usr/bin/env bash
# Tests for scripts/memory-capture.sh — the pinned encrypted-in-repo capture
# helper (ticket 0988). Disposable HOME throughout: the per-project key must
# never touch real user state, and key derivation is asserted across
# transports. Skips visibly when age is not installed.
set -euo pipefail

cd "$(dirname "$0")/.."
REPO="$PWD"
CAPTURE="$REPO/scripts/memory-capture.sh"

fail=0
SANDBOX=$(mktemp -d)
trap 'rm -rf "$SANDBOX"' EXIT

export HOME="$SANDBOX/home"
mkdir -p "$HOME"
export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_SYSTEM=/dev/null
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t

if command -v age >/dev/null 2>&1 && command -v age-keygen >/dev/null 2>&1; then
    HAVE_AGE=1
else
    HAVE_AGE=0
    echo "SKIP: age not installed — capture suites cannot run"
fi

_pass() { echo "PASS: $1"; }
_fail() { echo "FAIL: $1"; fail=1; }

DATE=$(date +%Y-%m-%d)
YEAR=$(date +%Y)

# A throwaway project repository with an origin remote (needed for key
# derivation). Args: <name> <origin-url> → sets $P.
_mkproject() {
    local name=$1 url=$2
    P="$SANDBOX/$name"
    git init --quiet --initial-branch=main "$P"
    git -C "$P" remote add origin "$url"
    (cd "$P" && git commit --quiet --allow-empty -m seed)
}

count_keys() { find "$HOME/.config/keys/memory" -name '*.age' -type f 2>/dev/null | wc -l; }

# ---------------------------------------------------------------------------
if [ "$HAVE_AGE" = 1 ]; then

# public: plaintext Markdown at the dated journal path, exact bytes.
_mkproject pub https://example.com/Owner/Proj.git
PUB="$P"
printf 'public entry text\nline two\n' | "$CAPTURE" "$P" public note-one >/dev/null
ENTRY="$P/memory/journal/$YEAR/$DATE-note-one.md"
if [ -f "$ENTRY" ] && [ "$(cat "$ENTRY")" = "$(printf 'public entry text\nline two\n')" ]; then
    _pass "public entry written as dated plaintext Markdown"
else
    _fail "public entry missing or bytes altered"
fi
if [ "$(count_keys)" = 0 ]; then
    _pass "public capture derives no key"
else
    _fail "public capture created a key"
fi

# private: .age ciphertext, decryptable with the derived key, plaintext
# nowhere in the tree.
SECRET_TEXT='private entry text, not cleared for the public audience'
printf '%s\n' "$SECRET_TEXT" | "$CAPTURE" "$P" private note-two >/dev/null
CIPHER="$P/memory/journal/$YEAR/$DATE-note-two.age"
KEY=$(find "$HOME/.config/keys/memory" -name '*.age' -type f | head -1)
if [ -f "$CIPHER" ] && [ "$(count_keys)" = 1 ]; then
    _pass "private entry written as .age ciphertext, one per-project key"
else
    _fail "private entry or key missing"
fi
if [ "$(age -d -i "$KEY" "$CIPHER")" = "$SECRET_TEXT" ]; then
    _pass "private entry decrypts to the captured text"
else
    _fail "private entry does not decrypt"
fi
if grep -rFq "$SECRET_TEXT" "$P" --exclude='*.age'; then
    _fail "private plaintext leaked into the tree"
else
    _pass "private plaintext never in the tree"
fi
if [ "$(stat -c %a "$KEY")" = 600 ]; then
    _pass "key created mode 600"
else
    _fail "key mode is not 600"
fi

# key selection: same project over another transport and case → same key.
_mkproject alt git@Example.com:Owner/Proj.git
printf 'alt transport entry\n' | "$CAPTURE" "$P" private note-three >/dev/null
if [ "$(count_keys)" = 1 ]; then
    _pass "key selection is stable across transports and case"
else
    _fail "transport/case variant derived a different key"
fi

# key selection: a different project → its own key.
_mkproject other https://example.com/other/proj.git
printf 'other project entry\n' | "$CAPTURE" "$P" private note-four >/dev/null
if [ "$(count_keys)" = 2 ]; then
    _pass "a different project derives its own key"
else
    _fail "different projects share or lose keys"
fi

# key selection: default ports are stripped — ssh://host:22 and ssh://host,
# https://host:443 and https://host derive the same key.
_mkproject ports ssh://git@port.example.com:22/owner/proj.git
printf 'explicit default port entry\n' | "$CAPTURE" "$P" private note-ports >/dev/null
KEYS_AFTER_22=$(count_keys)
_mkproject ports-noport ssh://git@port.example.com/owner/proj.git
printf 'implicit default port entry\n' | "$CAPTURE" "$P" private note-ports >/dev/null
KEYS_AFTER_NO=$(count_keys)
_mkproject ports-https https://Port.Example.com:443/owner/proj.git
printf 'https default port entry\n' | "$CAPTURE" "$P" private note-ports >/dev/null
KEYS_AFTER_443=$(count_keys)
if [ "$KEYS_AFTER_22" = 3 ] && [ "$KEYS_AFTER_NO" = 3 ] && [ "$KEYS_AFTER_443" = 3 ]; then
    _pass "default ports (22, 443) stripped in key derivation"
else
    _fail "default-port variants derived different keys ($KEYS_AFTER_22/$KEYS_AFTER_NO/$KEYS_AFTER_443)"
fi

# key selection: a non-default port participates in project identity (documented).
_mkproject ports-2222 ssh://git@port.example.com:2222/owner/proj.git
printf 'non-default port entry\n' | "$CAPTURE" "$P" private note-ports >/dev/null
if [ "$(count_keys)" = 4 ]; then
    _pass "non-default port keeps a distinct project identity"
else
    _fail "non-default port did not derive its own key"
fi

# key selection: a non-default port and a same-named path segment are distinct
# origins — host:2222/path (SSH port) must not share a key with host/2222/path.
_mkproject ports-pathseg https://port.example.com/2222/owner/proj.git
printf 'path-segment 2222 entry\n' | "$CAPTURE" "$P" private note-ports >/dev/null
if [ "$(count_keys)" = 5 ]; then
    _pass "port-carrying and slash-carrying origins derive distinct keys"
else
    _fail "port-carrying and slash-carrying origins share a key"
fi

# first private capture stays silent: age-keygen's public-key banner must not
# reach the caller's stderr on success.
_mkproject quiet git@quiet.example.com:owner/proj.git
ERR_TEXT=$(printf 'quiet capture entry\n' | "$CAPTURE" "$P" private note-quiet 2>&1 >/dev/null)
if printf '%s\n' "$ERR_TEXT" | grep -q "Public key"; then
    _fail "first private capture leaked the age-keygen banner to stderr"
else
    _pass "first private capture is stderr-silent"
fi

# a failed key creation surfaces age-keygen's stderr in full, not just the
# refusal line: a read-only key directory makes age-keygen fail inside the
# capture helper. Root ignores mode 0555, so the injection only works
# unprivileged — skip visibly rather than report a false failure as root.
if [ "$(id -u)" = 0 ]; then
    echo "SKIP: running as root — mode-0555 injection cannot deny key creation"
else
    _mkproject failing git@failing.example.com:owner/proj.git
    mkdir -p "$HOME/.config/keys/memory" && chmod 555 "$HOME/.config/keys/memory"
    FAIL_TEXT=$(printf 'doomed entry\n' | "$CAPTURE" "$P" private note-doomed 2>&1 >/dev/null) || true
    FAIL_RC=0
    printf 'doomed entry\n' | "$CAPTURE" "$P" private note-doomed >/dev/null 2>&1 || FAIL_RC=$?
    chmod 755 "$HOME/.config/keys/memory"
    if [ "$FAIL_RC" -ne 0 ] && [ -n "$FAIL_TEXT" ] \
       && printf '%s\n' "$FAIL_TEXT" | grep -qv "memory-capture:"; then
        _pass "failed key creation surfaces age-keygen's own stderr"
    else
        _fail "failed key creation did not surface age-keygen stderr (rc=$FAIL_RC)"
    fi
fi


# append-only: capturing the same slug on the same day is refused, the
# original entry untouched.
if printf 'second write\n' | "$CAPTURE" "$PUB" public note-one >/dev/null 2>&1; then
    _fail "overwriting an existing entry was allowed"
else
    if [ "$(cat "$ENTRY")" = "$(printf 'public entry text\nline two\n')" ]; then
        _pass "existing entry refused and left untouched"
    else
        _fail "refused capture altered the existing entry"
    fi
fi

# invalid inputs: bad audience, bad slug, not a repository.
if printf 'x\n' | "$CAPTURE" "$P" secret note-five >/dev/null 2>&1; then
    _fail "invalid audience accepted"
else
    _pass "invalid audience refused"
fi
if printf 'x\n' | "$CAPTURE" "$P" public 'bad/slug' >/dev/null 2>&1; then
    _fail "invalid slug accepted"
else
    _pass "invalid slug refused"
fi
if printf 'x\n' | "$CAPTURE" "$SANDBOX/not-a-repo" public note >/dev/null 2>&1; then
    _fail "non-repository accepted"
else
    _pass "non-repository refused"
fi

else
    echo "SKIP: all capture assertions need age"
fi

if [ "$fail" -eq 0 ]; then
    echo "ALL PASS: memory-capture helper"
fi
exit $fail
