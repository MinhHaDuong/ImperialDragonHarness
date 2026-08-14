<!-- last-reviewed: 2026-08-14 -->
# Fine typography — English, rendered deliverable

A **finishing** pass, on a deliverable something renders. It crosses two axes:
the language of the text and the markup language. It presupposes frozen content
— during drafting it is churn. A draft nothing renders owes it nothing, and the
pass runs on the deliverable, never retroactively on the draft source.

- **LaTeX: let the class and `babel` do the spacing** — hand-inserted `~` and `\,` double the correction later.
- **Markdown or HTML rendered in UTF-8: manual pass on the deliverable**, at finishing only.
- **Thousands separator**: thin space or comma per venue style (10,000 or 10 000), one choice held throughout.
- **Punctuation inside quotes in US style, outside in UK style** — follow the variety the document chose.
- **Leave math mode alone**: a mechanical sweep over `:` or spacing corrupts `$H_0 : f = 0$`.
- **Non-UTF-8 render or plain-text output: insert nothing** — a non-breaking space becomes a stray byte there.
