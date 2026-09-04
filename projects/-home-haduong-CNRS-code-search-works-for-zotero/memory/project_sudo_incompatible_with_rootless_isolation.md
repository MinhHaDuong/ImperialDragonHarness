---
name: project-sudo-incompatible-with-rootless-isolation
description: "sudo structurally cannot run inside podman unshare's rootless namespace, under strace/ptrace, or inside bwrap (no-new-privs) — an account-identity switch must wrap tracer+mechanism from the outside, never the reverse"
metadata: 
  node_type: memory
  type: project
  originSessionId: b5a31a66-a51d-4a0e-833f-c09839038053
  modified: 2026-09-04T07:13:03.108Z
---

Ticket 0637 (PR #334, 2026-09-04): the acceptance harness's account posture
(ticket 0625 — no target process runs as the operator, only as a dedicated
`tester` account via `sudo -n -u tester`) was composed *inside* the
`podman-unshare` network-isolation mechanism for one check (`R10-no-egress`).
`sudo` refuses there: inside a rootless user namespace the invoking user maps
to fake-root only within the namespace, so real host files `sudo` must trust
(`/etc/sudo.conf`, `/etc/sudoers`) appear owned by the overflow uid (65534)
from inside it, and `sudo` — correctly — refuses to trust that.

**Three separate refusal routes, not one**, discovered by testing each in
isolation:
- `podman unshare unshare -n -- sudo -n -u tester -- true` → `sudo: /etc/
  sudo.conf is owned by uid 65534, should be 0` (namespace uid remap).
- `strace -f -- sudo -n -u tester -- true` → `sudo: effective uid is not 0`,
  **with no namespace involved at all** — ptrace neutralises the setuid bit
  on its own.
- `bwrap` fails by a third route, `no-new-privs`.

**The fix**: the identity switch must be the outermost wrapper — around the
tracer AND the mechanism, not merely outside the mechanism. `sudo -n -u
tester -- podman unshare unshare -n -- true` works (verified: `tester` needs
its own subuid/subgid range, `/etc/subuid`/`/etc/subgid`, for rootless podman
to work as that account). This is mechanism-agnostic once composed
correctly, so it also covers `Bubblewrap`.

**How to apply**: any future harness/tooling work in this repo that combines
a process-isolation mechanism (network namespace, container, sandbox) with a
privilege-separation switch (`sudo -u <account>`) must put the identity
switch outermost, wrapping every other layer — never nested inside a
namespace or a tracer. If a `PostureUnavailable`/`sudo` refusal appears from
inside an isolation mechanism, check composition order before assuming a
sudoers misconfiguration — see [[project-acceptance-arena-permission-model]]
for the companion permission-model fix this same investigation needed.
