---
name: Verification contract — never rubber-stamp
description: When verifying PRs in the orchestrator Phase 6 or before any merge, run the full /verify loop. Never rubber-stamp. Cap at one retry round. Never merge from the verify skill itself.
type: feedback
originSessionId: 54d18314-1461-48f8-9048-cc2d7bc89989
---
For any PR verification before merge, invoke `/verify <pr-number>`. The skill runs:

1. `/verify-adherence` — mechanical-first (hygiene + IO-discipline + schema tests + grep ratchet), LLM only as fallback.
2. `/review` (built-in) + `/review-pr` or `/review-pr-prose` in parallel (read-only).
3. `/simplify` — applies must-fix findings as commits.
4. `/verify-gate` — anti-rubber-stamp gate.

Non-negotiables baked into the gate:

- **Evidence is concrete.** Commit SHA + file:line, test_id, or explicit rationale. "CI passes" / "simplify ran — no findings" / "tests pass" are NOT evidence.
- **Every ticket exit criterion gets ADDRESSED/MISSING + evidence.**
- **Every review comment is load-bearing** — commit changed the cited file, OR comment resolved with rationale, OR follow-up ticket opened.
- **Two rounds max** (round 1 initial, round 2 post-fix). Round 3 is forbidden → ESCALATE.
- **`/verify` never merges.** Merge is the author's call (interactive) or `/celebrate`'s call (autonomous).
- **`--force-approve` is a loud override**, logged on the PR. Use sparingly.

**Why:** The old orchestrator Phase 6 listed `/review` + `/review-pr` + `/simplify` inline — easy to skip steps, nothing forced evidence review. User flagged this during the 2026-04-17 session (Wave C PRs 689, 690 had skipped the `/review` step). The `/verify` skill family encodes the contract so Phase 6 can't cut corners.

**How to apply:**
- For any PR verification: `/verify <pr>` (not `/review-pr` alone).
- For a quick look: `/review` or `/review-pr` are still fine — `/verify` is full depth.
- The orchestrator's rewritten Phase 6 delegates to `/verify` per-ticket plus a separate wave-level integration subagent.

**Skill locations:** `~/.claude/skills/verify/SKILL.md`, `~/.claude/skills/verify-adherence/SKILL.md`, `~/.claude/skills/verify-gate/SKILL.md`. User-level, shipped with the ImperialDragonHarness repo, commit `e7e56b5` on `main`.

**Ratchet discipline:** `/verify-adherence` emits `suggested_test` entries for every semantic LLM finding. Next session, convert those into tests in `tests/test_hygiene_*.py` so the rule is mechanized permanently. LLM surface should shrink over time, not stay constant.
