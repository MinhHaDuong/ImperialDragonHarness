---
name: LaTeX notation conventions and pitfalls
description: Procedural rules for LaTeX edits in the fuzzy-corpus paper — notation tables, renaming, and math framing
type: feedback
originSessionId: 4976a990-7fcf-42e1-bfe2-baf96c4db9f1
---
Never document LaTeX macros as "symbol = expansion" in the notation table — both sides expand to the same rendered letter, producing "W=W, G=G" tautologies.
**Why:** An agent writing the notation table confused macro documentation with symbol definition.
**How to apply:** Symbol column = reader-facing math symbol, not `\macro = \expansion`.

Use Edit tool (never sed) for LaTeX renaming. sed backslash escaping corrupts LaTeX commands.
**Why:** A sed-based G→\Gamma rename produced `\$\\Gamma\` corrupted output.
**How to apply:** Any rename touching `\command` patterns must use the Edit tool.

"The starting condition is inflationary" is correct in Appendix C's monotone theorem — not "μ₀ is inflationary". Inflationarity (μ₀ ≤ Φ(μ₀,μ₀,Γ)) is a joint condition on (Φ, μ₀), not a property of μ₀ alone.

When body and appendix share a `\label{}`, LaTeX emits `multiply defined` warnings and `\ref{}` resolves to the first definition (body), breaking appendix cross-references. Fix: rename the body label (e.g. `thm:convergence-closed-world`), replace the body proof with "special case of \Cref{thm:...} in \Cref{app:...}", verify the appendix theorem is strictly more general before doing so.
**Why:** Duplicate labels `thm:monotone-convergence` and `prop:lambda-approx` silently misdirected cross-references for multiple sessions before being caught by a log grep.
**How to apply:** After adding any theorem to an appendix, grep for its label across all `.tex` files before committing.
