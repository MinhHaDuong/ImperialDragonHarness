# Review evidence carried by Git: an implemented harness workflow

Status: draft for author review, intended as a technical note for HAL. No
deposit is authorized or made. Author names, affiliations, final title, and
submission metadata remain for the author to approve. The companion
[practical draft](git-notes-review-tutorial-draft.md) teaches the workflow;
this note explains its design, evidence, and limits.

## Abstract

Code can move between Git hosts while the evidence supporting its review
remains attached to a forge. This note describes an implemented harness that
stores review requests, reports, and decisions in Git notes, with explicit
references retaining the examined commits. A stable review identity separates
the discussion from branch revisions. A helper manages note synchronization,
request binding, and retrieval checks. A disposable local example demonstrates
transport between clones, divergent writer histories, revision handling, and
record recovery. The example uses synthetic judgments and evaluates storage
behavior only. Git supplies objects and transport; the harness supplies the
review protocol. Neither alone establishes reviewer competence, authenticates
an approval, or provides a forge interface.

## Problem and scope

A review decision needs an identifiable proposal, the code examined, and the
evidence behind the decision. A branch name alone provides none of these
durably: branches move, rebases replace commits, and names can be reused.
Putting an approval in a forge comment also leaves a migration problem when
the repository changes host or a reviewer works without the forge.

The implemented solution is a Python helper,
[`scripts/review_notes.py`](../scripts/review_notes.py), integrated with the
harness's request, gaze, and merge-gate workflows. It uses ordinary Git remotes
that accept the required refs. The commissioned work documents this existing
implementation; it does not commission a separate Dyne executable. The git-erg
reassessment mentioned in ticket 1445 was not available in the assigned
repository and is not used as evidence here.

## Records and responsibility

A review has a stable `review_id`. A new proposal revision gets its own
`request_id`; a review run and reviewer seat have separate identifiers. Entries
also record a unique entry ID, timestamp, kind, author, publisher, and the
examined head and base. The publisher is the process recording the evidence;
it need not be the person or agent that produced it. Requested model names
must not be presented as observed identities.

The harness stores newline-delimited JSON in a note on a deterministic anchor
derived from the review ID. The note lives under `refs/notes/review`. The anchor
is an identifier, rather than a reviewed commit, so rebasing a branch does not
move the note. Blank separator lines are ignored. A request captures the
proposal and intent; later requests contain a range-diff. Reports preserve
findings and their seat/run identity, answers summarize review results, and
verdicts record the gate's decision. Other implemented entry kinds include
links, writer attribution, and explicit request abandonment.

`add --request` binds a late report to the request the reviewer actually
examined. A conflicting head is refused. Callers that omit the request select
the latest request, which is unsuitable for asynchronous work unless they have
verified that binding. A stored `REVIEWED` or `APPROVED` string is a claim;
the surrounding review and gate workflow must establish its warrant.

## Revisions, coverage, and retained code

Each request retains its head through
`refs/review-heads/<review_id>/<request_id>`. Notes alone would preserve the
head's name without guaranteeing the commit remains available after branch
deletion or rewriting. These refs make the examined code transportable too.
The helper never forces their updates, but a privileged remote writer can
still replace them. Their immutability is a convention checked by the harness,
not an access-control property of Git.

Coverage matches an identical head or an equal, nonempty verbatim patch ID of
the reviewed range. Verbatim mode distinguishes whitespace changes. A clean
rebase can carry coverage when that ID remains equal; changed context can
produce a conservative miss. An equal patch ID establishes a relationship
between diffs, not successful integration with the new base. Tests on the
actual merge candidate remain necessary. Empty ranges do not match through
patch ID. The gate has additional bounded rules for bookkeeping and reroll
fixes; its implementation, rather than a generic patch-equivalence claim,
determines whether a candidate is admitted.

## Transport and multiple writers

Git transports the refs requested by its refspecs. A normal clone of the
example's remote does not import the review notes. The helper's `setup` adds
fetch mappings for notes and retained heads while preserving ordinary branch
fetching. Notes are fetched into a tracking ref, then integrated with the local
review ref. Setup does not install a default notes push or a rewrite hook.
See the primary [Git fetch manual](https://git-scm.com/docs/git-fetch.html).

Within one clone, an exclusive file lock serializes note writes. Across clones,
the helper fetches, merges note histories, pushes without force, and retries a
bounded number of rejected pushes. Complete JSON entries occupy individual
lines; `cat_sort_uniq` merges their line sets. This preserves concurrent
append-only entries under the format's assumptions. It does not resolve
contradictory judgments. Conflicting gate rounds are a protocol problem that
the landing path refuses, even when Git has merged the bytes successfully.

`publish` explicitly verifies delivery: it refetches, compares the remote and
local notes tips, checks requested entry IDs, and verifies the associated
retained heads. It distinguishes local/unpublished, published, and retrievable
states. Background synchronization used by normal harness writers is only a
convenience; a started background process is no proof of publication.

## Recovery and integrity limits

The helper exports and imports JSONL records for relay or recovery. An export
does not contain the reviewed commit objects: preserve or fetch retained heads
as well. A fresh clone needs transport configuration before reading the
published evidence. With an unreadable remote, readers can report stale local
evidence; an unavailable store must not masquerade as an empty review list.

Synchronization compares remote history with the clone's previously seen
state. Rewritten history, missing entries, moved retained heads, and altered
content under an existing entry ID are distinct cases. This is useful local
tamper detection, not cryptographic authentication or protection against a
malicious first contact. Back up both note refs and retained heads, and keep
access control at the repository host. The harness does not enforce signed
approvals through this format.

Do not run `git notes prune` on this review ref. Git documents pruning notes
for unavailable objects; the harness intentionally uses anchors without stored
objects, so that operation can remove valid review records. The helper refuses
its own `prune` command. Git notes are an object annotation mechanism whose
merge and rewrite behavior is configurable, as described in the primary
[Git notes manual](https://git-scm.com/docs/git-notes.html).

## Relevant prior art

Git-appraise is direct prior art for distributed review through Git notes.
Its [project README](https://github.com/google/git-appraise#metadata) describes
JSON entries written one per line, automatic merging with `cat_sort_uniq`, and
separate refs for review requests, CI results, machine analyses, and human
comments. Requests annotate the first revision; updated requests are ordered
by timestamp. The harness reuses this broad design space while choosing a
single review ref, stable synthetic anchors, and separately retained heads.
This is a comparison of documented choices, not a claim that the harness
invented Git-native review or that git-appraise cannot handle revisions.

Gerrit's [NoteDb documentation](https://gerrit-review.googlesource.com/Documentation/note-db.html)
describes review metadata stored in Git, with revision refs and a per-change
metadata branch. It combines Git storage with Gerrit's server and change
model. Its documentation expressly qualifies auditability: metadata refs may
be rewritten. It is evidence that Git-backed review storage and explicit
revision retention precede this harness, while the operational system differs.

These primary sources were read for this draft. This bounded comparison is not
a systematic survey. The older local prior-art memo mixes inspected material,
search snippets, and unverified inferences; its absence claims and project
activity judgments are not adopted here.

## Reproducible evidence and remaining evaluation

Run [`notes_review_example.py`](../scripts/notes_review_example.py) as explained
in the companion tutorial. The committed
[evidence artifact](notes-review-example-evidence.json) records the Git version,
helper digest, commands, and checked outcomes. Its judgments are synthetic.
The demonstration constructs disposable local repositories with isolated Git
configuration and permits only file transport. It checks actual note changes
in the sample while comparing the harness's notes refs before and after.
That comparison can detect concurrent harness activity too; a mismatch requires
investigation rather than an attribution to the example alone.

The example demonstrates divergent appends merging without loss, an unchanged
diff retaining coverage after rebase, a revised diff losing coverage, both
request heads remaining readable in another clone, and JSONL record recovery.
It does not test a hosted remote's permissions, hostile simultaneous writers,
crash recovery at every protocol boundary, real reviewer behavior, or review
quality. Existing integration tests provide further targeted cases in
[`test_review_notes.py`](../tests/test_review_notes.py),
[`test_review_notes_gate.py`](../tests/test_review_notes_gate.py), and
[`test_notes_request_listing.py`](../tests/test_notes_request_listing.py).

## Operational boundary

The notes-backed `none` adapter can list native requests from a strict local
snapshot, with explicit abandonment and ancestry-based merged state. IDs are
opaque; PR-adopted reviews are excluded; listing does not fetch; ancestry does
not establish a merge timestamp. The full dashboard still requires origin and
origin/main. These commands are a local harness interface, not a standalone
forge. Git supplies no web discussion interface or CI runner, and the notes
format grants no access-control guarantee. A deployment needs an agreed review
policy, tested repository permissions, backups, and candidate validation.
