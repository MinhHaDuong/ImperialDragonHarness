---
name: supervised-runs-no-standing-guards
description: "Don't propose standing AST/adherence tests for failure modes that supervised runs already catch. Worker-pipeline guards yes; user-driven callsite guards no."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b1100c2e-2562-4422-9769-08c6f18e4d6b
---

When a celebrate-phase sweep finds a class of callsites vulnerable to the same failure mode as the just-fixed ticket, do NOT default to proposing a standing adherence test (AST scan, grep-ratchet) as a follow-up ticket.

**The decision rule is operational model, not code-shape:**
- Unattended/batch path (worker pool, scheduled raids) → guard infrastructure is justified.
- User-driven path (adapter smokes, pdf2md CLI tools, fusion experiments) → human kills the wedge; per-callsite fixes when convenient, no standing test.

**Why:** Filed ticket 0195 after raid 0183/0187/0191 proposing an AST-based adherence test for every `OpenAI()` constructor and every `client.*.create()` callsite missing `max_retries`/`timeout`. User pushback in one line: "Overengineering, the runs are supervised." The five flagged callsites (responses adapter, pdf2md, fusion) all run with a human in front of the terminal. The cost of a wedge is `Ctrl+C`, not lost throughput. Closed wontfix in PR #378.

**How to apply:** Before proposing a standing guard during a sweep, ask: is this code path ever invoked without a human watching? If no, the per-call fix-when-touched approach is sufficient. The worker-pipeline fix in PR #374 was justified because workers run in batches without supervision; the bypass callsites are different operational beasts.

Related: project rule against "Don't design for hypothetical future requirements" and "Three similar lines is better than a premature abstraction." Linked to [[raid_budget_recovery]] (another instance of over-instrumenting a recoverable failure mode).
