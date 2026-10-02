# Trial clone held earlier-session journal entries for the same events

Context: memory-v8 acceptance trial (ticket 0918), Claude Code session (Opus 5.5) in /tmp/mem0918/claude/clone, branch t0918-acceptance-trials at be1ea2fc, 2026-10-02. The trial steps were: invoke `skills/dream/read-index.py --help`, capture under slug memory-v8-smoke, run the relocated integration test, and report native instruction loading.

Observation: at the start of this session `git status` was reported clean, but `git status --short memory/` lists three untracked journal files: 2026-10-02-retired-read-index-invoked-in-trial.md, 2026-10-02-capture-slug-collision-refused.md and 2026-10-02-untracked-claude-md-contradicts-memory.md. They describe the same trial steps on the same commit. This session reproduced each of them: read-index.py missing (exit 2), the helper refusing memory-v8-smoke because the tracked 0923 entry exists (exit 1, nothing written), and an ignored, untracked CLAUDE.md loaded natively and contradicting the memory. The integration test passed (1 passed).

Consequence: this session found its own expected events already recorded. It made no duplicate entries for them, so its outputs are not independent of the earlier session's. A count of trial captures per session would read these files as shared.

Evidence: `git status --short memory/` and `git status --ignored` outputs, plus the three file contents, in the session transcript. The earlier files may have been left deliberately or by an incomplete reset; this session cannot tell which, or which session wrote them.
