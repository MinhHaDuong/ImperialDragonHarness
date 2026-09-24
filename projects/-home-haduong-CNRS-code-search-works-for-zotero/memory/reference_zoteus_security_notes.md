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

## Observability of the advisory

The REST view of a repository security advisory does not expose its discussion: `GET .../security-advisories/<GHSA>/comments` returns `[]` even when comments exist (the 2026-09-15 follow-up is invisible to it), and `updated_at` does not move on a comment. Whether a comment was posted can only be read on the web page, in the author's browser. Status log for each round: `patches-<date>/STATUS.md` in the same directory; the 2026-09-23 round refreshed the patches against v1.21.0 (which fixed findings 2, 3, 5).

Related: [[reference_zotero]], [[feedback_repo_prepares_upstream_it_ships_nothing]].

## Patches and how to tell whether the maintainer received them (2026-09-17)

`patches-2026-09-13/` beside the two notes holds four `git format-patch`
files (findings 1, 4, 5, 6), a zip, and `DRAFT-COMMENT.md`, the cover comment
drafted for the advisory thread. On 2026-09-17 nothing showed it had been
posted or acted on: the advisory sat in `triage` with `updated_at` still at
the 2026-09-08 submission, no private fork, none of the four fixes in
upstream main at c386e83 (fly.toml still `ZOTEUS_METRICS_ENABLED = "true"`),
no GitHub notification and no mail about the advisory since the 8th, while
the maintainer answered every public item within 48 h.

The REST advisory endpoint does not expose comments, so "did he receive it"
cannot be settled from the CLI: open the advisory page in the browser. What
the CLI can settle is "did he act on it": grep the patched files at the
upstream tip for the patch's own marker strings.
