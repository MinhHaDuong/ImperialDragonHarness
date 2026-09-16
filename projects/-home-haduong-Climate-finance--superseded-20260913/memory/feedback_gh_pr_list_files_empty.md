---
name: feedback_gh_pr_list_files_empty
description: "gh pr list --json files returns nothing, so a ticket-ID collision scan built on it reports clean without ever looking"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 5389b1f5-6e6b-4500-b022-37ae6d8e29fd
  modified: 2026-07-27T19:03:43.936Z
---

`gh pr list --json files` does not populate the `files` field. A cross-PR
ticket-ID collision scan written as a single `gh pr list` + `jq` filter
therefore always returns empty — indistinguishable from "no collision found".

**Why:** on 2026-07-27 this scan reported ID 0384 free:

    gh pr list --state open --limit 100 --json number,files \
      --jq '.[] | select(.files[]?.path | test("tickets/0384")) | .number'

PR #1210 was open at that moment with `tickets/0384-archive-guard-completeness-gaps-from-the.erg`.
The filing PR merged, putting a second 0384 on main, and the collision had to
be undone with a renumber PR afterwards. The scan never looked at a single
file.

**How to apply:** enumerate, then query each PR — `files` is populated by
`gh pr view`:

    for n in $(gh pr list --state open --limit 50 --json number --jq '.[].number'); do
      gh pr view "$n" --json files --jq '.files[].path' | grep -q "tickets/$ID" \
        && echo "PR $n uses $ID"
    done

The generalizable rule: a check whose "all clear" and "I could not look" are the
same output is not a check. Before trusting a scan that returns nothing, run it
against a case you know is positive. Here, one `gh pr view` on any open PR would
have shown `files` populated and `gh pr list` empty for the same PR.

`tickets/AGENTS.md` already mandates re-running the seat check at the merge
gate, not only at allocation — the `/roar` hygiene step is what caught this,
by listing open PRs and showing two 0384 titles side by side. Do that check
with the loop above, at both moments.

**Never take the next free ID — jump clear of the frontier.** One filing
collided three times in one session: 0384 hit open PR #1210, the renumber to
0385 hit PR #1213, the renumber to 0386 hit PR #1216, each landing minutes
after mine and leaving `origin/main` failing `erg check` twice. It finally
settled at 0400, twelve clear of the frontier.

The next-free ID is the most contended seat in the repo: every parallel
session computes the same value and races for it, so a renumber is exactly as
collision-prone as the original allocation, and chasing the frontier cannot
converge while siblings are filing. Pick a number well above the high-water
mark instead — IDs are free, and a gap costs nothing.

Two corollaries. Re-run the scan *immediately before pushing* a renumber, not
only at allocation. And after any ticket PR merges, run `erg check` against
`origin/main`, not against the branch — a branch-local check passes by
construction and structurally cannot see a cross-PR duplicate. That gap is why
main went red twice before anything noticed.

Related: [[feedback_gh_projects_classic_error]] [[feedback_check_the_detector_first]]
