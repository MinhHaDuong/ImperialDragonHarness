---
name: project-pending-reboot-kernel-635
description: "Kernel 6.17.0-35 installed 2026-06-06, reboot pending; post-reboot checklist and re-hold commands"
metadata: 
  node_type: memory
  type: project
  originSessionId: e0805b18-2519-4e53-8939-4f2db85f8a94
---

Kernel upgrade 6.17.0-29 → 6.17.0-35 (noble-security) installed on padme on
2026-06-06 via the manual procedure in `main-logbook.md` §I (snapper snapshot
`pre-upgrade-6.17.0-35` taken). **Reboot pending** — user will reboot later.
TTL: file a ticket or delete if not done by 2026-06-20.

**Post-reboot checklist:**
1. `uname -r` → expect `6.17.0-35-generic`
2. `nvidia-smi` → driver 580.159.04, both GPUs visible (RTX A4000 + RTX 3060)
3. `systemctl status fan2go` — came back cleanly
4. Re-hold the packages unheld for this upgrade:
   ```
   sudo apt-mark hold linux-generic-hwe-24.04 linux-headers-generic-hwe-24.04 \
     linux-image-generic-hwe-24.04 linux-modules-nvidia-580-generic-hwe-24.04
   ```
5. Only after all checks pass: `apt autoremove --dry-run` and review before any
   real autoremove (mid-transaction apt falsely listed the new -35 NVIDIA
   modules as removable).

**Do not touch:** CUDA-repo userland packages (`nvidia-modprobe`,
`nvidia-settings`, `nvidia-persistenced`, `libxnvctrl0/-dev`) stay held at 595
— the offered 610 is two branches ahead of the running 580 driver, no benefit.
The held-back 595→610 daily "updates could not be installed" nag is **accepted
as expected friction** (Option 1, decided 2026-06-08): the 26.04 LTS upgrade is
imminent and retires the whole 580-pin scheme, so uniform-580 downgrade churn
would be throwaway.

The post-reboot re-hold (step 4) is now tracked by **ticket 0019** (child of
tracker 0009); 0019 stays open until done on the host. Closing this reboot also
closes 0019.

Related: [[project-server-management]]
