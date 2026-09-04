# Perch adapter pilot

Ticket 0802 ports one behavior only. `skills/perch/SKILL.md` remains the live,
canonical workflow body. The provider-neutral installation target is
`~/.agents`, making that body `~/.agents/skills/perch/SKILL.md`. Codex and Pi
discover it there directly. Claude Code receives the only discovery link.

The current full harness still lives at `~/.claude` until the path and safe
migration slices land. This pilot proves the destination; it does not claim
that moving the whole checkout is safe yet.

The pilot records support only for the CLI versions listed in
`pilot-support.json`. Its check refuses an unparseable, missing or unlisted
version. Direct native discovery cannot enforce that check, so this is an
explicit support boundary rather than a runtime activation lock.

```bash
# Inspect the live Claude version without changing anything
python3 ~/.agents/adapters/perch.py check-version claude
python3 ~/.agents/adapters/perch.py check-version codex
python3 ~/.agents/adapters/perch.py check-version pi

# Install the sole provider-specific discovery link
python3 ~/.agents/adapters/perch.py install claude

# Remove only the link managed by this pilot
python3 ~/.agents/adapters/perch.py uninstall claude
```

Native expressions are intentionally different: Claude uses `/perch`, Codex
uses `$perch`, and Pi uses `/skill:perch`. The inventory records those facts;
the adapter does not invent a common invocation syntax.

## Manual smoke evidence

CI proves discovery, metadata, body identity, output-shape instructions,
fail-closed versions and managed-link behavior. It does not spend model tokens.
For each pending `manual-smoke` assertion in `pilot-support.json`:

1. record `git status --short`;
2. invoke the native expression in a session containing one completed item and
   one unresolved item;
3. verify `Done`, `Open`, `Stance`, and optional-only `Drift`;
4. record `git status --short` again;
5. replace the assertion's pending test text with date, exact version, prompt,
   result and observed headings, then set `result` to `pass`.

The pilot does not claim broader IDH parity.

## Observed duplication

This slice found no duplicated workflow prose and therefore proposes no prose
generator, intermediate representation or workflow DSL. Codex and Pi share the
de facto `.agents/skills` discovery convention, so no adapter is justified for
either. Claude alone needs a discovery projection. The version allowlist is
shared because all three clients need the same explicit support check for an
unmeasured CLI version. Keep this implementation perch-specific until a later
slice repeats a mechanism worth extracting.
