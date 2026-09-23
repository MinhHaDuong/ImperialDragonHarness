---
name: typography-finish
description: "Fine typography pass for a rendered text deliverable at finalization, after its wording is frozen. Handles French or English spacing by output format; never applies to drafts."
disable-model-invocation: false
user-invocable: true
argument-hint: "<rendered-deliverable-path>"
---

# Fine typography at finalization

Use this skill when the author asks for a typography pass or a rendered text
deliverable is entering finalization. Check the language of the text, its markup
and the actual renderer. Apply the pass to the deliverable or its final render
source only after wording is frozen. Do not retrofit source notes or drafts.

- **French LaTeX with `babel` or `polyglossia`:** the renderer supplies French
  spacing. Do not type hard nonbreaking spaces or `~` before `: ; ? !` by hand.
  If the language package is absent, inspect the actual PDF before choosing a
  correction.
- **French Markdown or HTML rendered as UTF-8:** manually check U+00A0 (or
  `&nbsp;` in HTML) before `: ; ? !`, inside « French quotes », and in
  thousands separators. Apply changes to the final deliverable source, not a
  note that feeds it.
- **English rendered text:** follow the document's US or UK quote punctuation
  convention. Use a thousands separator consistent with the venue and document.
  Do not add French nonbreaking spaces by habit.
- **Plain text or a non-UTF-8 output:** do not insert nonbreaking spaces merely
  to satisfy a typography convention.

Inspect math, code, links and markup before any replacement. A mechanical
substitution around colons can corrupt `$H_0 : f = 0$` or `$G(i,j) := …$`.
Verify the rendered result, including its extracted text when available.
