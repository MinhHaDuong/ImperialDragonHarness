---
name: external-peer-review
description: "Send a manuscript PDF to external frontier models (OpenAI + Mistral via OpenRouter) for peer review; synthesize convergent findings into one verdict."
user-invocable: true
disable-model-invocation: false
argument-hint: "<pdf-path> [--models openai/gpt-5.5,mistralai/mistral-large-2512] [--personas grinchy,student] [--text]"
---

# External peer review $ARGUMENTS

Send a manuscript PDF to real external models (OpenAI + Mistral, via one
OpenRouter key) under reviewer personas, then read the reviews back and present
a cross-reviewer synthesis. This is **complementary** to `/review-pr-prose`:
that skill runs a *simulated* in-harness panel; this one solicits *real
external* frontier-model reviews.

The bundled script is `~/.claude/skills/external-peer-review/peer_review.py`.

## Steps

1. **Locate the PDF.** Resolve the path argument. If it does not exist and the
   project has a Makefile target that builds the manuscript PDF (e.g. the rule
   whose output is that `.pdf`), offer to build it. Degrade gracefully if there
   is no such target — just ask the user for a path.

2. **Check the key.** Confirm `OPENROUTER_API_KEY` is available (in the
   environment or a `.env` walking up from the project root). The script reads
   it the same way; never echo the value. If it is missing, stop and tell the
   user.

3. **Pick models and personas.** Defaults: models
   `openai/gpt-5.5,mistralai/mistral-large-2512`, personas `grinchy,student`
   (four combos). Any OpenRouter model id is accepted. Personas are an
   extensible dict in the script — adding one is a single entry.

4. **Smoke-test ONE combo first** (project rule: test one before blasting).
   Run a single model×persona to confirm prompt assembly, that a review comes
   back non-empty, and that the input mode works:
   ```
   python ~/.claude/skills/external-peer-review/peer_review.py <pdf> \
       --models openai/gpt-5.5 --personas grinchy --out-dir <out>
   ```
   Inspect the written `review_*.md` for quality before launching the rest.
   - **Balance gate:** PDF-file mode (the default, via the `file-parser`
     plugin) needs the OpenRouter "files" balance minimum of **$0.50**. On
     HTTP 402 the script automatically falls back to local text extraction
     (`pdftotext`); you can also force this with `--text`. Text mode needs
     `pdftotext` (poppler-utils) installed.

5. **Run the rest in the background.** Launch the full set in the background so
   the long calls do not block:
   ```
   python ~/.claude/skills/external-peer-review/peer_review.py <pdf> \
       --models openai/gpt-5.5,mistralai/mistral-large-2512 \
       --personas grinchy,student --out-dir <out>
   ```
   Combos run concurrently; one failing combo is reported and the others
   continue. One `review_<model>_<persona>.md` is written per combo.

6. **Synthesize.** Read every written review and present a single cross-reviewer
   synthesis:
   - **Consensus verdict** (reject / major / minor / accept) — where reviewers
     agree, and where they split (preserve dissent).
   - **Convergent themes**, weighted by how many reviewers raised each one (a
     concern flagged by 3 of 4 reviewers outranks a solo gripe).
   - **Sharp individual catches** — incisive points a single reviewer made that
     the others missed.
   Reference the specific reviewer (model + persona) behind each point so the
   author can judge its source.

## Notes

- Forge-agnostic: this skill produces review artifacts; it does not open or
  touch any merge request itself.
- The reviews are advisory input for the author, never a CI gate.
- Output filenames are derived from the model id and persona, so re-running
  with the same combos overwrites in place.
