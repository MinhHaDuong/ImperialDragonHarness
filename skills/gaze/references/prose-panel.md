# Gaze — prose panel

Loaded from `skills/gaze/SKILL.md` § 3 when the plan reviews prose. It follows the seat protocol of `references/panel.md`; only what differs is here.

### Prose panel

Prose seats read the **full text**, not only the diff. Every seat is the
prose-reviewer profile (`agents/prose-reviewer.md`, contract
`profiles/prose-reviewer/PROFILE.md`); the seat's role, the rulebook or axes it
holds (`prose_predicate.py --axes`, `references/plan.md`), the anchor HEAD, the changed-file
roster and its `<panel>/<reviewer>.md` path ride in the launch prompt. First
name the manuscript files (the predicate's `prose` verdict) and the target
venue, then recruit for that venue and the what: an adversarial referee, a
venue expert when the project has venue rules. The plan lists one line per
reviewer, its role in the name field.
Seats with relevant expertise use the tools available to them (literature search, installed linters).

- **AI-tells lint, a check.** When the project ships `config/ai-tells.yml`
  (blacklisted words and phrases, density limits, patterns), the plan scans
  the revised text against it as a script item, reporting every hit with line
  and context; it is never a seat.
- **Editorial-brief auditor, when `conception/editorial-brief.md` exists and the what touches the manuscript.** Skip it
  otherwise, saying in the panel output that `conception/editorial-brief.md` is absent. The skill owns the schema, projects own the content: one
  standing decision per entry, with a title, **Decision:** (one sentence),
  **Rationale:** (one or two) and **Ticket:**. The seat reads the brief and the
  manuscript diff and returns a table, carried verbatim into the synthesis;
  every violation cites its line, and the seat has no other role:

  | Entry | Status | Evidence |
  |---|---|---|
  | decision title | upheld / violated / not touched by this diff | line ref, or "not in diff" |

In the synthesis, group findings as `blocking` (blocks acceptance), `concerns`
(should fix) and tagged suggestions, build the manuscript with the project's
declared build, and check the prose against its data. Prose `verifiable:` evidence is a line citation, a numeric
recheck or a lint hit; "readers may find X confusing" without a pointer is a
`consider:`.
