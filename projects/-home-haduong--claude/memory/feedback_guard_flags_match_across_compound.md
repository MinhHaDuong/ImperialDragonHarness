---
name: guard-flags-match-across-compound
description: guard-destructive-bash.sh blocks `git push && gh api … -f x=y` as a force push — the -f belongs to gh api; split the compound or use --field
metadata:
  type: feedback
---

`scripts/guard-destructive-bash.sh` blocked `git push && gh api -X PATCH -f
title=… -f body=…` with "BLOCKED: force push can destroy remote history"
(2026-07-28). No force push was present: the `-f` flags belonged to `gh api`
(shorthand for `--field`), but the guard pattern-matches `push` and `-f`
within the whole command string, not per-subcommand.

**Why:** a denied call means adjusting, not retrying verbatim — and the wrong
adjustment here (adding `--force-with-lease` to satisfy the guard's
suggestion) would turn a false positive into a real force push.

**How to apply:** when a compound mixes `git push` with another tool that
takes `-f`/`--force`-looking flags (`gh api -f`, `rm -f`, `curl -f`), split
into separate Bash calls, or use the long form (`--field`). Per
[[dont-codify-hard-rules]]'s sibling doctrine on guards (workflow § severity
floor): a misfire this cheap to route around is reported, not patched.
