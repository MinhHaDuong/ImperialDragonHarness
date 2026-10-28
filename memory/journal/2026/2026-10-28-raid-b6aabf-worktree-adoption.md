# Raid b6aabf: hunt worktree adoption had two mechanisms (2026-10-28)

Context: raid b6aabf on the two open tickets, 1328 (hunt worktree path collides with its orchestrator's) and tracker 1309 (runtime.py live controls). Merged as PR #1934 (42e82bbb) and PR #1935 (0b489ec1).

Events:
- The Imagine seat for 1328 (sonnet) proposed only a path-suffix change, `$PPID` → `$PPID-$RANDOM`. The Blind-Spot seat (opus) pointed out that `git worktree add` refuses an existing path, so a path collision alone fails rather than adopts. It named a second route: hunt's "Owned already?" accepted a clean tree "handed by path", and a subagent's shell starts in the spawner's cwd.
- The executor's first test, which runs the SKILL.md recipe word for word in two bash children of one parent, failed on origin/main: the failed `worktree add` was not chained, so the following `worktree lock` locked the spawner's tree. The fix chains add, lock and echo with `&&`, redraws the suffix while the path exists, and limits "handed" to a path named in the brief. Gaze's cross-family redteam seat (openai/gpt-6.1-sol) reported clear; gate APPROVED round 1.
- Both coder briefs stated that their starting cwd was the orchestrator's session worktree, not theirs; neither coder touched it.
- `bash -c 'PPID=5'` fails: PPID is readonly, so the test shares PPID through two subprocesses of one parent instead.
- Both `raid_land.py --cleanup` runs exited 0, and the enclosing shell then reported exit 1: a trailing `pwd` in the removed worktree. The forge read-back showed MERGED for both.
- 1309: live controls ran on claude (in session), codex (`codex exec -s read-only`, codex-cli 0.165.0) and pi (local provider, tmux), each recorded in the 1309 log with what it does not prove. Codex `session headless` answers no under exec, so `can wake` YES there is a false positive. AccuracySec=1s: a 2 s Codex timer fired in 3 s (about 53 s late before). doudou was unreachable (no route to host), so its systemd >= 254 check is still open.

Outcome: 1328 closed. 1309 stays open: the desktop notify popup control needs the author; the doudou systemd check is pending.
