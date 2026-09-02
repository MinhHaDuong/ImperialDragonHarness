---
name: project-spec-edit-mechanics
description: "Post-2026-09-01 layout: one SPEC.md (RFC order, DRAFT header, date-is-version, system-only prose), standing folded into README.md; the guard couplings that bite — quote coupling, standing-window digit rule, roster-line trap, ledger-decides-drift."
metadata:
  node_type: memory
  type: project
  originSessionId: 956366a1-d8ac-475f-8eb7-5fc00800752b
  modified: 2026-09-02T08:52:57.690Z
---

The layout changed radically on 2026-09-01 (PRs #135, #137): the spec/ dir is
gone. One `SPEC.md` at the root in RFC order (§2 Terminology, §3 Requirements,
§4 Constraints, §5 Design — old DESIGN §2.8 is now §5.2.8 — §6 Security),
`DECISIONS.md` at the root, and the standing report (bars, twenty-four table,
ladder rosters) folded into the top-level `README.md`. Guards are six:
deps, figures, models, names, progress, ticket-logs — five others retired on zero
catches, their rules now reader-kept.

Conventions an editing session must know:

- **SPEC.md speaks only of the system** (ruled 2026-09-01): no ruling dates,
  no DECISIONS breadcrumbs, no ticket numbers, no process narration. Ruling
  provenance lives in the ledger alone. System-incident rationale (the 92,7 %
  cautionary) stays; writing history goes.
- **SPEC.md header: Status DRAFT / Author Minh Ha-Duong (CNRS) / Date** — the
  date IS the version; bump it on any substantive change. Status changes only
  on the author's word.
- **The spec's subject is the capability, not zoteus** (author, 2026-09-01):
  requirements bind any implementation; Zotero-native integration ranks first
  among homes; zoteus is the vehicle the design is measured on.
- **Quote coupling**: README's standing rows quote SPEC §3 promise sentences
  verbatim — edit both in one commit or the intermediate commit is red.
- **Digit rule is windowed**: check_progress's DIGIT/BASELINE checks read only
  README's standing window ("## Where the promises stand" → "## How work
  leaves this repository"); digits there must be address forms ("goal 5",
  "R35", dates, tickets). Hand-maintained spelled-out counts carry a `\*`
  footnote mark (convention 2026-09-01); guarded counts never take the mark.
- **Roster trap unchanged**: the guard reads goal rosters from the LAST
  "Goal N binds:" line per goal in DECISIONS.md — never write that pattern
  except to rule rosters.
- **The ledger's own formatting decides drift-vs-exception** (44,9 not 44.9).
- **The increment train lives in GOVERNANCE.md** (moved 2026-09-01), not the
  spec: upstream filing order is process, the ladder on README is build order.
- **The ledger has two sections, and EOF is the wrong one.** `## Ratified`
  (line 18) runs to `## Awaiting ratification` (~line 3300); a ruling appended
  at end-of-file lands under Awaiting and reads as unratified (bit twice on
  2026-09-02, caught by /gaze). Insert ratified entries just before the
  Awaiting heading; when a ruling consumes an awaiting bullet, delete the
  bullet in the same commit. Nothing guards this — the sections are prose.

Ticket notes still ride `./tickets/erg log NNNN "claude note …"`.

**Amended 2026-09-02, four moves in one day.** `CLAUDE.md` is renamed
`AGENTS.md` and is the agent instruction file both Claude and Codex read; the
document map (file-to-role table) lives there now rather than in `README.md`,
because `AGENTS.md` is auto-loaded into every session and `README.md` is not.
The goals ladder left `SPEC.md` §3 for `README.md` — it is an implementation
strategy, not a specification — leaving a pointer subsection and a trimmed §2
glossary entry. And `bench/check_ticket_logs.py` joined the gate (no log stamp
may postdate the commit that wrote it). Twelve rulings landed that day; read
`DECISIONS.md` rather than trusting any state paragraph here.
