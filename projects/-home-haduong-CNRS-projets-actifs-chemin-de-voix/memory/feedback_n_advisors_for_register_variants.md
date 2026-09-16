---
name: n-advisors-for-register-variants
description: "When task requires generating content in an unfamiliar register/dialect/period, fan out N (≈4) parallel agents each constrained to a distinct register, then synthesize and recommend one. Used successfully on ticket 0248 (Aliénor en occitan)."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e3f105e8-39ba-4385-850c-64fc7795ba3a
---

When the user asks for prose or translation in an *unfamiliar register* (medieval Occitan, Mistralian Provençal, IEO modern, hybrid literary), spawning N≈4 parallel agents — each rigorously constrained to ONE distinct register with explicit period markers, lexicon, and orthography — produces strikingly different drafts that illuminate the choice.

**Why:** A single agent on its own waffles toward the safest register. Forcing 4 disjoint registers exposes the trade-offs (readability vs. period accuracy vs. anachronism vs. compromise) that the user can then arbitrate concretely.

**Why to apply:**
- Task is creative writing in an unfamiliar register, dialect, or period
- The user wants to *see* what each variant looks like before choosing
- The constraints between variants are register-level (not just stylistic)

**How to structure each agent prompt:**
- Name the register precisely (period, dialect, norm — e.g. "norme classique IEO, languedocien" vs "Mistralian rhodanien")
- Specify orthography conventions to use (and *not* use)
- Demand uncertain words/forms marked with `[?]` — better honest than confident-and-wrong
- Require a 50-word translator note on choices made
- "Return ONLY the translation + the note. No preface, no apology, no metalanguage."

**Synthesis step (back in main agent):**
- Save all N drafts in `content/drafts/<X>-drafts.md` for durable reference
- Recommend one with rationale, mention 1-2 strong alternates
- Apply visible polish to the chosen draft (resolve `[?]`, swap problematic words like *vaginas* → *gainas* for medieval Occitan) before integration
- Let the user veto the recommendation; present alternatives clearly

Counter-indication: pure information lookup, single-correct-answer tasks. The pattern is for creative *register* choices, not factual ones.
