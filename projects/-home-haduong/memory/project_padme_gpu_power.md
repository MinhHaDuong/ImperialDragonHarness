---
name: project-padme-gpu-power
description: "padme idle power — RESOLVED. GPU 3060 floor 11W (no D3cold), CPU 70→46W via balanced profile. Both documented in main-logbook §I."
metadata: 
  node_type: memory
  type: project
  originSessionId: e33b0ca5-eb5e-4b14-8deb-d91331e0ca78
---

padme idle-power work, **resolved 2026-06-01**. Full durable docs now in `padme/main-logbook.md` §I (subsections "Affichage et alimentation GPU au repos" + "Profil d'alimentation CPU") and `intervention-log.txt` — commit `a54269d` on branch `add-power-logger`.

**GPU — 11W floor, irreducible.** 3060 (PCI `0000:61:00.0`, idx 1) idles 11W P8, clientless. Reverse-PRIME fixed: display pinned to A4000 via `xorg.conf` `BusID "PCI:65:0:0"` (=0x41) + `AutoAddGPU false`; persistence off. Sub-11W needs D3cold, **unavailable by design**: upstream PCIe port `0000:60:03.1` has no ACPI `_PR3`, and NVIDIA RTD3 is notebook/Intel-Coffeelake-only — P620 is desktop AMD WRX80, off-target. Only <11W levers: pull the card or suspend host.

**CPU — 70→46W, fixed.** `power-profiles-daemon` was in `performance`, pinning all 24 threads to ~4.29 GHz at load 0.1. A/B at the logger: performance ~70W, balanced ~46W, power-saver ~46W (no extra idle gain). Set **`balanced`** (`powerprofilesctl set balanced`, persisted in `/var/lib/power-profiles-daemon/state.ini`) — recovers ~24W idle, full turbo on demand under load. Residual ~45W = Threadripper Pro platform floor (IO die + 8-ch memory + Infinity Fabric).

**Lesson:** on this box both idle floors (GPU 11W, CPU ~45W) are architectural, not tunable; the only real wins were a stuck render GPU and a needlessly-aggressive CPU power profile. RAPL `energy_uj` is 0400 (CVE-2020-8694) → power measurement needs sudo; user runs `tools/padme-power.sh` via `!`.

Related: `[[project-padme-power-logger-pr]]` — the padme-power.sh measurement tool (PR #1).
