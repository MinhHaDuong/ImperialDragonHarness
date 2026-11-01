# Design note template

The Imagine phase's deliverable when the author is in the loop
(`rules/workflow.md` § Cycle). One file per question:
`conception/YYYY-MM-DD-<topic>.md`. Write it with the author, section by
section; an agent drafting alone marks every judgment as its own.

## 1. Problem

What hurts, for whom, and how we know: the observation, not the cause.

## 2. Situation

What exists now, read from git: the files, scripts and rules involved, the
history that produced them (commits, tickets, journal), and what was tried.

## 3. State of the art

What others do: documentation, upstream projects, the web, forums. Cite each
source; say what was searched and found nothing.

## 4. Alternative solutions

At least two, described fairly:
- the most direct fix;
- one from a different family (another mechanism, not a variant of the first).

## 5. Synthesis and recommendation

The pick and why, with cost estimates for each alternative: author-hours,
agent time, USD where it applies, and what it costs to undo.

## 6. Implementation plan

Phases, each one merge request or ticket sized to one sign-off unit, in
order, with what each phase proves before the next starts.

## Review

Two advisor-level reviews, decorrelated (`skills/route/references/decorrelation.md`),
and a KISS pass: what can be removed and still solve section 1. Record
reviewers and their findings at the end of the note.
