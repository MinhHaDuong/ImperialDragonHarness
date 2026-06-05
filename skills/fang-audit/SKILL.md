---
name: fang-audit
description: "Fan-out mutation-testing audit — does each test FAIL on the defect it claims to catch? Surfaces toothless tests. EXPENSIVE on-demand (the validating run was ~1.3M tokens / ~29 min); never invoke casually."
disable-model-invocation: false
user-invocable: true
argument-hint: "[after editing the CONFIG block in fang-audit.js]"
---

# Fang Audit — does each test have teeth?

A green test suite tells you nothing about whether a test would go **red** if the
code it covers regressed. This skill answers, per test, the only question that
matters: **would it actually fail on the defect class it claims to catch?** It
answers empirically — mutate the source, run the test, observe red/green — using
the `Workflow` fan-out capability, one Opus agent per test file in its own
throwaway git worktree. Output is an audit report with suggestions; **no test or
source code is changed** in the real tree (mutations live and die in worktrees).

> ⚠️ **EXPENSIVE — on-demand only.** The validating git-erg run was **~1.3M
> tokens / ~29 minutes** across ~31 agents (one Opus agent per test file + a
> Sonnet skeptic per accusation). This is NOT a per-PR gate and NOT a casual
> check. Run it deliberately, on a stable suite, when you want a real mutation
> audit of test quality. The cheap per-PR tier is the `test-quality.py`
> flakiness/independence/speed utility (zero tokens) — see the precheck below.

This is **fang-only v1**. The handcuff (robustness), scope/altitude (class
coverage), three-axis report, and multi-language validation are a separate,
blocked follow-up — do not expect them here.

## How it runs

> **HARD REQUIREMENT: invoke from a session rooted in the TARGET repo.**
> The Workflow tool cuts each agent's throwaway worktree from the *session's*
> repository (probe-verified, ticket 0221). Launched from any other repo,
> every agent lands in a tree without the configured sources and fails at
> baseline. To audit `~/git-erg`, open the Claude session in `~/git-erg`.

The workflow is a `Workflow`-tool script: `skills/fang-audit/fang-audit.js`.
You configure it, then run it with the Workflow tool. Phases:

0. **Precheck (determinism gate)** — a precheck agent runs the `test-quality.py`
   flakiness gate (`~/.claude/scripts/test-quality.py flakiness`, exit-code
   contract: 0 = stable, 2 = new flakiness). **You cannot mutation-test a flaky
   suite** — a flaky verdict is noise that swamps the mutation signal. If the
   gate does not pass cleanly the workflow **aborts** with
   `suite is flaky, verdicts untrustworthy` and runs no mutations. This blocks
   the fan-out; it is a dependency, not a warning.
1. **Audit** (fan-out, Opus, `isolation: 'worktree'`) — one agent per behavioral
   test file from the pairing table. Each runs a self-contained
   mutate→test→revert loop and classifies every mutation (see verdict rules).
2. **Skeptic** (Sonnet, per accusation) — every `survived` (toothless) and every
   `equivalent` verdict passes through a cross-model adversarial skeptic before
   synthesis, policing both false accusations and false exonerations.
3. **Guards** (serialized) — the designated canary guard tests run alone (not
   under fan-out load) because they assert on timing / allocation / FD counts
   that skew under concurrent test processes.

Then the engine assembles a deterministic report (no LLM formatting) and returns
it; write it to `CONFIG.OUTPUT`.

## Configuration — `.fang-audit.json` in the target repo, never this skill

**You never edit any skill file to run an audit.** The target repo owns its
configuration in a committed `.fang-audit.json` at its root. At invocation,
read that file and pass its parsed content as the Workflow `args` input —
the script merges it over the built-in DEFAULTS (the validated git-erg
reference values, kept in `fang-audit.js` as living documentation of every
knob). Path values (`OUTPUT`, `UNTRACKED_SEED[].from`) may use a leading
`~/`; the script expands it.

If `.fang-audit.json` is missing, STOP and hand the user a template built
from the DEFAULTS block — do not edit `fang-audit.js`, do not guess a
pairing table.

**The knobs are explicit inputs, NOT name heuristics** — the
`X_test.go → X.go` heuristic returned a *nonexistent* file for 5 of 19
git-erg tests, including both canaries, silently breaking the validity gate.
Always supply the table.

| Knob | What it is |
|---|---|
| `PROJECT` / `LANGUAGE` / `PACKAGE_HINT` | Labels surfaced in prompts and the report title. |
| `OUTPUT` | Absolute path in the **main** repo where the report is written (worktrees are throwaway). |
| `RUN_TEST` (+ `DEFAULT_TAGS` / `GUARD_TAGS`) | The test command each agent runs; the engine substitutes `<TAGS>`. Keep the cache-buster (`-count=1` / `-p no:cacheprovider`) — a cached PASS falsely exonerates a mutation. |
| `MUTATION_HEURISTICS` | Language-specific examples of a minimal, compiling, behavior-changing mutation (steers agents off strawmen). |
| `BEHAVIORAL` | The **test↔source pairing table** — explicit map of each test file to the source target(s) it may mutate. |
| `GUARDS` | The **designated canary files** + each one's explicit primary `canary` mutation that MUST trip the guard. Canary designation is a CONFIG input — never an agent claim (see below). |
| `UNTRACKED_SEED` | Inputs the test build needs that are **not committed** (a fresh worktree only has the committed tree). Each `{dest, from}` is copied in by the guard agent before its baseline check. Empty list = no seeding. |
| `PRECHECK_CMD` | The determinism gate command (the 0184 `test-quality.py flakiness` invocation for this repo). |
| `RISK` | Optional per-file risk multiplier for the report sort. **The human owns the risk judgment** — it is never inferred. Default 1.0. |

## Verdict rules (precision-critical — kept verbatim from the proven prototype)

- **`caught`** — a test went red **AND at least one red test is defined in the
  audited file** (`failingTests ∩ OWN_FUNCS ≠ ∅`). Self-proving fang. A mutation
  caught only by a *sibling* file gives this file no fang credit → `survived`.
- **`survived`** (= toothless, an ACCUSATION) — no own-file test failed **and**
  the agent can exhibit a concrete distinguishing input where the mutated code is
  observably wrong. Must populate `survivedJustification`.
- **`equivalent`** (NOT an accusation) — no test failed and no distinguishing
  input exists (the classic equivalent-mutant trap). Carries a positive
  behavior-neutrality argument.
- **`compile-error`** — mutation didn't build; the agent picks a different one.

## Canary gate — scoped to designated guard files only

The canary (validity) gate asserts that the designated guard tests **caught**
their primary canary mutation. If a canary is not caught, the mutation harness
itself is miswired and the whole toothless list is suspect.

**The fix baked into this skill (ticket 0182, crit 7):** canary designation is a
**workflow input** (`CONFIG.GUARDS`), never an agent claim. The prototype trusted
an `isCanary` flag from *all* agents; behavioral audit agents mis-set it on their
own findings and produced a false `FAIL`. The engine tags findings structurally
(`_isGuardFile`, set from the `GUARDS` dispatch) and the gate counts only
`f._isGuardFile && f.isCanary` — a behavioral agent can never pollute it. The
prototype's ad-hoc filename-regex patch is now a structural invariant.

## Free riders + risk × churn (no extra runs)

Two extra lenses are computed from the mutation data already collected:

- **Oracle strength** — mutants killed per test func (strong assertion kills many).
- **Diagnosticity** — tests fired per killed mutant (fewer = sharper bisection).

The toothless list is sorted by **risk × churn** (churn = commit count per file
from `git log --follow`; risk = the human-supplied `CONFIG.RISK` weight, default
1) so the highest blast-radius × change-frequency gaps surface first.

## Steps

0. **Open the session in the target repo** (see the hard requirement above).
1. Confirm the suite is worth a 1.3M-token audit and is reasonably stable.
2. Read `.fang-audit.json` at the target repo root. Missing → STOP and give
   the user a template (from the DEFAULTS block); never edit skill files.
3. Run `skills/fang-audit/fang-audit.js` with the Workflow tool, passing the
   parsed config as `args`.
4. If it aborts at the precheck, stabilize the flaky tests first — the verdicts
   are untrustworthy on a flaky suite, by design.
5. Write the returned `report` to `CONFIG.OUTPUT`. **Spot-check 2–3 toothless
   rows** against their distinguishing input before acting on them.
6. Applying the suggested fangs is a separate follow-up — this audit changes no
   test code.
