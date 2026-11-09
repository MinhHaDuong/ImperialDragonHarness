# Ticket 1277 transport trial (2026-10-27). [M]=measured, [I]=inferred
Hosts: padme (git 2.43, GitHub over https, narrow token via `gh auth git-credential`); doudou (git 2.53, GitHub over
ssh git@github.com with the author's own key, gh keyring login as MinhHaDuong: NOT a narrow token); plain ssh bare
remote = `git init --bare` on doudou, pushed from padme via ssh://doudou/... Refs used: refs/notes/idh-trial-1277,
branch idh-trial-1277. Both deleted at end; `git ls-remote` then shows only refs/notes/gate [M]. Temp clones removed.

## Case 1 publish + fetch: PASS
padme: `git notes --ref=R add -m ... HEAD; git push origin idh-trial-1277; git push origin R:R` [M].
doudou: plain `git clone` and plain `git fetch origin` -> 0 notes refs [M]; `git fetch origin idh-trial-1277` -> still 0 [M].
Needed: `git fetch origin '+refs/notes/idh-trial-1277:refs/notes/idh-trial-1277'` (or a configured refspec) [M].
Same on the bare ssh remote: default clone gives 0 notes [M].

## Case 2 append + fetch: PASS
doudou `git notes --ref=R append -m ... HEAD; git push origin R:R`; padme fetch shows both entries, blank-line separated [M].

## Case 3 concurrent append: PASS with a trap
Both append from base bb5a005b; second push: `! [rejected] (non-fast-forward)`, hint "remote contains work you do not have" [M].
- Recovery A (merge-gate pattern): `git fetch +R:R` (discard local ref), re-append the same text, push. Lossless, entries
  intact and ordered. Cost: the entry text must be regenerable by the caller [M, on GitHub and on bare ssh].
- Recovery B: fetch to a side ref, `git notes merge -s S refs/notes-remote/x`. Two appends to the SAME commit conflict
  (one note blob per commit). `-s cat_sort_uniq` sorted lines across entries and collapsed the duplicate line
  "n: 3-concurrent": entries destroyed, unusable for multi-line records [M]. `-s union` concatenates local+remote whole
  blobs, so the shared base text appeared twice (entries 1-4 duplicated, both on GitHub and bare ssh) [M]. No data lost,
  but not idempotent and noisy. Appends to DIFFERENT commits would merge cleanly [I, documented git behaviour, not run].
- Consequence [I]: with one note per commit, "append entry" is read-modify-write of one blob; fetch-and-reappend is the
  only safe merge. merge-gate's 2-attempt loop already does it, and 2 attempts can fail under 3+ writers.

## Case 4 rebase survival: carry only locally, per-host config
- (a) no config: rebase of 3 commits onto main~1 -> `error: no note found` on all 3 new SHAs [M].
- (b) `git config notes.rewriteRef refs/notes/idh-trial-1277`: rebase and `commit --amend` both carried the note to
  the new SHA [M]. Default notes.rewrite.rebase/amend = true; rewriteRef is the opt-in that is missing by default.
- (c) `git notes copy OLD NEW` after rebase (pairing old/new rev lists in order): works, prints "Overwriting" if present [M].
  Pairing relies on equal commit counts and order; a dropped/squashed commit breaks it [I].
- Second host after `push --force-with-lease` of the branch + push of the notes ref: plain push of rebased branch is
  rejected non-fast-forward [M]; doudou must fetch with `+` and `switch -C`, then sees notes on the NEW SHAs only if the
  rebasing host had carried/copied and pushed them (it did: 3/3) [M]. Notes on old SHAs stay as orphans: 14 entries in
  the ref, 3 reachable from the branch [M]. The rewriteRef setting is not fetched; each host and each rebaser needs it [M].
- Rebase done anywhere without config (web session, other clone) silently drops the link; the old SHA still carries the
  note, so re-attachment by copy is possible while old SHAs exist in someone's object store [I].

## Case 5 cleanup + recovery: PASS
Removed padme clone and doudou clone; fresh `--bare --filter=blob:none` clone: 0 notes refs [M]; after adding refspec
`+R:R` to remote.origin.fetch and a plain `git fetch`, ref present, 24 commits of notes history, first request entry
(padme, 'git notes add') readable via `git show`, notes on rebased SHAs readable [M]. Blobless clones fetch note blobs
on demand without trouble [M].

## Case 6 GitHub refusals: none observed
Ruleset main-traceability (id 25543707, active): target = default branch only, rules deletion + non_fast_forward,
no bypass actors; main-required-checks disabled [M, via API with the narrow token]. With the narrow token: create of
refs/notes/idh-trial-1277 OK, fast-forward pushes OK, forced non-ff update of the notes ref OK (`+ ... (forced update)`),
deletion of the notes ref and of the branch OK [M]. A ruleset on refs/notes/* would be new [I]. The bare ssh remote with
receive.denyNonFastForwards=true was only tested for an up-to-date push, not a rejected one [not measured].
doudou used the author's full ssh key, so its result does not show what a narrow token can do from doudou [caveat].

## Needed in every environment
1. fetch refspec `+refs/notes/review:refs/notes/review` (explicit, or `remote.origin.fetch` added); neither clone nor fetch brings notes.
2. push `refs/notes/review:refs/notes/review`; on rejection fetch with `+` and re-append, never merge strategies.
3. `notes.rewriteRef=refs/notes/review` in any clone that rebases or amends, else copy explicitly after rebase.
4. Not run: ChatGPT Work, Claude Code Web (author legs); GitHub web UI shows nothing for notes [I].

## Does anything argue against one ref?
Measured: nothing refuses it; transport works on GitHub and plain ssh. Against: single-ref contention (one note blob per
commit, whole-ref fast-forward) makes concurrent writers retry; grows with orphans after rebase (11/14 here). Branch-backed
store (one file per entry, e.g. entries/<review_id>/<ts>-<host>.json on a dedicated branch) would make concurrent appends
conflict-free [I, not run], needs no rewriteRef, survives rebase (keyed by review_id, not SHA), and fetches with the
ordinary branch refspec; cost is a worktree/commit per write. One ref with fetch-and-reappend is adequate at 2-3 hosts.
