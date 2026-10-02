Ticket 0918 acceptance trial, step 3. Context: the trial prescribed
`python3 skills/dream/read-index.py --help` from the repository root as a
probe of the dream skill's index helper.

Observation: the invocation failed with exit code 2 — "python3: can't open
file '/tmp/mem0918/vibe/clone/skills/dream/read-index.py': [Errno 2] No such
file or directory". The skills/dream/ directory exists and holds only
SKILL.md; a repository-wide find at depth three found no read-index.py.
Git history and other branches were not searched, so whether the helper was
removed, renamed or never delivered is untested; this session cannot say.

Consequence: the trial step produced no --help output to report beyond the
failure itself. A separate untracked working-tree entry,
2026-10-02-skills-dream-read-index-not-found.md, records the same failure
from another session; both files are preserved under the append-only
convention.

Evidence: command output and exit code captured in this session on
2026-10-02, branch t0918-acceptance-trials at HEAD be1ea2fc.
