# The author's checklist

What the doctor looks for in skill and rule text. The script finds the
mechanical items; the doctor judges every hit and alone covers the rest.

| Item | Found by | Judged by |
|------|----------|-----------|
| Contradiction within one skill, or between skills and rules | the doctor | the doctor |
| A skill presuming or paraphrasing what another skill does or owns | the doctor | the doctor |
| Historical justifications in place of the rule's reason | script (phrases, dates) | the doctor |
| Ticket numbers or project names | script (ticket forms, project list) | the doctor |
| SKILL.md over 150 body lines: a warning, since splitting follows exclusivity, not length (`references/authoring-skills.md`) | script | the doctor |
| Long shell or Python blocks and heredocs in skill text: scripts belong in the harness's scripts directory | script | the doctor |

False positives are expected (a date in a command example, a template, a
quoted phrase) and dismissed with a word of reason. A hit the doctor keeps is
reported like any other finding.

Contradiction and ownership are the costly checks. Look for: two skills
stating opposite rules on the same act; a skill restating a step another
skill owns, which drifts when the owner changes; a rule body and a skill
disagreeing on who decides.

## Shared stance with test-doctor

The visit stance (complaint, hypotheses, probes that separate them, priced
proposals, revisit) is shared with `skills/test-doctor/SKILL.md`. The
harness doctor points at it in one line and restates only what differs: the
patient is harness text, not a project's suites, so the triage order, probes
and controls differ. The small duplication is accepted: a shared reference
for two skills adds a pointer hop and a drift owner. Extract one only when a
third doctor appears.
