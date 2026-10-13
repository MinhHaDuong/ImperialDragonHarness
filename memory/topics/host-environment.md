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

## Hypotheses, not facts

That snapshots pin the old venv copies is the entry's reading; no
subvolume listing confirmed it.

## Sources

- [2026-09-29 relocation lessons](../journal/2026/2026-10-09-import-2026-09-29-relocation-lessons.md) — imported from nine legacy native notes, blobs listed there.
- [Routing review round and host hygiene](../journal/2026/2026-10-09-routing-review-round-and-host-hygiene.md)
- [Permissions allow-all](../journal/2026/2026-10-10-permissions-allow-all-and-idh-install-sync.md)
- [Cycle 3, key displayed](../journal/2026/2026-10-12-t1048-cycle3-speed-stage-and-production-switch.md)
- Provenance: [source inventory](../../docs/memory-v8/source-inventory.md);
  revisions in [source-revisions.tsv](../../docs/memory-v8/source-revisions.tsv).
