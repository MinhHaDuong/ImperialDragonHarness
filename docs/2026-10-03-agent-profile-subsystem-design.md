# Agent profile subsystem — design note

Status: v2 (draft for author) · Date: 2026-10-03 · Ticket: 0938 (and 0802/0924 context)
Author: Minh Ha-Duong (design) / harness raid session (draft); two external
reviews on PR #1171 (gpt-6-astra-pro — reject-as-drafted;
claude-sonnet-4.5 — accept-with-changes), dispositioned per author doctrine.

## Abstract

Replace inline fork roles with named agent profiles. Each runtime keeps a
thin, write-once profile shell whose body is a pointer; the role's contract
(the rules to load, the skills it may invoke, its charter) lives in the
harness at `<root>/profile/<NAME>/PROFILE.md`. The mechanism is a
convention, not a subsystem: it leans on LLM training, exactly like every
other contract in this harness.

## Design doctrine

This harness runs on contracts-by-convention: skills, rules, AGENTS.md are
prose that a trained model reads and follows, with no mechanical
enforcement. Agent profiles join that pattern. The two external reviews
demanded a guard stack (launcher-side validation, trust boundaries,
contract versioning, snapshotting, bootstrap protocols, injection
fallbacks); the author rejected that direction: a single-operator research
harness does not carry a multi-tenant threat model, and mechanically
validated profiles would be the one guarded subsystem in an unguarded
house. Where a guard would have gone, the design puts one sentence of
doctrine and an observable failure instead.

## Issues and benefits sought

1. **Inline fork roles do not scale.** At the 2026-09-16 baseline, 86 fork
   launches across ten skills re-describe their role at each call site
   (`gaze` 37, `review-pr` 16, `review-pr-prose` 11, others 1-5). The same
   role drifts between skills; written ten times, fixed nowhere. The count
   is a dated baseline — the implementation recounts it before writing
   profiles.
2. **Portability is blocked at the role layer.** The capability survey
   (2026-09-16) found the declarative agent definition to be the most
   portable primitive (markdown + YAML frontmatter in Claude Code, Gemini
   CLI, OpenCode; same fields in TOML for Codex; via extension in Pi). An
   inline role ports by hand, per runtime, per edit — the largest single
   obstacle to the Codex work.
3. **The bare-context trap.** A fork inherits the parent's resident
   context; a named agent starts bare (memory:
   `feedback_fork_skills_bare_context`). Naive conversion ships reviewers
   without git discipline, guards, or MOE posture.
4. **Registration vs iteration.** Harness rules evolve daily; runtime
   registration files should be write-once.
5. **Budget.** The `agents` channel is capped at 800 chars of
   name + description (tests/test_resident_census.py:48). Bodies do not
   count. The cap is not raised by this work; current headroom is
   recounted at implementation (the roster changed since the baseline).

Benefits sought: named portable roles; one contract per role; review
quality preserved; write-once registration; census respected.

## Proposed solution

**Shell** — `agents/<name>.md`, the runtime-registered file. Frontmatter:
`name`, `description` (census-counted), `model` (short enum), `tools`
where the runtime supports grants. Frontmatter is authoritative for
launch parameters; the contract carries none (v2: the `Model:` section is
dropped — frontmatter selects the model before the contract is read, so
a contract-level model declaration was a second truth). Body: one
paragraph:

> Step 0: read your profile contract at
> `<root>/profile/<name>/PROFILE.md`. `<root>` is the harness root your
> launcher named, or `~/.agents` if you were launched with no root given.
> If you cannot find or read it, say so in your first output line and
> proceed no further. Never guess a different root and never search for
> one.

The last sentence is doctrine, not machinery: resolution failure is
reported, never fallback-searched — a stale sibling install can never be
silently picked up.

**Contract** — `profile/<name>/PROFILE.md`, plain prose, three sections:

- `Rules:` the files to read before working. Each contract lists the
  baseline disciplines explicitly — for a reviewer, that means at least
  the git discipline and the delegation/decorrelation sections — plus
  whatever the role adds. No inheritance, no injection: what the role
  needs is written in the file.
- `Skills:` names and contract paths the role may invoke.
- `Charter:` what the role decides, what it never decides, its posture.

**Launch flow.** The spawning skill already computes the harness root
(`IDH_ROOT`) and passes it in the launch prompt. That is the whole
mechanism. Nothing validates the contract before launch; the agent's
trained behavior plus the reported-failure doctrine is the mechanism, as
it is for every SKILL.md this harness already trusts.

**Install.** Shells are written once — by hand, or by `./bin/idh sync`
if the author opts to have it deploy them; the pointer names `~/.agents`
as the no-root-given default, consistent with the installation boundary
(the default location, used as a default — not a path API).

**Enforcement.** The house standard, nothing new: in-repo doc-pin tests
assert every shell template carries its pointer and every contract
exists and lists its rules; `make check` runs them. Deployed runtime
copies are outside the repo and outside the tests, exactly as deployed
skill registrations are today; drift there is caught the way it always
is — observed behavior in gaze runs, and the contract files themselves
evolve in-repo where review sees them.

**Runtimes without file-read tools.** Recorded limitation, house style:
the shell's step-0 failure sentence fires in the agent's output, the
caller sees it, the seat is recorded as no-report with the standard
status line. No injection fallback is built.

## State of the art

Corrected per review findings; claims scoped to the cited survey.

- **Claude Code:** `.claude/agents/*.md` subagent definitions, YAML
  frontmatter + markdown body; fresh context per subagent; file-read
  tools available. The pointer works as written.
- **Gemini CLI / OpenCode:** markdown agent/configuration with
  frontmatter; body preservation and default tool grants are unverified
  here — settled empirically by the 0938 Codex/Pi demonstration, not
  asserted.
- **Codex:** TOML `[profiles.*]` selects model/effort; no body field —
  the pointer rides in the launch prompt instead. Translation is
  therefore "pointer relocated", not "body copied".
- **Pi:** extension-mediated; unverified, settled by the same gate.
- **CrewAI:** declarative YAML agents (`role`, `goal`, `backstory`) —
  inline in spirit, file-backed in option. **LangGraph:** graph
  orchestration; instruction loading is the node author's choice.
  **OpenAI Agents SDK / AutoGen:** instructions as strings or callables,
  inline in application code.
- **AGENTS.md:** discovery convention loaded by supporting tools —
  closer to runtime-managed discovery than to a pointer the agent
  chooses to obey.
- Skill systems (including this harness) are the closest analogy to
  pointer-following. Novelty claims are withdrawn: the useful statement
  is that no surveyed framework couples write-once shells to
  harness-side contracts; whether others do is not asserted.

## Advantages of our way

- One contract per role; the ten per-skill copies collapse (the
  implementation's role inventory confirms which launches are genuinely
  the same role before merging any).
- Runtime registration becomes write-once.
- Only frontmatter is per-runtime; the body is prose and ports
  untranslated.
- Zero new mechanisms: no validation layer, no versioning, no injection
  — the same trust every existing SKILL.md already enjoys.
- Census untouched: shells keep name + description under budget.
- Failure is observable and reported at step 0, not silently degraded.

## Limits, stated plainly

- The contract is followed by training, not enforced — a profile that
  skips step 0 produces an ungrounded review. This is the same risk the
  harness accepts for every skill contract today; the step-0 sentence
  and gaze observations are the mitigations that exist.
- Two files to read a role (shell + contract).
- Per-runtime shells are still hand-written; reduced to frontmatter, not
  zero.
- Per-launch token cost: shell + contract + listed rules, paid in full
  each launch (no caching). The pilot measures it; large rule lists are
  an authoring problem, not a mechanism problem.
- Body support and default file-read per runtime are unverified until
  the 0938 demonstration.

## Portability discussion

Frontmatter translation per the survey's table is the only per-runtime
work; the pointer is prose. The honest open cell is Codex (no body
field — pointer moves to the launch prompt) and any runtime that strips
bodies. These are settled once, empirically, by the ticket's existing
gate: one inventory-derived profile demonstrated on Codex or Pi by
frontmatter translation alone. If that demonstration needs more than
frontmatter work, that is an explicit author decision at that point —
not silently absorbed by design.

## Alternatives not taken

- **A — projection mechanism** (harness code generating per-runtime
  profiles): rejected by the author. The reviews note, correctly, that
  v2's write-once shells are already a hand-run limited projection, and
  that a full generator could fail at install time rather than in the
  field. The remaining difference is who edits on drift: a human with a
  five-file roster, or a code generator plus its test surface. At the
  current roster size (2 shells, ~450 census chars, a handful of
  profiles), the generator costs more than it saves. Revisit if the
  roster grows past hand-scale.
- **Reviewer-demanded guard stack** (v1 review disposition): rejected —
  see Design doctrine.
- **Inline rule lists in each profile body:** per-runtime edits on every
  rule-list change.
- **Shared preamble injected into every shell:** needs a per-runtime
  injection mechanism — a small A — and loads baseline content into
  roles that do not need it. The same benefit is got by writing the
  three-line baseline into each contract, which is authoring, not
  mechanism.
- **Keep the forks:** zero portability gain; the drift cost is already
  paid. The ticket keeps forks where inherited context is the point,
  each justified in its skill body.

## Open questions

1. Naming: `profile/` (author's sketch) vs `profiles/` (house plural).
2. Pilot: `review-pr`'s 16 forks (the ticket's named pilot) vs the
   existing `gaze-pr-review.md` shell as a first bootstrap check.
3. Whether `idh sync` deploys shells or they stay hand-written.
4. Census recount and role inventory before any profile is written
   (implementation-phase gate, ticket Actions 2).
