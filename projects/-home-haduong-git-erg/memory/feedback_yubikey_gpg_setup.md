---
name: feedback_yubikey_gpg_setup
description: YubiKey GPG setup on this machine — pitfalls and recovery steps
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e7eeb647-d784-4a4b-9d5f-ff6ad9de9118
---

Install `scdaemon` first (`sudo apt install scdaemon`) — GPG silently fails with "no SmartCard daemon" without it.

During `gpg --card-edit` → `generate`: answer **n** to off-card backup. Answering **o** (yes) triggers a passphrase prompt for the backup key; if cancelled, the key is partially written to the YubiKey but no local stub is created. Recovery: re-run `generate`, say **n** to backup, say **o** to replace existing keys.

Change both PINs before generating (default user `123456`, admin `12345678`). The user only changed the user PIN in ticket 0151 — admin PIN is still default.

Key on this machine: `4A46C91E03B83B23` (RSA-2048, YubiKey serial 36002329, expires 2028-05-29, UID `minh.ha-duong@cnrs.fr`).

**Why:** partial key write on first attempt caused confusion; the recovery path is non-obvious.
**How to apply:** if GPG card-edit generate fails mid-way, check card-status — keys may be on the hardware already. Re-run generate with replace=yes rather than starting over.
