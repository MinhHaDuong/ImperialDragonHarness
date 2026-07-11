---
name: Compute on padme, not doudou
description: Heavy compute (ML inference, embedding generation) must run on padme via SSH, not locally on doudou
type: feedback
originSessionId: 791ae788-5308-4716-b2da-e0639978e7a9
---
Run ML-heavy tasks (sentence-transformers encoding, large data processing) on padme via SSH, not on the local machine (doudou).

**Why:** Local machine is too slow for batch encoding (5k works takes 2.75 min; 43k works ~23 min). Padme has better compute resources.

**How to apply:** When a script involves ML inference or large-scale data processing, SSH to padme and run there instead of running locally. Check padme status first with `ssh padme "hostname && nvidia-smi"` or similar.
