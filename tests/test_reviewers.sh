#!/usr/bin/env bash
# Tests for the /reviewers skill dispatcher (review-is-CI wiring).
# Covers: empty-roster no-op; a configured seat firing the (stubbed)
# 0217 seat-runner; per-seat fail-open; harvest normalization to the 0205
# contract shape with a WARN on unparseable input; scorecard appending a
# valid erg log line.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REVIEWERS="${REPO_ROOT}/skills/reviewers/reviewers.sh"
PASS=0; FAIL=0
WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"' EXIT

assert_eq() {
    local label="$1" expected="$2" actual="$3"
    if [ "$expected" = "$actual" ]; then echo "PASS: $label"; PASS=$((PASS+1))
    else echo "FAIL: $label"; echo "  expected: $(printf '%q' "$expected")"; echo "  actual:   $(printf '%q' "$actual")"; FAIL=$((FAIL+1)); fi
}
assert_contains() {
    local label="$1" needle="$2" hay="$3"
    # Pure-bash substring match, no subprocess: the quoted needle is a literal
    # (glob-free) comparison, identical to `grep -F`. Supersedes the here-string
    # `grep -qF <<<` form — a per-call grep subprocess reading a here-string
    # tmpfile intermittently returned no-match under parallel load (ticket 0329);
    # the bash builtin has neither pipe nor tmpfile.
    if [[ "$hay" == *"$needle"* ]]; then echo "PASS: $label"; PASS=$((PASS+1))
    else echo "FAIL: $label (missing: $needle)"; echo "  in: $hay"; FAIL=$((FAIL+1)); fi
}
assert_exit_0() { local label="$1"; shift; if "$@" >/dev/null 2>&1; then echo "PASS: $label"; PASS=$((PASS+1)); else echo "FAIL: $label (exit $?)"; FAIL=$((FAIL+1)); fi; }
assert_exit_nonzero() { local label="$1"; shift; if "$@" >/dev/null 2>&1; then echo "FAIL: $label (exited 0)"; FAIL=$((FAIL+1)); else echo "PASS: $label"; PASS=$((PASS+1)); fi; }

# ── empty-roster roster (default behaviour) ──────────────────────────────────
EMPTY="$WORK/empty.yml"; printf 'reviewers: []\n' > "$EMPTY"

out=$(REVIEWERS_PANEL="$EMPTY" "$REVIEWERS" list)
assert_eq "list: empty roster" "no reviewers configured" "$out"

out=$(REVIEWERS_PANEL="$EMPTY" "$REVIEWERS" request 42)
assert_eq "request: empty roster" "no reviewers configured" "$out"
assert_exit_0 "request: empty roster exits 0" env REVIEWERS_PANEL="$EMPTY" "$REVIEWERS" request 42

out=$(REVIEWERS_PANEL="$EMPTY" "$REVIEWERS" harvest 42)
assert_eq "harvest: empty roster, empty output" "" "$out"

# ── configured roster + stub seat-runner ─────────────────────────────────────
ROSTER="$WORK/panel.yml"
cat > "$ROSTER" <<'YAML'
reviewers:
  - name: stub-good
    kind: local-model
    status: advisory
    trial-ticket: tickets/0207-agnostic-cli-reviewer-seat-one-config-op.erg
    endpoint: http://127.0.0.1:9/v1
    model: openai/stub
  - name: stub-bad
    kind: local-model
    status: advisory
    trial-ticket: tickets/0207-agnostic-cli-reviewer-seat-one-config-op.erg
    endpoint: http://127.0.0.1:9/v1
    model: openai/stub
YAML

# Stub seat-runner: 'stub-bad' (by --out basename) exits non-zero to exercise
# fail-open; everyone else emits one contract-shaped FINDING + a SUMMARY.
STUB="$WORK/seat-runner-stub.sh"
cat > "$STUB" <<'STUBEOF'
#!/usr/bin/env bash
set -euo pipefail
out=""; while [ $# -gt 0 ]; do [ "$1" = "--out" ] && { out="$2"; shift 2; continue; }; shift; done
name="$(basename "$out" .findings)"
if [ "$name" = "stub-bad" ]; then echo "stub: boom" >&2; exit 1; fi
{ echo "FINDING|severity=verifiable|file=foo.sh:10|rationale=off-by-one"; echo "SUMMARY|findings=1|verdict=revise"; } > "$out"
STUBEOF
chmod +x "$STUB"

list_out=$(REVIEWERS_PANEL="$ROSTER" "$REVIEWERS" list)
assert_contains "list: shows configured seat" "stub-good" "$list_out"

FDIR="$WORK/findings"
req_err=$(REVIEWERS_PANEL="$ROSTER" SEAT_RUNNER="$STUB" REVIEWERS_FINDINGS_DIR="$FDIR" \
          REVIEWERS_PR_BRANCH="some-branch" "$REVIEWERS" request 42 2>&1 >/dev/null)
assert_contains "request: good seat ran" "seat 'stub-good' ok" "$req_err"
assert_contains "request: bad seat fail-open WARN" "WARN seat 'stub-bad' failed" "$req_err"
assert_eq "request: good seat wrote findings" "yes" "$([ -s "$FDIR/42/stub-good.findings" ] && echo yes || echo no)"

# One seat failing beside one that ran is fail-open working, and must stay exit 0:
# the point of the aggregate check below is the absence of a verdict, never a
# minority of failures. This assertion is what stops that change going too far.
assert_exit_0 "request: a failing seat beside a good one still exits 0" \
    env REVIEWERS_PANEL="$ROSTER" SEAT_RUNNER="$STUB" REVIEWERS_FINDINGS_DIR="$FDIR" \
    REVIEWERS_PR_BRANCH="some-branch" "$REVIEWERS" request 42

# Every attempted seat failing is not a lenient verdict, it is no verdict. A caller
# gating on the exit status must be able to tell it from a clean review (0870).
ALLBAD="$WORK/allbad.yml"
cat > "$ALLBAD" <<'YAML'
reviewers:
  - name: stub-bad
    kind: cli-agent
    status: advisory
    trial-ticket: tickets/0207-agnostic-cli-reviewer-seat-one-config-op.erg
    endpoint: http://127.0.0.1:9/v1
    model: openai/nothing
YAML
allbad_err=$(REVIEWERS_PANEL="$ALLBAD" SEAT_RUNNER="$STUB" REVIEWERS_FINDINGS_DIR="$FDIR" \
             REVIEWERS_PR_BRANCH="some-branch" "$REVIEWERS" request 43 2>&1 >/dev/null || true)
assert_contains "request: no seat reviewed says so" "no seat reviewed MR #43" "$allbad_err"
assert_contains "request: and refuses to read as approval" "This is not an approval" "$allbad_err"
assert_exit_nonzero "request: every attempted seat failing exits non-zero" \
    env REVIEWERS_PANEL="$ALLBAD" SEAT_RUNNER="$STUB" REVIEWERS_FINDINGS_DIR="$FDIR" \
    REVIEWERS_PR_BRANCH="some-branch" "$REVIEWERS" request 43

harv_out=$(REVIEWERS_PANEL="$ROSTER" REVIEWERS_FINDINGS_DIR="$FDIR" "$REVIEWERS" harvest 42 2>/dev/null)
assert_contains "harvest: normalized to contract shape" "verifiable: foo.sh:10 — off-by-one" "$harv_out"
assert_contains "harvest: tags the seat" "[stub-good]" "$harv_out"

# Unparseable input → WARN, not silently dropped.
# Every `harvest` call pins REVIEWERS_PANEL: harvest's panel-integrity pass
# walks the roster, so an unpinned call reads the real production panel.yml and
# judges these fixtures against the live seats. The assertions here are
# substring-only and would stay green through that, which is exactly why the
# coupling has to be closed rather than tolerated.
mkdir -p "$FDIR/99"; printf 'garbage line not a finding\n' > "$FDIR/99/x.findings"
XROSTER="$WORK/x.yml"
cat > "$XROSTER" <<'YAML'
reviewers:
  - name: x
    kind: local-model
    status: advisory
    trial-ticket: tickets/0207-agnostic-cli-reviewer-seat-one-config-op.erg
    endpoint: http://127.0.0.1:9/v1
    model: openai/stub
YAML
harv_warn=$(REVIEWERS_PANEL="$XROSTER" REVIEWERS_FINDINGS_DIR="$FDIR" "$REVIEWERS" harvest 99 2>&1 >/dev/null)
assert_contains "harvest: WARN on non-contract line" "WARN non-contract line" "$harv_warn"

# ── template-echo detection ─────────────────────────────────────────────────
mkdir -p "$FDIR/200"
cat > "$FDIR/200/noisy-seat.findings" <<'NOISY'
FINDING|severity=verifiable-or-consider|file=PATH:LINE|rationale=ONE SENTENCE
FINDING|severity=verifiable|file=foo.sh:10|rationale=off-by-one
FINDING|severity=verifiable|file=foo.sh:10|rationale=off-by-one
FINDING|severity=consider|file=bar.py:5|rationale=unused import
SUMMARY|findings=1|verdict=approve-or-revise
NOISY
NROSTER="$WORK/noisy.yml"
cat > "$NROSTER" <<'YAML'
reviewers:
  - name: noisy-seat
    kind: local-model
    status: advisory
    trial-ticket: tickets/0207-agnostic-cli-reviewer-seat-one-config-op.erg
    endpoint: http://127.0.0.1:9/v1
    model: openai/stub
YAML
harv_out=$(REVIEWERS_PANEL="$NROSTER" REVIEWERS_FINDINGS_DIR="$FDIR" "$REVIEWERS" harvest 200 2>/dev/null)
harv_err=$(REVIEWERS_PANEL="$NROSTER" REVIEWERS_FINDINGS_DIR="$FDIR" "$REVIEWERS" harvest 200 2>&1 >/dev/null)
# Template-echo line must be dropped, not emitted as a finding.
if [[ "$harv_out" == *'verifiable-or-consider'* ]]; then
    echo "FAIL: harvest: template-echo leaked through"; FAIL=$((FAIL+1))
else
    echo "PASS: harvest: template-echo dropped"; PASS=$((PASS+1))
fi
assert_contains "harvest: template-echo logged as DROP" "DROP template-echo" "$harv_err"
# Duplicate collapsed: only one copy of off-by-one.
count=$(printf '%s\n' "$harv_out" | grep -c 'off-by-one' || true)
assert_eq "harvest: duplicate collapsed to one" "1" "$count"
assert_contains "harvest: duplicate logged as DROP" "DROP duplicate" "$harv_err"
# Both real unique findings survive.
assert_contains "harvest: real finding 1 survives" "verifiable: foo.sh:10 — off-by-one" "$harv_out"
assert_contains "harvest: real finding 2 survives" "consider: bar.py:5 — unused import" "$harv_out"

# ── scorecard appends a valid erg log line ───────────────────────────────────
# Build a throwaway erg ticket store so the real erg accepts the note.
ERG_BIN="${REPO_ROOT}/tickets/erg"
if [ -x "$ERG_BIN" ]; then
    TSTORE="$WORK/tickets"; mkdir -p "$TSTORE"; cp "$ERG_BIN" "$TSTORE/erg"
    cat > "$TSTORE/0207-agnostic-cli-reviewer-seat-one-config-op.erg" <<'ERG'
%erg 0.1
Title: Fixture
Created: 2026-06-05
Author: test

--- log ---
2026-06-05T00:00Z test created

--- body ---
## Context
Fixture.
ERG
    SCROSTER="$WORK/sc.yml"
    cat > "$SCROSTER" <<YAML
reviewers:
  - name: stub-good
    kind: local-model
    status: advisory
    trial-ticket: tickets/0207-agnostic-cli-reviewer-seat-one-config-op.erg
    endpoint: http://127.0.0.1:9/v1
    model: openai/stub
YAML
    TF="$TSTORE/0207-agnostic-cli-reviewer-seat-one-config-op.erg"
    # Point FINDINGS_DIR at a clean dir so no stale sidecar leaks into the
    # no-sidecar case (default is /tmp/reviewers, shared across runs).
    SC_FDIR="$WORK/sc-findings"; mkdir -p "$SC_FDIR"
    ( cd "$WORK" && REVIEWERS_PANEL="$SCROSTER" ERG="$TSTORE/erg" REVIEWERS_FINDINGS_DIR="$SC_FDIR" \
        "$REVIEWERS" scorecard 42 stub-good "PASS — 0 verifiable, 2 consider" ) >/dev/null 2>&1
    if "$TSTORE/erg" validate "$TF" >/dev/null 2>&1 \
       && grep -q 'MR #42 seat=stub-good' "$TF"; then
        echo "PASS: scorecard appends a valid erg log line"; PASS=$((PASS+1))
    else
        echo "FAIL: scorecard did not append a valid erg log line"; FAIL=$((FAIL+1))
    fi
    # ── ticket 0353: request-path latency folds into the scorecard line ──────
    # No sidecar → the line is byte-identical to the pre-0353 schema (no latency).
    line42=$(grep 'MR #42 seat=stub-good' "$TF" | head -1)
    if [[ "$line42" == *"latency="* ]]; then
        echo "FAIL: scorecard: no-sidecar line must not carry latency="; FAIL=$((FAIL+1))
    else
        echo "PASS: scorecard: no-sidecar line is byte-identical (no latency=)"; PASS=$((PASS+1))
    fi
    assert_contains "scorecard: no-sidecar line ends at the verdict" \
        "MR #42 seat=stub-good verdict: PASS — 0 verifiable, 2 consider" "$line42"
    # A `.latency` sidecar (left by `request`) → its seconds fold in at END.
    mkdir -p "$SC_FDIR/43"; printf '12.3' > "$SC_FDIR/43/stub-good.latency"
    ( cd "$WORK" && REVIEWERS_PANEL="$SCROSTER" ERG="$TSTORE/erg" REVIEWERS_FINDINGS_DIR="$SC_FDIR" \
        "$REVIEWERS" scorecard 43 stub-good "PASS — 1 verifiable, 0 consider" ) >/dev/null 2>&1
    line43=$(grep 'MR #43 seat=stub-good' "$TF" | head -1)
    assert_contains "scorecard: sidecar latency folded into the line" "latency=12.3s" "$line43"
    "$TSTORE/erg" validate "$TF" >/dev/null 2>&1 \
        && { echo "PASS: scorecard: ticket still valid after latency-bearing note"; PASS=$((PASS+1)); } \
        || { echo "FAIL: scorecard: latency-bearing note broke ticket validity"; FAIL=$((FAIL+1)); }
else
    echo "SKIP: erg binary absent — scorecard erg-integration test"
fi

# ── credential-env threads from roster to seat-runner (0207) ─────────────────
# A seat carrying `credential-env: NAME` must pass `--credential-env NAME` to
# the seat-runner; a seat without it must NOT pass the flag. The stub captures
# each seat's full argv so both cases are checked against real invocations.
CE_STUB="$WORK/seat-runner-ce-stub.sh"
cat > "$CE_STUB" <<'STUBEOF'
#!/usr/bin/env bash
set -euo pipefail
argv="$*"; out=""
while [ $# -gt 0 ]; do [ "$1" = "--out" ] && { out="$2"; shift 2; continue; }; shift; done
name="$(basename "$out" .findings)"
printf '%s\n' "$argv" > "${out%.findings}.argv"
{ echo "FINDING|severity=verifiable|file=foo.sh:10|rationale=x"; echo "SUMMARY|findings=1|verdict=revise"; } > "$out"
STUBEOF
chmod +x "$CE_STUB"

CEROSTER="$WORK/ce.yml"
cat > "$CEROSTER" <<'YAML'
reviewers:
  - name: seat-with-cred
    kind: cli-agent
    status: advisory
    trial-ticket: tickets/0207-agnostic-cli-reviewer-seat-one-config-op.erg
    endpoint: https://openrouter.ai/api/v1
    model: openai/stub
    credential-env: MY_ROSTER_KEY
  - name: seat-no-cred
    kind: local-model
    status: advisory
    trial-ticket: tickets/0207-agnostic-cli-reviewer-seat-one-config-op.erg
    endpoint: http://127.0.0.1:9/v1
    model: openai/stub
YAML

CEDIR="$WORK/ce-findings"
# A keystore fixture so the credential-env seat can authenticate (ticket 0393).
# NON-secret synthetic sentinel, and a BARE assignment with no `export` — the
# real ~/.config/keys files have that shape, which is why sourcing must enable
# allexport for the value to reach a child process at all.
CEKEYS="$WORK/ce-keystore"; mkdir -p "$CEKEYS"
printf 'MY_ROSTER_KEY=ce-sentinel-not-a-secret\n' > "$CEKEYS/fixture.env"
REVIEWERS_PANEL="$CEROSTER" SEAT_RUNNER="$CE_STUB" REVIEWERS_FINDINGS_DIR="$CEDIR" \
    REVIEWERS_KEYSTORE="$CEKEYS" \
    REVIEWERS_PR_BRANCH="some-branch" "$REVIEWERS" request 77 >/dev/null 2>&1
assert_contains "request: credential-env seat passes the flag through" \
    "--credential-env MY_ROSTER_KEY" "$(cat "$CEDIR/77/seat-with-cred.argv" 2>/dev/null || true)"
if grep -qF -- '--credential-env' "$CEDIR/77/seat-no-cred.argv" 2>/dev/null; then
    echo "FAIL: request: no-cred seat must not pass --credential-env"; FAIL=$((FAIL+1))
else
    echo "PASS: request: no-cred seat omits --credential-env"; PASS=$((PASS+1))
fi

# ── ticket 0393: the seat credential resolves, and a seat that cannot ────────
# authenticate is REPORTED, never omitted in silence.
#
# Background: panel.yml pins `credential-env: OPENROUTER_API_KEY_IDH`, but the
# BASH_ENV keystore path is default-deny — it exports a provider's variables
# only where a `.env` KEYS= line selects that provider. From a cwd with no such
# selection the variable is simply absent, the seat dies, and `request`'s WARN
# goes to stderr while `harvest` prints nothing and exits 0 — the panel reads as
# complete. The fix is consumer-side (the author's key files are never edited):
# resolve the named variable from the keystore, and make the failure visible on
# the report stream.
#
# Credential hygiene: every fixture value below is a synthetic sentinel, and
# every assertion is on PRESENCE or LENGTH — never on a credential's content.
# The suite must never run against a real key: a failing assertion prints what
# it found, so the failure message would BE the leak (rules/coding-bash.md).
#
# Hermetic children, mandatory here (rules/coding-bash.md § "Unsetting a
# variable in the parent does not unset it in the child"): BASH_ENV re-runs the
# harness loader — credential selection included — at the startup of EVERY child
# bash, so a check run against the ambient environment can pass on a variable
# the loader re-injected rather than on the code path under test. Every
# invocation below is spawned `env -i` with a FAKE BASH_ENV loader that exports
# one recognisable dummy and no credential: what the seat sees can then only
# have come from reviewers.sh's own resolution.
FAKE_LOADER="$WORK/fake-bash-env.sh"
printf 'export T393_LOADER_SENTINEL=loader-ran-not-a-secret\n' > "$FAKE_LOADER"
FHOME="$WORK/fake-home"; mkdir -p "$FHOME/.config/keys"
# The fake HOME's keystore is EMPTY: a lookup that ignored REVIEWERS_KEYSTORE
# and fell back to $HOME/.config/keys would find nothing — and could never
# reach the author's real keystore from this suite.

# Run reviewers.sh in a cleared environment with the fake loader in place.
hermetic_reviewers() {  # $@: reviewers.sh argv; extra env via H_ENV array
    env -i HOME="$FHOME" PATH="$PATH" BASH_ENV="$FAKE_LOADER" \
        ${H_ENV[@]+"${H_ENV[@]}"} bash "$REVIEWERS" "$@"
}

# Stub seat-runner that records only whether the credential arrived and how long
# it is. It never writes the value anywhere.
K_STUB="$WORK/seat-runner-key-stub.sh"
cat > "$K_STUB" <<'STUBEOF'
#!/usr/bin/env bash
set -euo pipefail
out=""; cred=""
while [ $# -gt 0 ]; do
    case "$1" in
        --out) out="$2"; shift 2 ;;
        --credential-env) cred="$2"; shift 2 ;;
        *) shift ;;
    esac
done
val=""
[ -n "$cred" ] && val="$(printenv "$cred" || true)"
# The loader sentinel is the CONTROL: it proves BASH_ENV really ran in this
# child, so "credential absent" cannot be explained by a loader that never fired.
loader="${T393_LOADER_SENTINEL:-none}"
if [ -n "$val" ]; then
    printf 'present len=%s loader=%s\n' "${#val}" "$loader" > "${out%.findings}.cred"
else
    printf 'absent loader=%s\n' "$loader" > "${out%.findings}.cred"
fi
{ echo "FINDING|severity=verifiable|file=foo.sh:10|rationale=x"; echo "SUMMARY|findings=1|verdict=revise"; } > "$out"
STUBEOF
chmod +x "$K_STUB"

KSTORE="$WORK/keystore"; mkdir -p "$KSTORE"
# 24-character synthetic sentinel, bare assignment (no `export`).
printf 'T393_FIXTURE_KEY=keystore-sentinel-000000\n' > "$KSTORE/fixture-provider.env"

KROSTER="$WORK/k.yml"
cat > "$KROSTER" <<'YAML'
reviewers:
  - name: keyed-seat
    kind: cli-agent
    status: advisory
    trial-ticket: tickets/0207-agnostic-cli-reviewer-seat-one-config-op.erg
    endpoint: https://example.invalid/v1
    model: openai/stub
    credential-env: T393_FIXTURE_KEY
YAML

KDIR="$WORK/k-findings"
H_ENV=(REVIEWERS_PANEL="$KROSTER" SEAT_RUNNER="$K_STUB" REVIEWERS_FINDINGS_DIR="$KDIR"
       REVIEWERS_KEYSTORE="$KSTORE" REVIEWERS_PR_BRANCH="some-branch")
k_err=$(hermetic_reviewers request 393 2>&1 >/dev/null)
k_cred="$(cat "$KDIR/393/keyed-seat.cred" 2>/dev/null || echo missing)"
# `loader=loader-ran` is the control: the fake BASH_ENV loader DID run in the
# seat's child shell, and it exported no credential — so a present credential
# can only have come from reviewers.sh resolving it.
assert_eq "request: keystore credential reaches a hermetic seat child (presence + length only)" \
    "present len=24 loader=loader-ran-not-a-secret" "$k_cred"

# The environment wins over the keystore: an already-exported variable is used
# as-is and the keystore is not consulted. Distinct length (20) proves which
# source won, without either value ever being printed.
KDIR2="$WORK/k-findings-env"
H_ENV=(REVIEWERS_PANEL="$KROSTER" SEAT_RUNNER="$K_STUB" REVIEWERS_FINDINGS_DIR="$KDIR2"
       REVIEWERS_KEYSTORE="$KSTORE" REVIEWERS_PR_BRANCH="some-branch"
       T393_FIXTURE_KEY="env-sentinel-0000000")
hermetic_reviewers request 393 >/dev/null 2>&1
assert_eq "request: an environment credential takes precedence over the keystore" \
    "present len=20 loader=loader-ran-not-a-secret" \
    "$(cat "$KDIR2/393/keyed-seat.cred" 2>/dev/null || echo missing)"

# No credential value may appear in any output or sidecar the run produces.
leak_hay="$k_err$(cat "$KDIR"/393/* 2>/dev/null || true)"
if [[ "$leak_hay" == *"keystore-sentinel-000000"* ]]; then
    echo "FAIL: request: credential value leaked into output or a sidecar"; FAIL=$((FAIL+1))
else
    echo "PASS: request: credential value never printed or written to a sidecar"; PASS=$((PASS+1))
fi

# ── unresolvable credential: loud, recorded, and visible in the report ───────
UROSTER="$WORK/u.yml"
cat > "$UROSTER" <<'YAML'
reviewers:
  - name: unauthenticated-seat
    kind: cli-agent
    status: advisory
    trial-ticket: tickets/0207-agnostic-cli-reviewer-seat-one-config-op.erg
    endpoint: https://example.invalid/v1
    model: openai/stub
    credential-env: T393_NOWHERE_KEY
YAML

UDIR="$WORK/u-findings"
H_ENV=(REVIEWERS_PANEL="$UROSTER" SEAT_RUNNER="$K_STUB" REVIEWERS_FINDINGS_DIR="$UDIR"
       REVIEWERS_KEYSTORE="$KSTORE" REVIEWERS_PR_BRANCH="some-branch")
u_err=$(hermetic_reviewers request 394 2>&1 >/dev/null)
assert_contains "request: unresolved credential WARNs and names the variable" \
    "T393_NOWHERE_KEY" "$u_err"
assert_contains "request: unresolved credential names the seat" \
    "unauthenticated-seat" "$u_err"
assert_exit_0 "request: an unresolved credential stays fail-open (exit 0)" \
    hermetic_reviewers request 394

# The load-bearing half (ticket 0393 action 3): the panel REPORT — harvest's
# stdout — must say the seat did not review. A stderr WARN is exactly what was
# lost the day the seat failed open during a live gaze.
H_ENV=(REVIEWERS_PANEL="$UROSTER" REVIEWERS_FINDINGS_DIR="$UDIR")
u_report=$(hermetic_reviewers harvest 394 2>/dev/null)
assert_contains "harvest: report names the seat that did not review" \
    "SEAT-FAILED: unauthenticated-seat" "$u_report"
assert_contains "harvest: report names the unresolved credential" \
    "T393_NOWHERE_KEY" "$u_report"
assert_contains "harvest: report carries the panel-integrity headline" \
    "PANEL-INTEGRITY" "$u_report"
if [[ "$u_report" == *"keystore-sentinel"* || "$u_report" == *"env-sentinel"* ]]; then
    echo "FAIL: harvest: a credential value leaked into the report"; FAIL=$((FAIL+1))
else
    echo "PASS: harvest: no credential value in the report"; PASS=$((PASS+1))
fi

# A roster seat with no findings AND no run record — `request` never reached it
# — is reported too: an empty harvest must never be indistinguishable from a
# panel that never ran.
H_ENV=(REVIEWERS_PANEL="$UROSTER" REVIEWERS_FINDINGS_DIR="$WORK/never")
never_report=$(hermetic_reviewers harvest 500 2>/dev/null)
assert_contains "harvest: a seat that never ran is reported, not silence" \
    "SEAT-MISSING: unauthenticated-seat" "$never_report"

# A seat that ran and found nothing is NOT flagged — silence there is a real
# result, and over-reporting would make the integrity line noise.
QUIET="$WORK/quiet-findings/600"; mkdir -p "$QUIET"
printf 'ok\n' > "$QUIET/unauthenticated-seat.status"
printf 'SUMMARY|findings=0|verdict=approve\n' > "$QUIET/unauthenticated-seat.findings"
H_ENV=(REVIEWERS_PANEL="$UROSTER" REVIEWERS_FINDINGS_DIR="$WORK/quiet-findings")
quiet_report=$(hermetic_reviewers harvest 600 2>/dev/null)
assert_eq "harvest: a seat that ran and found nothing stays silent" "" "$quiet_report"
assert_exit_0 "harvest: clean panel still exits 0" hermetic_reviewers harvest 600
unset H_ENV

# ── stale per-run artefacts: `request` starts each run from a clean slate ────
# A per-PR findings directory is reused across runs. Without a clear, run 1's
# `.findings` outlive a run 2 in which the same seat could not authenticate, and
# `harvest` then prints run 1's finding attributed to the seat AND SEAT-FAILED
# for it — one report asserting the seat both reviewed and did not. Same root
# cause: a seat dropped from the roster between runs leaves an orphaned
# `.findings` that harvest's roster-independent glob reports forever.
STALE_STUB="$WORK/seat-runner-stale-stub.sh"
cat > "$STALE_STUB" <<'STUBEOF'
#!/usr/bin/env bash
set -euo pipefail
out=""; while [ $# -gt 0 ]; do [ "$1" = "--out" ] && { out="$2"; shift 2; continue; }; shift; done
{ echo "FINDING|severity=verifiable|file=foo.sh:10|rationale=stale-run-1-finding"
  echo "SUMMARY|findings=1|verdict=revise"; } > "$out"
STUBEOF
chmod +x "$STALE_STUB"

STALEROSTER="$WORK/stale.yml"
cat > "$STALEROSTER" <<'YAML'
reviewers:
  - name: stale-seat
    kind: cli-agent
    status: advisory
    trial-ticket: tickets/0207-agnostic-cli-reviewer-seat-one-config-op.erg
    endpoint: https://example.invalid/v1
    model: openai/stub
    credential-env: T393_FIXTURE_KEY
YAML

SDIR="$WORK/stale-findings"
# RUN 1 — the credential resolves from the keystore; the seat reviews.
H_ENV=(REVIEWERS_PANEL="$STALEROSTER" SEAT_RUNNER="$STALE_STUB" REVIEWERS_FINDINGS_DIR="$SDIR"
       REVIEWERS_KEYSTORE="$KSTORE" REVIEWERS_PR_BRANCH="some-branch")
hermetic_reviewers request 700 >/dev/null 2>&1
assert_contains "request: run 1 wrote the seat's findings" "stale-run-1-finding" \
    "$(cat "$SDIR/700/stale-seat.findings" 2>/dev/null || echo missing)"

# Leave an orphan behind too: a seat that will not be on run 2's roster.
printf 'FINDING|severity=verifiable|file=old.sh:1|rationale=orphan-seat-finding\n' \
    > "$SDIR/700/departed-seat.findings"

# RUN 2 — same merge request, empty keystore: the credential is now unresolvable
# and the seat does NOT review.
EMPTYSTORE="$WORK/empty-keystore"; mkdir -p "$EMPTYSTORE"
H_ENV=(REVIEWERS_PANEL="$STALEROSTER" SEAT_RUNNER="$STALE_STUB" REVIEWERS_FINDINGS_DIR="$SDIR"
       REVIEWERS_KEYSTORE="$EMPTYSTORE" REVIEWERS_PR_BRANCH="some-branch")
hermetic_reviewers request 700 >/dev/null 2>&1
H_ENV=(REVIEWERS_PANEL="$STALEROSTER" REVIEWERS_FINDINGS_DIR="$SDIR")
stale_report=$(hermetic_reviewers harvest 700 2>/dev/null)
if [[ "$stale_report" == *"stale-run-1-finding"* ]]; then
    echo "FAIL: harvest: run 1's finding survived into run 2's report"; FAIL=$((FAIL+1))
else
    echo "PASS: harvest: a stale run's finding is not attributed to a seat that did not review"; PASS=$((PASS+1))
fi
assert_contains "harvest: the seat that could not authenticate is reported as failed" \
    "SEAT-FAILED: stale-seat" "$stale_report"
if [[ "$stale_report" == *"orphan-seat-finding"* ]]; then
    echo "FAIL: harvest: an off-roster seat's orphaned findings still reported"; FAIL=$((FAIL+1))
else
    echo "PASS: harvest: an off-roster seat leaves no orphaned findings behind"; PASS=$((PASS+1))
fi
unset H_ENV

# ── forge-bot seat: on-demand request via the forge review API (0206) ────────
# A forge-bot seat has no seat-runner; `request` asks the forge to run its
# server-side reviewer on the PR. Stub `gh` to capture the call.
GHBOT="$WORK/ghbin"; mkdir -p "$GHBOT"
cat > "$GHBOT/gh" <<'GHSTUB'
#!/usr/bin/env bash
set -euo pipefail
echo "$*" >> "$GH_CALL_LOG"
[ -n "${GH_FAIL:-}" ] && exit 1
exit 0
GHSTUB
chmod +x "$GHBOT/gh"

BOTROSTER="$WORK/bot.yml"
cat > "$BOTROSTER" <<'YAML'
reviewers:
  - name: copilot
    kind: forge-bot
    status: advisory
    login: copilot-pull-request-reviewer[bot]
    trial-ticket: tickets/0206-copilot-review-in-the-verify-panel-on-demand.erg
YAML

GHLOG="$WORK/gh-calls.log"; : > "$GHLOG"
bot_err=$(PATH="$GHBOT:$PATH" GH_CALL_LOG="$GHLOG" \
          REVIEWERS_PANEL="$BOTROSTER" REVIEWERS_PR_BRANCH="some-branch" \
          "$REVIEWERS" request 42 2>&1 >/dev/null)
assert_contains "request: forge-bot seat requested" "forge-bot seat 'copilot' requested" "$bot_err"
assert_contains "request: forge API call carries the login" "copilot-pull-request-reviewer[bot]" "$(cat "$GHLOG")"
assert_contains "request: forge API call targets the PR" "pulls/42/requested_reviewers" "$(cat "$GHLOG")"

# Forge API failure → WARN, fail-open (exit 0).
bot_fail_err=$(PATH="$GHBOT:$PATH" GH_CALL_LOG="$GHLOG" GH_FAIL=1 \
               REVIEWERS_PANEL="$BOTROSTER" REVIEWERS_PR_BRANCH="some-branch" \
               "$REVIEWERS" request 42 2>&1 >/dev/null)
assert_contains "request: forge-bot failure fail-open WARN" "WARN forge-bot seat 'copilot'" "$bot_fail_err"
assert_exit_0 "request: forge-bot failure exits 0" env PATH="$GHBOT:$PATH" GH_CALL_LOG="$GHLOG" GH_FAIL=1 \
    REVIEWERS_PANEL="$BOTROSTER" REVIEWERS_PR_BRANCH="some-branch" "$REVIEWERS" request 42

# A forge-bot seat with no login → WARN, skipped, others unaffected.
NOLOGIN="$WORK/nologin.yml"
cat > "$NOLOGIN" <<'YAML'
reviewers:
  - name: mystery-bot
    kind: forge-bot
    status: advisory
    trial-ticket: tickets/0206-copilot-review-in-the-verify-panel-on-demand.erg
YAML
nologin_err=$(PATH="$GHBOT:$PATH" GH_CALL_LOG="$GHLOG" \
              REVIEWERS_PANEL="$NOLOGIN" REVIEWERS_PR_BRANCH="some-branch" \
              "$REVIEWERS" request 42 2>&1 >/dev/null)
assert_contains "request: forge-bot without login WARNs" "WARN forge-bot seat 'mystery-bot' has no login" "$nologin_err"

# ── scores: read-back of trial scorecards + audition blocks (0348) ───────────
# scores greps the fixed-schema trial lines out of the ticket store — corpus
# wide, including tickets/closed/ — and prints one sortable table. Read-only:
# it never edits a roster or writes an erg-log line. Prove the closed/ search
# by putting the scorecard lines only in a closed ticket.
STICK="$WORK/score-tickets"; mkdir -p "$STICK/closed"
cat > "$STICK/0207-trial.erg" <<'ERG'
%erg 0.1
Title: Trial fixture
Created: 2026-07-14
Author: test

--- log ---
2026-07-14T20:15Z claude note audition candidate=hy3-free model=openai/tencent/hy3:free board=10MR findings=59 duplicate=23 unique-verified=0 unique-hallucinated=36 overlap=38% latency=3419.1s cost=n/a
2026-07-14T20:16Z claude note audition candidate=broken model=x board=1MR

--- body ---
## Context
Fixture.
ERG
cat > "$STICK/closed/0206-copilot.erg" <<'ERG'
%erg 0.1
Title: Copilot trial fixture
Created: 2026-07-13
Author: test
Closed: 2026-07-13

--- log ---
2026-07-13T19:43Z claude note MR ImperialDragonHarness#537 seat=copilot verdict: PASS — 0 verifiable, 1 consider (memory consolidation)
2026-07-13T19:43Z claude note MR ImperialDragonHarness#559 seat=copilot verdict: PASS — 0 verifiable, 0 consider (accurate summary)
2026-07-13T19:44Z claude note MR ImperialDragonHarness#560 seat=copilot verdict: PASS — 1 verifiable, 2 consider (rejected 9 verifiable-looking; noted 7 consider-style nits in prose)
2026-07-13T19:45Z claude note MR ImperialDragonHarness#561 seat=copilot verdict: rejected 8 verifiable, all bogus — true 4 verifiable, 6 consider (final)

--- body ---
## Context
A ticket body may quote the card schema as documentation, e.g.
audition candidate=doc-example model=x board=99MR findings=1 duplicate=1 unique-verified=1 unique-hallucinated=1 overlap=100% latency=1.0s cost=n/a
and MR #0 seat=doc-example verdict: PASS — 5 verifiable, 5 consider (illustration).
These body lines MUST NOT appear in the table (ticket 0348: scan log only).

## Format example
A trial ticket's log section is delimited like this:
--- log ---
2026-01-01T00:00Z claude note MR phantom#1 seat=ghost verdict: PASS — 9 verifiable, 9 consider (body re-entry decoy — must be ignored)
ERG

scores_out=$(REVIEWERS_TICKETS="$STICK" "$REVIEWERS" scores 2>/dev/null)
assert_contains "scores: header names OVERLAP column" "OVERLAP" "$scores_out"
assert_contains "scores: lists audition candidate" "hy3-free" "$scores_out"
assert_contains "scores: audition row carries findings count" "59" "$scores_out"
assert_contains "scores: finds scorecard seat in closed/ ticket" "copilot" "$scores_out"
assert_contains "scores: scorecard row carries the MR ident" "ImperialDragonHarness#537" "$scores_out"

# Greedy-regex poison guard: a verdict whose freeform prose contains later
# "<digit> verifiable/consider" phrases must still report the TRUE counts (1/2),
# taken from the first occurrence — not 9/7 from the parenthetical (0348 review).
poison_row=$(printf '%s\n' "$scores_out" | grep 'ImperialDragonHarness#560')
assert_contains "scores: count taken from first occurrence, not poisoned by prose" \
    " 1     2 " "$poison_row"
if [[ "$poison_row" == *" 9 "* || "$poison_row" == *" 7 "* ]]; then
    echo "FAIL: scores: freeform verdict prose poisoned the VERIF/CONS count"; FAIL=$((FAIL+1))
else
    echo "PASS: scores: freeform verdict prose did not poison the count"; PASS=$((PASS+1))
fi

# Poison-BEFORE guard: freeform prose carrying "<digit> verifiable" BEFORE the
# real tally must not poison the count either — the counts come from the anchored
# "N verifiable, M consider" unit (0348 review round 2). True tally is 4/6.
poison2_row=$(printf '%s\n' "$scores_out" | grep 'ImperialDragonHarness#561')
assert_contains "scores: count anchored to the real tally, not leading prose" \
    " 4     6 " "$poison2_row"
if [[ "$poison2_row" == *" 8 "* ]]; then
    echo "FAIL: scores: leading verdict prose poisoned the count"; FAIL=$((FAIL+1))
else
    echo "PASS: scores: leading verdict prose did not poison the count"; PASS=$((PASS+1))
fi

# Log-section-only guard: cards quoted in a ticket BODY are documentation, not
# real trial results — they must never surface as table rows (0348 review).
if [[ "$scores_out" == *"doc-example"* ]]; then
    echo "FAIL: scores: a body-quoted card leaked into the table"; FAIL=$((FAIL+1))
else
    echo "PASS: scores: body-quoted cards excluded (log section only)"; PASS=$((PASS+1))
fi

# Body re-entry guard: a body line quoting "--- log ---" must NOT re-open the
# scan — the phantom#1/ghost card sits after the real body boundary (0348 r2).
if [[ "$scores_out" == *"ghost"* || "$scores_out" == *"phantom"* ]]; then
    echo "FAIL: scores: body-quoted '--- log ---' re-opened the scan (phantom row)"; FAIL=$((FAIL+1))
else
    echo "PASS: scores: body-quoted '--- log ---' did not re-open the scan"; PASS=$((PASS+1))
fi

# Filter to one name → only that seat/candidate; the other kind is excluded.
scores_filt=$(REVIEWERS_TICKETS="$STICK" "$REVIEWERS" scores copilot 2>/dev/null)
assert_contains "scores: filter shows the requested seat" "copilot" "$scores_filt"
if [[ "$scores_filt" == *"hy3-free"* ]]; then
    echo "FAIL: scores: filter leaked a non-matching candidate"; FAIL=$((FAIL+1))
else
    echo "PASS: scores: filter excludes non-matching rows"; PASS=$((PASS+1))
fi

# A malformed trial line WARNs on stderr, never silently dropped.
scores_warn=$(REVIEWERS_TICKETS="$STICK" "$REVIEWERS" scores 2>&1 >/dev/null)
assert_contains "scores: WARN on malformed line" "WARN" "$scores_warn"

# scores is read-only: it must not mutate the ticket store.
before=$(cat "$STICK/0207-trial.erg" "$STICK/closed/0206-copilot.erg")
REVIEWERS_TICKETS="$STICK" "$REVIEWERS" scores >/dev/null 2>&1
after=$(cat "$STICK/0207-trial.erg" "$STICK/closed/0206-copilot.erg")
assert_eq "scores: leaves the ticket store unchanged" "$before" "$after"

# ── help: explicit verb, exit 0, names every subcommand (0348) ───────────────
assert_exit_0 "help: exits 0" "$REVIEWERS" help
help_out=$("$REVIEWERS" help 2>/dev/null)
for verb in list request harvest scorecard audition scores help; do
    assert_contains "help: names '$verb'" "$verb" "$help_out"
done
# No-arg still exits 1 (the unknown/no-verb fallback is unchanged).
if "$REVIEWERS" >/dev/null 2>&1; then echo "FAIL: no-arg should still exit 1"; FAIL=$((FAIL+1)); else echo "PASS: no-arg still exits 1"; PASS=$((PASS+1)); fi

# ── arg validation ───────────────────────────────────────────────────────────
if "$REVIEWERS" request >/dev/null 2>&1; then echo "FAIL: request missing arg should fail"; FAIL=$((FAIL+1)); else echo "PASS: request missing arg fails"; PASS=$((PASS+1)); fi

echo ""; echo "Results: ${PASS} passed, ${FAIL} failed"
[ "$FAIL" -eq 0 ] || exit 1
