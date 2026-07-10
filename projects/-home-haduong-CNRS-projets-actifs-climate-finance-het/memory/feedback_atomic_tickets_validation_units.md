---
name: feedback-atomic-tickets-validation-units
description: "Tickets must be atomic — one MOA validation unit per ticket/PR; any number in an instruction is contingent, the principle binds"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: abeb176f-22ca-461f-bb52-7bdffd08f43b
---

2026-07-08, R&R pipeline session. The author said "0172 est triphasique, je préfère trois tickets courts". I split 0172 into exactly three — then he had to intervene AGAIN for 0175 ("elle est multiple") because I had not generalised. His correction: the cardinality (three) was contingent on my message showing three phases; the instruction was the *principle* — atomic tickets.

**Why:** The author signs off work PR by PR (MOA receives each delivery). A ticket bundling several validation decisions produces an unvalidatable monolithic diff. Literal-minded execution of an example forces the author to repeat the rule for every new case — the opposite of maîtrise d'œuvre.

**How to apply:** When sizing tickets, ask: how many distinct author sign-offs does this work contain? One sign-off unit = one ticket = one PR. When the user states a preference with a number or example, extract the underlying rule and apply it to every subsequent structure without being re-asked. See [[user-moa-moe-contract]] and [[feedback_decide_dont_micromanage]].
