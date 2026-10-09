kind: review-attribution
pr: 1290 · merged 2026-10-09 · project: .agents
writer: runtime=claude-code · model=anthropic/claude-sonnet-5-5 · effort=unrecorded
reviewer: seat=retro-1072-sonnet · runtime=claude-code · model=anthropic/claude-sonnet-5-5 · status: ran
  finding: verifiable · adapters/claude-code/hooks/hooks.json:43 · adopted: no
  finding: verifiable · tests/test_claude_code_adapter.py:92 · adopted: no
reviewer: seat=retro-1072-codex · runtime=codex-cli-0.161.0 · model=openai/gpt-6.1-sol · status: ran
  finding: verifiable · adapters/claude-code/hooks/hooks.json:43 · adopted: no
  finding: verifiable · tests/test_claude_code_adapter.py:92 · adopted: no
  finding: verifiable · scripts/validate-projections.py:70 · adopted: no

Reviewed base b3a50d61, head 39314d86, merge 51c21a28. Retroactive review under ticket 1072 (2026-10-09), shape of /review-pr plus /verify-gate, orchestrated by a Claude Code team lead. Launch lines: `sonnet | Anthropic | default | high | per-PR diff-vs-criteria review; same family as the writer, so replication only`; `codex gpt-6.1-sol | OpenAI | medium | high | other-family seat for independence on a Claude-produced diff; headless codex exec, read-only sandbox`. PANEL-INTEGRITY: OK (other-family seat ran). Writer model taken from the head commit's Co-Authored-By trailer; writer effort was not recorded. Severity floor: no finding blocks merge, corrupts state or bites the science; below-floor findings were fixed in small PRs or accepted. Anchor revision: the path:line anchors in the finding lines resolve on origin/main 9b280d56 (the checkout the reviewers read), not at the reviewed head named above; the reviewed revision is that head, its changes are read as the diff base..head.

Criteria (PR body; Ticket: none): hosts without rtk get no hook error MET with caveat; validator accepts guarded and bare forms MET; absent-rtk and stub-rtk tests MET; make-check figure not re-run. Stdin passthrough, rtk failure passthrough and non-executable rtk all clean. Dispositions: hooks.json:43 (guard needs sh on PATH; a PATH without sh exits 127 exactly as the bare form did, so no regression) ACCEPTED, the guarded form is protected by the Fixing rule and dropping sh -c is a design change for 1071; test_claude_code_adapter.py:92 (absence test supplies sh) ACCEPTED, follows from the former; validate-projections.py:70 (managed_hooks filter untested directly) ACCEPTED below floor, behaviour confirmed by reading.
