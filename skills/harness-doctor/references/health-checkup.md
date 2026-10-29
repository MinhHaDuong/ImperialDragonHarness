# Health checkup: the journal and its metrics

`"$IDH_ROOT/scripts/health_checkup.py"` appends one JSON object per visit to
`health/journal.jsonl` (committed, append-only, `merge=union` in
`.gitattributes`). Each record holds `schema`, `ts`, `host`, `commit`,
`window` (since the previous record; the first covers 7 days; never more
than 30, starting at the newest `ts`, whatever the line order union merges
leave) and a flat `metrics` object of `name -> {value, unit, source}`.

A source that is missing or unreadable writes `value: null` with a `gap`
reason. Read a gap as "not measured", never as zero. Readers ignore names they
do not know, so a metric can be added, renamed (the old series stays) or
dropped without migrating the journal.

| Prefix | Read from |
|--------|-----------|
| `ticket.solve_*` | `slow_tickets.collect`: `duration:` lines, else PR open to merge (an upper bound), else unknown |
| `tickets.*` | `created` / `closed` entries in ticket logs |
| `quality.*` | `refs/notes/review` for the PRs of tickets closed in the window; first pass means no REROLL or ESCALATE |
| `main.after_merge_*` | `pass:` / `red:` lines of `idh/after-merge.log` for main commits in the window |
| `timing.gaze_*` | `duration:` lines of gaze answers in `refs/notes/review` |
| `timing.test_gate_median_s` | the `pytest-guard` check of after-merge records in `refs/notes/gate` |
| `timing.session_start_s` | always a gap: no store records it |
| `billed.openrouter.<KEY_ENV>.*` | OpenRouter `GET /api/v1/key`: the key's cumulative usage in USD; the window is the difference from the previous record |
| `billed.anthropic`, `billed.openai` | a gap unless an admin key is held: their cost endpoints refuse ordinary keys |
| `size.*`, `complexity.*` | file lines; functions and branch nodes from the stdlib `ast`; steps, table rows and cross-references per skill |

Billed cost is what the provider charged and nothing else: no token-count
estimate and no subscription usage. A cumulative figure that fell (key reset or
rotated) gives a gap for the window, never a negative bill. The checkup fetches
`origin/main` first; `window.main_fetched: false` means main figures may stop short. Local review notes are read as they are;
fetch `refs/notes/review` first if this clone has fallen behind.
