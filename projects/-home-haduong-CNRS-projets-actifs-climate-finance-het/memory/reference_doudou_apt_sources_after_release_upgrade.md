---
name: reference_doudou_apt_sources_after_release_upgrade
description: "doudou's Ubuntu release upgrade (2026-05-11) silently disabled third-party apt sources (NetBird, GitHub CLI); stale NetBird 0.70.5 broke ssh padme and, probably, Firefox to GitHub Pages"
metadata:
  node_type: memory
  type: reference
  originSessionId: 93dc4598-7818-4bb8-b7ae-fc2584b8e87b
  modified: 2026-09-24T20:06:42.766Z
---

On 2026-05-11 doudou's Ubuntu release upgrade could not migrate two
third-party `.list` sources to deb822 and left them as
`/etc/apt/sources.list.d/*.list.disabled` with the `deb` line commented out:
NetBird and GitHub CLI. Both packages then froze without any warning.

Symptoms found 2026-09-24:
- `ssh padme` timed out on every route. padme's ufw allows 22/tcp only from
  100.64.0.0/10 (NetBird), so the LAN route is blocked by design. doudou's
  NetBird 0.70.5 showed padme "Connected, P2P" while passing no traffic, even
  ping, to padme's 0.79.0.
- Firefox on doudou timed out on every GitHub Pages site (pages.github.com
  included), while Chromium and curl -4 loaded them in under a second. Not DNS,
  DoH, IPv6, HTTP/3, a proxy, add-ons or ufw. It worked right after the NetBird
  upgrade: NetBird is the probable cause, not reproduced.

Fix applied: recreate the source as `<name>.sources` (deb822) with the
existing keyring, `apt update`, upgrade. GitHub CLI also needed its new
signing key: the 2022 key expired 2026-09-05; the new one is
`7F38 BBB5 9D06 4DBC B3D8 4D72 5612 B364 6231 3325`, taken from
cli.github.com/packages/githubcli-archive-keyring.gpg. On padme, Ubuntu Pro
ESM pins its own `gh` at 510, which beats GitHub's 500 regardless of version,
so `/etc/apt/preferences.d/github-cli` pins `gh` from cli.github.com at 600.

**How to apply:** when a machine-level tool misbehaves after a release
upgrade, check for `*.disabled` files in `/etc/apt/sources.list.d` and
compare the NetBird version on both peers first. The agent's /tmp is
private: files the author must run `sudo` on go under `~`. Related:
[[reference_machine_padme]], [[feedback_ssh_padme]].
