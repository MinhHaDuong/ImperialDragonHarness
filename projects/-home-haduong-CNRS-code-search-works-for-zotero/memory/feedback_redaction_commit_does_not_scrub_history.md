---
name: feedback-redaction-commit-does-not-scrub-history
description: a forward-fixing commit does not remove leaked content from git history -- its own diff re-exposes the original text
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e37b49a7-3ac7-49b2-883b-481b96af87f8
  modified: 2026-09-01T13:48:11.801Z
---

Editing a file to remove sensitive content and committing that edit does
**not** scrub the content from a pushed, public branch. `git show
<fix-commit>` still contains the original leaked text as removed (`-`)
diff lines -- visible to anyone browsing the PR's "Commits" or "Files
changed" tabs, or running `git log -p`. The fix commit is itself a leak.

**Why:** the author flagged that specific titles from his private Zotero
library had leaked into public repo content (SOTA review, a
`DECISIONS.md` ruling, ticket bodies -- ticket 0028, 2026-09-01). The
first response was to edit the current file content and commit that --
which felt like a fix and was not one. A direct check (`git show <sha> |
grep <leaked term>`) found 4 of 7 commits on the branch still carried the
titles, including the "redaction" commit itself. The only real fix was
`git reset --soft <merge-base>` to collapse history back to before the
leak, recommit clean from the already-corrected working tree, and
`git push --force-with-lease`.

**How to apply:** when asked to remove sensitive content that has already
been committed and pushed, don't stop at edit-and-commit-forward. Check
whether the content appears in any prior commit's diff across the whole
branch range back to its merge-base (`git show <sha> | grep -i <term>`
for each commit, or `git log -p -- <path> | grep`). If it does:
1. Redact the current working-tree content immediately regardless --
   this is safe, non-destructive, and stops further exposure on every
   subsequent push while a bigger decision is pending.
2. Rewriting history (force-push) is destructive on a pushed/public
   branch -- get the user's explicit go-ahead before doing it, per the
   standing git safety rules. Tag the pre-rewrite tip locally first
   (`git tag backup/<name> HEAD`, never pushed) as a cheap safety net.
3. After the rewrite, verify with the same grep against every new
   commit's diff *and* against the platform's own served diff (e.g.
   `gh api repos/.../pulls/N.diff`) before considering it closed --
   don't trust the local check alone.

See also [[feedback_verify_the_load_bearing_claim]] -- same shape: the
sentence that most needs verifying (did the fix commit actually remove
the content?) is the one that's easiest to assume rather than check.
