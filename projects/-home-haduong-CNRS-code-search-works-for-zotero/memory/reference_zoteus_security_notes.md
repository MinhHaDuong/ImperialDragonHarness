---
name: zoteus-security-notes
description: "Confidential zoteus security findings live at ~/.local/state/zoteus-security/, deliberately outside the git tree; the public repo carries only neutral requests"
metadata: 
  node_type: memory
  type: reference
  modified: 2026-09-08T07:53:53.271Z
  originSessionId: a0465653-bed4-450c-a2b2-a9fe384d1532
---

# Security findings live outside the repository

`~/.local/state/zoteus-security/` holds the confidential working record for
`oscardvs/zoteus` security work:

- `review-2026-09-07.md` — the findings as first recorded, plus a revalidation
  section appended 2026-09-08 at upstream `4467663`
- `advisory-draft-2026-09-08.md` — the six-finding report submitted through
  GitHub private vulnerability reporting as **GHSA-wm62-f2g5-j33x**

The placement is the point, and `GOVERNANCE.md` explains it: this repository is
public and the maintainer reads it, so nothing security-sensitive goes into
tickets, commits, issues, pull requests or logs. Public issue #66 asked only for
the private channel to be enabled and says in its own body that it carries no
vulnerability detail.

## The search lesson, which cost a day

When these notes were needed on 2026-09-08, two searches failed to find them: a
content grep over the whole project tree, and a delegated sweep across all 44
worktrees, both `fork/` checkouts, every Claude and Codex session store, and the
ChatGPT app storage. Both correctly inferred from `GOVERNANCE.md` that the
material would be kept out of anything git-visible, and both scoped that to
*untracked inside the repo*. The actual discipline is stronger — **outside the
project directory altogether** — so no filesystem walk rooted at the repo could
have found it. The author supplied the path in one line.

So: when a project's own governance says security material is kept out of the
tree, search `~/.local/state`, `~/.config` and `~/.cache` before concluding the
material does not exist, and ask the author early rather than after a full
sweep. A negative result from a search rooted in the wrong place is not a
finding.

## Handling

Both files carry a confidentiality header. Do not copy their content into this
repository, into ticket logs, or into any public forge artifact. The
non-security half of a mixed review goes public; the security half goes through
the private channel, and the two are written as separate documents so the split
cannot be lost by accident.

Related: [[reference_zotero]], [[feedback_repo_prepares_upstream_it_ships_nothing]].
