---
name: zotero-pending-removal-race
description: "Zotero deletes a freshly installed add-on if a removal of the same id was still pending — the cause of ticket 0727, witnessed in the host's own log 2026-09-14"
metadata: 
  node_type: memory
  type: reference
  originSessionId: f7d7cc4a-5b20-40a1-9710-3d81ce55aa58
  modified: 2026-09-15T05:12:42.422Z
---

Remove an add-on in Zotero's Plugins window and the removal is **queued**, not
performed: `uninstallAddon`'s `aForcePending` branch writes
`extensions/staged/<addon-id>/`, sets `pendingUninstall`, and calls
`bootstrap.shutdown(ADDON_UNINSTALL)`. Install a fresh copy of the same id
before restarting and the install fully succeeds — visible, active, `update`
then `startup` — and then the queued removal **finalises anyway**, through the
non-pending branch (`bootstrap.uninstall()` → `installer.uninstallAddon(id)`),
destroying the copy that just replaced it. It completes by add-on id without
rechecking that a newer install holds that id.

Measured on Zotero 10.0.2, four occurrences in one hour, three watched at 50 ms
from outside the process; the host's own `addons.manager` log shows
`bootstrap.uninstall` 1.53 s after the new copy's `startup`. No restart is
needed. The interval varies (1.5–4.7 s), the *order* does not.

**Workaround:** remove → **quit Zotero** → relaunch → install. Never remove and
install in one session. Checkable first:
`ls -l ~/.zotero/zotero/*/extensions/staged` — absent or empty is safe.

**Two traps this cost a fortnight of misdiagnosis.** The add-on's own
`shutdown()` *is* called, so "no death certificate exists" does not mean the
teardown was skipped — the certificate is gated on
`extensions.sdt-pack-sitter.debug`, and the removal clears the add-on's whole
preference branch, so the FIRST disappearance on a machine silences every later
one. And `extensions.logging.enabled` routes through a `Log.ConsoleAppender` to
the Browser Console, never to stderr: capturing Zotero's stdout from a terminal
yields nothing. Read it with `Services.console.getMessageArray()` from inside
the process instead.

Reported upstream 2026-09-14:
https://forums.zotero.org/discussion/133758/installing-a-plugin-while-its-removal-is-still-pending-deletes-the-new-copy

Evidence in the repo: `verification/incidents/0727-2026-09-14-*`, ticket 0727.
Not reproducible over the AddonManager API — `bench/sitter_pending_uninstall_arm.py`
drives the same sequence with the pending state confirmed present and the
add-on survives, which is what localises the fault to the Plugins window.
