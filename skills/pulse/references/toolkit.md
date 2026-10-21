# Remedies

For each: when it fits, its prerequisite, what to check first, how to verify, how to undo. Offer a remedy only after checking its prerequisite in this project. Prices are rough; replace them with a figure for the case at hand.

## Parallel workers

- **Fits.** A serial runner on a multi-core host, with independent tests.
- **Prerequisite.** No shared mutable state, fixed ports or shared temporary paths. The worker plugin is installed or declared.
- **Check first.** `pulse_profile.py profile <record> --workers N` for the lower bound: the longest test sets a floor, so one dominant test caps the gain.
- **Verify.** Run twice with workers; compare the pass set with the serial run. Time it in the environment agents use.
- **Undo.** Drop the flag. Price: about 0.5 author-hours.

## Tiering (markers, collection hook, duration budget)

- **Fits.** A few heavy tests on the fast path while a slower tier already runs in the merge or ex-post gate.
- **Prerequisite.** Something runs the slower tier before it matters (the pre-merge gate, or an ex-post run of the main branch). Confirm that.
- **Check first.** The exact tests moved, and where they now run. Moving a test later removes none of its coverage only if the later run exists.
- **Verify.** `compare` before and after; the fast-tier total and its top-N share.
- **Undo.** Remove the marker. A duration budget on the fast path keeps the fix from decaying.

## Path-scoped gate

- **Fits.** Doc-only or ticket-only changes paying for a code gate.
- **Prerequisite.** A map from paths to gate targets that falls back to the full gate for any source file or unmapped path (the harness provides a selector for this and prints `selected:` and `skipped:`).
- **Verify.** Dry-run on a docs-only diff, a code diff and a mixed diff; the code and mixed diffs must select the full gate.
- **Undo.** Delete the map. Price: about 1–2 author-hours.

## Stage-level caching (pipeline stages, build stamps)

- **Fits.** The cost is a data stage the tests exercise, not the tests themselves.
- **Prerequisite.** The stage's inputs are fully declared (code, parameters, data). A cache keyed on declared inputs fails silently on an undeclared read; only a sandbox that exposes declared inputs alone fails loudly.
- **Verify.** Change an input and see the stage rerun; delete an output and see it rebuilt.

## Smaller fixtures

- **Fits.** A smoke test that runs the real pipeline on a large input.
- **Check first.** What the test asserts: a smaller input must still exercise the same branches.

## Flake quarantine with a deadline

- **Fits.** A confirmed intermittent test that blocks the gate and whose cause is not yet found.
- **Rules.** It keeps running and is reported. A date is written beside it. Past the date, fix or delete.

## Environment set-up cost

- **Fits.** A slow first run per session (see *collect*: first-of-session against later).
- **Check first.** Whether each new worktree rebuilds its environment from scratch, and whether the package cache and the environments share a filesystem so links are possible.

## Thin the wording pins

- **Fits.** Tests whose only assertion is that a phrase appears in a skill, rule or doc. The gain is fewer two-file wording changes, not time.
- **Keep.** Behaviour tests; structural invariants (frontmatter, catalog, links and pointers that must resolve, files that must stay absent, personal-data and agnostic checks); interface strings another program or skill consumes (a script path, a verdict token, a heading a parser reads); tests tied to a named past incident, frozen allowlists included.
- **Cut.** Pure phrase pins: whole files when only pins, single tests where a file mixes. One line of reason per deletion; search the repository for anything that imports the file's helpers or names the file.
- **Bound.** One batch per merge request, within its file limit (15 in the harness). Further batches are further merge requests.
- **Verify.** The full gate passes; test count and gate time before and after, on one host; a reviewer samples the cuts against the keep classes.
- **Undo.** Revert the batch.
- **No guards on guards.** Add no test, check or rule whose subject is another test or guard (a file that must stay deleted, a negative control required of every test, a scan of the tests). Adding, removing and judging guards is this skill's work, nowhere else.

## Not remedies

Deleting tests to save time; a rule telling every agent to use a cache; selection in a merge gate; blanket retries; raising a timeout to hide a slow gate.
