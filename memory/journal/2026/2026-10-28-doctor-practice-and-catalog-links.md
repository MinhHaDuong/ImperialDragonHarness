# 2026-10-28 — Doctor practice factored; catalog links (PRs #1881, #1885)

Session: Claude Code, claude-opus-5-5, host padme, background job e7e3e853.

- PR #1881 (author option A): `skills/harness-doctor/references/doctor-practice.md` holds an ethic layer for every doctor and a consultation layer for practitioners; trace-doctor accepted as the surveying doctor under the whole ethic (author's option A after gaze round 3). Four gaze rounds: round 1 found a journal duty added to trace-doctor, and as a consider that the edited test no longer pinned hypotheses before probes; checking that, the session found the merged consultation ordered examination before differential and fixed it; round 2 a consent rule stricter than both sources; round 3 three undeclared trace-doctor duties and a false memo claim; round 4 REVIEWED. Above-bar findings per round: 1, 3, 2, 0.
- Round 1's cross-family seat failed: gaze planned it through Pi, which has no OpenAI key on padme; later rounds used the codex door.
- First observed writer identity from the new profile line (#1880): the #1881 coder reported `worker: model=claude-sonnet-5-5`.
- PR #1885: each catalog command links to `skills/<dir>/SKILL.md` (author request); landing refused once with "gate record stale twice" while sibling sessions moved main; one rebase (tier unchanged) and retry landed it.
- trace-doctor gains `disable-model-invocation: true` (this bundle), matching "called, never self-started"; no skill or script invokes it.
