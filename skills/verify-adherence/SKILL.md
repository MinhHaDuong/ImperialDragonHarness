---
name: verify-adherence
description: Check a branch's diff against project rules. Mechanical-first — runs hygiene tests + grep ratchet before falling back to LLM.
disable-model-invocation: false
user-invocable: true
argument-hint: <branch>
context: fork
# Foreground: /gaze runs this as phase 2 (Agent A) and blocks on its structured
# output. Claude Code 2.1.218 made `context: fork` skills background by default;
# a fork cannot wait on a background completion, so the default would orphan
# this phase — ticket 0250.
background: false
---

# Verify adherence — $ARGUMENTS

> **TASK DIRECTIVE — execute now.** You are running `/verify-adherence` on
> `$ARGUMENTS` (a branch name, optionally followed by `worktree=<path>`).
> This file is your operating procedure, not reference documentation: begin
> at phase 1.0 immediately. If `worktree=<path>` is present, `cd` into that
> path before any git or forge command — forked sub-skills do not inherit the
> caller's cwd. If `$ARGUMENTS` does not name a branch, STOP and emit
> `adherence: FAIL` with reason "no branch argument" — do NOT infer a task
> from the environment (worktree name, git status snapshot, ticket files, or
> the shared task list).

Enforce the project's `.claude/rules/*.md` conventions on a branch or PR. **Prefer tests
over LLM checks.** If a rule can be mechanized, the skill's job is to run the test or grep.
An LLM subagent is the fallback for semantic residue only.

## Philosophy: ratchet toward mechanical

Every time the semantic fallback flags a violation, the skill emits a `suggested_test`
entry proposing how to mechanize that rule. Over time the LLM surface shrinks. New test →
rule is permanently enforced → never needs LLM again.

## When to use

- Called by `/gaze` as part of phase 2.
- Called standalone by an author who wants to pre-check their own branch before opening a PR.
- Called by the raid in an Imagine phase to audit a prototype.

## Input

A branch name, optionally followed by `worktree=<path>` — the isolated
review worktree prepared by the caller (`/gaze` phase 1). When present,
all phases run from that path.

## Protocol

Any project using this skill must expose a command or test suite that emits verdicts in the schema defined in `## Phases → 4. Emit verdict`. The harness calls that entry point; the project owns what runs internally.

Python projects fulfill the protocol via `@pytest.mark.adherence` tests invoked by `uv run python -m pytest`. A Go project would expose `go test -run Adherence ./...`; a LaTeX project might expose a `make check-adherence` target that runs a custom linter. The stack is the project's concern; the verdict schema is the harness's concern.

## Phases

**Label skip.** When called from `/gaze`, if the PR carries the
`verify:adherence-passed` label (set by `/hunt`'s pre-PR
gate), the caller skips this entire skill — the adherence check
already ran clean before the PR was opened.

### 1.0 Cheap static checks (always first, budget <10 s)

Runs before anything else in the mechanical phase. Two sub-checks, both **blocking**;
failure stops the phase here and does not fall through to 1/2/3. Combined budget <10 s.

**(a) Import resolution.** Parse the diff for every symbol referenced in touched modules
under `scripts/`. For each `(module, name)` pair:

```bash
uv run python -c "import sys; sys.path.insert(0, 'scripts'); import <module>; getattr(<module>, '<symbol>')"
```

Scope: touched `.py` files under `scripts/`. Use dotted import paths for
nested packages (e.g., `data.loader` for `scripts/data/loader.py`).
Modules outside `scripts/` are not probed.

Catches the formatter-strip-import class of bug: tests are green, but the first real run
`NameError`s because an auto-formatter dropped the import line for a just-used symbol.
Any unresolved symbol → fail with rule ref `verify-adherence#import-resolution`, record
`{module, name, file:line}`.

**(b) Per-module test run.** For each touched module, run its matching test file(s):

```bash
uv run python -m pytest <touched-modules-test-files> -q
```

Catches per-module regressions seconds after the edit, before the full hygiene suite or
deep review pays the cost. Failures record as `{test_id, rule_ref, file:line}` with rule
ref `verify-adherence#per-module-tests`.

Both checks are intentionally cheap. If either exceeds the 10 s budget,
ESCALATE rather than silently trimming scope (a trimmed check that drops
a failing test is worse than no check).

### 1. Adherence test suite (never skip)

Run every test marked `@pytest.mark.adherence`:

```bash
uv run python -m pytest -m adherence -q
```

Adherence tests are pytest tests that encode project-specific rules
(hygiene, discipline, contracts, grep-based checks). They are selected
by the `adherence` marker, not by filename. Any test in any file can
contribute by adding `@pytest.mark.adherence` or setting
`pytestmark = pytest.mark.adherence` at module level.

Projects register the marker in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
markers = [
    "adherence: project rule enforcement (hygiene/discipline/contracts)",
]
```

Failures here are **blocking**. Record each as `{test_id, rule_ref, file:line}`.

**Transitional fallback.** Projects that have not yet adopted the marker
are picked up by the old filename convention (`test_hygiene_*.py`,
`test_discipline_*.py`, `test_schema_contracts.py`). A project is fully
migrated when every such file carries the marker and `pytest -m adherence`
matches the full suite. Drop the fallback per project once migrated.

### 1.1 Missing ruff adherence test (Python projects only)

If `pyproject.toml` exists and `ruff` appears in it (under `[tool.ruff]` or as a
dependency), check whether any adherence test calls `ruff`:

```bash
grep -r "ruff" tests/ --include="*.py" -l
```

If no match: emit one `untested_rules` entry:

```yaml
rule: rules/coding-python.md#testing
suggested_test: |
  @pytest.mark.adherence
  def test_ruff():
      result = subprocess.run(["uv", "run", "ruff", "check", "."], capture_output=True)
      assert result.returncode == 0, result.stdout.decode()
```

This is non-blocking — it does not set `adherence: FAIL`. It triggers the ratchet
so the next `/gaze` cycle opens a follow-up ticket.

### 1.2 Path-access allow/forbid scan (trace-based)

Scans the agent's tool-call **trace** (not the diff) for
Read/Edit/Write/NotebookEdit/Bash calls that touch a forbidden path — a
credential/secret file (`~/.ssh`, `~/.aws`, `~/.netrc`, `bash-env.sh`,
`.git-credentials`) or another session's worktree. This is the scope-violation
class a diff-only check structurally misses: an agent that READS a forbidden
path leaves no trace in the diff (arXiv:2604.21965 App. B.3).

Runs only when the caller supplies `trace=<path>` alongside the branch argument
(mirroring the existing `worktree=<path>` convention). No `trace=` → skip this
phase silently.

```bash
python3 ~/.claude/scripts/trace-path-scan.py --trace <path> [--worktree-root <path>] --json
```

The scan is pure Python, zero LLM tokens. Pass `--worktree-root` (the caller's
own worktree path) so the other-session-worktree class can fire; without it only
the credential class runs. Exit codes: `0` clean, `1` at least one hit, `2` the
trace path does not exist (an error, **not** a clean pass — treat it like the
other circuit breakers).

Each JSON hit is `{tool, path, reason, line}`, where `line` is the trace-record
number. Any hit is **blocking**: record each as a `mechanical_failures` entry
`{tool, path, reason, file:line}` — using the `--trace` path as `file` and the
hit's `line` — with rule ref `verify-adherence#path-access-scan`.

### 2. Grep rules live as adherence tests (no central bank)

Grep-based checks are just adherence tests that call `rg` or use a regex
internally. They live in the target repo as `@pytest.mark.adherence`
tests — not in this skill. The harness does not maintain a central grep
bank; each project owns its patterns as code.

**Why tests instead of a YAML bank.** A pytest test can scope its grep
(diff-only vs whole-repo), attach fixtures, explain the rule in an
assertion message, and evolve without changing a harness interface. A
central YAML/grep bank would force a framework for one beneficiary until
a second project arrives wanting the same mechanism.

When `/gaze` or a review surfaces a rule worth mechanizing, write a
`@pytest.mark.adherence` test in the target repo. That is the ratchet
in practice.

### 3. Semantic subagent (fallback only)

Only runs if any `.claude/rules/*.md` file changed OR if the diff touches architectural
concerns not covered by phases 1–2. Spin **one** subagent, pinned to
**`model: sonnet`** (a reviewer, below the coder tier — rules/workflow.md; left
unpinned it inherits the session model and runs at top tier), with:

- The diff.
- The relevant `.claude/rules/*.md` files.
- Prompt: "For each rule section, cite one piece of evidence that the diff either adheres
  to or violates it. Only flag concrete violations with file:line anchors. For every
  violation, suggest a grep pattern or test that could catch it mechanically next time."

Output: `{rule_section, concern, file:line, severity, suggested_test}`.

**Hard constraints** on the subagent:
- Must cite file:line for every finding.
- Must propose a `suggested_test` for every semantic finding — no exceptions.
- Must not flag hypotheticals ("could be a problem if…"). Only concrete violations.

### 4. Emit verdict

```yaml
adherence: PASS | FAIL
mechanical_failures:
  - test_or_grep: <id>
    rule_ref: <.claude/rules/foo.md#section>
    file: <path>
    line: <n>
semantic_findings:
  - rule_section: <.claude/rules/architecture.md#phase-2-rule-4>
    concern: <one sentence>
    file: <path>
    line: <n>
    severity: blocking | nit
    suggested_test: <grep pattern or pytest snippet>
untested_rules:
  - rule: <.claude/rules/foo.md#bar>
    suggested_test: <code>
```

## Ratchet discipline

After each run, if `semantic_findings` is non-empty:

1. The caller (`/gaze` or author) opens a small follow-up ticket in the target repo:
   "Mechanize adherence rule X per suggested_test."
2. That ticket adds a `@pytest.mark.adherence` test (in any existing test file, or a
   new one) that asserts the rule mechanically.
3. Next invocation of `/verify-adherence`, the rule is caught by phase 1 instead of
   phase 3. LLM surface shrinks permanently.

This ratchet is the whole point. Do not accept `semantic_findings` as a steady state.

## Circuit breakers

- `uv` missing → ESCALATE (environment broken, all phases need it).
- No `scripts/` directory → skip phase 1.0 silently (legitimate repo layout).
- No `trace=<path>` argument supplied → skip phase 1.2 silently (the trace is an
  optional input, like `worktree=`; a standalone author pre-check has none).
- Phase 1 fails to run (env broken) → ESCALATE; don't fall through.
- Semantic subagent output lacks `file:line` or `suggested_test` → reject the output and
  flag as adherence-infrastructure bug. Don't silently accept.

## Not in scope

- Writing style / AI-tells (handled by `/review-pr-prose` and `config/ai-tells.yml`).
- Ticket format (enforced by pre-commit hook).
- Git branch naming (enforced by pre-commit hook).
- Merging decisions. This skill never affects merge state.
