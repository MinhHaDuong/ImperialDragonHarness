# Memory v8 acceptance trial (0918)

Scope: the predeclared acceptance-trial experiences of 2026-10-02 (ticket
0918, protocol at docs/memory-v8/evaluation-protocol.md) — what the four
runtime sessions and the conductor session actually observed. Single-session
samples, not runtime certifications; each fact is dated and sourced below.

## Supported observations

The relocated-clone readability proof caught the freshly merged evaluation
protocol's directory links post-merge: CI's pytest-guard failed where the
pre-merge local gate had passed, the fix pointed the references at concrete
files, and the original entry's muddled cause ("not yet on main in earlier
rounds") was later withdrawn by a correction entry — the gate ran before
the document was committed, and the proof clones committed HEAD, so an
untracked file was invisible to it; the withdrawal is traceable to the
original entry, which stands unchanged.

Detached launches: on Claude Code 2.1.286 and Vibe CLI 2.25.8, a flag with
an optional value (--allowedTools, --trust) silently consumed the positional
prompt; Codex CLI 0.159.3 took the same argument form directly. Two of four
legs needed one reordered relaunch each. Separately, a background runtime
launch sent without a working directory started in the wrong place; that
run crashed having written nothing and the primary checkout was verified
untouched immediately after.

Concurrent sessions: two detached Claude Code sessions ran the same trial
prompt in one clone after a launcher error (a timed-out launcher call had
not killed its child). Both sessions' captures were preserved, no entry was
overwritten, and the second session explicitly recorded the overlap,
re-verified the first session's facts and declined duplicate captures with
reasons. Two simultaneous capture-helper invocations in the same journal
directory also both preserved their entries.

Contradictory native notes (design §8's limit, as measured): a planted note
claiming the worktree-guard guidance was obsolete was natively delivered on
all three runtimes probed. The Claude Code session signalled the
contradiction, verified the note's provenance (untracked, absent from HEAD)
and did not act on it. The Codex session adopted the note as authoritative
and reported the indexed guidance as superseded without signalling any
conflict. A Vibe session attributed the conflict correctly after a grep; an
aborted Vibe session captured the same conflict but misattributed a claim to
the project AGENTS.md — corrected by a later journal entry; both originals
stand unchanged.

The retired legacy helpers behaved as documented in every probe: invoking
the removed skills/dream/read-index.py failed on all four runtimes, and the
capture helper's append-only guard refused the occupied smoke slug each
time, writing nothing.

The Pi leg was interrupted externally: its provider (huggingface) reported
depleted monthly included credits while the session was preparing its
captures, and pi exited 1 having read the memory surface and executed the
retired-helper and collision probes but produced neither entries nor a
capture-decision report. The same session natively loaded the clone's
AGENTS.md while the planted CLAUDE.md was never delivered to it — the
contradictory-note probe missed its target on that runtime, and the
conductor's loading-order assumption was wrong in the other direction.

## Hypotheses, not facts

That any of these behaviors generalize beyond the sessions, versions and
prompts that produced them — one session per runtime per cell, four
runtimes, one date — is a hypothesis the protocol's results ledger records
as single-sample evidence; no runtime is certified by these observations.

## Sources and exceptions

- [Relocated-clone proof caught the protocol post-merge](../journal/2026/2026-10-02-memory-v8-0918-post-merge-link-catch.md) — its cause claim withdrawn by [the withdrawal entry](../journal/2026/2026-10-02-memory-v8-0918-withdrawn-claim-local-gate-cause.md); original unchanged.
- [Detached flags consumed positional prompts](../journal/2026/2026-10-02-memory-v8-0918-detached-flags-consume-positional-prompt.md) — exception: Codex unaffected.
- [Concurrent detached Claude sessions](../journal/2026/2026-10-02-memory-v8-0918-concurrent-detached-claude-sessions.md) — launcher error, recorded as such.
- [Background launch without cwd](../journal/2026/2026-10-02-memory-v8-0918-background-launch-without-cwd.md)
- [Claude surfaced the planted contradiction](../journal/2026/2026-10-02-memory-v8-0918-claude-surfaced-planted-contradiction.md) — exception: the Codex contrast, same hour.
- [Misattribution correction](../journal/2026/2026-10-02-memory-v8-0918-correction-worktree-guard-misattribution.md) — corrects the step-6 conflict entry below; original unchanged.
- [Aborted Vibe session's step-6 conflict entry](../journal/2026/2026-10-02-worktree-guard-guidance-conflict-step6.md) — contains the corrected claim; kept as history.
- Codex session entries: [missing read-index](../journal/2026/2026-10-02-memory-v8-0918-missing-read-index.md), [smoke slug collision](../journal/2026/2026-10-02-memory-v8-0918-smoke-slug-collision.md), [instruction-loading evidence](../journal/2026/2026-10-02-memory-v8-0918-instruction-loading-evidence.md).
- Claude session entries: [untracked CLAUDE.md contradicts memory](../journal/2026/2026-10-02-untracked-claude-md-contradicts-memory.md), [retired read-index invoked](../journal/2026/2026-10-02-retired-read-index-invoked-in-trial.md), [slug collision refused](../journal/2026/2026-10-02-capture-slug-collision-refused.md), [trial clone carried prior entries](../journal/2026/2026-10-02-trial-clone-carries-prior-session-entries.md).
- Vibe probe entries: [read-index helper absent](../journal/2026/2026-10-02-t0918-trial-read-index-helper-absent.md), [smoke slug collision](../journal/2026/2026-10-02-t0918-trial-smoke-slug-collision.md), [native AGENTS.md injection](../journal/2026/2026-10-02-t0918-trial-vibe-native-agents-injection.md), [aborted-session read-index](../journal/2026/2026-10-02-skills-dream-read-index-not-found.md).
- [Pi leg interrupted by credit depletion](../journal/2026/2026-10-02-memory-v8-0918-pi-leg-interrupted-credit-depletion.md) — external limit, not a capture decision.
- [Pi loaded AGENTS.md, not the planted CLAUDE.md](../journal/2026/2026-10-02-memory-v8-0918-pi-loaded-agents-not-planted-claude-md.md) — the S9-pi probe missed its target; delivery channel confirmed.
- Provenance: [evaluation protocol](../../docs/memory-v8/evaluation-protocol.md) and [results](../../docs/memory-v8/evaluation-results.md); the pre-trial smokes
  ([0923](../journal/2026/2026-10-02-memory-v8-smoke.md),
  [0924](../journal/2026/2026-10-02-memory-v8-runtimes-verified.md)) are
  excluded from the acceptance margins by the protocol.
