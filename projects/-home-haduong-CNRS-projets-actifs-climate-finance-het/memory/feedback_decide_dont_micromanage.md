---
name: feedback_decide_dont_micromanage
description: "Make the coherent decision across the whole logical unit; don't hardcode, don't half-do, don't ask piecemeal"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 298c9eb2-1548-4794-b4ea-f8cdfefa7522
---

When the author asks for a change, deliver the *coherent whole*, not the literal
minimum. Two failures that drew sharp rebukes ("Bac-3", "faut micropiloter !",
2026-06-28) on the conf manuscript numbering task:

1. **Reached for the hardcoded pattern first.** Asked to "start at 1. Introduction",
   I mechanically shifted hardcoded section numbers instead of proposing Quarto
   `number-sections: true` + `{#sec-…}` labels + `@sec-…` cross-refs. In 2026 the
   default is compile-time numbering, not numbers typed into headings.

2. **Half-did it and didn't flag the choice.** Numbered intro + acts but left the
   Conclusion `{.unnumbered}` by reflex (Œconomia house style) — on a *conference*
   version whose whole point was numbering. Inconsistent, and silent.

**Why:** Opus is expected to see the whole logical unit and act on it without the
author steering each piece. Piecemeal questions and literal-minimum edits feel
like micromanaging a junior.

**How to apply:** When told to renumber/restructure/rename, sweep the entire
unit (all headings, all cross-refs, conclusion, appendix), pick the modern
compile-resolved mechanism, apply one coherent convention throughout, and state
the one or two judgment calls you made (e.g. "appendix stays lettered A.x —
scholarly convention") rather than asking about each. See [[feedback_simplest_fix]]
and the autonomy rule "Better approach found → voice it before proceeding".
