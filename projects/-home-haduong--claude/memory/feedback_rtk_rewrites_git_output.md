---
name: feedback_rtk_rewrites_git_output
description: rtk rewrites git diff/porcelain output (injects "--- Changes ---" lines); use `rtk proxy git ...` when parsing machine output
metadata:
  type: feedback
---

The rtk hook rewrites `git` output for token savings, including `git diff
--name-only`, `git diff`, and `git worktree list --porcelain`. It injects
decorative lines (e.g. `--- Changes ---`) and reformats porcelain into a pretty
form. This silently corrupts any downstream parse: `comm` on two
`git diff --name-only | sort` lists aborts with "l'entrée n'est pas dans l'ordre
trié", and `--porcelain` greps miss the real field prefixes.

**Why:** the rewrite is invisible until a parser chokes on the injected text —
you lose time blaming the pipeline, not the wrapper.

**How to apply:** when you need raw, machine-parseable git output, bypass the
hook with `rtk proxy git <subcommand> ...`. Reserve plain `git` for output you
read yourself. Bit repeatedly during the 2026-07-10 eight-PR merge session
(file-overlap `comm`, porcelain worktree parse). Related: [[feedback_gh_pr_edit_broken_use_rest]].
