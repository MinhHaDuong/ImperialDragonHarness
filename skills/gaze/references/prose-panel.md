# Gaze — prose panel

Loaded from `skills/gaze/SKILL.md` § 2–5 when the diff routes `prose`. It follows the seat protocol of `references/panel.md`; only what differs is here.

### Prose panel

Prose seats read the **full text**, not only the diff. Every seat is the
prose-reviewer profile (`agents/prose-reviewer.md`, contract
`profiles/prose-reviewer/PROFILE.md`); the seat's role, the rulebook or axes it
holds (`prose_predicate.py --axes`, § 2–4), the anchor HEAD, the changed-file
roster and its `<panel>/<reviewer>.md` path ride in the launch prompt. First
name the manuscript files (the predicate's `prose` verdict) and the target
venue. A caller brief names the prose seats and gaze recruits exactly those;
under the default brief, recruit for that venue and the scope of the change:
always an adversarial referee, a venue expert when the project has venue
rules. The
manifest lists one line per reviewer, its role in the perspective field.
Seats with relevant expertise use the tools available to them (literature search, installed linters).

- **AI-tells auditor, every default-brief run** (a caller brief runs it when
  it names `ai-tells`). One seat holds `config/ai-tells.yml`
  (blacklisted words and phrases, density limits, patterns), scans the full
  text and reports every hit with line, context and severity; it has no other
  role, it is a lint pass. Revised passages are new surface for it, so a
  repeat run includes it too.
- **Editorial-brief auditor, when `docs/editorial-brief.md` exists.** Under
  the default brief, skip it silently otherwise; a caller brief naming it
  without the file is refused. The skill owns the schema, projects own the content: one
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
