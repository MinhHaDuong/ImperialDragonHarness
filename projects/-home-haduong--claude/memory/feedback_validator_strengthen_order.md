---
name: Repair before strengthening a validator
description: When adding a stricter rule after fixing the bug that violated it, sequence the repair commits BEFORE the rule commit so the validator does not block its own repair work
type: feedback
originSessionId: 90d5a236-5de6-4511-a1e4-6dd20af8996d
---
When strengthening a validator (or pre-commit hook, or schema check) after fixing the bug that produced violations: order the commits as (1) fix the producer, (2) repair existing violations, (3) add the rule. Reversing 2 and 3 makes the rule reject every commit that touches a still-violating ticket — including the repair commits themselves.

**Why:** advisor surfaced this exact pitfall on ticket 0060. I was about to commit the validator extension and the repairs together; the validator would have rejected the repair commit because the still-corrupt sibling tickets in the working tree fail the new rule the moment it's compiled into the binary used by any pre-commit hook. Splitting into three commits (fix → repair → rule) keeps each step independently bisectable and avoids self-blocking.

**How to apply:** any time you propose to add a "must not contain X" rule and there are existing instances of X in the codebase, plan three commits in that order. Same shape applies to lint rules, type-check escalations, schema constraints, and pre-commit grep ratchets — anywhere the rule itself is enforced against the same tree it's added to.
