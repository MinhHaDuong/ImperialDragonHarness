# Attribution identity inventory: where model, effort and step identity is lost

Ticket 1148, child A of tracker 1146. Documents only: no schema, parser, `/merge`
or skill change here (ticket 1149 owns those). Written 2026-10-20 against
`origin/main` 03f748a1.

Conventions. "Exposed" means a runtime, tool or file states the fact. A launch
parameter the orchestrator chose is a request, not an observation. Unstated
effort is written **not stated**; no cell below infers a model id from a
description or an effort from a default.

## 1. Table: one row per step

| Step | Identity exposed | Where it is exposed | Where it is lost |
|---|---|---|---|
| **Plan** (Imagine, Plan, `/route` triage) | Worker, family, effort, risk row and reason as a spoken "launch line" (`skills/route/references/decorrelation.md` § The launch line). Model token the orchestrator passes (`sonnet`, `fable`, ...). Own model and effort: only when the runtime prints them. Independence basis: the launch line's family and risk row. | Conversation text only. The route grid and cache (`skills/route/grid.json`, `routes.json`) hold the *menu*, not what ran. | Never written anywhere that lands with the PR: the launch line is chat text. The grid says what an effort label means, not that it was used. Effort of the planning session itself: **not stated**. |
| **Execute** (`/hunt` coder, or the root session) | Alias passed at launch (`claude -p "/hunt N" --model <token>`, `Agent` `model`). Commit trailer `Co-Authored-By: Claude <Family> <ver> <noreply@...>`: a display name. Subagent transcripts under `~/.claude/projects/<project>/<session>/subagents/agent-<id>.jsonl` carry `model` and `effort` (probe in ticket 1145, not repeated here). | Trailer in commits; launch parameters in the orchestrator's context; transcript files. | Trailer: 105 of the last 200 non-merge commits on `origin/main` carry one (measured with `rev-list` + per-commit `show`); 95 carry none. Where present it holds a display name (`Claude Sonnet 5.5`), never an effort, never a resolved provider id. Squash or merge commits do not retain per-step lines. Effort: **not stated** to the orchestrator in the task notification. Codex root: the runtime describes its model only as "GPT-6" (PR 1466): model id and effort unavailable. |
| **Review seat, native** (`/review-pr` perspective agents, `/verify-adherence` seat, panel coordinator) | `<panel>/manifest.txt` columns `perspective<TAB>model<TAB>family<TAB>reason` (`skills/review-pr/SKILL.md` step 1, checked by `scripts/panel-manifest-check.py`): a short token or provider/id, a family, a reason. Seat report `<perspective>.md`. Verdict roster (approve / comment / request-changes / no report). | `<worktree>/.panel/<pr>/` in the review worktree. | The manifest has **no effort column** and no ran/failed/skipped status. `.panel/<pr>` is deleted at `/gaze` review-scratch cleanup (`skills/gaze/SKILL.md` § Review scratch cleanup, unless tracked) and the worktree removed, before `/roar` runs. Only the PR comment survives, which names seats and at best an alias. Inline-only `/gaze` runs launch no seat, so nothing marks a `skipped` attempt. Reused contexts (fix rounds, regression checks) are indistinguishable from fresh seats in the roster. Codex-native collaboration contexts: requested route only (for example `gpt-6-astra` high, `gpt-6.1-sol` medium), resolved id masked. |
| **Review seat, external CLI** (headless OpenAI or Anthropic process from bash) | OpenAI CLI prints `model`, `provider`, `reasoning effort`, sandbox and session id in its transport header. Anthropic CLI JSON `modelUsage` names the canonical model and the cost; effort is the **flag that was passed**, internal effort not independently exposed. | Transport logs and JSON, normally in `/tmp` or the panel directory. | Transport logs live outside the PR and outside the schema. In PR 1466 they survived only because they were copied into `memory/evidence/2026-10-19-pr1466-review-trail.md` (by hand, after the fact). The schema cannot hold the effort (section 2). |
| **Gate** (`/verify-gate`, `/gaze` verdict) | `verdict`, `round`, `gate_session_id`, `review_worktree_path`, `ruled_tip_sha` in the verdict block (`skills/gaze/SKILL.md`, § verdict yaml). Footer `telemetry: tier risk_band wall agents tokens cost~` (§ Verdict footer). `PANEL-INTEGRITY: COMPLETE|DEGRADED` states whether a cross-family seat was reachable. | Verdict comment on the PR. | No model, effort, family or seat list in the verdict block or footer. `agents=<n>` counts subagents without naming them. The gate's own model and effort: **not stated**. `review_worktree_path` points at a tree that is removed on every exit path. `PANEL-INTEGRITY` gives the independence outcome, not the basis (which seat, which family). |
| **Roar** (`skills/roar/runbooks/capture.md`) | Re-reads "session outputs or durable PR review comments", writes one `review-attribution-prNNNN` journal entry through `scripts/attribution_record.py --capture`. | Journal entry in project memory, after merge. | Captures *after* the merge from evidence that has already decayed (previous rows). The runbook forbids rebuilding an id from an alias, so each gap becomes a capture failure or a pending file (`memory/evidence/review-attribution-pr14xx-pending.md`). Also: the schema holds one `writer:` line, so the plan step, a second executor and the gate have no line at all. |

## 2. Schema check (verified by execution, 2026-10-20)

Source: `scripts/attribution_record.py:36-39` and design doc section 4.

- Writer line requires `runtime` and `effort` (and `model`, or the two
  `model-*` masked fields). The effort value is free text, so `not stated` is
  accepted. Probe: a record with `effort=not stated` parsed and printed JSON.
- Reviewer line requires `seat`, `runtime`, `status` (and `model` or masked
  fields); only `model-version` is optional. Any other field, `effort` included,
  is rejected. Probe: the same record with `effort=medium · ` added to the
  reviewer line fails with `line 4: missing or unexpected identity field`.
- Consequence: a reviewer's effort, route and independence basis have nowhere
  to go, whatever the runtime exposes. No `step` field exists, so plan, gate and
  roar cannot be told apart from reviewers.

## 3. Loss points, ordered by what they cost

1. **Capture happens after the merge.** Everything in the table that is
   recoverable at launch or verdict time (manifest, transport headers,
   transcript fields) is read later from artifacts that a worktree removal or a
   `/tmp` purge has already deleted.
2. **Review scratch is deleted by design** (`.panel/<pr>` at `/gaze` cleanup).
   The verdict comment does not carry the seat table.
3. **Schema shape.** Single writer line, no effort on reviewers, no step, route
   or independence fields.
4. **Effort is never stated to the orchestrator** for native subagents, so it
   can only be a recorded request or **not stated**. For external CLIs it is the
   flag passed (Anthropic) or the CLI's own header line (OpenAI).
5. **Commit trailers are partial and coarse**: 95 of 200 recent non-merge
   commits have none; the rest hold a display name only.

## 4. Positive control: the table reproduces the PR 1466 facts

Source: `memory/evidence/2026-10-19-pr1466-review-trail.md` (file read in
the tree; it is the record of that PR's review, not re-derived).

| PR 1466 fact (from the trail) | Row of the table that predicts it | Match |
|---|---|---|
| Root Codex runtime describes its model only as GPT-6; writer model id and effort not exposed; nothing inferred | Execute: Codex root, id and effort unavailable | yes |
| Native collaboration contexts expose requested routes only (`gpt-6-astra` high, `gpt-6.1-sol` medium requested), resolved ids masked, recorded `runtime-masked` | Review seat, native: requested route, masked id | yes |
| External OpenAI seats: transport header gives `model: gpt-6.1-sol` / `gpt-6-luna`, `reasoning effort: medium`, read-only sandbox | Review seat, external CLI: model exposed; header effort | yes |
| External Anthropic seats: `modelUsage` canonical model `claude-sonnet-5-5`; medium is a requested flag, internal effort not independently exposed | Review seat, external CLI: model exposed, effort only as the flag | yes |
| Review attribution lives outside the merged PR (unmerged PR 1481, then the evidence file) | Roar and Gate rows: post-merge capture, no durable seat table | yes |

Difference to note from the ticket wording ("external CLI seats expose the
model, effort only as the requested flag"): that holds for the Anthropic CLI.
The OpenAI CLI also prints a `reasoning effort` line in its header; it equals
the requested value and the trail records it as header-observed. The table
keeps the two cases apart.

Parser control (section 2) is the second positive control: the reviewer-effort
rejection reproduces, so the "schema cannot hold it" claim is observed, not
read off the code.

## 5. Overlap and one owner per job

| Job | Owner | Not here |
|---|---|---|
| Read model and effort from subagent transcripts at roar time; transcript retention; map a run to a PR (ticket 1145, option 1) | 1145 | 1146 consumes the result; it builds no transcript reader. |
| Write-time seat table in the gate verdict (role, runtime, model, effort, status, ruled tip, report hash, findings) and `.panel` reports kept with the verdict (1145 option 2) | 1142 (evidence core, seat table, report hashes) and 1143 (gaze rebuild); 1145's exit criterion adds the field list to them | 1146 reuses that table as its review rows; it does not define a second one. As of this inventory, 1142's exit criteria do not yet name the identity fields (observed in the ticket file). |
| `Authored-by` for the writer from the executor transcript (1145 option 3) | 1145 | 1146 child B's block carries the line once 1145 can fill it; until then **not stated** is valid. |
| Schema: step, effort on every line, `not-stated`, `route=`, `independence=` | 1149 (1146 child B) | This inventory only fixes the field list that table rows justify: step, model, effort, route, independence basis. |
| PR-body block, `erg-pr-merge` warning, roar copy of the block | 1149 | |
| Fold the pending `review-attribution-pr14xx-pending.md` files | 1150 | |
| This inventory | 1148 | |

The one hand-off to settle in 1149 and 1142: the gate or `/gaze` appends the
review rows to the PR-body block (1149) from the seat table it already builds
(1142/1143). 1149 must not wait for 1145's transcript reader: rows it cannot
fill carry **not stated** and `runtime-masked` where the contract allows it.

## 6. Not verified

- Verdict comments on the forge: the claim that they name seats and give an
  alias at best comes from ticket 1145; I did not fetch a live comment.
- Subagent transcript fields (`model`, `effort`) and the 180-day
  `cleanupPeriodDays` setting in `~/.claude/settings.json`: ticket 1145 probed
  the first; I saw the setting but did not establish what prunes transcripts.
  Retention is 1145's exit criterion.
- Whether the runtime shows effort to a *root* Claude session in any status
  line: not tested; recorded as **not stated** where nothing was observed.
- Trailer coverage is one sample of the last 200 non-merge commits on
  `origin/main`, not the whole history.
- The Codex and Pi runtimes' transcript layouts: not inspected.
