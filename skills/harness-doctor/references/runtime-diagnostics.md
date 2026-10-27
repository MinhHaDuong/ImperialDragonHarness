# Runtime diagnostics

What each runtime ships that can tell the doctor something about skills and
rules, cheapest first. Every runtime is treated alike: run what it ships, in
this order, and read the output as evidence beside the doctor's own pass.
Health of an install is context; what a runtime actually loads is the
strongest evidence of shadowing and precedence.

Each line is labelled: **no user** (runs headless), **author** (interactive,
the author runs it and pastes the output), **spends** (model usage, opt-in
with a cost cap). Never run a **spends** line without the author's agreement.

Reporting rule: a diagnostic that is absent, refuses, times out or was not
run is reported as *unavailable* with the reason, never as clean. "Ships
nothing" is recorded only against a control: the runtime's own command list,
seen to answer.

## Claude Code

<!-- harness-extension-point -->
- `claude plugin validate "$IDH_ROOT"` (no user, no spend): validates the
  skills tree as a manifest-less plugin. Observed: flags a skill with no
  `description:`; passed a skill whose frontmatter does not parse as YAML, so
  its pass is not a parse check. Ignore its plugin-directory submission notes
  (licence, icon, manifest).
- `claude doctor` (no user): install health, settings that do not parse,
  unused skills and their context cost, duplicated instructions, slow hooks.
  Scope is the author's own setup.
- `/skill-doctor` (author): per-skill context cost, recent usage,
  never-invoked skills. Usage evidence, not a lint.
- `/doctor` (author): the in-session form; proposes fixes, the author decides.
- `claude plugin eval` (spends): behaviour evals against `evals/` cases, with
  `--json <file> --no-publish --max-cost-usd N`. The harness ships no eval
  cases; report it unavailable until it does.

## Codex

<!-- harness-extension-point -->
- `codex debug prompt-input` (no user, no spend): JSON of the model-visible
  input, instructions and skills included. Direct evidence of what Codex
  loads from the shared skills root. Observed: a skill marked not
  model-invocable still appears in it; read that as an observation to check
  against Codex's documentation, cause not established.
- `codex doctor --json` (no user): `overallStatus` and per-check results for
  config, sandbox, state and install. Install health, not skill text.
- `codex review` (spends): a reviewer from another family, not a diagnostic.

## Pi

<!-- harness-extension-point -->
Pi discovers skills from the shared Agent Skills root (`~/.agents/skills`),
the same root as Codex, so a skill visible to one is a candidate for the
other; their precedence rules still differ.
- No doctor or validate command. Control: `pi --help` lists every command
  (install, remove, update, list, config, auth, mcp) and none checks skills.
  Report "no skill diagnostic shipped".
- `pi list` (no user): installed extensions; `pi auth` and `pi mcp`: provider
  and server readiness. Context only.
- `pi --skill <path> -p --mode json` (spends): loads one skill headless; the
  only way to see Pi read a given skill body.
- `pi config` (author): the interactive view of enabled package resources.
