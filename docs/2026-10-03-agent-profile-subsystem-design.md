# Agent profile subsystem — design note

Status: draft for review · Date: 2026-10-03 · Ticket: 0938 (and 0802/0924 context)
Author: Minh Ha-Duong (design) / harness raid session (draft)

## Abstract

Replace the harness's inline fork roles with named agent profiles. Each
runtime keeps a thin, write-once profile shell; the role's actual contract
(the rules to load, the skills it may invoke, its charter) lives in the
harness at a fixed path. The shell's body is a pointer: *"your profile of
rules and skills is defined at `<root>/profile/<NAME>/PROFILE.md`"*.

## Issues and benefits sought

1. **Inline fork roles do not scale.** At the 2026-09-16 baseline, 86 fork
   launches across ten skills re-describe their role at each call site
   (`gaze` 37, `review-pr` 16, `review-pr-prose` 11, others 1-5). The same
   role drifts between skills; the description is written ten times and
   fixed nowhere.
2. **Portability is blocked at the role layer.** The runtime capability
   survey (2026-09-16) found the declarative agent definition to be the
   most portable primitive — markdown + YAML frontmatter works in Claude
   Code, Gemini CLI and OpenCode; Codex wants the same fields in TOML; Pi
   accepts them through an extension. An inline role ports by hand, per
   runtime, per edit. This is the largest single obstacle to the Codex work.
3. **The bare-context trap.** A fork inherits the parent's resident context;
   a named agent starts bare (memory: `feedback_fork_skills_bare_context`).
   Naive conversion ships reviewers that do not know the git discipline,
   the guards, or the MOE posture — clean-looking and silently weaker.
4. **Registration vs iteration.** Harness rules evolve daily; runtime
   registration surfaces (per-runtime config files) should not be edited
   every time a role's rule list changes.
5. **Budget.** The `agents` channel is capped at 800 characters of
   name + description (tests/test_resident_census.py:48), ~450 free after
   `team-lead`. Bodies do not count. The cap is not raised by this work.

Benefits sought: named portable roles; one source of truth per role;
review quality preserved after conversion; write-once runtime
registration; census respected.

## Proposed solution

**Shell** — `agents/<name>.md`, the runtime-registered file. Frontmatter
only: `name`, `description` (census-counted), `model` (short enum), `tools`
where the runtime supports grants. Body: one pointer paragraph —

> Step 0 is mechanical: read your profile contract at
> `<root>/profile/<name>/PROFILE.md` — the path your launcher supplies, or
> the installer-stamped path, or the default `~/.agents/profile/<name>/PROFILE.md`.
> If you cannot read it, record that limitation and stop; never proceed
> without your contract.

**Contract** — `profile/<name>/PROFILE.md`, harness-side, fixed sections:

- `Rules:` ordered paths under `rules/` the role loads before working;
- `Skills:` names + contract paths the role may invoke;
- `Charter:` what the role decides and what it never decides;
- `Model:` model-level and effort intentions;
- `Posture:` MOE stance, decorrelation, containment rails.

**Launch flow.** The spawning skill resolves the harness root (it already
computes `IDH_ROOT`) and passes it in the launch prompt. Path resolution is
three-tier: launcher-supplied > installer-stamped > default install root.

**Install.** `./bin/idh install` / `sync` (the 0999 registration surface)
substitutes the resolved root into every registered shell when it writes it.

**Enforcement.** Mechanical: doc-pin tests asserting (i) every
`agents/*.md` shell carries its pointer, (ii) every shell has a
`profile/<name>/PROFILE.md` listing at least one rule, (iii) census
unchanged. Behavioral: gaze observations catch an agent that skipped its
contract; a profile that cannot read it records the limitation, never
silently proceeds.

## State of the art

- **Claude Code, Gemini CLI, OpenCode:** markdown agent definitions with
  YAML frontmatter; role instructions inline in the body; subagents start
  with fresh context. No external-contract indirection in common use.
- **Codex:** TOML `[profiles.*]` selects model/effort; roles live in prompts.
- **CrewAI, LangGraph, OpenAI Agents SDK, AutoGen:** `role`/`goal`/
  `backstory` or instruction strings inline in application code.
- **agents.md convention, skill systems (including this harness):** the
  pointer pattern — the agent is told where the contract lives and reads
  it. Established for repo-level guidance and skill contracts.
- **Automatic projection of harness-side role definitions into multiple
  runtimes:** not found in the surveyed tools; exists only as bespoke glue.

Inline embedding is the norm; indirection is established where
write-once/multi-runtime matters. Write-once shells plus harness-side
contracts is not found in the surveyed frameworks — new here, not exotic.

## Advantages of our way

- One source of truth per role; the ten per-skill copies collapse.
- Runtime registration becomes write-once: harness rule-list changes never
  touch runtime configs.
- Only frontmatter is per-runtime; the body is plain prose and ports
  untranslated — the projection problem is reduced to key renames.
- Same-house pattern as skill contracts (loaded by path, never paraphrased).
- Token cost per launch is proportional to the listed rules only.
- Census untouched: shells keep name+description under budget.

## Limits and mitigations

- Two files to debug a role (shell + contract) — accepted indirection.
- Step 0 is not runtime-enforced — doc-pin tests + gaze observations;
  a skipped contract surfaces as a bad review, not silently.
- Two-truths risk (shell frontmatter vs contract) — pinned by tests.
- Relocated checkouts need re-stamping — fallback default path covers
  hand installs; `idh check` flags stale stamps.
- Shells are still written per runtime — reduced to frontmatter, not zero.
- Agents without file tools cannot load contracts — record the limitation.

## Portability discussion

The survey's translation table applies to frontmatter only:

| Runtime | Shell format | Body translation |
|---|---|---|
| Claude Code | `agents/*.md`, YAML | none (pointer is prose) |
| Gemini CLI | same shape | none |
| OpenCode | same shape | none |
| Codex | TOML keys | none |
| Pi | third-party extension | none |

The pointer must not hardcode `~/.agents` (the installation boundary:
default location, not a path API). The three-tier resolution keeps a
relocated checkout working (0999), and `idh install`/`sync` re-stamps.

## Alternatives not taken

- **A — projection mechanism** (harness code generating per-runtime
  profiles): rejected by the author. Every runtime's format drift becomes
  harness test surface; one more subsystem; generation failures surface at
  launch time in the field.
- **(a) inline rule lists in each profile body:** every harness rule change
  edits every runtime's shell — A's edit-tedium returning through the back
  door.
- **(b) shared preamble injected into every shell:** universal ballast per
  launch; injection needs a per-runtime mechanism (a small A); trades
  under-loading risk for over-loading cost.
- **Keep the forks:** zero portability gain; 0938 exists because the drift
  and portability costs are already paid.
- **Raise the census budget:** out of scope — a defended author decision.

## Open questions

1. Naming: `profile/` (author's sketch) vs `profiles/` (house plural).
2. Pilot: `gaze-pr-review.md` (newest shell, fewest fork bindings) vs
   `review-pr`'s 16 forks.
3. May a mechanical role list zero rules (charter-only contract)?
4. Stamp format inside the shell body (comment vs sentence variable).
