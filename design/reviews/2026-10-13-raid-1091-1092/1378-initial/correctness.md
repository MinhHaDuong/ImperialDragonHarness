# Correctness — PR 1378

Reviewer: gpt-6.1-sol | OpenAI | low | ordinary risk. Same-family review, not independent.
Anchor: 7e1f77b1928ee49de97990940fd4b24b3df49cc7, base origin/main. The review-pr-anchor helper passed and listed the four assigned paths.

No correctness findings. Confidence: high for the implementation and contained controls.

Evidence: read the actual diff, full census implementation, ticket 1091 exit criteria, and tests. `_skill_index` uses Git index paths/modes rather than symlink appearance, checks that the requested root is the repository top, and handles unavailable Git/invalid metadata as unknown. A directly indexed card or directory symlink with mode 120000 remains budgeted; untracked directory cards and links enter skills-local. Unknown cards retain their full cost in skills. The supplemental channel participates in session_chars through the same totals dictionary; memory retains its maximum-index semantics. Both report modes enumerate all classified cards and display link presence and the supplemental subtotal. Existing consumers found by rg do not assume channel_chars has exactly CHANNELS keys.

Validation: using the existing primary virtualenv interpreter with PYTHONDONTWRITEBYTECODE=1 and pytest cache disabled, tests/test_resident_census.py passed: 8 passed in 3.27s. This covers clean absence, planted three links (+832), old combined-budget overflow, tracked directory links, untracked ordinary directories, unknown metadata, and full session-total inclusion. An initial ambient-interpreter collection failed because PyYAML was absent; the project environment resolved that environment issue.

Verification boundary: the caller reports full make check at this exact head in the clean checkout and the contained same-head checkout with the three live symlink targets (1606 passed, 4 skipped each), plus the old-code positive control (7784 versus 6952 at cap 7000) and read-only measurement of the actual primary (43994 session characters). These full-gate results are supplied evidence, not independently rerun by this seat. The literal actual-primary same-commit make-check criterion remains a post-merge check; the ticket explicitly identifies the authorized contained proxy and does not claim that actual-primary validation already occurred. The inherited 1092 annotation introduces no census behavior change.

Verdict: approve.
