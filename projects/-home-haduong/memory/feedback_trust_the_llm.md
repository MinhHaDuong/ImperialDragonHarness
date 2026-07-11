---
name: Trust the LLM — skill authoring principle
description: Skills should only contain non-obvious constraints. Do not re-teach domain knowledge, specify step-by-step procedures the LLM can infer, or invent fake-precision thresholds.
type: feedback
---

Skills should only contain constraints the LLM cannot infer from the task description alone: policy decisions, output formats, safety invariants, organizational conventions, and things it would get wrong by default.

**Why:** Over-specified skills re-teach domain knowledge (how to parse biblatex, how to do research, what git commands to use), which risks contradicting or confusing the LLM. Arbitrary thresholds without measurement backing (e.g., "50% token overlap", "≤3 years old") are make-believe rules. Silence is better than contradicting or confusing instructions.

**How to apply:** When writing or reviewing a skill, ask: "Would the LLM get this wrong by default?" If no, delete the line. Keep: append-only invariants, output formats for tooling, escalation policy, organizational conventions (Zotero is canonical, biblatex not BibTeX). Cut: research methodology, git command flags, biblatex parsing instructions, academic writing style guidance.

Validated 2026-04-17: slimmed 5 skills from 916 to 325 lines (-65%) with user approval.
