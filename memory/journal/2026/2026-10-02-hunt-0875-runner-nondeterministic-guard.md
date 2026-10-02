# Hunt 0875: runner-nondeterministic guard verdict and the supervised review that caught it (PR #1133)

A `/hunt 0875` (hermeticity guard blind to script-path spawns) ran detached
on 2026-10-02 with the supervising session owning review and merge. The
executor delivered the guard extension and ten suite reclassifications with
all local gates green, but its own review round posted PANEL-INTEGRITY:
DEGRADED — the executor runtime has no Agent tool, so no perspective could
run. The supervisor ran a proportionate battery instead: two internal seats
(correctness, scope+consistency), the external openrouter-frontier seat, and
Copilot.

The scope seat found the substantive blocker: CI pytest-guard was red on the
final commit and the PR did not say so. The suite-wide `export BASH_ENV=`
exemption fired for test_erg_pr_merge.sh locally under mawk, busybox awk and
gawk, but not on the GitHub runner — twice, same line numbers, on
blob-identical trees, with LC_ALL=C set by the guard and no local race in
twelve concurrent iterations. The root cause was the class, not a version:
awk built the \x01-delimited logical-lines stream and `grep -E` re-parsed it
(bracket classes over control bytes) to decide the exemption. The diagnostic
cycle printed the runner's tools (GNU Awk 5.2.1, grep 3.11, bash 5.2.21) and
the same code passed there on the same bytes — the verdict flipped across
runner allocations. The fix removed the second tool: the exemption is now
matched inside the same read loop that scans the file, one implementation
end to end.

Two findings converged independently between an internal seat and the
external openrouter-frontier seat: the unconditional quote-unwrapped scan
flagged inert quoted text (`echo "run bash /tmp/foo.sh for help"`) as a
non-hermetic spawn. Fixed with a gate regex requiring the interpreter as
code outside quotes, pinned by a red-first control (0p); judged spawn count
unchanged at 32.

Two residual facts worth remembering: the UNTERMINATED check in the same
guard still re-parses the awk stream with grep — same class, verdict-deciding,
filed as tickets/1015 — and the executor-without-Agent-tool pattern repeated
for the second time today, reinforcing what ticket 0853 (worktree/cwd
contracts for reviewer subagents) already tracks. CI now prints awk/grep/bash
versions in the pytest job permanently, and the guard's BAD line carries a
diagnostic (raw-export-line, stream-exempt-token, stream-lines, file-lines)
that would have named this failure class in one run instead of three.
