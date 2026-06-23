---
name: Quarto var vs meta shortcode
description: "{{< var >}} only reads _variables.yml; use {{< meta >}} with metadata-files for per-document variables"
type: feedback
---

Quarto's `{{< var X >}}` shortcode only reads from a project-level `_variables.yml` file. It ignores `metadata-files:` and front-matter keys entirely — they show up in Pandoc metadata but the `var` shortcode doesn't look there.

Use `{{< meta X >}}` instead: it reads from document metadata including `metadata-files:`. Missing keys render as literal `?meta:X` (with a WARNING), which is better than `var`'s silent empty string.

**Why:** Discovered during #201 — `corpus_total_approx` was defined in manuscript front matter but `{{< var >}}` silently ignored it, falling back to the project-level `_variables.yml`.

**How to apply:** Any time variables need to be injected into Quarto documents, use `metadata-files:` + `{{< meta >}}`, not `_variables.yml` + `{{< var >}}`.
