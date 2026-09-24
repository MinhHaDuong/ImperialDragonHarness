---
name: feedback_exit_criteria_carry_author_intent
description: "An agent-written child ticket must state the author's acceptance in the author's words, not the mechanism; 0832 encoded \"downloadable\" where the author meant \"explorable\" and M1a was declared delivered without being reached"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b5a60d4e-2e95-41b2-bf5c-51ffa295522e
  modified: 2026-09-17T17:01:54.288Z
---

On 2026-09-17 ticket 0832 (written by the agent from tracker 0725) set M1a's
exit as "expose the four tables and their manifest as downloadable local MVP
data". It was delivered, reviewed twice, merged, closed, and STATE.md read
"M1a accepted on main". The author's idea of M1a was that the MVP lets one
explore the data. Nobody was wrong at execution: the specification did not
carry the intent, and the gate verified the specification.

**Why:** a mechanism ("download", "publish", "export") is what an agent can
verify; an outcome ("the author can follow a fact to its page") is what the
author accepts. A child ticket that names only the mechanism passes every gate
and misses the milestone.

**How to apply:** when writing a child ticket from a tracker, quote the
author's acceptance sentence verbatim in the exit criteria and add a concrete
acceptance script on a named case (here: South Africa and Viet Nam). If the
tracker has no such sentence, ask for it before splitting. Related:
[[feedback_changement_de_decision_reecrire_les_actions]],
[[project_jetp_three_stages_m1a]].
