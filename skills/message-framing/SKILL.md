---
name: message-framing
description: "Frame the central message of a talk, abstract or article before drafting it."
---

# Message framing

The single upstream step for slides, abstracts and articles: settle **one
claim** the piece exists to deliver, before any structure or prose. Downstream
skills assume it is settled and send the author back here when it is not.

**One piece, one message.** A message is a claim someone could dispute, stated
in one sentence — not a topic, not a summary, not three findings joined by
"and". Everything else in the piece is evidence for it or goes.

## The pass, in order

Run it sequentially, in one conversation with the author: each step narrows
the next, and nothing here is worth delegating.

1. **Context.** Ask two or three questions at a time, not a questionnaire:
   format (talk length, abstract word limit, article type), function (inform,
   convince, report, open a discussion), audience (expertise, what they already
   believe), constraints (what must not be said or spoiled). Read the source
   material first so the questions are ones only the author can answer.
2. **Candidates.** Draft three to five candidate messages from the source, each
   a one-sentence claim. Reject topics outright ("the history of X" names a
   field, not a message).
3. **Select.** Weigh each candidate on: does it serve the function, will this
   audience accept the premise, does it break a constraint, would a peer
   already say it (a truism is not a contribution), can the source carry it.
   Recommend one, with the runner-up and why it lost; the author decides.
4. **Validate** the chosen sentence:
   - *Dispute test*: someone competent could disagree. Nobody could → too vague.
   - *Substitution test*: if the piece were replaced by this sentence, its
     purpose would still be served.
   - *Citation test* (abstracts, articles): it is what the piece would be cited
     for saying.
   - *Source test*: the material supports it as stated. A message the evidence
     does not carry is reframed or dropped, never stretched.

When the author has "several equally important points", the others become
supporting evidence or another piece. When the material supports no focused
claim, say so: the message is not there yet, and drafting will not find it.

## Illustrative example (invented)

*Not a real case; no figures.* An author has a working paper on how a policy
term entered an international negotiation's vocabulary, and a 20-minute slot
at a history of economic thought conference, audience of historians of
economics, not climate specialists.

- "The history of the term in negotiations" — a topic; rejected.
- "Economists shaped the term" — a truism this audience expects; weak.
- "The term was defined by accounting conventions before economists theorised
  it" — disputable, differentiating, supported by the paper's archival
  chapter. **Selected.**
- "The negotiations failed because the term was vague" — the source does not
  establish causation; fails the source test.

## Output

```
Message: <one sentence>
Rationale: <two or three sentences: why this claim, for this audience and function>
Runner-up: <sentence> — <why it lost>
Next: <downstream step>
```

## Downstream

- Talk → `/slides` (slide titles build toward the message; doctrine in
  `rules/doctype/slides.md`).
- Conference abstract → `/conference-submission-prep`; a slot-limited abstract
  over budget → `/cut-prose`.
- Article → `rules/doctype/article.md` (the introduction states the message as
  the contribution).
