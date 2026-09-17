---
name: verify-adherence
description: "Check a branch's diff against project rules. Mechanical-first — runs hygiene tests + grep ratchet before falling back to LLM."
disable-model-invocation: false
user-invocable: true
argument-hint: "<branch> [worktree=<path>] [trace=<path>]"
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

Any project using this skill must declare an adherence command in its own
instructions, build file, or CI contract. That command owns the stack-specific
checks: imports, targeted tests, hygiene, linters, and rule enforcement. It
returns zero on success and non-zero on failure, with diagnostic output. The
harness invokes it unchanged and maps its result to phase 4's verdict schema;
the project need not implement that schema itself.

Discover the declaration, never infer a package manager from the language or
invent a test command. A named build target is one possible interface, not a
requirement for every consumer. The phases below run sequentially because an
earlier blocking failure must stop later review work.

## Phases

**Label skip.** When called from `/gaze`, if the PR carries the
`verify:adherence-passed` label (set by `/hunt`'s pre-PR
gate), the caller skips this entire skill — the adherence check
already ran clean before the PR was opened.

### 1.0 Cheap static checks (always first, budget <10 s)

Runs before the project command. Reference resolution is **blocking**;
failure stops the phase here and does not fall through to 1/2/3. Budget <10 s.
Import resolution and per-module tests belong to the project runner (phase 1).

**Reference resolution (prose).** This has a
blocking verdict: in a manuscript, `\cite`/`\ref` are external references and the
`.bib` is the symbol table, but there is no link step to reject a dangling one —
the toolchain warns, renders a placeholder, and exits 0. Skip when the diff
touches no `.tex`/`.qmd`/`.bib`.

**Scope by blast radius, not by touched files.** If the diff modifies a `.bib`,
check **every manuscript in the repo that cites it**, touched or not. This is the
whole point of the check: a purge scoped to one manuscript can remove an entry
from under another, and the victim is not rebuilt in that change, so its own build
gate stays silent. Restricting to touched files reproduces the blind spot. The
same holds one level down: a `\label` deleted in one file breaks a `\ref` in an
untouched sibling, so the resolution universe is the whole source tree of each
manuscript checked, never the touched file alone.

Textual, no build — that is what lets it see manuscripts this change never
rendered:

- LaTeX citations: every key of every citation command resolves to an entry in
  the project's `.bib`. Match the whole family, not one spelling: `\cite`,
  `\citep`, `\citet`, `\citeauthor`, `\citeyear`, `\nocite`, their starred
  forms, and the biblatex set `\parencite`, `\textcite`, `\autocite`. A
  multi-key argument (`\citep{a,b}`) counts as many keys as it lists.
- LaTeX crossrefs: every `\ref`, `\eqref`, `\autoref`, `\pageref`, `\cref`,
  `\Cref` resolves to a `\label{...}` somewhere in that manuscript's sources.
- Quarto/pandoc: same two checks, different syntax — `@key` and `[@key; @key2]`
  resolve to `.bib` entries, `@fig-`/`@tbl-`/`@sec-`/`@eq-` crossrefs to a
  labelled block. Enumerating the LaTeX forms alone leaves the check inert on a
  `.qmd` repo it claims to cover.

**Two exemptions, or the check cries wolf on valid sources.** `\nocite{*}` is a
wildcard meaning "every entry in the `.bib`", not a key — resolving it as one
fails a legitimate manuscript. And in a `.qmd`, `@` inside fenced blocks, inline
code, and verbatim spans is not a citation: pandoc ignores it there, so a Python
decorator or an email address in a code cell is not an unresolved reference.
Strip those contexts before scanning.

Any unresolved reference → fail with rule ref `verify-adherence#reference-resolution`,
record `{key, file:line, kind}`. Do not flag `Underfull`/`Overfull` or pre-existing
BibTeX field warnings. Doctrine and per-tool build recipes: `rules/manuscript-build.md`.

This check is intentionally cheap. If it exceeds the 10 s budget,
ESCALATE rather than silently trimming scope (a trimmed check that drops
a failing test is worse than no check).

### 1. Project runner (never skip)

Read the project instructions, build file, and CI configuration for an explicit
adherence entry point. Record the declaring file and line with the exact command.
A filename or a target named `lint` alone is not a declaration of adherence;
its documented purpose must establish that contract. If declarations conflict,
ESCALATE with their locations rather than choosing silently.

If none is declared, stop with blocking `adherence: FAIL`, reason
`no declared adherence runner`, rule ref `verify-adherence#project-runner`.
Do not guess from installed tools or add a dependency manifest to satisfy the
harness. A declared command whose executable or dependencies are missing is an
environment error: ESCALATE; never report a clean pass or skip the gate.

Invoke the declared command verbatim from the project worktree, including its
declared environment or wrapper. Keep its output and exit status. A non-zero
test/check result is blocking: map diagnostics into `mechanical_failures`,
preserving their test IDs and source anchors when available. If no finer anchor
is emitted, use the declaration's file and line and rule ref
`verify-adherence#project-runner`. A timeout or failure to execute is an
infrastructure escalation, not a test verdict. This runner is not subject to
phase 1.0's 10 s static-check budget.

For the harness repository itself, the Makefile explicitly documents its
adherence target: validate it with `make -n lint`, then run `make lint`.
Other projects may declare another target or a command without Make. All
stack-specific import probes and per-module tests remain project-owned.

### 1.2 Path-access allow/forbid scan (trace-based)

Scans the agent's tool-call **trace** (not the diff) for
Read/Edit/Write/NotebookEdit/Bash calls that touch a forbidden path — a
credential/secret file or sensitive environment loader (`~/.ssh`, `~/.aws`, `~/.netrc`, `bash-env.sh`,
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
internally. They live in the target repo as tests run by its declared adherence
command — not in this skill. The harness does not maintain a central grep
bank; each project owns its patterns as code.

**Why tests instead of a YAML bank.** A project test can scope its grep
(diff-only vs whole-repo), attach fixtures, explain the rule in an
assertion message, and evolve without changing a harness interface. A
central YAML/grep bank would force a framework for one beneficiary until
a second project arrives wanting the same mechanism.

When `/gaze` or a review surfaces a rule worth mechanizing, write a
test covered by the declared adherence command in the target repo. That is the ratchet
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
    suggested_test: <grep pattern or project test snippet>
untested_rules:
  - rule: <.claude/rules/foo.md#bar>
    suggested_test: <code>
```

## Ratchet discipline

After each run, if `semantic_findings` is non-empty:

1. The caller (`/gaze` or author) opens a small follow-up ticket in the target repo:
   "Mechanize adherence rule X per suggested_test."
2. That ticket adds a test run by the declared adherence command (in an existing test file, or a
   new one) that asserts the rule mechanically.
3. Next invocation of `/verify-adherence`, the rule is caught by phase 1 instead of
   phase 3. LLM surface shrinks permanently.

This ratchet is the whole point. Do not accept `semantic_findings` as a steady state.

## Circuit breakers

- No declared adherence runner → blocking contract failure (phase 1).
- A declared runner cannot execute → ESCALATE (environment broken).
- No `scripts/` directory → **reference resolution still runs** when prose is
  in scope. A manuscript-only layout does not exempt phase 1.0 or the project runner.
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
