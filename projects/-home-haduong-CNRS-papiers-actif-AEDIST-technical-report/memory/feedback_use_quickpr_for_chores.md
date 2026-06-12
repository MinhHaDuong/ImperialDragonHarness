---
name: feedback-use-quickpr-for-chores
description: "For chore-only PRs (tickets/, docs/, .claude/, top-level docs, .github/workflows/, *.md) call scripts/quickpr.sh instead of the manual 7-command git+gh ceremony — saves ~2.5k tokens and ~15s per delivery"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ef36d227-f425-4d48-bbf5-0c3b86f02df9
---

For one-shot chore deliveries in this repo, **call `scripts/quickpr.sh "<message>" <files...>`** instead of the manual `git switch -c` / `git add` / `git commit` / `git push` / `gh pr create` / `gh pr merge --auto` sequence.

**Why:** The manual ceremony was ~5–7 Bash tool calls per chore (≈2.5k tokens, ≈15 s wall-clock). `quickpr.sh` collapses all of it to one tool call. It also restores the starting branch on exit, so it's safe to run from a worktree mid-ticket.

**Scope where quickpr fits:**
- `tickets/**` (open/close/edit)
- `docs/**`
- `.claude/**`
- `.github/workflows/**`
- Top-level `*.md` (README, AGENTS, STATE, CLAUDE, ADR, MASTERPLAN, PLAN)
- Other markdown notes

**Scope where it does NOT fit — keep using the proper skill:**
- Anything under `src/`, `tests/`, `experiments/` — the script refuses these paths by design. Implementation work needs `/start-ticket` → `/celebrate` so ticket bookkeeping happens.
- Multi-commit work or anything needing rebase / scope-overflow handling.
- Closing a ticket as part of an implementation PR — the proper celebrate flow does the ticket close commit AND integration review.

**How to apply:**
- One file: `scripts/quickpr.sh "docs: ingestion design" docs/ingestion-layer-design.md`
- Several files: `scripts/quickpr.sh "tickets: open 0380–0382" tickets/0380-*.erg tickets/0381-*.erg tickets/0382-*.erg`
- Output is the PR URL. The script returns immediately after `--auto` is set; merge fires when CI greens (~30 s for chore PRs because the chore path filter short-circuits the heavy steps).

**Note:** The script assumes default branch `main`, remote `origin`, authenticated `gh`. Fails loudly if any of those is missing.
