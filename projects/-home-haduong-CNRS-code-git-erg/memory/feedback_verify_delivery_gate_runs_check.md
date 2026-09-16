---
name: feedback_verify_delivery_gate_runs_check
description: "When a deliverable relies on an existing gate (CI, pre-commit hook) running a new check, verify the gate actually invokes it before claiming the exit criterion met"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 0c21a6fc-6aaa-49e2-a05f-b17a7267252d
---

When a ticket's deliverable is "promote check X so the existing gate catches
problem Y on path Z" (e.g. promote a warning to an error so CI/pre-commit
blocks it), do not infer that the gate runs the check — open the gate's config
and confirm it. Claiming the exit criterion met on an inferred invocation risks
shipping half the deliverable.

**Why:** raid 0241 (git-erg #298) chose hybrid option (1)+(3): (3) was realized
by making `erg check` error on closed-but-unarchived tickets, relying on "CI
runs erg check." That CI invocation was inferred from the Makefile, not read.
The advisor flagged it pre-merge: if no PR-triggered workflow actually ran
`make check`/`erg check tickets/`, only the local pre-commit path (option 1)
would be covered and the server-side/UI-merge escape — the whole point of
option 3 — would still be open. Reading `.github/workflows/CI.yml` confirmed it
runs `make test` + `make validate` (→ `erg check tickets/`), so coverage was
real — but the claim preceded the evidence.

**How to apply:** for any exit criterion of the form "gate G now catches Y,"
the verification step is `cat`/read G's actual config and find the line that
invokes the check. A green local `make check` does not prove the *server-side*
gate runs it. This is [[feedback_verify_premises_before_code]] applied to the
delivery mechanism rather than the premise — verify before claiming done, not
just before implementing.
