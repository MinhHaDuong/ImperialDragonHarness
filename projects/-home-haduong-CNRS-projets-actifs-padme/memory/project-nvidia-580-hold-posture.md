---
name: project-nvidia-580-hold-posture
description: Why padme pins NVIDIA 580 + the exact apt-mark hold set the quarterly baseline expects
metadata: 
  node_type: memory
  type: project
  originSessionId: 7418070e-b816-481b-927f-d8d3015cc954
---

padme stays on the **proprietary NVIDIA 580** driver (decided ticket 0019, 2026-06).
580 is the last branch with a proprietary driver; 590/595/610 ship only as
`nvidia-open`. Going to 610 is a flavor switch (proprietary→open) needing reboot +
CUDA/llama/unsloth revalidation, and all of 610's gains are display-side (HDR, Vulkan,
Wayland) — **zero benefit for a headless compute box**. The held 580.159.04 supports up
to CUDA 13.0; installed toolkit is 12.8 (llama-server links `/usr/local/cuda` at runtime,
so the system-CUDA axis has a live consumer — not a free bump).

**Settled hold set** (what `verify-system-baseline` `EXPECTED_HOLDS` checks, ticket 0034):
HWE kernel metas `linux-{generic,image-generic,headers-generic}-hwe-24.04`,
`nvidia-driver-580`, `nvidia-dkms-580`, and defensive `cuda` / `cuda-toolkit` /
`cuda-drivers`. NOT the bare non-HWE `linux-image-generic`/`linux-headers-generic` — 0019
dropped those; expecting them was a false-WARN bug fixed in 0034. Keep installing only
`cuda-toolkit-X-Y`, never bare `cuda`/`cuda-drivers` (the defensive holds block those
pulling the 610 driver).

The daily "N updates could not be installed" nag (held-back 595→610 userland) is **accepted
friction**, not a fault. The whole 580-pin scheme is **24.04-scoped — retire it at the
26.04 upgrade** (CUDA moves to the Ubuntu archive; proprietary 580 likely won't build on
kernel 7.0). Do NOT carry the holds across the LTS upgrade. See [[project_server_management]].
