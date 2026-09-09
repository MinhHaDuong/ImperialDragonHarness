---
name: feedback_rtk_rewrites_git_output
description: rtk rewrites the OUTER Bash-tool command's output for a reader, not a parser — wrong counts, dropped merge commits, a silent no-op push; v0.45.0 skips piped/redirected output, one `git log` case stays open, and an agent session structurally cannot measure it
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

---

## Second generation of findings (2026-08-14 → 2026-09-09)

Consolidated here from the `rules/git.md` bullet that carried them, which had
grown to 866 words — 23% of a file resident in every session — for a rule that
does not depend on any of it. The operative rule stays in `git.md`: never read a
SHA, a count or a tip from a bare command; use plumbing that answers in exit
codes. The rest is here.

**Three silent wrong answers in one session (0.34.3), nothing errored:**
`wc -l < rows.jsonl` returned `0` on a three-line file; `git log --oneline -4
origin/main` omitted the merge commits and back-filled with older ones to honour
the count; `head -1 rows.jsonl | consumer` emitted `[3 more lines]` — a
truncation notice standing where the data should be — killing the consumer with
`JSONDecodeError … (char 3)`, since `[` opens valid JSON and `3 ` fails right
after.

**v0.45.0 fixed the plumbing, not the compaction.** The passthrough upstream had
been asked for (rtk-ai/rtk #1282, "piped **or redirected**"): the rewrite is
skipped when output goes down a pipe or into a file. Measured here — bare `ls`
comes back compacted, `ls | cat` and `ls > f` both come back raw. That guard
sits *above* the individual commands, which is why `src/cmds/system/read.rs`
carries no `IsTerminal` reference and needs none; grepping the command file for
the guard and concluding it is absent is a wrong inference (an upstream
commenter made and retracted exactly that one). All three symptoms above fed a
pipe or a redirect, and all three retired. This also supersedes the 0.34.3
target table above: the gate is the command's output form, not a per-subcommand
list.

**One case stays open.** A bare `git log` was still lossy on v0.45.0: over one
range, same session, bare against `rtk proxy`, **9 lines and zero merges versus
14 lines and 5 merges** — the difference being exactly the merges, and the
range's newest commit being a merge, so the bare output silently omitted **the
tip**. An earlier draft named `git.rs` injecting `--no-merges` as the cause; it
is not. On re-probe the difference reproduced only when another `git log`
preceded it in the same call, and vanished when the command ran alone. Two
sibling merge requests carried that invented cause, each green, and one landed
before the cross-check — the same diagnosis failure this note already records
for the #584 premise.

**Isolating it needs a channel an agent cannot use.** Capturing output through a
pipe or a redirect disarms the rewrite, and under an agent harness every
command's output is captured. So an agent session cannot observe the bare
behaviour it is trying to measure, and a probe run from one reports "no
difference" whether or not the defect is there: the all-clear indistinguishable
from "I could not look". Settling this takes a real terminal. A regression probe
must choose a range known to contain merges and assert the count — a
path-filtered range whose history happens to have none makes bare and proxy
agree and proves nothing.

**The gate is not a runtime tty test.** Under an agent harness `[ -t 1 ]` is
false for every command, including the ones that plainly do get rewritten. Read
the consequence carefully, because the plausible conclusion is wrong in both
directions: rtk is not globally disabled under an agent, and it is not
unobservable either. What is unavailable is the lazy probe. Compare a **bare**
command against `rtk proxy <cmd>`; that is how every finding here was
established.
