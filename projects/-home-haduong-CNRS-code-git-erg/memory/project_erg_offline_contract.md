---
name: erg offline contract
description: erg must work offline in isolated VMs — network resolution is opt-in, not default
type: project
originSessionId: d324ddfb-617b-4869-86a4-9040f910dc4c
---
erg's defining contract is that it works offline in isolated VMs.

**Why:** Users run erg in air-gapped or network-restricted environments; defaulting to network calls would break the core use case.

**How to apply:** Any feature that touches the network must be behind an explicit opt-in flag (e.g., `--resolve`). Offline behavior is the default and must never require a flag. Cross-repo refs that can't be resolved return `Unknown` — not an error.
