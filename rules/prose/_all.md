<!-- last-reviewed: 2026-07-07 -->
# Prose rules — every prose file

Applies to all prose formats (tex, qmd, md, txt) regardless of document type or
language. Injected on the first prose edit of a session by the
`inject_rule_on_edit.py` PreToolUse hook. This is the universal layer; doctype-
and language-specific rules compose on top of it.

## LLMism guards — phrasings to avoid

These are the tics that mark text as machine-written. Cut them.

- **No "It's not just X, it's Y"** and its cousins ("not only… but…", "isn't merely… but rather…"). The antithesis-reversal cadence is the single strongest LLM tell.
- **No empty intensifier openers**: "It's important to note that", "It's worth noting", "Needless to say", "In today's fast-paced world".
- **No "delve", "tapestry", "landscape", "realm", "navigate the complexities", "testament to", "boasts", "underscores", "leverage" (as a verb), "robust", "seamless", "game-changer".**
- **No tricolon padding**: avoid reflexive three-item lists ("fast, reliable, and scalable") where two items, or one, carry the meaning.
- **No summary that restates the body** ("In conclusion, as we have seen…"). End on a point, not a recap.
- **No hedging stacks**: "may potentially", "could possibly", "it seems likely that perhaps". One hedge maximum.
- **No second-person life-coaching** ("Let's dive in", "You've got this") in formal prose.
- **No em-dash chains**: at most one em-dash per paragraph — a second usually hides a sentence that wants a period.
- **No transition-word drumbeat**: "Moreover", "Furthermore", "Additionally", "Notably" opening consecutive sentences; let the logic carry the link.
- **No importance inflation**: "crucial", "critical", "key", "vital", "essential" — reserve for claims that would change a decision.
- **No panorama adjectives**: "comprehensive", "holistic", "multifaceted", "nuanced" — name what is covered instead.
- **No filler verbs of inquiry**: "unpack", "explore", "dive deeper into" — state the finding, not the gesture of looking.
- **No authorial winks**: "fittingly", "ironically", "amusingly", litotes like "should not surprise" — state the coincidence or the reflexive fact flat and let the reader feel it (HET manuscript de-winking, 2026-07-08).
- **No structure words borrowed from music or drama unless exact**: "coda", "overture", "interlude", "finale" — a coda ends the piece; a mid-paper section is not one. Name sections by function (2026-07-08).
- **No "significant" without a test**: in scientific prose the word claims statistics; write "large" or give the number otherwise.
- **No weak copulas where a verb exists**: "serves as", "acts as", "plays a role in" — "X regulates Y", not "X plays a role in regulating Y".
- **No bold-lead bullet cascades in running prose**: if every paragraph is a bullet with a bolded lead, it is a list, not an argument — write the paragraph.

## Elements of Style — the load-bearing few

- **Omit needless words.** Every word must earn its place. Cut "the fact that", "in order to" → "to", "due to the fact that" → "because".
- **Use the active voice.** "We measured X" not "X was measured", unless the actor is genuinely irrelevant.
- **Put statements in positive form.** Assert what is, not what is not.
- **Use definite, specific, concrete language.** A number beats "several"; a name beats "various stakeholders".
- **Keep related words together.** Subject next to verb; modifier next to what it modifies.
- **One paragraph, one idea.** If a paragraph turns, it is two paragraphs.
- **Begin each paragraph with its topic sentence.** The argument should be readable from first sentences alone.
- **Place the emphatic word at the end of the sentence.** The last slot carries the stress; do not spend it on a qualifier.
- **Express coordinate ideas in parallel form.** Items in a series share one grammatical shape.
- **Avoid the feeble qualifiers**: "rather", "very", "little", "pretty" — they drain the word they modify.
- **Do not overstate.** One unearned superlative makes the reader doubt every other claim.
- **Prefer the standard word to the fancy one.** "use" over "utilize", "before" over "prior to".
- **Cutting to a word budget? Remove whole before you condense** — see `cutting.md`: rank and cut weak/redundant passages entire, then condense the remainder; never a condense-only plan.

## Scope note

This is a seed. Grow it deliberately — add a guard only when you have seen the
defect in real drafts, and keep each entry one line so the injected body stays
small. Document-type conventions (techreport, slides, book) and language norms
(fr, en) live in `rules/doctype/` and `rules/lang/`, not here.
- **Generated texts carry the correct date.** Render-time dates (`date: today`, `\today`) for working documents; a pinned date only on a frozen submission artifact, updated at each submission event (stale March date on a July revision, 2026-07-24).
