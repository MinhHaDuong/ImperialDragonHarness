# PR 1704 review evidence: runtime-masked seat identities

Round 0 (pre-gaze): one Claude Code Agent seat launched with the alias `sonnet`; the runtime returns no verbatim model id to the launcher.
Round 1 gaze result: https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1704#issuecomment-6436678981 (seats named by route alias only: opus, sonnet, haiku; verbatim ids not exposed).
Round 2 gaze result: https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1704#issuecomment-6437074779 (Claude seats by alias; red-team seat via the codex runtime default, id not exposed).
Round 3 gaze result: https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1704#issuecomment-6437428383 (same seat set and aliases as round 2).
Round 4 gaze result: https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1704#issuecomment-6437611608 (same seat set and aliases as round 2).
Round 5: gaze stopped by the author before a result; its correctness seat (alias opus) finished and reported to the session only; no comment posted.
