---
name: release
description: Pre-release audit, GPG tag signing, and download-URL update for a target repo. Runs audits autonomously; pauses at the human-only signing step.
user-invocable: true
argument-hint: [new-tag-name]
---

# Release $ARGUMENTS

Encode the release checklist as a repeatable flow: run audits autonomously,
pause at the human-only step (GPG signing), then verify and summarise. The
skill **never signs** a tag — that is the human's sole responsibility.

## When to use

- Invoke from the **target repo's working directory**, on its **main
  branch**, with **all feature work already merged**.
- **Cross-repo prerequisite**: the caller must ensure cwd is the target
  project before invoking `/release`. The skill is cwd-based — it never
  takes a repo or path argument. For cross-repo flows, change into the
  target project directory and fetch from the forge before the call.

## 1. Pre-flight gate

- Run the target repo's `make check`. **HALT** on failure — print the failing
  output and stop. A release never ships on a red suite.
- Scan open tickets for the `needs-human` tag. If any are tagged, **HALT**,
  list them, and stop — these are blocking human-judgment items that must be
  resolved before a release. Degrade gracefully with a warning if there is no
  `tickets/` directory or no `erg` binary available (the gate is informational
  in that case, not blocking).
- **Research-artifact citability (WARN, graceful).** If the release ships a
  research artifact — `CITATION.cff`, a manuscript, or a `data/` tree — check
  that the **code and data** have a persistent identifier (a real DOI), not
  only the paper. Flag — do **not** HALT — when `CITATION.cff` carries a
  placeholder DOI (`10.XXXXX`-style), when the sole code/data pointer is a
  mutable forge URL, or when no Zenodo/DOI deposit is referenced. Rationale:
  disseminating the paper is not disseminating the work — "errors must be
  locatable" needs a citable deposit, and a paper-only release silently omits
  the artifact (deposit a snapshot, cite the Zenodo **concept** DOI). WARN not
  HALT, because the deposit may be deliberately deferred; the point is to make
  that a conscious choice, not an oversight. Skip silently if the release is
  not a research artifact.

## 2. Parallel audits

Launch **three background agents in parallel** (single message, all as
background agents), each pinned to **`model: sonnet`** — these are read-and-audit
reviewers (security, UX, doc/test coherence), so they stay below the coder tier
(rules/workflow.md § "Reviewer decorrelation"); left unpinned they inherit
the session model and silently run the fan-out at top tier. Wait for all to
return, then consolidate.

**Agent A — security audit.** Review the release surface for:
- supply chain (dependencies, pinned versions, fetched scripts),
- permissions (file modes, capabilities, token scopes),
- injection (unsanitised input reaching a shell, eval, or template),
- signing (tag-signing path, key handling, attestation of downloads).

**Agent B — UX dry-run.** Read the target repo's `tickets/0152` for the
audience definitions and install paths, and walk each one. If `0152` is
absent, degrade to generic heuristics: a clean install from scratch, plus a
first-use walkthrough of the primary command.

**Agent C — foundations coherence.** Follow the target repo's
`FOUNDATIONS-PROCESS.md` if present (sweep stated contracts across
constitution/rationale/spec/process docs; verify the disjoint union against
guard tests — stated-without-guard needs a test, guarded-without-statement
needs a sentence; flag inter-doc tensions). If absent, degrade to a light
pass: do the stated-vs-guarded comparison on whatever convention docs and
test suites the repo has.

Each agent files **one ticket per finding** via `tickets/erg new`, with a severity
of HIGH / MEDIUM / LOW in the title or body. If there is no `tickets/`
directory, the agent prints its findings to output instead of filing.

After all three return, print a **consolidated summary**: count of findings by
severity, grouped by agent.

## 3. Resolve HIGH findings

If any finding is **HIGH**, print the list, **STOP**, and await a human
"continue". A release does not proceed past an open HIGH finding without
explicit human go-ahead.

## 4. Update the download URL

- Determine the new tag: the **skill argument** if given, else the current
  **UTC date** in `YYYY-MM-DD` form.
- Verify the tag does not already exist: `git tag -l <tag>` must be empty. If
  it exists, STOP — a release tag is never reused.
- Run the helper on `README.md` (and on `src/go/assets/integration.md` if that
  file is present):

  ```bash
  ~/.claude/skills/release/rewrite-download-url README.md <tag>
  ```

  The helper rewrites the tag-like segment inside raw-download / release URLs
  to the new tag and prints a match count; it exits non-zero (with a
  diagnostic) if **no** such URL is found, so a missing URL surfaces
  immediately. An already-current URL is a normal match: the helper prints its
  count and exits 0 (idempotent no-op).
- Commit the change: `release(<tag>): update download URL to <tag>`.

## 5. GPG signing pause (human-only)

Print **exactly** this command, then end the turn:

```
git tag -s <tag> HEAD && git push --tags
```

The human signs the tag with their GPG key and pushes it, then replies to
resume. The skill never runs this step itself.

## 6. Verify the tag

On resume, confirm the signature:

```bash
git verify-tag <tag>
```

If verification fails, print the error and **STOP** — an unverifiable tag is
not a release.

## 7. Blog post (stub)

File a **deferred** ticket via `tickets/erg new` titled
`Write release blog post for <tag>`. This is a documented placeholder — there
is no blog implementation until blog infrastructure exists.

## 8. Summary

Print: the tag, the findings count (by severity), whether the download URL was
updated, and whether the tag verified.

## Language and identity

- Forge-agnostic: "merge request" not the forge-specific term, "ticket" not
  the tracker-specific term, "forge" for the hosting service.
- No forge-CLI commands in this prose.
- The Imperial Dragon is not a bird — no avian analogies. Scale, power,
  taxonomy.
