# Agent role inventory — ticket 0938, Actions step 2

Date: 2026-10-03 · Base: 57de67c · Method: recount first, derive the roles
from what each launch decides, then judge each against the census. Every
count below was run on this tree with `rg`; none is carried from the
2026-09-16 baseline.

## Recount (verified on 57de67c)

- `rg 'subagent_type: "fork"'` across `skills/` and `tests/`: **zero
  matches.** The 86-fork baseline is obsolete; the attribution train
  (1004–1009), detached-seat substitution (1017) and orchestrator-run shapes
  (0990) replaced them.
- `rg 'context: fork'` in `skills/*/SKILL.md`: **five skills declare their
  own execution context** — `gaze`, `review-pr`, `review-pr-prose`,
  `verify-adherence`, `verify-gate` (frontmatter line 7 of each). These are
  the caller-side contexts, not spawned roles; they stay as they are.
- Census, `scripts/resident_census.py`: agents channel **438/800** —
  `gaze-pr-review` 88 (name 14 + description 74), `team-lead` 350 (name 9 +
  description 341). Headroom: **362 characters.**

## The roles, named by what each decides

### gaze battery (skills/gaze/SKILL.md)

| Role (what it decides) | Call site | Profile? |
|---|---|---|
| **Adherence verdict** — does the branch diff obey project rules; blocking vs clean | skills/gaze/SKILL.md:386 (Agent A; label-skip at 386–389, spawn contract 390–398) | Justified: repeats on every gaze PR, and the seat rails (read-only, `git -C`, first action = live `Skill(verify-adherence)`) are restated at each launch — the exact drift shells fix. Proposed: `adherence-seat`. |
| **Built-in review wrap** (Agent B) — the runtime's own `/review` verdict on prose or code | skills/gaze/SKILL.md:410 | Stays inline: the runtime substitutes the reviewer itself; a shell would pin what the runtime already supplies, and the prose/code routing decision (axes at 400–417) is gaze-local. |
| **PR review panel** (Agent C) — the five code perspectives' findings, or the prose panel's | skills/gaze/SKILL.md:436; already a named profile `agents/gaze-pr-review.md` | Already converted (PR #980). |
| **Exit-criteria verdict** — APPROVED / REROLL / ESCALATE against ticket criteria and review comments | skills/gaze/SKILL.md:551–576 (phase 6 gate; containment rails at 560–576) | Justified: one seat per PR, every PR; its containment rails are the longest restated block in the skill. Proposed: `gate-seat`. |
| **REROLL fix** — how to resolve review findings on the PR branch, then re-enter the gate | skills/gaze/SKILL.md:636–644 (round-1 spawn, ≤10 min, worktree-bound), 626, 862 | Justified: the same coder role raid Phase 5 executes and hunt's detached executor plays. Proposed: `coder`. |

### review-pr panel (skills/review-pr/SKILL.md — the wave 1 pilot)

| Role | Call site | Profile? |
|---|---|---|
| **Five code perspectives** — correctness, consistency, scope, red team, doc propagation; each returns findings against its one perspective | skills/review-pr/SKILL.md:37 (parallel spawn), roster at 60, round scoping at 99–130 | Justified: one seat contract, five launches per review, reused by Agent C. The perspective itself rides in the launch prompt, so **one** shell serves all five. Proposed: `code-reviewer`. |
| **Detached-seat seats** — same five perspectives on a headless CLI when Agent-spawn is unavailable | skills/review-pr/SKILL.md:143–178 (ticket 1017) | Stays inline: the contract must be embedded in the launch prompt by design — a detached CLI seat cannot be relied on to read a shell. |

### review-pr-prose panel (skills/review-pr-prose/SKILL.md)

| Role | Call site | Profile? |
|---|---|---|
| **Adversarial referee** — challenges the manuscript's claims and the panel's search space | skills/review-pr-prose/SKILL.md:73 | Justified: mandated on every prose panel ("Always include"), yet recruited ad hoc today. Proposed: `prose-reviewer` (one shell, role in the prompt). |
| **AI-tells audit** — flags blacklisted words, conditional words, density and pattern violations, full text not diff | skills/review-pr-prose/SKILL.md:83–85, exempt from round scoping at 160 | Justified: runs on every prose panel unchanged — the most stable role text in the harness, restated each time. Proposed: `prose-reviewer` (role in prompt) or, if the author prefers a dedicated seat, `ai-tells`. |
| **Editorial-brief audit** — optional, project-specific | skills/review-pr-prose/SKILL.md:89 | Stays inline: conditional on `docs/editorial-brief.md`, degrades gracefully — a shell for an optional seat is overhead. |

### raid phases (skills/raid/SKILL.md)

| Role | Call site | Profile? |
|---|---|---|
| **Scope reframing** (Imagine) — why now, simplest path, YAGNI scan per ticket | skills/raid/SKILL.md:106–115 | Stays inline for now: single caller (raid), once per ticket per raid, and the phase text is the contract — a shell would carry a pointer to prose that lives one screen away. Revisit if imagine-style reframing spreads to another skill. |
| **Blind-spot check** — what the whole team failed to look for, across tickets | skills/raid/SKILL.md:120–135 | Stays inline: same single-caller argument; the probe list is the role. |
| **Plan writing** — Actions, first test, dependencies per ticket | skills/raid/SKILL.md:170–180 | Stays inline: same argument. |
| **Feasibility (mechanical)** — paths/lines/signatures exist (cheap tier) | skills/raid/SKILL.md:189–190 | Stays inline: pure lookup whose checklist is phase-local. |
| **Feasibility (cross-ticket)** — conflicts, cross-cutting registries, PR size (standard tier) | skills/raid/SKILL.md:190–197 | Stays inline: same. |
| **Wave execution** — implements one ticket in a worktree: branch, test, gate, PR, evidence | skills/raid/SKILL.md:269 (spawn: `isolation: "worktree"`, `model-level: strong`) | Justified: repeats per ticket per wave every raid, and is the same role as gaze's REROLL fix and hunt's detached executor. Proposed: `coder`. |
| **Wave integration review** — do merged PRs compose; does `make check` pass on the union | skills/raid/SKILL.md:315–327 | Stays inline for now: one seat per wave, checklist is wave-local; a shell adds indirection without deduplication. |

`hunt` names `Agent(isolation: "worktree")` only for its worktree-ownership
check (skills/hunt/SKILL.md:82–90) — no role to inventory there; its
detached executor is the same coder role counted above.

## Proposed shell roster (census-checked, no budget raise)

Census arithmetic: agents channel 438/800 today; 362 chars headroom.
Proposed roster, name + description exactly as they would register:

| Shell | name | description | chars |
|---|---|---|---|
| `coder` | 5 | Executes a ticket contract in a worktree; branch, PR, evidence. | 63 → 68 |
| `code-reviewer` | 13 | Code-review seat; perspective arrives in the prompt. | 52 → 65 |
| `prose-reviewer` | 14 | Prose-panel seat; role and rulebook arrive in the prompt. | 57 → 71 |
| `gate-seat` | 9 | Read-only verify-gate seat; verdict only. | 41 → 50 |
| `adherence-seat` | 14 | Read-only verify-adherence seat; verdict artifact only. | 55 → 69 |

Roster total **323** characters → agents channel **761/800**, 39 spare.
Within budget with no raise; the spare covers one more terse shell (≤39
chars) if the pilot asks for the dedicated `ai-tells` seat
(name 8 + a ≤31-char description), else wave 1 should spend it, not
grow it.

The five perspective roles deliberately share `code-reviewer` (and the
prose seats `prose-reviewer`): the seat contract is identical across
perspectives — same read-only rails, same `.part`-then-rename artifact
protocol, same exit criteria — and only the perspective differs, which is
launch-prompt material, not shell material. Per-perspective shells would
spend 5× the census for no contract difference.

## What wave 0 shipped alongside this inventory

`rules/guards.md` (both hoisted guards, resident) with the AGENTS.md
pointer "Guards every agent: rules/guards.md."; AGENTS.md net-freed 359
chars on the import channel (4491 → 4132 of 4500). The rules channel paid
733 chars (17048 → 17781 of 17800, the owning budget raised from 17500
with the argument in `tests/test_rules_resident_budget.py`). Bare-context
profiles (wave 1+) list `rules/guards.md` in their `Rules:` instead of
relying on inherited AGENTS.md text.
