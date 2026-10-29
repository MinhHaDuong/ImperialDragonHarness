# Hosts, shells and credentials

Scope: what was observed about the author's two machines (doudou, padme),
their shells, tool environments, permissions and credential handling while
working on this harness: the 2026-09-29 relocation session (imported on
2026-10-09) and 2026-10-09 to 2026-10-12. Standing guidance lives in
`rules/guards.md` (credentials), `rules/coding-python.md` (uv cache and link
mode) and the `infrastructure` skill. This topic records episodes only.

## Supported observations

Shells. On 2026-09-29, replacing a dotfile block "from the start marker to
EOF" worked on doudou and silently dropped three trailing lines on padme. The
lines were restored from a backup, and the loader gained an end marker (0987,
PR #1060). Under `ssh host bash -s < script`, a command that read stdin inside
the script swallowed the rest of it, and ssh exited 0 with no output;
`< /dev/null` fixed it. `grep` is a shell function routed to ripgrep, which
honours `.gitignore`, so a credential sweep missed two ignored transcripts that
`/usr/bin/grep -RlF` found. The bare `pytest` on PATH is a pipx install without
PyYAML; `python3 -m pytest`, which `make check` uses, passed. On 2026-10-09 a
review reported doudou as lacking several tools, but a non-login `ssh` PATH
omitted `~/.local/bin`. Doudou lacked only `age` and `act`.

uv and snapshots (2026-10-09). Padme exported `UV_LINK_MODE=copy` with its uv
cache in another btrfs subvolume, where hardlinks fail and reflinks succeed. It
was changed to `clone`, and doudou's cache moved beside the projects. Four
rebuilt venvs then showed about 5 MiB exclusive against 626 MB of copies.
`df` did not fall, which the entry attributes, unverified, to old snapshots.
The author added the uv cache and `.venv` directories to doudou's snapshot
exclusions; the `.venv` exclusion was not yet exercised on a real snapshot.
The harness adopted uv (`pyproject.toml`, `uv.lock`). The uv rule now in
`rules/coding-python.md` agrees with these measurements.

Permissions (2026-10-10, PR #1344). At the author's request,
`settings.shared.json` moved from 36 per-tool allows to `Bash` plus a few named
tools, with no `deny` block. A drafted destructive-git deny list was dropped
after an audit found it would block commands the harness itself runs
(`branch -D`, `push --force-with-lease`, a clean-tree `reset --hard`) and that
`git -C` bypassed every pattern. Those pattern semantics were read from
documentation, not tested. `idh install` now unions permission lists without
propagating removals, and `idh check` reports no permission drift. Doudou's
live settings had registered the rtk hook twice, and the author had the hooks
block removed.

Credentials. On 2026-09-29 a classic token was found saved as an allow rule,
after an inline-token command had been approved with "don't ask again". Copies
also sat in editor history, a backup and transcripts, and all were redacted or
deleted after the token was confirmed revoked. A token check that put the value
on `curl`'s argv was readable by `ps`; `-H @-` from stdin avoids that. The
author rejected copying a runtime's credentials file into a disposable HOME.
On 2026-10-12 a tool output displayed an API key stored in a pi model config
on doudou, and the author was told to rotate it. That is an occurrence of what
`rules/guards.md` forbids, recorded as an episode; the key is not reproduced
here.

## Refresh: 2026-10-15 to 2026-10-29

Shells and PATH. `timeout 200 command grep …` exits 127 because `command` is a
builtin ([legacy import](../journal/2026/2026-10-09-import-2026-09-29-relocation-lessons.md)).
A French decimal comma broke a `bc`/`printf` timing wrapper
([1583](../journal/2026/2026-10-21-gc-liveness-scan-lazy-pr1583.md)).
`~/.local/bin` appeared three times on padme's PATH (an unconditional
`~/.bashrc:1` prepend, Ubuntu's `~/.profile`, the systemd user manager); the
classifier denied the agent's dotfile edit and the author applied it by hand
([dangling prune](../journal/2026/2026-10-27-dangling-prune-moves-to-install-pr1701.md)).
In the Bash tool `pkill` first resolves to a Claude Code shell function keyed on
`CLAUDE_PID`. The ticket 1216 `pgrep`/`pkill` PATH wrapper was found absent
until `idh install`, then retired as heavy-handed by the author; PR #1914 instead
refuses `pgrep -f`/`pkill -f` without `-A` or a bracketed pattern in
`scripts/guard-destructive-bash.sh`, a hook all three runtimes run
([pgrep](../journal/2026/2026-10-28-pgrep-wrapper-retired-pr1914.md)). The
shell-init disk warning moved off stdout after it broke a test (PR 1967).

Skill links. On Claude Code 2.1.311 the skill header names a directory, not a
SKILL.md path, so a literal substitution into the helper seam gives the wrong
`IDH_ROOT`; whether the runtime changed or the contract was always loose is not
isolated ([IDH_ROOT](../journal/2026/2026-10-27-harness-doctor-idh-root-paragraph-1240.md)).
Pi 1.4.0 scans `~/.agents/skills`; the author removed the Pi skill projection
(PR 1690) and `idh install` retired 37 receipt-owned links
([Pi root](../journal/2026/2026-10-27-pi-skills-standard-root-pr1690.md)).
Dangling `~/.claude/skills` links on doudou were unlinked on request
([skills audit](../journal/2026/2026-10-20-raid-skills-audit-1128-1129-1130.md)).

Hosts and credentials. Padme's daily `claude-harness-pull.timer` failed on a
retired directory and was removed on the author's instruction
([1466](../journal/2026/2026-10-19-smart-testing-1466-wrap-up.md)). Doudou was
unreachable on 2026-10-20, 10-26, 10-28 and 10-29; on the last day the author
stated it runs Ubuntu 24.04 LTS (systemd 255), recorded from the release, not a
live read ([1309](../journal/2026/2026-10-29-tracker-1309-closed.md)). Agent
sessions use a fine-grained PAT under `GH_CONFIG_DIR=~/.config/gh-agent`; it was
regenerated with about one year's expiry, padme re-logged and verified, doudou
still on the old token at the time; `idh.mainGuard` was set to enforce on both
hosts on 2026-10-27 ([held tickets](../journal/2026/2026-10-27-session-close-held-tickets.md),
[forge-less raid](../journal/2026/2026-10-27-raid-forge-less-and-guard.md)). On
2026-10-23 the author authorized task-necessary transmissions to Claude, Codex
and OpenRouter; it is carried in session-start context, keeping local-only,
confidentiality and credential restrictions
([transmission](../journal/2026/2026-10-23-model-transmission-authorization.md)).
A mis-quoted ssh heredoc ran documentation lines as commands on doudou; a
follow-up scan found no side effect ([wave 0](../journal/2026/2026-10-27-raid-prep-wave0-and-1206-doudou.md)).

## Hypotheses, not facts

That snapshots pin the old venv copies is the entry's reading; no
subvolume listing confirmed it.

## Sources

- [2026-09-29 relocation lessons](../journal/2026/2026-10-09-import-2026-09-29-relocation-lessons.md) — imported from nine legacy native notes, blobs listed there.
- [Routing review round and host hygiene](../journal/2026/2026-10-09-routing-review-round-and-host-hygiene.md)
- [Permissions allow-all](../journal/2026/2026-10-10-permissions-allow-all-and-idh-install-sync.md)
- [Cycle 3, key displayed](../journal/2026/2026-10-12-t1048-cycle3-speed-stage-and-production-switch.md)
- Provenance: [source inventory](../../conception/memory-v8/source-inventory.md);
  revisions in [source-revisions.tsv](../../conception/memory-v8/source-revisions.tsv).
