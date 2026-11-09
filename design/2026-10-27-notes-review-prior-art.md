# Prior art: git-native review storage (ticket 1277)
Legend: [R] read this session; [S] search snippet only; [I] inferred or from memory, unverified.

## 1. git-appraise (Google) - closest design
- Stores: review request, CI status, robot analyses, human comments. [R] https://github.com/google/git-appraise
- Refs: refs/notes/devtools/{reviews,ci,analyses,discuss}, one ref per kind. [R]
- (a) Fetch/push: own `git appraise pull|push [remote]`; pull auto-merges. [R] Plain git does not fetch them. [I]
- (b) Concurrency: each entry is one line of JSON, so notes merge with `cat_sort_uniq` (concat, sort, dedup). [R]
  Several requests on one commit: sorted by timestamp, last wins. [S]
- (c) Rebase: README is silent. [R] From memory, a review is keyed to the reviewed commit and a
  `rebase` subcommand re-issues the request on the new commit (no notes.rewriteRef). [I]
- (d) Identity: README says nothing on signing. [R] Optional GPG signing of requests may exist. [I]
- (e) Last push 2023-08-12, not archived, 32 open issues, Travis badge. [R, GitHub API]
  Dormant, not formally dead. Reason not documented. Inferred: Google internal use moved on; forge UIs won.

## 2. Gerrit refs/notes/review (reviewnotes plugin)
- Stores: one note per SUBMITTED change: submitter, time, review URL, label scores. [S]
  https://gerrit.googlesource.com/plugins/reviewnotes/+/master/src/main/resources/
- (a) Users must fetch the ref manually; clones do not include it. [S] https://opendev.org/opendev/gerrit/commit/0456fcf583c31423638d967cc2ba1994a5bc9cf7
- (b) Single writer (the server), so no race by construction. [I]
- (c) Written after submit, on the merged commit, so rebase is moot. [I]
- (d) Identity = Gerrit account; the note is an export, not the source of truth. [S]
- (e) Maintained as a plugin. Live review data is in NoteDb (refs/changes/*, refs/meta), not notes. [S]
  Lesson: Gerrit itself did not keep live review state in notes.

## 3. Radicle (COBs)  https://lwn.net/Articles/966869 [S]; https://radicle.xyz/2025/06/02/radicle-1.2.0 [S]
- Stores patches/issues as collaborative objects: CRDT-like, any node appends, merges without conflict. [S]
- Refs: refs/patches for pushing; COBs under refs/cobs/* [I]. Per-repo signed refs; seeds cannot alter data. [S]
- (b) Solved by design: append-only DAG of signed ops, not a notes tree. (c) Revisions are explicit objects. [I]
- (d) Strong: signed by node key (DID). (e) Active (1.1 Dec 2024, 1.2 Jun 2025). [S]
- Cost: needs its own node/daemon and protocol; not plain git/ssh.

## 4. git-bug / git-dit
- git-bug: issues as git objects, push/pull to ordinary remotes. [S] Pushed today 2026-10-27, active. [R, API]
  Custom refs (refs/bugs/*, refs/identities/*) [I]; one commit chain per bug, merge = op-log union [I];
  identities are git objects with optional GPG [I]. Closest to Radicle's model without a network.
- git-dit: commit tree per issue under refs/dit/<hash>, leaf refs per reply. [S] https://hn.svelte.dev/item/13732598
  Bash proof of concept, 2017; Rust successor existed. [I] Status unverified.
- Key point: both put each entry in its own commit/ref, not in a shared notes tree. Appends cannot race.

## 5. git.git amlog (Junio)  [S] https://public-inbox.org/git/20140218052827.GA25291@sigill.intra.peff.net/
- refs/notes/amlog: commit -> Message-Id, written by a post-applypatch hook on one maintainer machine.
- (c) Doc says set `notes.rewriteRef=refs/notes/amlog` to survive amend/rebase; cherry-pick does not carry notes. [S]
- Junio called the reverse mapping an experiment that "did not work well". [S]
- Single writer again; published next to the maintainer's branches.

## 6. b4 / lore (kernel)  https://people.kernel.org/monsieuricon/introducing-b4-and-patch-attestation [S]
- Reviews live in email, not git. b4 am collects Reviewed-by/Acked-by trailers from the thread and writes them into commit messages. [S]
- Identity: trailer ignored if its name/email differs from the follow-up From header (-S overrides). [S]
- Experimental `b4 attest` signs patches. [S] Trailers rebase with the commit for free, notes do not.

## 7. Forges and notes
- GitHub stopped displaying notes in 2014. [R] https://tylercipriani.com/archives/2022/11/
- Forgejo displays and can edit notes; Gitea reads refs/notes/commits. [S, mirrored source]
- GitLab: request to show notes still open (issue 15029). [S] https://gitlab.com/gitlab-org/gitlab/-/issues/15029
- Cipriani article lists usability and forge-support drawbacks only, nothing on rewriteRef. [R]

## 8. Pitfall sources for fetch/push/rewrite
- Notes are not in default refspecs; the tree is versioned as a whole (Peff). [S] https://lkml.iu.edu/hypermail/linux/kernel/1210.2/04734.html
- A forced `+refs/notes/*` refspec can clobber; replacing the default refspec made pushes notes-only. [S] https://lore.kernel.org/git/ZM%2F9+YyOAbWWXQtC@nand.local/
- Jenkins JENKINS-23082: fresh workspace pushing a note hits a conflict; fix = fetch notes first. [S]
- wxWidgets: fetch before write; on rejected push, reset to remote and redo. [S]
- notes.rewriteRef takes a pattern (refs/notes/*) since Thomas Rast's series. [S]
- AI-agent tooling: git-memento (session transcripts in notes), Morph SDK (refs/notes/morph). [S] No tool found
  recording AI review verdicts in git. That is a null from three searches, not a proven absence.
- Not found / not searched: Fossil, git-series, GitHub ruleset behaviour on notes refs.

## Verdict
- Closest: git-appraise (same idea: notes keyed to commit, kinds as separate refs, requests+CI+discuss).
  Dormant since 2023, so copy the design, do not depend on the tool.
- Reuse: (1) one ref per kind (refs/notes/review/{request,plan,report,verdict}) not a single ref with `kind:`.
  A single ref makes every writer contend on one tip. (2) One JSON object per line plus `notes.mergeStrategy=cat_sort_uniq`
  (`git config notes.<ref>.mergeStrategy`): this answers the concurrent-append race in the notes tree,
  merge instead of reject. Add a unique id and timestamp per line so dedup is safe.
  (3) A wrapper command that does fetch-notes, append, merge, push-with-retry (appraise pull/push; Jenkins and wxWidgets say the same).
  (4) Last-timestamp-wins for a superseded request.
- Solved elsewhere: concurrency (appraise line format); fetch (own wrapper or explicit refspec set in clone setup);
  no-forge UI (Forgejo shows notes).
- Not solved by anyone found: rebase following. amlog says set rewriteRef; appraise is silent; Gerrit avoids it by writing post-merge.
  Safer pattern: key each entry by something that survives rebase (patch-id via `git patch-id`, or a Change-Id trailer, or branch+round)
  and keep the commit-attached note only as a hint. Orphaned notes: prune with `git notes prune`. [I]
- Identity/attestation: notes are unsigned. Only Radicle and git-bug give signed identity. Cheapest: sign the commit that updates the
  notes ref, or add an SSH-signature field per line. [I] Rulesets/protection of notes refs: nobody found; assume unprotected.
- Alternative worth pricing: git-bug-style one-commit-per-entry refs (refs/review/<id>/<n>) remove both the race and rewrite problem,
  at the cost of a bespoke layout and no `git log --notes` display.
