---
name: feedback_rtk_rewrites_git_output
description: rtk rewrites the OUTER Bash-tool git command's diff/porcelain output (not a script's internal git calls); use `rtk proxy git` for machine output you parse yourself, and prefer exit-code/plumbing checks over porcelain parses in scripts
metadata:
  type: feedback
---

The rtk hook rewrites `git` output for token savings, including `git diff
--name-only`, `git diff`, and `git worktree list --porcelain`. It injects
decorative lines (e.g. `--- Changes ---`) and reformats porcelain into a pretty
form. This silently corrupts any downstream parse: `comm` on two
`git diff --name-only | sort` lists aborts with "l'entrée n'est pas dans l'ordre
trié", and `--porcelain` greps miss the real field prefixes.

Worse than a parse glitch: a wrapped **mutation can silently no-op**. A
`git push --force-with-lease` once printed a mangled line ending in `ok` yet
did not push — local and `origin/<branch>` stayed diverged, and CI kept
grading the old commit (2026-07-10). The "ok" is not proof the push happened.

**Why:** the rewrite is invisible until a parser chokes on the injected text —
you lose time blaming the pipeline, not the wrapper — and a garbled mutation
looks like success.

**How to apply:** when you need raw, machine-parseable git output OR a
mutation whose success you must trust, bypass the hook with
`rtk proxy git <subcommand> ...`. After any push, verify
`git rev-parse HEAD` == `git rev-parse origin/<branch>` before trusting it.
Reserve plain `git` for output you read yourself. Bit repeatedly during the
2026-07-10 merge sessions (file-overlap `comm`, porcelain worktree parse,
force-push no-op). Related: [[feedback_gh_pr_edit_broken_use_rest]].

**Hook surface — the rewrite fires on the OUTER Bash-tool command only, never
on a script's internal subprocess git calls** (rtk 0.34.3, verified with
`rtk hook check`, 2026-07-14). The PreToolUse hook reads the command text you
hand the Bash tool and rewrites that; a `git` call made *inside* a committed
script the tool merely launches is untouched, whatever its subcommand. So the
#584 incident premise — that rtk corrupted `erg-pr-merge`'s internal
`git ls-tree` — is empirically disproven, and that incident's root cause stays
unconfirmed. `ls-tree` and `rev-parse` are also absent from the rewrite table;
only `branch --show-current`, `diff`, and `worktree list --porcelain` are
confirmed targets. Diagnosis discipline caught a plausible-but-wrong causal
story a prior session had already written into ticket 0333.

**Design rule — prefer exit codes and plumbing over parsing porcelain in any
script whose git output a framing hook could reach.** A check that reads no
stdout is rewrite-proof by construction: `git cat-file -e HEAD:<path>`
(presence by exit code) over grepping `ls-tree`; `compgen -G '<glob>'` (a
filesystem read) over listing tree entries; `git symbolic-ref --quiet --short
HEAD || true` over `git branch --show-current`. Where a porcelain parse is
unavoidable, filter to known record keys and assert field arity (`NF == 2` on a
`branch` record) so an injected banner cannot satisfy a match. This is the 0333
fix (erg-pr-merge branch + existence guards, `sync-local-main.sh`,
`worktree-gc.sh`) and the durable takeaway even though the rtk exposure it was
chartered against turned out not to apply — it hardens against *any*
output-framing hook, present or future.
