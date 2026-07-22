---
name: feedback_secret_migration_is_credential_audit
description: "A secret-store migration is a credential audit — validate each secret end-to-end against its issuer (boolean-only, never printing it), never trusting inline metadata; a present-and-parses check is not a valid check."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a645ef77-f8e4-4301-bc40-961e61b43b5b
---

Centralizing or migrating credentials is a credential *audit*, not a copy job. Validate each secret against the service that issued it before declaring the migration done. Trusting inline metadata (a `.env` comment claiming an expiry date) hides dead credentials.

**Cost:** migrating the AEDIST repo to the least-privilege `KEYS=` loader (ticket 0679), the inline GitHub PAT was **dead** — `GH_TOKEN=… gh api user` returned HTTP 401 — despite a `.env` comment asserting expiry `2027-01-03`. The migration's end-to-end validity check surfaced it, and swapping to the valid central token fixed a latent broken-auth bug that had been masked because nothing exercised the token.

**How to apply:** when migrating/centralizing credentials, for each secret run a boolean end-to-end check against its own service (presence AND HTTP status, e.g. `gh api user`, a provider `/models` probe) and **never print the token** — compare values as booleans only. A "present and parses" check is not a valid check; only the issuer's `200` proves the credential works. See [[project_bash_env_secret_loading]] and [[reference_keys_config_dir]]. (AEDIST secret migration, PR #1166, 2026-07-14)
