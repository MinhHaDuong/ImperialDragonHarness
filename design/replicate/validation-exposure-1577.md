# Validation exposure source and scenario audit

Ticket: 1577. Documentation-only boundary; no scientific execution.

## Sources

- Replicator `03af9ef6ff3b64230addbae96e8be3403e1cf971`,
  `replications/gavard2026climate/reproduce/README.md`: choices calibrated on
  Tables 1 and B3, then fixed for the other tables. This supports a same-paper
  unused-table check, not fresh-paper validation. `COMPARE-PORT.md` preserves
  the later comparison with the September port; this change leaves the dated
  September findings intact.
- Replicator `a0bac78e9a8dac4647786822f2395cfcfad6d2b0`,
  `memory/journal/2026/2026-11-27-skill-rule-dispatch.md` and
  `tickets/0004-held-out-benchmark-of-replicate-on-about.erg`: Weschle and
  Atanasov reports informed development, so validation of those rules requires
  papers outside the development-exposed split.

## Scenario audit

| Scenario | Before | After |
|---|---|---|
| Blind validator follows the top-level Gavard worked-example link | Case answers retrieved before the probe-only exposure rule | Shared exposure check precedes retrieval; helpers inherit exclusions; exposed case excluded from independent validation |
| Implementation choices matched to some published tables, then checked on unused tables | No generic calibration freeze or distinction from fresh-paper validation | Choices, alternatives, targets, and identifiers frozen before unused-target evaluation; separate results and post-hoc history |
| Rules developed after reading Weschle/Atanasov reports, executor has not read them | Probe wording centers on executor/report exposure | Development-paper/cohort exposure separately excludes those cases even for a fresh executor |
| Ordinary reproduction of an exposed case (positive control) | Reproduction and report appraisal allowed | Remains allowed with disclosure; historical Gavard record retained |
| Fresh paper with unexposed executor/helpers and eligible cohort (positive control) | Blind assess restricts retrieval; probe hides report answers | Same retrieval boundary extends across verbs; prospective rules/selection/targets retained until frozen outputs |

## Preservation audit

Canonical assessment schema, ACRe categories, printed-digit tolerance, selected
scope freezes, signed probe execution, and publication gates are unchanged.
The mapping retains its September numerical findings and case history; the
new preface distinguishes their date and exposure from current authority.
No test pins these instructions' wording. No new estimates, scoring decision,
API call, or signing authority is introduced.
