---
name: feedback_path_scoped_rules_miss_bash_driven_work
description: "A rule scoped with `paths:` loads when a matching file is opened, so work done entirely through a CLI (erg new, erg log) never triggers it — keep the one-line essential resident and scope only the detail"
metadata:
  type: feedback
---

Restructuring climate's and search-works' project rules on 2026-09-24 (0971),
both restructures scoped the ticket rules to `tickets/**`: the ID-collision scan
in one, `erg log` stamping in the other. The independent review caught what both
authoring agents had half-noticed: tickets are filed and stamped with `erg`
through Bash, which opens no file under `tickets/`, so the rule meant for that
moment would never load in it.

**Why:** path scoping keys on the files a session reads or edits, not on the
paths named in a shell command. Any workflow driven by a CLI — erg, dvc, make
targets that write files the agent never opens — is invisible to it, and the
failure is silent: the rule simply is not there.

**How to apply:** before scoping a rule, ask how the work it governs is actually
performed. If a CLI performs it, keep a one-line resident essential (in
`AGENTS.md` or an unscoped rule) that names the rule file, and scope only the
detail and the incident history.
