kind: review-attribution
pr: 1307 · merged 2026-10-09 · project: .agents
writer: runtime=claude-code · model=anthropic/claude-opus-5-5 · effort=high
reviewer: seat=compat-r1 · runtime=claude-code · model-state=runtime-masked · model-evidence=memory/journal/2026/2026-10-09-review-attribution-pr1307.md:12 · status: ran
  finding: verifiable · skills/aap-annonce/SKILL.md:8 · adopted: yes
  finding: verifiable · skills/aap-annonce/SKILL.md:69 · adopted: yes
  finding: verifiable · skills/aap-annonce/SKILL.md:73 · adopted: yes
  finding: verifiable · skills/aap-annonce/SKILL.md:26 · adopted: yes
  finding: consider · skills/aap-annonce/SKILL.md:30 · adopted: yes
  finding: consider · skills/aap-annonce/SKILL.md:3 · adopted: no

One code-reviewer subagent launched with the Agent tool's model alias "sonnet"; Claude Code does not report the resolved provider id to the caller, so the reviewer identity is runtime-masked. Anchors are lines of the reviewed pre-fix SKILL.md. Finding 6 (move to private skills dir) not adopted: that dir has no git history; public skills already cite ~/CNRS paths. Review trail: PR 1307 body.
