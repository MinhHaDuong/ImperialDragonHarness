---
name: maw-audit
description: "Audit test-suite quality by mutation testing: verify that each test actually catches the defect it claims to catch, stays green under harmless refactors, and guards the whole defect class rather than one instance. The three lenses: fang (a behavior-changing mutation must turn the test RED — else toothless), handcuff (a behavior-preserving refactor must keep it GREEN — else over-scoped), scope (a caught mutation replayed at sibling sites — survivors mean instance-pinned). Discovers its own config — no per-repo setup. EXPENSIVE on-demand (the validating fang-only run was ~1.3M tokens / ~29 min); never invoke casually. The name: the maw is the beast's devouring jaws — the audit inspects every tooth, not just one fang. Formerly fang-audit."
disable-model-invocation: false
user-invocable: true
argument-hint: "[run in the target repo; it discovers its own config — optional overrides via the Workflow args input]"
---

# Maw Audit — does each test have teeth, and the right ones?

*The **maw** is a predator's mouth, jaws, and gullet seen as the thing that
devours — the whole bite, not one tooth. v1 of this skill audited single fangs
(sensitivity only) and was named `fang-audit`; since the handcuff and scope
passes landed it inspects the entire jaw, and the name grew with it.*

A green test suite tells you nothing about whether a test would go **red** if the
code it covers regressed — nor whether it goes red on a harmless refactor, nor
whether it guards the whole defect class or just one instance. This skill answers
all three, per test, empirically — mutate the source, run the test, observe
red/green — using the `Workflow` fan-out capability, one Opus agent per test file
in its own throwaway git worktree. Output is an audit report with suggestions;
**no test or source code is changed** in the real tree (mutations live and die in
worktrees).

Three axes, three oracles, ONE workflow:

- **🦷 Fang (sensitivity)** — a behavior-CHANGING mutation must make the test go
  RED. A test that stays green is **toothless**.
- **🔓 Handcuff (robustness)** — a behavior-PRESERVING refactor must keep the test
  GREEN. A test that goes red is **over-scoped**: it asserts on internal form the
  contract does not promise, and blocks legitimate evolution. (INVERTED oracle —
  here red is bad.)
- **🧬 Scope / altitude (class coverage)** — each caught mutation operator is
  replayed at structurally-similar SIBLING sites. If siblings survive, the test
  is **instance-pinned** — it guards the past, not the future; flag for promotion
  to a class/invariant guard.

Right-scoped on all three = bites the defect, tolerates refactors, guards the
whole class.

> ⚠️ **EXPENSIVE — on-demand only.** The validating git-erg fang-only run was
> **~1.3M tokens / ~29 minutes** across ~31 agents (one Opus agent per test file
> + a Sonnet skeptic per accusation). The three-axis run is larger still (it adds
> a handcuff and a scope pass). This is NOT a per-PR gate and NOT a casual check.
> Run it deliberately, on a stable suite. The cheap per-PR tier is the
> `test-quality.py` flakiness/independence/speed utility (zero tokens) — see the
> precheck below.

## Just Work (tm) — discovery, not per-repo config

**There is NO per-repo CONFIG block to pre-author, and you never edit any skill
file to run an audit.** At run start a **DISCOVERY** phase reads the LAUNCH repo
(the repo this session is rooted in) — Makefile, `pyproject.toml`, `go.mod`,
`package.json`, the test tree, and each test file's imports and call sites — and
**derives** everything the audit needs:

- the test command (with a cache-buster — a cached PASS would falsely exonerate a
  mutation) and the directory it runs in,
- the **test↔source pairing table** (each test mapped to the source file(s) it
  actually exercises, with the import/call-site evidence recorded),
- language-specific mutation + refactor heuristics,
- the `test-quality.py` flakiness-gate invocation **if** the language has an
  adapter (`test-quality.py` ships a **Go adapter only** today — a Python/other
  suite gets an empty `PRECHECK_CMD` and the determinism gate skips openly).

This is **informed derivation by reading** — allowed. The **BANNED** thing is the
blind filename-glob heuristic (`X_test → X.go`), which returned a *nonexistent*
file for 5 of 19 git-erg tests, including both canaries, silently breaking the
validity gate. Discovery never guesses from a name alone.

If discovery cannot derive a pairing table (and no override is supplied), the run
**aborts openly** — it will not fall back to the banned glob.

### Optional overrides (never prerequisites)

Anything discovery would derive can be **pinned** by passing it through the
Workflow `args` input — an explicit override always wins. But every key is
optional; discovery fills whatever the args omit. The merge order is
`FALLBACKS < discovery < args`. Override keys: `PROJECT`, `LANGUAGE`,
`PACKAGE_HINT`, `SRC_DIR`, `OUTPUT`, `RUN_TEST`, `DEFAULT_TAGS`, `GUARD_TAGS`,
`MUTATION_HEURISTICS`, `HANDCUFF_HEURISTICS`, `BEHAVIORAL`, `GUARDS`,
`UNTRACKED_SEED`, `PRECHECK_CMD`, `RISK`, `HOME`. Path values (`OUTPUT`,
`UNTRACKED_SEED[].from`) may use a leading `~/`; the script expands it only if
you also pass `HOME` (the Workflow sandbox has no Node `process` global, so HOME
cannot come from the environment — pre-expand to absolute form when in doubt).

`GUARDS` (the designated canary files that validate the audit itself) stays an
explicit human **opt-in** — never auto-discovered. With no guards designated the
canary gate is **skipped openly** (the report says so); it is never faked on an
empty set.

> **Reproducing the git-erg reference run** (the one with a live canary gate)
> therefore needs **two overrides discovery cannot derive**: `GUARDS` (the
> designated canary file + its primary canary mutation — an opt-in, never
> auto-discovered) and `UNTRACKED_SEED` (the uncommitted build inputs the guard
> build needs, which a fresh worktree lacks — only the committed tree
> propagates). A `GUARDS`-only reproduction whose guard test depends on an
> untracked input will fail at the guard baseline; pair the two. Without
> `GUARDS` the run still completes — the canary gate just skips openly.

## How it runs

> **HARD REQUIREMENT: invoke from a session rooted in the TARGET / launch repo.**
> The Workflow tool cuts each agent's throwaway worktree from the *session's*
> repository (probe-verified, ticket 0221). Launched from any other repo, every
> agent lands in a tree without the configured sources and fails at baseline. To
> audit `~/git-erg`, open the Claude session in `~/git-erg`.

The workflow is a `Workflow`-tool script: `skills/maw-audit/maw-audit.js`.
Phases:

0. **Discovery** (read-only, non-isolated) — derives the config from the launch
   repo (above).
1. **Precheck (determinism gate)** — a precheck agent runs the `test-quality.py`
   flakiness gate (exit-code contract: 0 = stable, 2 = new flakiness). **You
   cannot mutation-test a flaky suite.** On a non-clean gate the workflow
   **aborts** with `suite is flaky, verdicts untrustworthy`. If discovery finds
   no flakiness adapter for the language, the gate **skips openly** (warn-and-
   proceed) rather than aborting a language it cannot pre-vet — the report records
   the un-vetted state.
2. **Audit — fang pass** (fan-out, Opus, `isolation: 'worktree'`) — one agent per
   behavioral test file. Each runs a self-contained mutate→test→revert loop and
   classifies every behavior-CHANGING mutation (see verdict rules).
3. **Skeptic** (Sonnet, per accusation) — every `survived` (toothless) and every
   `equivalent` verdict passes through a cross-model adversarial skeptic.
4. **Handcuff pass** (fan-out, Opus, isolated; own Sonnet skeptic) — applies
   behavior-PRESERVING refactors with the INVERTED oracle (red = over-scoped). Its
   skeptic re-checks every accusation: a red on a refactor that *secretly* changed
   behavior is a legitimate fang, withdrawn (mirror of the equivalent-mutant
   skeptic).
5. **Scope pass** (fan-out, Opus, isolated) — replays each fang-caught operator at
   sibling sites; surviving siblings = instance-pinned contract.
6. **Guards** (serialized) — the designated canary guard tests run alone (not
   under fan-out load). Skipped openly if none designated.
7. **Cleanup** — prunes any hand-rolled `/tmp/fang-*` scratch worktrees agents
   left on detached HEAD.

Then the engine assembles a deterministic report (no LLM formatting) and returns
it; write it to `CONFIG.OUTPUT`.

## Verdict rules (precision-critical — kept verbatim from the proven prototype)

Fang pass:

- **`caught`** — a test went red **AND at least one red test is defined in the
  audited file** (`failingTests ∩ OWN_FUNCS ≠ ∅`). Self-proving fang. A mutation
  caught only by a *sibling* file gives this file no fang credit → `survived`.
- **`survived`** (= toothless, an ACCUSATION) — no own-file test failed **and**
  the agent can exhibit a concrete distinguishing input where the mutated code is
  observably wrong. Must populate `survivedJustification`.
- **`equivalent`** (NOT an accusation) — no test failed and no distinguishing
  input exists (the classic equivalent-mutant trap).
- **`compile-error`** — mutation didn't build; the agent picks a different one.

Handcuff pass (inverted): **`robust`** (stayed green — healthy), **`handcuff`**
(red on a TRULY behavior-preserving refactor — over-scoped, an accusation),
**`not-preserving`** (the refactor secretly changed behavior — the red is a fang,
withdrawn by the skeptic).

Scope pass: **`class-guarded`** (siblings also caught — right altitude),
**`instance-pinned`** (a sibling survived — under-scoped, flag for class
promotion), **`no-siblings`** (no structurally-similar site to widen to).

## Canary gate — scoped to designated guard files only

The canary (validity) gate asserts that the designated guard tests **caught**
their primary canary mutation. **Canary designation is a workflow input
(`GUARDS`), never an agent claim.** The engine tags findings structurally
(`_isGuardFile`) and the gate counts only `f._isGuardFile && f.isCanary`, so a
behavioral agent's self-set `isCanary` can never pollute it (the isCanary-pollution
fix, 0182 crit 7). With no guards designated, the gate is **skipped openly**.

## Free riders + risk × churn (no extra runs)

Two extra lenses are computed from the mutation data already collected — **oracle
strength** (mutants killed per test func) and **diagnosticity** (tests fired per
killed mutant). The toothless list and the unified per-test three-axis table are
sorted by **risk × churn** (churn = commit count per file from `git log --follow`;
risk = the human-supplied `CONFIG.RISK` weight, default 1) so the highest
blast-radius × change-frequency findings surface first.

> **`RISK` override keys are the full repo-root-relative test path** (e.g.
> `{"tests/test_foo.py": 2.0}`), matching the identity discovery returns — not a
> bare basename. Test identity is one canonical path everywhere in the engine
> (0226); a basename key silently weights nothing on a path-prefixed repo.

## Steps

0. **Open the session in the target repo** (see the hard requirement above).
1. Confirm the suite is worth a ≥1.3M-token audit and is reasonably stable.
2. Run `skills/maw-audit/maw-audit.js` with the Workflow tool. Pass an `args`
   object only if you want to **override** a derived value or **opt in** to guard
   files; otherwise pass nothing — discovery derives the config.
3. If it aborts at discovery (no pairing table) or the precheck (flaky suite),
   resolve that first — supply an explicit `BEHAVIORAL` override, or stabilize the
   flaky tests.
4. Write the returned `report` to `CONFIG.OUTPUT`. **Spot-check 2–3 rows on each
   axis** against their evidence before acting on them.
5. Applying fangs, loosening handcuffs, and promoting instance-pinned tests to
   class guards are separate follow-ups — this audit changes no test code.

## Language-pluggable — the documented zero-prep path (non-Go validation)

Because discovery derives the config by reading the repo, a non-Go run is
**zero-prep**: no `.maw-audit.json`, no pairing table to author. The validated
second-language target is **`~/aedist-technical-report`** (a `uv` Python project,
30+ test files). The exact launch procedure:

1. Open a Claude session **rooted in `~/aedist-technical-report`** (the
   hard requirement — Workflow agents cut their worktrees from the session repo;
   this run **cannot** be launched from a `~/.claude`-rooted session).
2. Invoke `maw-audit` with **no args** (or pass `{ "RISK": {...} }` / a `GUARDS`
   opt-in only if desired). Discovery reads `pyproject.toml` / `pytest.ini` and
   the `tests/` tree, derives `pytest -p no:cacheprovider ...` (cache-buster
   included) and the test↔source pairing table from imports.
3. The precheck. `~/.claude/scripts/test-quality.py` ships a **Go adapter only**
   (`--adapter` accepts `go`; there is no Python adapter today), so for a Python
   suite discovery returns an empty `PRECHECK_CMD` and the determinism gate
   **skips openly** (warn-and-proceed; the report carries a ⏭️ banner). Do NOT
   hand-wire `PRECHECK_CMD` with `--adapter python` — argparse rejects it (exit
   2) and the precheck aborts the run. Stabilize a Python suite manually (or add
   a Python adapter to `test-quality.py`) before trusting the toothless rows.
4. **Expected cost scale.** The git-erg reference run was ~1.3M tokens / ~29 min
   for 19 files, fang-only. AEDIST has ~30+ test files and the v2 workflow adds a
   handcuff pass and a scope pass, so budget on the order of **2–4×** the git-erg
   run (~3–5M tokens / ~1–1.5 h). It is an explicit, human-authorized spend — not
   a casual check.

The real AEDIST run is a **separate human-authorized follow-up**, not part of the
skill's own validation (it cannot be driven from this harness session). This
documented path satisfies the "validated on a non-Go repo OR a documented plug-in
path" criterion via the documented-path branch.
