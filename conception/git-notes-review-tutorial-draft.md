# Carry a review between clones with Git notes

Draft for author review. Intended audience: a Git user evaluating the harness
workflow. The [technical companion](git-notes-review-technical-draft.md)
explains design choices and prior art. Neither draft has been published or
deposited.

A branch can travel to another Git host without carrying its forge's review
discussion. This harness stores the review records in notes and keeps the
examined commits under explicit refs. The following exercise demonstrates
that transport locally, with an author clone, a reviewer clone, and a bare
repository standing in for a host.

Every review report, `REVIEWED` answer, and `APPROVED` verdict created here is
**synthetic demonstration data**. No person or model reviews the sample, and
no actual merge gate runs. The exercise checks storage and retrieval.

## Run the complete example

Use a checkout of this harness, Python 3.10 or later, Git with `switch`,
`range-diff`, and `patch-id --verbatim`, and a writable temporary directory.
The example needs no Python packages, model credentials, or network service.
From the checkout root:

```bash
python3 scripts/notes_review_example.py --output /tmp/notes-review-result.json
python3 -m json.tool /tmp/notes-review-result.json
```

The output path is yours to choose. The script builds and removes its own
temporary repositories. It ignores inherited Git environment variables,
uses isolated system/global configuration and a disposable home, and allows
only local file transport. All helper operations name a disposable repository
with `-C`. The only operations aimed at the harness itself read its note refs
and helper source. Its result asserts that the sample notes changed while the
harness notes did not. A concurrent harness writer can invalidate that check;
investigate a mismatch before rerunning.

The committed [result](notes-review-example-evidence.json) identifies the
tested Git version and helper digest. IDs and timestamps vary between runs.
The `checks` object should contain successful boolean outcomes, `patch-id`
for the unchanged rebased diff, and `none` for the changed revision. A nonzero
exit means the example did not verify its contract.

## Read the commands in context

The executable script is the complete, self-contained recipe. The commands
below explain its stages; variables denote repositories and identifiers
created by the script, so these snippets are not a second copy-paste program.
Commands beginning with `git` are Git commands. `review_notes.py` and
`forge.py` belong to the harness and require this checkout. Git alone does
not supply `open`, `publish`, or `coverage` as review operations.

### Create a request

The example initializes a bare `origin.git`, commits a base and a feature
change in `author`, and pushes both branches. These are ordinary Git actions.
The harness then creates a native review:

```bash
python3 "$HARNESS/scripts/review_notes.py" -C "$AUTHOR" open \
  --branch feature --base-ref origin/main \
  --why 'DEMONSTRATION: review the value change' --intent 'synthetic example'
python3 "$HARNESS/scripts/review_notes.py" -C "$AUTHOR" show "$REVIEW_ID"
python3 "$HARNESS/scripts/review_notes.py" -C "$AUTHOR" publish "$REQUEST_ENTRY_ID"
```

`open` prints the review ID. `show` returns JSONL, including the request ID
and its pinned head. `publish` must return `retrievable`; merely finding a
local entry is insufficient. Notes and retained heads are separate refs from
the source branches.

### Retrieve it in another clone

The example clones the local bare remote after publication and confirms that
the default clone lacks the review ref. It then configures and reads it:

```bash
python3 "$HARNESS/scripts/review_notes.py" -C "$REVIEWER" setup
python3 "$HARNESS/scripts/review_notes.py" -C "$REVIEWER" refresh
python3 "$HARNESS/scripts/review_notes.py" -C "$REVIEWER" show "$REVIEW_ID"
git -C "$REVIEWER" rev-parse \
  "refs/review-heads/$REVIEW_ID/$REQUEST_ID"
```

Setup preserves branch fetching and adds review-specific fetch mappings.
Refresh fetches and integrates evidence without publishing. The retained head
must equal the head in the request. A real reviewer must inspect that code,
then record evidence tied to that request; a declared reach line alone proves
no inspection. The sample deliberately fabricates its reports instead.

### Append review evidence from both clones

The script appends a report in each clone before either report is published.
Both start from the same earlier note history, so their local histories
diverge. It publishes each, refreshes the author clone, and requires both
entry IDs to remain present. The helper merges line-delimited entries with
Git's `cat_sort_uniq` notes strategy and retries rejected pushes without force.
This resolves the storage collision; incompatible opinions remain separate
records for the review workflow to judge.

For asynchronous reports, the binding matters:

```bash
python3 "$HARNESS/scripts/review_notes.py" -C "$REVIEWER" add report \
  --review "$REVIEW_ID" --request "$REQUEST_ID" --head "$HEAD" \
  --json '{"run_id":"example-run","seat_id":"example-seat","status":"ran","text":"DEMONSTRATION ONLY"}'
```

The example also appends a labelled synthetic answer and verdict. It records
the verdict with `--remote local-only`, a nonexistent remote, to use local
mode without launching a detached background synchronization process. Normal
`publish` then transports the evidence to the disposable origin. This is a
demonstration technique, not a recipe for bypassing a real review or gate.

### Handle rebase and a changed revision

The example advances main in another file and rebases feature. The head
changes, but the feature diff's verbatim patch ID stays equal in this case:

```bash
python3 "$HARNESS/scripts/review_notes.py" -C "$AUTHOR" coverage \
  "$REVIEW_ID" "$REBASED_HEAD"
```

The asserted match is `patch-id`. The script then changes the feature again;
coverage for that new head must be `none`. Equal patch IDs do not prove that
the old review considered interactions with a new base. Re-run the project's
required candidate checks and obtain a fresh review when needed.

A changed revision stays in the same review but gets a new request:

```bash
python3 "$HARNESS/scripts/review_notes.py" -C "$AUTHOR" request \
  --review "$REVIEW_ID" --branch feature --base-ref origin/main \
  --why 'DEMONSTRATION: revised value' --intent 'needs a fresh review'
python3 "$HARNESS/scripts/review_notes.py" -C "$AUTHOR" publish "$NEW_REQUEST_ENTRY_ID"
python3 "$HARNESS/scripts/review_notes.py" -C "$REVIEWER" refresh
```

The script checks the new request's distinct identity and range-diff. Both old
and new retained-head refs must resolve in the reviewer clone. The new code
travels in its retained-head ref; this exercise does not force-update the
original feature branch on the remote. Updating that branch in a real project
is a separate action governed by its Git policy.

### Recover records and list local requests

The script exports the review, imports it into a fresh repository without a
remote, and checks record equality:

```bash
python3 "$HARNESS/scripts/review_notes.py" -C "$AUTHOR" export "$REVIEW_ID" > review.jsonl
python3 "$HARNESS/scripts/review_notes.py" -C "$RECOVERY" import review.jsonl
```

This recovers records only. Back up or fetch the retained code refs too.
Never run `git notes prune` on this harness's review ref: valid review anchors
need not exist as stored objects. The helper refuses its own prune operation.

The current `forge.py --forge none list --state all` adapter can list native
requests from local notes when run in that repository. It does not fetch.
Its `number` field is an opaque review ID, and PR-adopted reviews are excluded.
Explicit abandonment closes the named request; a later request reopens it.
Ancestry can establish merged state but supplies no landing date, so
`mergedAt` remains null. The dashboard still needs origin and origin/main;
this local listing does not make the whole dashboard remote-free.

## Before adopting it

The helper and the review policy are prerequisites. The remote must accept
the notes and retained-head refs, and its actual permissions need testing.
Notes transport does not provide a web forge, reviewer authentication, a CI
runner, or access control. The local example exercises none of those services.
Do not put secrets or private transcripts in published notes.

This approach has established predecessors. Git-appraise already documents
distributed review using JSON lines in Git notes and automatic note merging;
see its [README](https://github.com/google/git-appraise). Git documents the
underlying [notes](https://git-scm.com/docs/git-notes.html) and
[fetch](https://git-scm.com/docs/git-fetch.html) mechanisms. The technical
companion compares the implemented choices without claiming novelty.
