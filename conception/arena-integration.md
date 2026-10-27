# Arena integration — 2026-10-13

Arena is an independent repository, currently checked out at
`~/CNRS/code/arena`. Set `ARENA_ROOT` to its checkout; there is no implicit
fallback to the harness. Its protocol is `skills/arena/SKILL.md`, its analysis
is `scripts/tournament-analysis.py`, and its reports are `docs/tournament-graphs/`
and `docs/tournament-graphs-en/` relative to that repository.

The harness owns the worker routing skill, its grid, coverage and door cache.
It consumes reviewed arena evidence; it does not host the tournament runner,
protocol, reporting scripts, reports or their tests. Legacy grid numbers were not
changed during the separation and remain historical evidence rather than
corrected publication scores. The 2026-10-15 refresh adds two author-selected,
provisional cycle-3 candidates (f1x and f2m); their pinned readout, metric
definitions and coverage limits are recorded in the route grid and coverage
files. Existing legacy rows and role clusters remain unchanged.

To prepare an explicit refresh in a harness review branch, set both roots:

```bash
python3 "$ARENA_ROOT/scripts/tournament-analysis.py" --arena "$ARENA_ROOT" \
  --grid "$IDH_ROOT/skills/route/grid.json"
```

Review coverage/provisional marks and update `routes.json` in the same pass.
This command writes the specified grid and its sibling coverage file.

Open tickets transferred with their original IDs and complete journals:
1048, 1049, 1050, 1051, 1058, 1061, 1087, 1093. Their current files live in
arena's `tickets/`; transfer does not mean completion. At the author’s request,
1048 and 1087 have historical copies closed as `wontdo` in the harness,
with explicit transfer reasons; their arena copies stay open. Closed harness tickets
and dated harness memories remain historical records. The independent repo
also holds copies of the closed tournament tracker/report/runner tickets.
Old harness-relative report paths resolve in arena with the same suffix;
use Git history for their pre-transfer harness versions.

The arena migration manifest `migration/from-harness-2026-10-13.json` records
original SHA-256 hashes and the source harness commit. Sources were compared
byte for byte before removal. Subsequent portability edits and frozen route
test fixtures are documented in arena's `migration/README.md`.
