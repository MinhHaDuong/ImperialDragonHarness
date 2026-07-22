---
name: feedback-aitells-scope-manuscript-vs-crossdoc
description: "config/ai-tells.yml's blacklisted_words feeds a cross-document reduction guard — a per-document house-style choice (spelling variant) does not belong there"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 4416da70-2381-4a58-904a-29125c1a1dde
---

`config/ai-tells.yml`'s `blacklisted_words` list is consumed by two things
with different scopes: `test_manuscript_prose.py` (manuscript.qmd-scoped) AND
`scripts/qa_llm_judge_guards.py`'s `introduced_llmisms` (source-agnostic,
applied to whatever document pair an editorial reduction touches). Adding a
per-document decision — e.g. ticket 0243's Oxford-vs-Cambridge British
spelling choice for the Œconomia manuscript — to `blacklisted_words` would
leak into the cross-document reduction guard and false-positive on any other
deliverable that legitimately keeps -ise spelling.

`blacklisted_phrases` in the same file, by contrast, is NOT read by
`qa_llm_judge_guards.py` (only `blacklisted_words` + `conditional_words` are)
— it's manuscript-prose-review-only, so genuinely universal LLM-tell phrases
are safe to add there.

**Why:** caught before merge (ticket 0243, PR #1016) by checking
`grep -rln "ai-tells" --include="*.py"` and reading both consumers before
adding a spelling ratchet — the naive move would have added the -ise/-ize
list to `blacklisted_words` since that's the existing pattern for word-level
bans.

**How to apply:** before adding anything to `ai-tells.yml`, check what
consumes each key (`blacklisted_words` vs `blacklisted_phrases` vs
`conditional_words`). A **document-specific** choice (spelling variant, a
document's own register decision) goes in a scoped test file
(`tests/test_<doc>_prose.py`) as a local pattern list, not the shared config.
A genuinely **universal** LLM-tell (padding phrases, hedging stacks) is safe
in the shared `blacklisted_phrases`/`blacklisted_words`.
