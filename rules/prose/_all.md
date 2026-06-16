<!-- last-reviewed: 2026-06-16 -->
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

## Elements of Style — the load-bearing few

- **Omit needless words.** Every word must earn its place. Cut "the fact that", "in order to" → "to", "due to the fact that" → "because".
- **Use the active voice.** "We measured X" not "X was measured", unless the actor is genuinely irrelevant.
- **Put statements in positive form.** Assert what is, not what is not.
- **Use definite, specific, concrete language.** A number beats "several"; a name beats "various stakeholders".
- **Keep related words together.** Subject next to verb; modifier next to what it modifies.
- **One paragraph, one idea.** If a paragraph turns, it is two paragraphs.
- **Prefer the standard word to the fancy one.** "use" over "utilize", "before" over "prior to".

## Scope note

This is a seed. Grow it deliberately — add a guard only when you have seen the
defect in real drafts, and keep each entry one line so the injected body stays
small. Document-type conventions (techreport, slides, book) and language norms
(fr, en) live in `rules/doctype/` and `rules/lang/`, not here.
