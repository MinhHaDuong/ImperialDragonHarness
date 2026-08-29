---
name: reference-author-voice-corpus
description: The author's own English/French prose corpus, assembled by him to capture his voice — use it before any "write in the author's voice" pass
metadata:
  type: reference
---

The author curated a voice corpus at
`/home/haduong/data/projets/chemin-de-voix/corpus/clean/`:

- `voix-auteur-en/` — 34 texts, 48 311 words. Two solo academic papers (the
  1/n scenario-possibility paper; the Lacq CCS case study), op-eds (OECD
  Insights 2016, Mekong Eye 2023, Tia Sáng 2021–23, SAPIENS 2009), and a
  confidential self-interview, which is the most unmediated English in the set.
- `voix-auteur-fr/` — 7 texts.

He assembled it *for the purpose of capturing his voice*, which settles the
provenance question any voice-matching pass has to ask: this is text he wrote,
not text an agent wrote and he tolerated. Silence is not endorsement, so
agent-drafted prose in a repo is weak evidence of his voice even when he never
vetoed it.

**Why:** a "write in the author's voice" pass without this corpus falls back on
removing LLM tics, which reaches neutral, not his voice. Measured on
search-works-for-zotero 2026-08-29: after a tic-removal pass scored **zero on
34 of 35 tic patterns**, the prose still carried em-dashes at **7x** his rate
(21,9 vs 3,2 per 1 000 words). Tics and register are different targets.

**How to apply:** read the corpus before rewriting, and write down an explicit,
falsifiable description of the voice first — the author can correct a wrong
model of his voice in one sentence, far cheaper than correcting thousands of
words written against it. Score the result mechanically against the corpus
(em-dash rate, semicolon rate, median sentence length), because a model can
state the right voice spec and still overshoot in execution: the 2026-08-29
pilot fixed em-dashes (21,7 → 5,0) while pushing median sentence length
*away* from his 23 words, down to 15.

Related: [[feedback-subagent-model-effort-levers]].
