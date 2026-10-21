# Treatment convention (ticket 1170)

A closed ticket that fixes a friction class declares it in two body lines, at
line start, anywhere after `--- body ---`:

```
Treats: no_such_tool
Baseline: 2026-10-20=26 2026-10-21=14
```

- `Treats:` is one of the classes of `scripts/trace-friction.py`:
  `worktree_guard`, `no_such_tool`, `write_outside_worktree`, `other`.
- `Baseline:` lists `date=errors` pairs, the daily count of that class on the
  days before the merge, taken from the friction series (the traces expire, so
  the baseline is copied into the ticket). Use the days just before the merge.
  A zero baseline can never read `improved`: with errors afterwards the
  verdict is `worse`, with none it is `unchanged`. A ticket whose class was
  already quiet applied no treatment and declares no `Treats:` line.

The script `scripts/trace-treatments.py` reads these lines as declared fields
only; it never parses prose. The merge date is the date of the first-parent
commit on the `--ref` branch (default `origin/main`) that added or renamed the
ticket under `tickets/closed/`, read as its committer date; the first such
commit wins. The baseline of 1167 (2026-10-20, 2026-10-21) includes the merge
day itself, while the series after the merge starts the next day. Verdicts
compare mean errors per day of the class (baseline days against series days
strictly after the merge date): `improved` (after <= half of before), `worse`
(after >= 1.5x before), `unchanged`, `too_few_days` (fewer than 7 days after),
`unmeasured` (no baseline, merge date, known class, or series day after the
merge; never read as improved). Days without transcripts are absent, not zero.
The verdict is a before/after association, not proof of cause; the report only
proposes, it closes and reopens nothing.
