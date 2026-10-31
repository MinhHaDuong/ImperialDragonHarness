# Skill case notes: design note and pilot ticket 1394 (2026-10-31)

Context: author's idea in an interactive session on padme (claude-opus-5-5):
per-skill notes of four dated cases (latest, usual, best, worst) in the
case-method shape, kept per project, delivered when the skill loads. Note
`conception/2026-10-31-skill-case-notes.md`, pilot ticket 1394 (child of 1346).
Merged as PR 2084 at 7fe6aa23.

Events:
- Skill shadowing checked against runtime documentation and rejected: Claude
  Code ranks personal (`~/.claude/skills`, where the harness is linked) over
  project skills; Codex lists same-named skills side by side; Pi keeps the
  first discovered with a warning, order undocumented and not verified locally.
- A Sonnet KISS review (same family) corrected the script location
  (`scripts/` via `idh-hook`, not `adapters/hooks/`, which does not exist) and
  cut sha256 re-delivery, the compaction reset and the slash trigger until a
  read-back shows the gap. Its proposal to drop Codex and Pi was not taken
  (author asked for portability); the pilot is staged instead.
- Gaze round 1 at dfdcf72c: REVIEWED with a cross-family seat (gpt-6-luna)
  and two consider notes. Applying them in 7fe6aa23 left the gaze answer stale:
  verify-gate refused admission (no round spent), gaze ran again (REVIEWED, one
  new consider note on `memory/smelts/`, left unapplied), then verify-gate
  APPROVED in round 1.
