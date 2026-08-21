<!-- last-reviewed: 2026-08-21 -->
# systemd units — what PID 1 reads at boot lives on the root filesystem

Loaded when a systemd unit is deployed, or its deployment method changes.

## The defect class

systemd builds its initial transaction before `local-fs.target`. Any unit file
it must read at that moment has to be on a filesystem already mounted — in
practice, the root filesystem. A unit that lives anywhere else, or a symlink in
`/etc/systemd/system/` pointing anywhere else, is simply unreadable:

```
systemd[1]: backup-to-hetzner.timer: Failed to open
            /etc/systemd/system/backup-to-hetzner.timer: No such file or directory
```

The timer never starts. That alone would be a loud failure. What makes this a
class worth a rule is the second half: a later `daemon-reload` — run by an apt
hook, or by hand, long after the filesystem mounted — finds the unit and marks
it **loaded and enabled**. From then on `systemctl is-enabled` answers
`enabled` while nothing runs, at every boot, and the failure silences its own
alarm.

Cost, 2026-08-21 (padme): units deployed by symlink into a repo checked out
under the user's home, itself a separate btrfs subvolume. Seven timers dead
since June, including the nightly off-site backup — **72 days with no backup**,
discovered by accident during an unrelated pre-vacation review.

## The rules

- **Install unit files as real copies** into `/etc/systemd/system`. Never a
  symlink into a home directory, a data volume, or any separately-mounted
  subvolume. `install -m 0644` from the repo, by an idempotent script.
- **Purge the old symlinks, including the live ones in `*.target.wants/`.**
  That is the link systemd actually reads at boot; leaving one is enough to
  keep the defect while everything else looks fixed.
- **Scripts may stay symlinked.** They are read when the service runs, long
  after mount, so `git pull` can keep updating them. The distinction is the
  whole point: units are read by PID 1 at boot, payloads are not.
- **Pay the copy's price deliberately.** A copy no longer follows the repo, so
  the deployment check must compare *content* — repo versus installed — and
  alert on drift. Without that, this rule trades a boot failure for a silent
  staleness.
- **Derive the deployed set from the repo, never from a hand-written list.**
  A list in a README is how one script goes undeployed for two months while
  its unit fails at every firing.
- **`is-enabled` is not evidence.** To know whether the units were readable at
  boot, grep the boot journal:
  `journalctl -b | grep -c "Failed to open /etc/systemd/system"` must be 0.
  Seven timers showing `active` proves only that something started them — a
  manual `systemctl start` looks identical. The absence of the error line is
  what says PID 1 read them.
- **Verify by rebooting, while you can still reach a console.** No inspection
  of configuration substitutes for the event the fix is about.

## Related

`Persistent=true` makes systemd run every occurrence missed while a timer was
dead. Restoring a long-dead timer therefore fires its service immediately —
usually what you want, and a surprise if the service is a 90-minute backup.
Announce it rather than letting an operator launch a second copy by hand; see
the oneshot trap in [coding-bash.md](./coding-bash.md), which is how the
announcement itself first got the answer backwards.
