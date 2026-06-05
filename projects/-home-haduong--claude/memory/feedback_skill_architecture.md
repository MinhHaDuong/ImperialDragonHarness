---
name: feedback_skill_architecture
description: "Skills must not call anthropic.Anthropic() directly — Claude Code has subscription auth, not a funded direct-API key"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b7a83bab-a233-4299-90c7-1ed937340f71
---

Skills are SKILL.md procedures that Claude executes inline. They must NOT be standalone Python scripts calling `anthropic.Anthropic()` directly.

**Why:** Claude Code uses subscription auth. A direct-API key (`ANTHROPIC_API_KEY`) may be present in the environment but may have zero credits — the script would silently fail in production. The correct pattern: SKILL.md for reasoning + pure I/O helper scripts (no Anthropic imports) for mechanical operations.

**How to apply:** When writing a skill that needs LLM reasoning, put the reasoning in SKILL.md steps that Claude executes inline. Delegate only file I/O, git operations, and JSON formatting to helper scripts. Test that no helper script contains `import anthropic` or `from anthropic`.

[[feedback_rogue_agent_pattern]]
