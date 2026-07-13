---
name: skill-invocation-flag-gates-mandates
description: A skill mandating Skill(X) fails at runtime if X's frontmatter has disable-model-invocation true — check the target's flag, no text check catches it
metadata:
  type: feedback
---

When a skill, rule, or agent prompt mandates a mechanical `Skill(X)`
invocation, the Skill tool refuses it if `skills/X/SKILL.md` frontmatter
has `disable-model-invocation: true`. The failure is runtime-only: greps,
adherence gates, and reviews all pass because the mandate text is correct.
Discovered in raid 0293 (2026-07-13): raid Phase 5's new `Skill(hunt)`
mandate was refused by hunt's own frontmatter; the execute agent fell back
to following the SKILL.md manually — exactly the paraphrase drift the
mandate was built to kill.

**Why:** the invocation flag and the mandate live in two different files;
nothing links them, so they drift independently.

**How to apply:** whenever adding or reviewing a `Skill(X)` mandate, read
X's frontmatter flag in the same pass, and pin the pair with a guard test
(pattern: `tests/test_raid_invokes_hunt.py::test_hunt_is_model_invocable`).
Related: [[feedback_fork_skills_bare_context]].
