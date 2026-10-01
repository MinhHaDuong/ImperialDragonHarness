---
name: external-peer-review
description: "Send a manuscript PDF to external frontier models (independent providers via the configured gateway) for peer review; synthesize convergent findings into one verdict."
user-invocable: true
disable-model-invocation: false
argument-hint: "<pdf-path> [--models <resolved-advisor-models>] [--personas grinchy,student] [--text]"
---

# External peer review $ARGUMENTS

For helper commands, set `IDH_ROOT="$(cd -P "$(dirname "<loaded-SKILL.md>")/../.." && pwd -P)"` in the same shell call. Replace `<loaded-SKILL.md>` with the absolute path the runtime supplied for this skill. This follows a projected skill symlink to the canonical checkout; do not derive the helper root from the project cwd.

Send a manuscript PDF to real external models (independent providers, via the configured
OpenRouter gateway) under reviewer personas, then read the reviews back and present
a cross-reviewer synthesis. This is **complementary** to `/review-pr-prose`:
that skill runs a *simulated* in-harness panel; this one solicits *real
external* frontier-model reviews.

The bundled script is `"$IDH_ROOT/skills/external-peer-review/peer_review.py"`.

## Steps

1. **Locate the PDF.** Resolve the path argument. If it does not exist and the
   project has a Makefile target that builds the manuscript PDF (e.g. the rule
   whose output is that `.pdf`), offer to build it. Degrade gracefully if there
   is no such target — just ask the user for a path.

2. **Check the key.** The script resolves its OpenRouter credential from the
   variable named by `--credential-env` (default `OPENROUTER_API_KEY_IDH`):
   from the environment if it is set there, else from
   `~/.config/keys/openrouter.env`, which is sourced as shell code so an
   `export`-prefixed assignment resolves like a bare one. There is no `.env`
   search: a project that exported only a bare `OPENROUTER_API_KEY` now fails
   loud rather than resolving, which is deliberate — the keystore is the system
   of record, and the identity being billed should be named, not inherited.
   Pass your project's own uppercase, credential-shaped keyset variant
   (`--credential-env OPENROUTER_API_KEY_MYPROJECT`) to bill your own identity
   rather than the harness one. The name must contain an underscore-delimited
   `API_KEY`, `KEY`, `TOKEN`, `PASSWORD`, or `SECRET` component. The provider
   must be a regular file no larger than 256 KiB; only a scalar, single-line
   value is accepted. Resolution failure names the variable and the file probed
   and stops; never echo the value.

3. **Resolve advisor roles and personas.** Request two independent smartest
   advisor models (`model-level: frontier`, `effort: intensive`) from runtime
   configuration, preferably from different providers. Pass their resolved IDs
   explicitly with `--models`; do not rely on the helper's concrete defaults.
   If no mapping is available, ask for runtime configuration. Default personas
   are `grinchy,student` (four combinations). Personas are extensible in the script.

Set `ADVISOR_MODEL` to the first resolved ID and `ADVISOR_MODELS` to the
   comma-separated pair in the shell used for the commands below.

4. **Smoke-test ONE combo first** (project rule: test one before blasting).
   Run a single model×persona to confirm prompt assembly, that a review comes
   back non-empty, and that the input mode works:
   ```
   python "$IDH_ROOT/skills/external-peer-review/peer_review.py" <pdf> \
       --models "$ADVISOR_MODEL" --personas grinchy --out-dir <out>
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
   python "$IDH_ROOT/skills/external-peer-review/peer_review.py" <pdf> \
       --models "$ADVISOR_MODELS" \
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
