---
name: project-systemd-linked-vs-enabled
description: "systemd linked vs enabled: deploy order, disable-before-link trap, on-demand vs standalone classes"
metadata: 
  node_type: memory
  type: project
  originSessionId: 8f01c72d-011c-4307-9484-39dd71fff182
---

`systemctl is-enabled --quiet` exits 1 for `linked` state (direct symlink into `/etc/systemd/system/`), not just for `disabled`. In padme, all `.service` files are deployed as symlinks (`ln -sf repo/foo.service /etc/systemd/system/`), giving them `linked` state.

For timer-companion services, only the `.timer` needs `systemctl enable`. Calling `is-enabled` on the service itself produces a false negative.

Three service classes in `check_deploy_units` (check-system-daily.sh):
- **timer-companion**: timer enabled+active is sufficient; service only checked for `is-failed`
- **on-demand** (`_ON_DEMAND` allowlist, e.g. `llama-server`): only `is-failed` — legitimate idle spin-down
- **standalone**: both `is-enabled` and `is-active` required

## Deployment order trap (confirmed 2026-06-09, PR #56)

`systemctl disable` removes **all** symlinks to the unit — including manually created `ln -sf` ones, not just those created by `enable`. The wrong order is self-defeating: `ln -sf` creates the unit file, `disable` immediately deletes it.

**Correct deploy sequence for on-demand units:**
```bash
sudo systemctl disable llama-server 2>/dev/null || true   # clear stale .wants/ first
sudo ln -sf ~/padme/tools/llama-server.service /etc/systemd/system/llama-server.service
sudo systemctl daemon-reload
```

Never `enable` an on-demand unit: `enable` creates a `default.target.wants/` symlink that permanently wants the unit, which defeats `StopWhenUnneeded=yes`. Expected state: `systemctl is-enabled llama-server` → `linked`.

**Why:** Fixed PR #56 — install comment said `cp + enable`, causing the deploy sequence to destroy its own symlink. Confirmed empirically: user ran the old sequence, reported "done", `ls` showed the file absent.

**How to apply:** When writing or reviewing a service file's install comment, check (1) use `ln -sf` not `cp`, (2) `disable` before `ln -sf`, (3) never `enable` for on-demand units (`StopWhenUnneeded`).
