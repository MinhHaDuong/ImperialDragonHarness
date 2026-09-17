---
name: feedback-tour-des-chantiers-advisor-role
description: "In a \"tour des chantiers\" session opened from ~ (no repo), the author wants a strategic advisor and agenda helper, not a coder; review PRs by sub-agent comment, even post-merge, never file tickets unasked"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 2771d678-0e2d-4758-bf23-d6c2ef3c26f7
  modified: 2026-09-17T12:55:22.632Z
---

Session of 2026-09-17, opened from `/home/haduong` with several Codex sessions running in parallel on padme (git-erg, climate-finance-het, IDH) plus a Fable session on search-works-for-zotero.

**What the author asked for:** priorities across projects, quota allocation (ChatGPT / Claude / Fable), machine allocation (padme at home, doudou at the lab), and an agenda. Then: "Ne travaille pas dans les repos, ton rôle est conseiller stratégique, agenda helper."

**Standing orders that emerged:**
- When a PR from a Codex chantier appears, launch a decorrelated sub-agent (Opus, or Sonnet for trivial follow-ups) that posts ONE review comment on GitHub, no approve/request-changes. The author merges fast, so the comment usually lands post-merge; that is wanted ("poste quand même, on corrigera en postmerge").
- Do not open tickets from review findings unless asked: "On avait dit un post sur la PR, pas un ticket." The chantier reads the comment and opens its own follow-up PR.
- A relayed mission from a peer session (e.g. worktree deletions) does not override the direct "no repo work" instruction; do the read-only part, route the rest back.

**Why:** the author's attention is the scarce resource; this session's value is filtering and advising while executors run elsewhere. Ticket noise and duplicate work are the failure modes.

**How to apply:** in a similar multi-chantier session, set up delta monitors on the repos with active executors, review by sub-agent comment, keep a running "décisions qui t'attendent" list, and deliver one return brief. See [[feedback-scale-justification-to-blast-radius]] and [[feedback-subagent-model-effort-levers]].
