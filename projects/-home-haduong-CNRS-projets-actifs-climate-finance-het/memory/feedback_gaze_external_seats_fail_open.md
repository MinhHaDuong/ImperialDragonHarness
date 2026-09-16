---
name: feedback_gaze_external_seats_fail_open
description: "The /gaze external reviewer seats fail open and silently in this repo — two config causes, and the invocation that actually works"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 69fadc0c-d582-4ce1-adea-c507e9c40443
  modified: 2026-09-16
---

`/gaze` reports a full-tier panel while its two `cli-agent` seats never run. They
fail **open**, so the verdict is internal-only and nothing says so (PR #1195,
2026-07-27). Two independent causes, either one sufficient:

1. `~/.claude/skills/reviewers/panel.yml` pins `credential-env:
   OPENROUTER_API_KEY_IDH`, but this project's `.env` `KEYS=` line is
   default-deny and selects only `OPENROUTER_API_KEY_CLIMATEFINANCE`. The seats
   cannot authenticate here at all.
2. `reviewers.sh` resolves the repo to **its own** (`SCRIPT_DIR/../..` = the
   harness) unless `REVIEWERS_REPO` is set — note the name, `REPO_ROOT` as an
   env var does nothing. Even authenticated, the seat-runner then clones the
   harness repo and dies with "pathspec … does not match any file known to git"
   on a branch that exists only in the project.

What actually runs both seats, from the project worktree:

```bash
set -a && . ~/.config/keys/openrouter.env >/dev/null 2>&1 && set +a && \
  REVIEWERS_REPO="$PWD" ~/.claude/skills/reviewers/reviewers.sh request <PR> <branch>
```

**Why it stayed hidden**: `reviewers.sh harvest` prints nothing and exits 0 for
both "no findings" and "no seat ran". Same shape as the `gh pr list --json files`
trap in `tickets/AGENTS.md` — a check whose all-clear is indistinguishable from
its I-could-not-look is not a check. Before trusting an empty harvest, confirm a
seat ran (`/scratch/tmp/reviewers/<PR>/*.findings` present, `*.err` absent).

The `copilot` forge-bot seat is unaffected — it goes through the forge API, not
the clone — but it needs the same `REVIEWERS_REPO` fix to resolve the repo.

Seat quality when they do run, on that PR: frontier 0 findings, budget 2
verifiable + 2 consider, **all four refuted** against the tree. Treat their
`verifiable:` class as a hypothesis, not a defect — see
[[feedback_check_the_detector_first]].

**Provenance.** Written 2026-07-27 as `feedback_external_panel_inert` under the
project key `-home-haduong-Climate-finance`. The 2026-09-13 consolidation folded
that key into `-home-haduong-CNRS-projets-actifs-climate-finance-het`, where a
*different* note had since claimed the same slug — the reviewer-preference note
that [[feedback_external_panel_inert]] now holds. Two unrelated memories had
collided on one filename and the fold kept only the newer. Re-filed here under
its own slug on 2026-09-16 so the fold is a union, not a replacement.
