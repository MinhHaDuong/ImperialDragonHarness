---
name: Persistent-state writes are opt-in
description: Cache, log, and journal writes default to off; user opts in explicitly. ARCHITECTURE.md §2.3 defaults to zero state.
type: feedback
originSessionId: bedc8f6c-19b5-4a8f-8ef3-63817b717c63
---
When MAIBA writes anything to disk that isn't the explicitly requested output RIS — caches, logs, run journals, sidecar files — the default must be off. Users opt in with a flag (`--cache`, `--log`, etc.).

**Why:** ARCHITECTURE.md §2.3 commits to "zero state by default — RIS in / RIS out, no DB, no cache." On-by-default writes quietly relax that contract for one-shot users who didn't ask for it. Author called this out on PR #21 (HTTP cache initially shipped on-by-default; flipped to opt-in via `--cache` before merge).

**How to apply:** When designing any feature that touches the filesystem outside the user-named output path, default the flag to `False`. Document the opt-in in `--help`. The dev-loop ergonomics argument (fast re-runs) is a one-character flag away; the principle of "don't write state without asking" is stronger than convenience.
