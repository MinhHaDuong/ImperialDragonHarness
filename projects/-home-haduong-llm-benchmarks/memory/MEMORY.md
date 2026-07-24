# Project Memory — llm_benchmarks

## Machine: padme (Lenovo ThinkStation P620)
- CPU: AMD Ryzen Threadripper PRO 3945WX (12 cores)
- RAM: 128 Go DDR4 RDIMM
- GPU0: NVIDIA RTX A4000 16 Go (PCI 41:00.0) — power cap 140W, PCIe 4×16, sm_86
- GPU1: NVIDIA GeForce RTX 3060 12 Go (PCI 61:00.0) — power cap 170W, PCIe 4×16, sm_86
- Quadro RTX 4000 8 Go (PCI 42:00.0) — removed (confirmed 2026-05-12)
- Driver: 580.126.09 / CUDA 13.0
- Fan control: fan2go daemon (remplace nvfd) — GPU fans + 120mm boîtier
- ODD fan: Alphacool Apex Stealth Metal 120mm — rewired to Front Fan header (canal 3, PWM), intake bas-droite, zip-ties
- Front fan original: chaîné sur 3-pin pass-through du 120mm (12V permanent)
- SuperIO: Nuvoton NCT6686D-L at 0x2e:0xa20
- Thermal: Post-atelier GrosBill 2026-02-22: repasting CPU+3 GPUs, nettoyage ailettes, A4000 57°C max@140W (was 80°C@120W), CPU 72°C (was 79°C idle). Power caps restored to defaults

## GPU index mapping
- nvidia-smi GPU0 = A4000 (PCI 41:00.0)
- nvidia-smi GPU1 = RTX 3060 (PCI 61:00.0)
- NVML GPU0 = nvidia-smi GPU0 = A4000
- (Quadro RTX 4000 removed — old nvidia-settings ordering note no longer relevant)

## Key files
- Project docs: ~/nextcloud/CNRS/projets/actifs/padme/llm-models.md
- Intervention log: ~/nextcloud/CNRS/projets/actifs/padme/intervention-log.txt
- Thermal report: ~/llm_benchmarks/thermal/rapport-thermique-A4000.md
- fan2go config: /etc/fan2go/fan2go.yaml
- fan2go service: /etc/systemd/system/fan2go.service (enabled)
- fan2go binary: /usr/local/bin/fan2go v0.12.0
- fan2go db: /var/lib/fan2go/fan2go.db (calibration data, rm to recalibrate)
- nvfd: purgé (binaire, service, config supprimés 2026-02-23)

## Benchmark conventions
- Run with: cd src && uv run bench_tps.py
- Results in: benchmark_history.json (append-only)
- Thermal profiles: uv run bench_thermal.py
- Power limits now recorded in hardware.gpus[].power_limit_w and thermal[].power_limit_w
- Throttle display: 🔥 THERMAL (>90°C) vs ⚡ POWER_CAP (power limit hit)

## User preferences
- Language: French for conversation, mixed FR/EN for technical docs
- User is CNRS researcher, project PADME
- Prefers Mistral > European > others for model selection
- Located in Bagneux (92), near Paris
- Does NOT trust courier services (Tech Premium)
- Uses uv exclusively, no pip/venv

## NCT6686D PWM register map (2026-02-23)
- PWM READ registers: 0x160+channel (read-only feedback)
- PWM WRITE registers: 0xA28+channel (actual control!)
- FAN_CTRL_MODE: 0xA00 (bit per channel: 1=manual, 0=firmware)
- FAN_CFG_CTRL: 0xA01 (config sequence: write 0x80=request, 0x40=done)
- FANOUT_CFG: 0x1D0+channel (bit 0x80 = active)
- FANIN_CFG: 0x1C0+channel (bit 0x80 = active)
- Config sequence: write 0x80→0xA01, wait, set mode+PWM, write 0x40→0xA01

## NCT6686D channel mapping (confirmed 2026-02-23)
- Channel 3: Front fan / alim, PWM_WRITE=8, seul canal acceptant les écritures via 0xA2B
- Channel 6: DIMM FAN 2 (header #9), PWM_WRITE=255 (plein régime)
- Channels 0,2,4,5: actifs mais écritures rejetées (EC override)
- Channels 1,7: hidden (FANOUT inactive 0x20), écritures rejetées
- Tacho 120mm: NON connecté au SuperIO (test doigt confirmé)

## ODD_FAN control — DÉFINITIVEMENT RÉSOLU (2026-02-23)
- **Conclusion : le header ODD_FAN est un header "bête" — 12V sans signal PWM, fan 4-pin tourne à 100%**
- Toutes les pistes logicielles épuisées :
  1. NCT6686D PWM read (0x160+i) → aucun effet
  2. NCT6686D PWM write (0xA28+i, séquence config) → aucun effet
  3. NCT6686D canaux cachés (1, 7) → écritures rejetées
  4. Test tacho (freinage physique) → aucun fan SuperIO ne chute
  5. ACPI EC → absent (desktop, pas laptop)
  6. IPMI/BMC → absent
  7. WMI FanControlStepping → déjà à 1 (min), pas d'effet sur ODD_FAN
  8. ACPI fan methods → inexistantes
- WMI BIOS: FanControlStepping=1, QuadM2PCIeCardFanControl=Low Speed (via think_lmi)
- **Solution finale : rewiring 120mm sur front fan header** (canal 3, PWM contrôlable, 0 €)
- Aquacomputer QUADRO — commande annulée (rewiring + fan2go suffisent)
- Modules debug: /scratch/tmp/nct_dump/ (nct_pwm_v2) — survivent aux reboots
- nct6686d DKMS: /usr/src/nct6686d-1/ (AUTOINSTALL=yes, survit aux reboots+kernel updates)
- Module name: nct6686 (pas nct6686d!), nécessite force=1 pour customer ID 0x0511
- Chargement: sudo modprobe nct6686 force=1
- Auto-load configuré: /etc/modules-load.d/nct6686.conf + /etc/modprobe.d/nct6686.conf
- GRUB: acpi_enforce_resources=lax ajouté
- Docs Lenovo HMM: ~/nextcloud/CNRS/projets/actifs/padme/Lenovo Thinkstation P620 30E0/p620_hmm_en-*.pdf

## Known issues
- Nemotron-Orchestrator-8B ollama modelfile broken: no chat template, no stop tokens → verbose, benchmark not representative
- Nemotron-Nano-9B-v2: no official ollama quant, only broken community quants
- nvidia-settings 510 (Ubuntu package) incompatible with driver 580 for fan control writes
