---
name: test-audit-llm
description: "Read-and-judge audit of test quality: one judge reads each test file and scores four lenses — faithfulness (does it exercise real paths or a mocked fiction?), intent legibility (does the name lie? does it pass for the wrong reason?), negative-space coverage (only the happy path?), and change-detector smell (asserts HOW the code works, not WHAT it produces?). Runs nothing — no mutation, no test execution. Cheap-model bulk pass plus strong-model escalation for the top flagged files. Advisory only: findings feed ticket creation, never a CI gate. The read-and-judge sibling to maw-audit (which mutates and runs); this one only reads. EXPENSIVE on-demand, but much cheaper than maw-audit (no compile/run loop)."
disable-model-invocation: false
user-invocable: true
argument-hint: "[run in the target repo; it discovers the test-file list itself — optional overrides via the Workflow args input]"
---

# Test-Audit (read-and-judge) — does each test mean what it says?

A green test suite tells you nothing about whether a test **mocks away the very
thing it claims to verify**, whether its **name lies** about what it checks,
whether it ever leaves the **happy path**, or whether it asserts **how** the code
works rather than **what** it produces. None of those can be measured by running
the test — they require *reading* it and *judging* intent. This skill is that
judge.

It is the **read-and-judge sibling to `maw-audit`** (ticket 0182/0219). maw-audit
**mutates** the source and **runs** the suite to mechanize three lenses (fang /
handcuff / scope). A second family of test-quality lenses cannot be measured that
way; they need a reader's judgement with **no execution**. Different mechanism,
separate skill, so neither bloats the other (ticket 0183).

> ⚠️ **ADVISORY ONLY — these are SOFT opinions, never a gate.** Every verdict is
> a reader's judgement, not a pass/fail oracle. The report leads with a banner
> saying so. Findings **feed ticket creation** (`tickets/erg new`); they do NOT
> wire into CI, do NOT fail an exit code, and MUST NOT block a merge. Spot-check
> each row against its cited evidence before acting — a judge can be wrong.

## The four lenses (one judge, one read, four verdicts)

ONE judge agent reads each test file **once** and returns a verdict on each lens
it violates — **not four passes** (YAGNI; one read is enough):

- **🪞 Faithfulness / test-reality gap** — does the test exercise prod-like
  paths, or a **mocked fiction** that stays green while production breaks? Flag
  heavy mocking that stubs the very thing under test.
- **🪧 Intent legibility** — can a reader tell WHICH contract is asserted and
  WHY, without running it? Flag a test whose **name lies**, or that **passes for
  the wrong reason** (a vacuous assertion that cannot fail).
- **🕳️ Negative-space coverage** — does it test error paths, boundaries,
  malformed / empty / huge inputs — or **only the happy path**?
- **🔁 Change-detector smell** — does it assert **HOW** the code works (call
  sequences, mock-interaction order, internal call counts) instead of **WHAT**
  it produces? The structural cause of over-scoped tests.

## Cost — EXPENSIVE on-demand, but cheaper than maw-audit

This is a fan-out of one LLM judge per test file, so it is **token-heavy and
on-demand** — not a per-PR gate, not a casual check. But it is **materially
cheaper than maw-audit**: there is **no compile/run/revert loop and no worktree**
(it executes nothing), and the bulk pass uses a **cheap model**. Only the top
**K = 8** flagged / low-confidence files escalate to a strong model, so a large
suite can never fan a second full wave. Run it deliberately, on a stable suite.

## Two-tier model strategy (cheap bulk + capped strong escalation)

Model choice is **only** via the `agent()` `{ model }` parameter — there is no
direct API call (Claude Code uses subscription auth, like maw-audit).

1. **Bulk pass** — one **`haiku`** judge per test file, four lenses in one read.
   Each finding carries a `confidence`.
2. **Escalate** — files with a **low-confidence** or **high-severity** finding
   are ranked by **severity × risk × churn** and only the **top K = 8** are
   re-judged with **`sonnet`**. The sonnet verdict **replaces** the haiku verdict
   for that file (final say, mirroring maw-audit's skeptic). **The escalation
   wave is capped at ≤ K agents** — this is the invariant that keeps a big suite
   from fanning a second full pass; `ESCALATE_K` is an optional override.

Churn is **decoration** (a sort weight) and is computed in a `try/catch` that
degrades to severity-only ranking — it can never kill the run (maw-audit's churn
agent once threw and discarded a 1.36M-token run; this one cannot).

## Just Work (tm) — discovery, not per-repo config

**There is NO per-repo CONFIG block, and you never edit a skill file to run an
audit.** A run-start **DISCOVERY** phase reads the launch repo (build/test config
+ the test tree) and **derives the test-file list** plus the framework
conventions the judge needs for context.

Discovery here is **deliberately slimmer than maw-audit's**: because this skill
**executes nothing**, it derives **no test command, no test→source pairing table,
and no mutation heuristics** — just the files to judge. It excludes files the
project does not collect (e.g. anything under a pytest `norecursedirs` directory
such as `skills/*/fixtures`). If discovery cannot derive a file list and no
override is supplied, the run **aborts openly**.

Optional overrides (never prerequisites), passed via the Workflow `args` input —
merge order `FALLBACKS < discovery < args`: `PROJECT`, `LANGUAGE`, `FRAMEWORK`,
`OUTPUT`, `TEST_FILES`, `ESCALATE_K`, `RISK`, `HOME`. Path values (`OUTPUT`) may
use a leading `~/`; the sandbox has no Node `process`, so `~/` is expanded **only
if** you also pass `HOME` (pre-expand to absolute when in doubt).

## Identity & composition (file granularity)

Every finding's **identity is the repo-root-relative test-file path** assigned by
the dispatch loop — **never** the agent's self-report. This is the same identity
maw-audit reports (its `file.test`).

This skill reports at **FILE granularity**. 0184's per-function
`<package>::<TestName>` and 0229's `<file>::<function>` are finer-grained, so
**composition with them is a file-level roll-up on the shared file key**. The
ticket's exit criterion offers "compose with maw-audit OR a clean standalone
report"; this is the clean standalone, sharing the file key so a downstream tool
can join it to maw-audit's per-file rows.

## Output

The engine assembles a **deterministic** report (no LLM formatting):

- a **markdown** report (`CONFIG.OUTPUT`, default `~/TEST-AUDIT-LLM.md`) — banner,
  per-lens summary, an all-findings table sorted by severity × risk × churn, and
  per-file summaries; and
- a **JSON sidecar** (`OUTPUT` with the extension replaced by `.json`) — one object per finding
  with the canonical `{ identity, lens, severity, rationale }` schema (plus
  `suggestion`, `confidence`, `escalated`), the machine-readable composition
  artifact.

## Smoke fixture (acceptance anchor)

`skills/test-audit-llm/fixtures/` ships a **known-bad** sample test
(`fixture_payment_gateway_test.py` + its subject `payment_gateway.py`) the judge
**MUST flag on ≥ 1 lens** — it trips all four: it **mocks the subject-under-test**
(faithfulness), is **named `test_charge_succeeds` while asserting call order**
(intent), exercises **only the happy path** (negative-space), and **asserts the
internal call sequence** (change-detector). The filename is `fixture_*_test.py`,
not `test_*.py`, and `pytest.ini` excludes `skills/*/fixtures` via
`norecursedirs`, so the project run never collects it. Do not "fix" it — its
badness is the fixture.

## Steps

0. **Open the session in the target repo** (Workflow agents derive context from
   the session's repo).
1. Confirm the suite is worth an on-demand fan-out audit.
2. Run `skills/test-audit-llm/test-audit-llm.js` with the Workflow tool. Pass an
   `args` object only to **override** a derived value (e.g. `RISK`, `TEST_FILES`,
   `ESCALATE_K`); otherwise pass nothing — discovery derives the file list.
3. If it aborts at discovery (no file list), resolve that first — supply an
   explicit `TEST_FILES` override.
4. Write the returned `report` to `CONFIG.OUTPUT` and the `sidecar` to
   `sidecarOutput`. **Spot-check 2–3 rows against their rationale** before acting
   — the verdicts are advisory.
5. Triage findings into tickets (`tickets/erg new`). This audit changes no test
   code and gates nothing.
