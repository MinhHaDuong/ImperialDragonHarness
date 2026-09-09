---
name: if-gated-hooks-get-unparsed-commands
description: "A PreToolUse hook's `if:` pattern in settings.json hands over any command it cannot decompose, so the hook must read the command itself"
metadata: 
  node_type: memory
  type: reference
  originSessionId: a8061a5d-7030-44c4-aea6-5357128dbb82
  modified: 2026-09-08T08:25:57.337Z
---

`settings.json` can gate a PreToolUse hook with a permission-rule pattern, e.g. `"if": "Bash(gh pr merge *)"`. That matcher decomposes a compound command to test each part. **A command it cannot decompose — command substitution, a heredoc, a `for` loop, a subshell — it hands to the hook anyway.**

Measured 2026-09-08 in a search-works-for-zotero worktree, on `block-pr-merge-in-worktree.sh`, whose header claimed the matcher filtered its input and which therefore did `cat > /dev/null` and decided on worktree-ness alone:

| Command | Reached the hook |
|---|---|
| `erg list tickets/` | no |
| `erg log 0029 "$(cat note.txt)" tickets/` | **yes** — refused, citing `gh pr merge` |
| `cat > f.py <<'EOF' … EOF` | **yes** |
| `cd repo && grep …; for f in …; do …; done` | **yes** |

**How to apply:** an `if:`-gated hook must parse `tool_input.command` from its stdin payload and decide on the content; the `if:` is a cheap pre-filter, never the filter. Keep an *unread* command fail-closed — "I could not look" is not "it is safe". And when a guard refuses something that plainly is not its business, suspect this before suspecting the guard's predicate: the message you get names the guard's *purpose*, not the reason it fired.

Fixed in ImperialDragonHarness PR #831, with the three test cases the file lacked — the five that existed all fed `echo '{}'`, an empty payload, on which a guard that reads the command and one that never looks score identically. Same family as [[probe-needs-discriminating-control]].

Second, separate obstacle in the same worktree, not fixed by that PR: `guard-worktree-identity.sh` refuses `erg`/`git` invocations wrapping a `$(...)` substitution, and refuses a bare `git status`/`log`/`diff`/`branch` because the rtk rewrite makes the launcher unreadable to it. Remedies it states itself: split into plain commands, drive from a script file, or append `| cat`. See [[git-in-a-worktree-session]].
