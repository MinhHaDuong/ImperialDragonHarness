# Imperial Dragon Harness — State

Last updated: 2026-09-28T06:31Z

## North star
A reusable, science-backed personal harness for AI-assisted research: code and prose, day and night, across projects and machines. The harness itself is the deliverable.

## Status
<!-- generated 2026-09-28T06:31Z · as of 95cf190d -->

**Tickets:** 20 ready · 21 blocked — `erg ready tickets/` for full list
  next: 0205 External-reviewer panel for verify — contract, … · 0485 EDM: dédoublonner la bibliothèque Zotero exista…
**In flight:** no open PRs · CI main: success
**Recent (first-parent):**
  95cf190d Merge pull request #1033 from MinhHaDuong/housekeeping-20260928
  f88262a6 Merge pull request #1032 from MinhHaDuong/memory-followup-20260924
  8ea9db08 Merge pull request #1031 from MinhHaDuong/tickets/0977-essai-pi-backends

## Resume point
**2026-09-28.** 0977 essai run to completion and closed (#1031): padme passes the tool-call smoke test; Albert and ILaaS declared in `~/.pi/agent/models.json` awaiting author keys (ProConnect / consortium); HumaNum has no inference API; Pi's silent reroute to `openrouter/auto` on model-resolution failure filed as **0979**. 0800 amended (#1030): Mistral Vibe is the fourth target runtime, "runtime" is the word for hosts, and the `~/.idh` relocation is ticketed as **0978** (child of 0909). Stranded 2026-09-24 memory lessons landed (#1032).

Owed to the author, outside any diff:
- **Rotate** the six values a plain `bash -x` exposed (`~/.codex/auth.json` holds its own OpenAI key) — and the Albert key: its original hyphenated env name broke sourcing and echoed it into an agent session log on 2026-09-28 (renamed `ALBERT_API_KEY` since; rotation still pending, 0977 addendum).
- **ILaaS key**: clé consortium → `~/.config/keys/ilaas.env`, then replace the placeholder in `~/.pi/agent/models.json` and enumerate ids via `GET /v1/models`. Albert is done: activated 2026-09-28, `gpt-oss-120b` passes tool calls (1–2 s), `qwen3-coder` emits calls as text — use gpt-oss-120b or llm-proxy (0977 addendum).
- `scripts/projects.json`: **kept** — zero readers (0941) but a candidate mapping input for 0920's project-memory; delete after 0920 if unconsumed.
- Live `settings.json` re-alignment: the specific deleted-script wiring is gone (checked 2026-09-28); the drift class remains 0886's to reconcile.

## Blockers
(none)

## Next actions
- **Memory v7** (tracker 0909): foundations 0911, 0917 unblocked, nothing started. Standing red row: disjoint roots need the repo out of `~/.claude` — now ticketed as **0978** (child of 0909); re-read 0920/0923 before picking them up.
- **Portable model policy** (tracker 0974): Phase 0 is 0975.
- **Open defects worth a slot**: 0875 (hermeticity guard blind to script-path spawns), 0879 (gate writes malformed log lines), 0955 (credential-shaped names), 0979 (Pi silent reroute to openrouter).
- **Watch**: re-open 0062 (Firecracker) when agents run against secret-bearing projects; lift the merge-review gate into the harness when a second consumer project grows one (0900).

## Backlog
- Merge REALF guidelines and business rules
