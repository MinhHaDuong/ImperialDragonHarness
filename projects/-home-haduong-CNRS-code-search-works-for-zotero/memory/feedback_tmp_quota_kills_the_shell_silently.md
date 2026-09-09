---
name: tmp-quota-kills-the-shell-silently
description: "On doudou /tmp is a user-quota'd tmpfs; when other sessions' arenas fill it, every Bash call returns exit 1 with no output while Read/Edit still work"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a690b729-abc6-4ef5-a712-f0be4683c51b
  modified: 2026-09-06T16:16:02.083Z
---

On doudou, `/tmp` is a `usrquota`'d tmpfs shared by every Claude session of uid 1001 (systemd 259 caps each user at 80 % at login). On 2026-09-06 it filled mid-session. The 1.9 GB of session arenas (`smoke*`, `matrix-hosted`) this session's agent measured were not the filler: the author's purge history names `/tmp/zoteus-wrong*` and `/tmp/zoteus-validation-*`, which the upstream vitest suite leaks one per test (ticket 0714, see [[crash-recovery-under-worktree-guard]]). A partial `du` of the directory you can see is not a culprit. The Bash tool then returned exit 1 with no output for every command, including `true`, because its command and output capture live under the session's `/tmp` directory. Read and Edit on the home filesystem kept working, and the agent transcripts under `/tmp/.../tasks/` are symlinks, so truncating them frees nothing.

**Why:** the failure is silent and looks like a broken shell or a hook crash; the discriminating probe is a tiny Write into the scratchpad, which fails with `EDQUOT`.

**How to apply:** when every Bash call dies with exit 1 and no output, Write a one-line file into the scratchpad first. On `EDQUOT`, do not debug hooks: ask the author to purge `/tmp/claude-1001/*` arenas that are not this session's, never delete another session's arena yourself. Commit worktree edits as soon as the shell returns, since they sat uncommitted on home through the outage and a reboot. Related: [[preserve-agent-output]].
