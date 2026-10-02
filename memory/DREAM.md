# DREAM — project memory consolidation prompt

Prompt revision: v8-r1 (2026-10-02)

This is the versioned consolidation prompt for this repository's project
memory. Every dream report states this revision. Changing the prompt is a
reviewed change like any other: a new revision lands by PR, and reports name
the revision they ran. The workflow contract lives in the installed dream
skill; this prompt is the per-project editorial layer.

## Read

1. `memory/MEMORY.md`, every `topics/` file it indexes, previous accepted
   reports in `memory/dreams/`, and the entries of `memory/journal/YYYY/` not
   yet covered by an accepted report.
2. Applicable harness rules (AGENTS.md, rules/) as authority sources — read,
   never edited.
3. Native notes only as attributed sources when available; report an
   unavailable source as unknown, not empty. Preserve the audience-appropriate
   text of any native note actually used in the report or a versioned annex;
   a fingerprint alone is not a retrievable source.

A source revision (git blob) already examined by an accepted report is
processed: cite its revision, do not re-import its content as new. A changed
revision is re-examined. Record every examined source in the report ledger,
one line each:

- <path> blob <40-hex git blob id>

## Consolidate

Apply to `memory/topics/` and `memory/MEMORY.md`:

- **Pruning:** remove outdated, irrelevant or superseded claims. Record the
  reason and the retained source references in the report; the journal episode
  stays.
- **Merging:** combine duplicate or overlapping entries into one accurate
  record, preserving source links, conditions, exceptions and unresolved
  contradictions.
- **Refreshing:** update still-relevant context from current evidence; flag
  uncertainty when it cannot be verified.

Group related positive and negative outcomes; keep conditions, exceptions and
contradictions. A connection between episodes is not an established cause.
Present a hypothesis as such, distinct from a supported observation, and
distinguish canonical author decisions from hypotheses. A dream may derive no
lesson at all; it must not invent one.

## Coherence

Compare claims, scope, conditions and exceptions across every memory the
index references, and against the applicable harness rules. A memory cannot
override a rule. Correct or withdraw a conflicting consolidated claim only
where the evidence and the applicable authority are clear, and explain the
change in the report; otherwise expose the contradiction without presenting
either claim as settled advice. The factual episode stays in the journal even
when it relates a derogation.

## Encrypted entries (.age)

Material not cleared for the repository audience stays in this repository as
age ciphertext, from birth. Dream uses the same pinned commands and the same
per-project key as capture — there is no second mechanism:

- key: `~/.config/keys/memory/<sha256(normalized origin URL)[:16]>.age`
  (scheme, user, default ports 22/443/80 and `.git` stripped, lowercased)
- recipient: `age-keygen -y <key>`
- decrypt: `age -d -i <key> <entry>.age`
- encrypt: `age -r <recipient> -o <entry>.age`

Without the key, skip `.age` entries, record the skipped count in the report
and never treat them as empty. With the key, decrypt in memory only —
plaintext is never written to the working tree — consolidate, then
re-encrypt the consolidated entry; sources preserved.

Failure handling — stop and report; never leave plaintext or a partial
ciphertext in the tree:

- **authentication failure** (key missing, unreadable or wrong): treat the
  entry as unavailable — skip it, count it among the skipped, and name the
  error class in the report. Never guess content and never treat the entry
  as empty.
- **malformed ciphertext** (`age -d` fails): leave the `.age` file untouched
  and mark it unreadable in the report with its path and error class; never
  delete or overwrite it.
- **re-encryption failure** (`age -r` fails): abort the write, keep the
  original `.age` entry in place untouched, and report the failure — that
  entry's consolidation is not done.

## Report

Write `memory/dreams/YYYY-MM-DD-<slug>.md` recording:

- Prompt revision, runtime and model.
- Sources examined with their git blob revisions (the ledger), the count of
  encrypted entries skipped, and unavailable sources.
- Editorial changes: what was pruned, merged or refreshed, with the reason
  and retained sources; corrections with the evidence that revised them.
- Unresolved questions and exposed contradictions.
- What the pass wrote, then a second pass over the same revision set: it
  imports nothing as new and re-examines each correction against its sources.

## Bounds

The journal is append-only: never rewrite, move or delete an entry; a
correction is a new entry linking the original. `memory/MEMORY.md` stays at
most 100 lines, headings and blank lines counted; check before committing.
Dream writes only `memory/MEMORY.md`, `memory/topics/` and
`memory/dreams/` in this repository. It proposes no rule, edits no AGENTS.md
or runbook, opens no crystallisation issue and writes nothing into the
harness for another project. Commit on the dream branch and submit a PR for
review; do not merge automatically. Only an accepted report counts as
completed processing for the runs that follow.
