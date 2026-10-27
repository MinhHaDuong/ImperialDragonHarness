# Doudou measurement (orchestrator, 2026-10-14, read-only over ssh)

Taken when doudou came back up after round 2. Commands: `df`, `du`, `ls`,
`findmnt`, and `probe2.py.txt` run unchanged with `python3 -I -` over ssh.

## Filesystems
- Booted 2026-10-13 11:29, so `/tmp` holds about one day of accumulation (derived).
- `/tmp`: tmpfs 12G, 1.7G used (15%), 1042 entries, mount options include `usrquota`.
- `/`: 234G, 87G used (40%).

## Largest entries
- `/tmp` (MB): `idh-1080-uv-cache` 230, `legacy-inventory` 191, `pytest-of-haduong` 145,
  `rv1378` 43, `t1091-old-control-*` 43, `compat-interfaces` 34, `t1091-primary-overlay-check` 31;
  40 `glossary-0882-*` directories at about 27 MB each (about 1.1G in all, derived: 40 × 27).
- `~/.cache` (MB): task temporaries `t2043-tmp` 1644 and `lair-tmp` 1258; tool and desktop caches
  `tracker3` 16877, an old Firefox expiry 3815, `codex-runtimes` 1754, `ms-playwright` 1265,
  `mozilla` 1114, `zotero` 838, `pre-commit` 598, `Codex` 366, `uv` 307.

## Attribution probe (7049 history files, 5683 MB)
| Candidate | Scanned | Hit files | Seconds | First hits |
|---|---|---|---|---|
| `~/.cache/t2043-tmp` | 1900 | 3 | 3.2 | JETP-observer t2043 worktree session `b3d5362d…` line 1675, its subagent, one Codex rollout of 2026-10-14 |
| `~/.cache/lair-tmp` | 1900 | 0 | 1.5 | MISS by absolute path; see below |
| `/tmp/idh-1080-uv-cache` | 114 | 17 | 0.1 | harness session `e1dc8d5c…`, Codex rollouts of 2026-10-14 |
| `/tmp/legacy-inventory` | 60 | 2 | 0.0 | JETP-observer t2043 session `b3d5362d…` line 2213 and a subagent |
| `/tmp/rv1378` | 277 | 6 | 0.2 | review-1378 worktree session `33c79cde…` line 58, Codex rollouts of 2026-10-13 |
| `/tmp/t1091-primary-overlay-check` | 277 | 17 | 0.1 | same review-1378 session line 38, Codex rollouts |
| `/tmp/does-not-exist-1095` (control) | n/a | n/a | n/a | MISSING, as expected |

`lair-tmp` miss explained: the history wrote the path with a tilde
(`mkdir -p ~/.cache/lair-tmp && TMPDIR=~/.cache/lair-tmp …`), and the probe searched only
the absolute path. A search for the path's spelling variants (`~`, `$HOME`, absolute) finds it
in 3 history files. Its contents include another `glossary-0882-*` directory: the project
test leak follows `TMPDIR` into `~/.cache`.

## Readings
- The STATE-line-31 mitigation (TMPDIR under `~/.cache`) protects the tmpfs quota but moves the
  leak to `~/.cache`, where no lifecycle removes it: 2.9G of task temporaries there today (derived: 1644 + 1258 MB).
- Attribution reached 5 of 6 real candidates by absolute path, 6 of 6 with spelling variants.
- Doudou's `/tmp` is not near its quota today; one day since boot is too short to say more.
