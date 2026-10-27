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
