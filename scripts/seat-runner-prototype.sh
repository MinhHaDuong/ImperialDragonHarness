#!/usr/bin/env bash
# seat-runner-prototype — run an agnostic CLI reviewer (aider --ask) inside an
# OS-level rootless container (podman) over a LOCAL branch diff. No forge
# round-trip.
#
# Prototype for ticket 0217 (sandbox-runner reviewer-seat spinoff), embodying
# the "review is CI" model: the seat is a contained job over a read-only
# checkout, emitting findings on stdout; the orchestrator owns everything else.
#
# Why podman, not bwrap: this host sets
# kernel.apparmor_restrict_unprivileged_userns=1 and ships AppArmor userns
# profiles for podman/crun/runc but not bwrap — rootless podman is the
# sandbox that works unprivileged here, and a container IS the CI-runner
# primitive the architecture wants.
#
# Containment (v1, honest about gaps):
#   - repo + diff mounted READ-ONLY; container rootfs --read-only
#     (kernel-enforced; a write attempt fails even for a misbehaving seat)
#   - HOME is a throwaway tmpfs; the real $HOME is NOT mounted (no ~/.ssh,
#     no scripts/bash-env.sh, no memory files) except ~/.local (ro, code only)
#   - env is explicitly constructed (no BASH_ENV, no inherited secrets; only
#     a dummy OPENAI_API_KEY for the local endpoint)
#   - the containment self-test FAILS LOUD if the sandbox itself does not
#     start: a blocked write only counts when the probe also proves the
#     sandbox executes (first version of this script counted "bwrap refused
#     to run" as "write blocked" — a fail-open self-test)
#   - KNOWN GAP: --network=host (the seat must reach the local llama-server
#     on 127.0.0.1). True isolation needs a private netns with only the
#     endpoint reachable, or the endpoint inside the container. Acceptable
#     while the endpoint is local-only; NOT acceptable for a cloud-endpoint
#     seat. Tracked in 0217.
#
# Usage:
#   seat-runner-prototype.sh --branch BRANCH [--repo PATH] [--base REF]
#                            [--endpoint URL] [--model NAME] [--out FILE]
set -euo pipefail

REPO="$(pwd)"
BASE="origin/main"
BRANCH=""
ENDPOINT="http://127.0.0.1:8012/v1"
MODEL="openai/devstral-small-2"
OUT="/dev/stdout"
IMAGE="localhost/seat-runner:v1"   # ubuntu:24.04 + python3 + git + ca-certs
                                   # (aider's uv venv symlinks /usr/bin/python3,
                                   # absent from the bare ubuntu image)

while [[ $# -gt 0 ]]; do
    case "$1" in
        --repo)     REPO="$2"; shift 2 ;;
        --base)     BASE="$2"; shift 2 ;;
        --branch)   BRANCH="$2"; shift 2 ;;
        --endpoint) ENDPOINT="$2"; shift 2 ;;
        --model)    MODEL="$2"; shift 2 ;;
        --out)      OUT="$2"; shift 2 ;;
        *) echo "seat-runner: unknown arg $1" >&2; exit 2 ;;
    esac
done
[[ -n "$BRANCH" ]] || { echo "seat-runner: --branch required" >&2; exit 2; }
command -v podman >/dev/null || { echo "seat-runner: podman not installed" >&2; exit 1; }

# Fail loud if the endpoint is down (0217: unreachable endpoint = non-zero).
curl -sf --max-time 5 "${ENDPOINT%/v1}/health" >/dev/null \
    || { echo "seat-runner: endpoint ${ENDPOINT} unreachable" >&2; exit 1; }

WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

# ── 1. Detached read-only checkout (no shared object store, no GitHub) ──────
git clone --quiet --local --no-hardlinks "$REPO" "$WORK/clone"
git -C "$WORK/clone" checkout --quiet "$BRANCH"
git -C "$WORK/clone" diff "${BASE}...${BRANCH}" > "$WORK/review.diff"
[[ -s "$WORK/review.diff" ]] || { echo "seat-runner: empty diff ${BASE}...${BRANCH}" >&2; exit 1; }

# ── 2. Review prompt (single-shot; the 0205 contract shape) ─────────────────
cat > "$WORK/prompt.txt" <<'PROMPT'
You are an advisory code reviewer on a merge gate panel. Review the unified
diff in /review.diff (the full checkout is at /repo, read-only, for context).
Report only findings you can ground in the diff. For EACH finding emit exactly
one line in this shape:
FINDING|severity=verifiable-or-consider|file=PATH:LINE|rationale=ONE SENTENCE
verifiable = objectively checkable defect (logic, broken reference, format
violation); consider = judgment-call improvement. After the findings emit one
line: SUMMARY|findings=N|verdict=approve-or-revise
If there are no findings, emit only the SUMMARY line with findings=0.
PROMPT

# ── 3. The sandboxed seat ────────────────────────────────────────────────────
HOMEDIR="/home/haduong"   # aider's uv-tool venv carries absolute shebangs
run_seat() {
    podman run --rm \
        --network=host \
        --userns=keep-id \
        --read-only \
        --tmpfs "$HOMEDIR":rw,size=256m \
        --tmpfs /tmp:rw,size=64m \
        -v "$HOMEDIR/.local":"$HOMEDIR/.local":ro \
        -v "$WORK/clone":/repo:ro \
        -v "$WORK/review.diff":/review.diff:ro \
        -e HOME="$HOMEDIR" \
        -e PATH="$HOMEDIR/.local/bin:/usr/bin:/bin" \
        -e TERM=dumb \
        -e COLUMNS=500 \
        -e OPENAI_API_KEY=local-dummy \
        -e OPENAI_API_BASE="$ENDPOINT" \
        -w /repo \
        "$IMAGE" "$@"
}

# ── 4. Containment self-test (0217: proven, not assumed; alive-then-blocked) ─
echo "seat-runner: containment self-test..." >&2
PROBE=$(run_seat bash -c '
    echo SANDBOX-ALIVE
    touch /repo/PWNED 2>/dev/null         && echo WRITE-ALLOWED || echo WRITE-BLOCKED
    cat '"$HOMEDIR"'/.ssh/id_* '"$HOMEDIR"'/.claude/scripts/bash-env.sh 2>/dev/null \
        | grep -q . && echo SECRET-READ || echo SECRET-BLOCKED
') || { echo "seat-runner: FATAL sandbox failed to start" >&2; exit 1; }
grep -q SANDBOX-ALIVE   <<<"$PROBE" || { echo "seat-runner: FATAL probe did not run" >&2; exit 1; }
grep -q WRITE-BLOCKED   <<<"$PROBE" || { echo "seat-runner: FATAL repo write was NOT blocked" >&2; exit 1; }
grep -q SECRET-BLOCKED  <<<"$PROBE" || { echo "seat-runner: FATAL secret read was NOT blocked" >&2; exit 1; }
echo "seat-runner: containment OK (sandbox alive; repo write blocked; secrets unreachable)" >&2

# ── 5. Run the reviewer seat ─────────────────────────────────────────────────
echo "seat-runner: reviewing ${BRANCH} vs ${BASE} with ${MODEL}..." >&2
run_seat "$HOMEDIR/.local/bin/aider" \
    --no-git --chat-mode ask --model "$MODEL" \
    --message "$(cat "$WORK/prompt.txt")" \
    --read /review.diff \
    --yes-always --no-check-update --no-show-model-warnings --no-pretty \
    --no-stream --map-tokens 0 \
    > "$WORK/raw.out" 2> "$WORK/raw.err" \
    || { echo "seat-runner: reviewer exited non-zero; stderr follows" >&2; tail -20 "$WORK/raw.err" >&2; exit 1; }

# ── 6. Normalize: keep only contract-shaped lines; surface the rest as WARN ─
grep -E '^(FINDING|SUMMARY)\|' "$WORK/raw.out" > "$OUT" || {
    echo "seat-runner: WARN no contract-shaped lines in reviewer output; raw output follows" >&2
    cat "$WORK/raw.out" >&2
    exit 1
}
echo "seat-runner: done." >&2
