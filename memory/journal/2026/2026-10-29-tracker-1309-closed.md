# Tracker 1309 (runtime.py) closed (2026-10-29)

Context: after raid b6aabf (PRs #1934, #1935) left 1309 open on the author-only notify popup and the doudou systemd check.

Events:
- The author ran `runtime.py notify --key test --title T --body B` on padme and confirmed the popup. The orchestrator then ran the Codex and Pi notify backends from a padme shell (`--runtime codex|pi notify`), both NOTIFIED, exit 0; the author confirmed both popups. Alert files land in `.git/idh-alerts/` (an `ls` of `.git/idh/alerts` first listed nothing: wrong directory, found via `scripts/runtime_notify.py` alert_dir).
- `erg log` inserted a line above the exit criteria, so a `sed '104s/…/'` written from a line number read before the log edited nothing; the printed line showed the miss, and a text-matching edit followed in a second commit before merge (PR #1937, ea8f2684).
- doudou stayed unreachable (no route to host) on 2026-10-28 and 2026-10-29. The author stated it runs Ubuntu 24.04 LTS, whose systemd is 255 (>= 254 for `--expand-environment=no`); recorded as settled from the release, not a live read.
- PR #1938 (f804911b) closed 1309 with all three exit criteria ticked. Both PRs were ticket-only, bookkeeping tier, merged without review; attribution capture refused them (no review on notes).

Outcome: IDH open-ticket count 0.
