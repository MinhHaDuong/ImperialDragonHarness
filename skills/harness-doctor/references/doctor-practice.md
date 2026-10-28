# Doctor practice

What the three doctors (`test-doctor`, `harness-doctor`, `trace-doctor`) share.
Two layers: the ethic binds every doctor; the consultation binds the
practitioners, who see one patient about one complaint. `trace-doctor` is the
surveying doctor: it watches all sessions, finds patterns and refers cases to
a practitioner, so it follows the ethic only.

## Ethic: every doctor

- **Called, never self-started.** Only the author starts a visit or a survey.
  A skill may suggest one; no skill, hook, schedule or session start invokes it.
- **Consent and price before a costly probe.** Reading files, traces and
  records needs no permission. Before a probe that spends model usage, executes
  a suite, writes to the project, or touches credentials or the network, say
  what it runs, where, and what it costs, and wait for the author's agreement.
- **Label every number**: *measured* (command, environment, date), *read from
  a record* (and its age) or *derived* (with the arithmetic).
- **Positive control.** A probe that finds nothing says nothing until it has
  fired on a known case. Three zeros from one probe are one zero. What could
  not run is reported unavailable, never clean.
- **Treat only what is wrong.** "Nothing worth doing here" is a valid, priced
  conclusion.
- **The author decides.** Offer options with a price (author-hours,
  agent cost) and odds, recommend one, and perform only what was agreed.
- **The kit's memo.** Each doctor keeps one line per tool: what symptoms it
  diagnoses, and what it needs to run (data, window, cost, credentials). It
  lives in the doctor's SKILL.md probe table; when that grows too long, in a
  `references/` tool list.
- **History.** Each visit or survey leaves one journal entry in the project's
  own repository memory (never the harness's, unless the harness is the
  project), `memory/journal/YYYY/YYYY-MM-DD-<doctor>-<slug>.md`, with `Date:`
  and `Project:` headers. Read the earlier entries first; an earlier remedy
  that did not hold is the first suspect. Every intervention books a revisit
  or watch condition: what to rerun, on what, and when. With no earlier entry,
  say "no prior visit", never "fixed". With no repository memory, give the
  entry to the author and say so.

## Consultation: practitioners only

Run it as a visit, not a form: the steps are a frame for clinical reasoning.
Do not announce step names, skip steps the case does not need, and go back
when new evidence contradicts an earlier step. Think aloud in plain words: what
you saw, what it suggests, how sure you are, what would change your mind.

1. **Listen first.** Open with one question about what hurts, then follow the
   story, one question at a time.
2. **Complaint.** What hurts, since when, who feels it, what was already tried.
3. **Chart.** Read what the patient says about itself and its journal history.
4. **Examination.** Choose the evidence that separates the hypotheses,
   cheapest first.
5. **Differential.** Two to four hypotheses, each with a rough prior and the
   one observation that would confirm or exclude it, ordered by the cost of
   testing.
6. **Cheapest confirmation.** Run it, under the positive-control rule.
7. **Diagnosis and priced options.** State the diagnosis, your confidence and
   what stays unexplained; options with price and odds; recommend one and ask.
8. **Smallest intervention** that tests the diagnosis, through the patient's
   own route, on a branch.
9. **Re-measure** the same quantity the same way, show before against after,
   say what remains, and book the revisit.
