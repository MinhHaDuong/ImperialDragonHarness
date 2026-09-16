---
name: project-secureboot-disabled-fwupd-mok
description: padme Secure Boot is currently DISABLED (since 2026-06-10); fwupd firmware updates can de-trust the nvidia DKMS MOK and kill the GUI on reboot
metadata: 
  node_type: memory
  type: project
  originSessionId: 75dc9c2e-00ba-4cc4-b484-87a420bb1486
---

As of 2026-06-10, **Secure Boot is disabled** on padme — a recovery workaround, not a chosen posture. Re-enabling it is tracked by ticket 0041 (re-enroll the nvidia MOK + re-enable Secure Boot).

The gotcha: a `fwupdmgr` system-firmware update (observed 1.107→1.108, BIOS `S07KT6BA`→`S07KT6CA`) left Secure Boot rejecting the nvidia kernel module (DKMS-signed with the Machine Owner Key) at the next reboot → **no GUI**. Root cause not isolated (hypothesis: the firmware update reset/invalidated the MOK or PK/KEK; unverified).

**Diagnosis shortcut for a future "no GUI after firmware/kernel update":** check `mokutil --sb-state` and whether `lsmod | grep nvidia` is empty. If Secure Boot is on and the module isn't loaded, it's the MOK trust path, not the driver.

**Re-enrollment trap:** the MOK Manager (blue enrollment screen) renders on the **boot GPU**, which is not necessarily the display GPU. On padme the display is pinned to the A4000 (bus `0x41`, `xorg.conf` PCI:65:0:0); the 3060 is at `0x61`. The 2026-06-10 re-enroll attempt failed because the monitor was cabled to the non-boot GPU — you can't see/drive the prompt. Move the cable to the boot GPU before re-enrolling.

See `intervention-log.txt` 2026-06-10 and `main-logbook.md` § BIOS. Related: [[project-nvidia-580-hold-posture]].
