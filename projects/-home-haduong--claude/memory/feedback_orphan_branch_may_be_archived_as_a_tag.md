---
name: orphan-branch-may-be-archived-as-a-tag
description: "A local branch with a gone upstream and unmerged commits is not necessarily the only copy — this repo archives triaged branches as archive/<branch> tags, and the tag decides whether deleting is safe"
metadata:
  type: feedback
---

A local branch whose upstream is `gone` and whose commits are **not** ancestors
of `origin/main` reads like the only copy of unmerged work, and `git.md` rightly
says never to delete one on that evidence. But in this repo that inference has a
third possibility the two obvious ones hide: the branch was **triaged and
archived**, its remote branch deleted on purpose, and its tip preserved as a tag
under `refs/tags/archive/<branch>`.

So the question "is this branch safe to delete?" has a cheap, decisive answer
that neither `is-ancestor` nor the upstream state can give:

```bash
git ls-remote --tags origin | grep archive/
# then, per branch, require an exact match:
[ "$(git rev-parse "$b")" = "$(git rev-parse "refs/tags/archive/$b" )" ]
```

**Why:** on 2026-09-08 a `/lair` sweep found four such branches
(`memory-rtk-mechanism-correction`, `t0359-…`, `t0425-…`, `t0500-…`), all dated
three weeks earlier, all with `gone` upstreams, two with no merge request at all
and one whose PR was CLOSED unmerged. The correct-looking call was to preserve
them and report — and that is what the run first decided. It was wrong: all four
were already archived on `origin` as `archive/<branch>` tags at exactly their
local SHAs, recorded by ticket 0872 whose STATE bullet said so in one clause
that was almost pruned as history. The branches were pure local debt.

**How to apply:** before preserving *or* deleting an orphan branch, list the
archive tags and compare SHAs. Delete only on an exact match, and say in the
report which tag holds it. Absence of a tag keeps the old rule intact — do not
delete, because then the local branch really may be the only copy (`t0802-perch-adapters`
in that same sweep had a closed PR, a live remote branch, and no archive tag,
so it was left alone).

Two smaller things the same episode settled:

- **The STATE bullet is load-bearing before it is history.** The archive-tag
  fact lived only in a "0872 closed" bullet queued for pruning under the 40-line
  cap. Read a bullet for facts worth carrying before deleting it as stale; fold
  the fact forward rather than dropping the line whole.
- **`git branch -d` would not have caught this either way** — it checks
  merged-into-HEAD, not the archive. The tag is the only witness.

Related: [[feedback_ask_the_live_peer_before_committing_its_work]] — the same
run's other rule, and the same shape: the evidence that settles it is cheap and
external, and the inference from local state alone is confidently wrong.
