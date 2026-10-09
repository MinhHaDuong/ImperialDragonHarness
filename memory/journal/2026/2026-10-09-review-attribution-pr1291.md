kind: review-attribution
pr: 1291 · merged 2026-10-09 · project: .agents
writer: runtime=claude-code · model=anthropic/claude-sonnet-5-5 · effort=unrecorded
reviewer: seat=retro-1072-sonnet · runtime=claude-code · model=anthropic/claude-sonnet-5-5 · status: ran
  finding: verifiable · .github/workflows/CI.yml:280 · adopted: yes
reviewer: seat=retro-1072-codex · runtime=codex-cli-0.161.0 · model=openai/gpt-6.1-sol · status: ran
  finding: verifiable · Makefile:4 · adopted: yes

Reviewed base 51c21a28, head ce3488f9, merge 488a4b9a. Retroactive review under ticket 1072 (2026-10-09), shape of /review-pr plus /verify-gate, orchestrated by a Claude Code team lead. Launch lines: `sonnet | Anthropic | default | high | per-PR diff-vs-criteria review; same family as the writer, so replication only`; `codex gpt-6.1-sol | OpenAI | medium | high | other-family seat for independence on a Claude-produced diff; headless codex exec, read-only sandbox`. PANEL-INTEGRITY: OK (other-family seat ran). Writer model taken from the head commit's Co-Authored-By trailer; writer effort was not recorded. Severity floor: no finding blocks merge, corrupts state or bites the science; below-floor findings were fixed in small PRs or accepted. Anchor revision: the path:line anchors in the finding lines resolve on origin/main 9b280d56 (the checkout the reviewers read), not at the reviewed head named above; the reviewed revision is that head, its changes are read as the diff base..head.

Criteria (PR body; Ticket: none): secretless CI MET; xdist probe after RUN MET; setup-uv v10.2.0 exact tag exists MET; requires-python >=3.11 matches tomllib use and 3.11 grammar parse MET; dev ranges unchanged MET; requirements-dev.txt references updated MET; test-count claim not re-run. Dispositions: CI.yml:280 (uv sync --frozen never checks lock freshness; reproduced) FIXED, PR #1301; Makefile:4 (comment claims CI sets VIRTUAL_ENV) FIXED, PR #1298. Notes accepted: setup-uv installs latest uv; xdist probe runs at parse time; stale VIRTUAL_ENV bypasses uv by design.
Guard note: the Makefile comment fix in #1298 carries no regression test; it is a comment with no behaviour to reintroduce (accepted).
