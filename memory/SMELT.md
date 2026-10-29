# SMELT — project memory consolidation prompt

Prompt revision: v8-r3 (2026-10-29)

This is the versioned consolidation prompt for this repository's project
memory. Every smelt report states this revision. Changing the prompt is a
reviewed change like any other: a new revision lands by PR, and reports name
the revision they ran. The workflow contract lives in the installed smelt
skill; this prompt is the per-project editorial layer.

## Read

1. `memory/MEMORY.md`, every `topics/` file it indexes, previous accepted
   reports in `memory/smelts/`, and the entries of `memory/journal/YYYY/` not
   yet covered by an accepted report. Skip `*review-attribution-*` files:
   attribution records are route-grid telemetry, not experiences; they live in
   `memory/evidence/attribution/`, and a project that has not moved its
   records yet still holds some in the journal.
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

## Job of a topic and caps

A topic is the as-built guide to one department of the project: what is true
now, in the present tense, each claim with its scope and a link to the journal
episode that supports it. It is a guide to the journal, not a replacement for
it. When a claim and its source episode disagree, the episode wins and the
claim is corrected or retired. A superseded claim leaves the page: the journal
and git keep the history; never annotate it in place, and never split a page
by date.

Page shape: current guidance, hazards, open questions, Retired (one line per
retired claim, naming the change that retired it), Sources (journal links), and
a fallback box for material that fits no department, emptied at each smelt.

Caps, in UTF-8 bytes (`scripts/memory_sizes.py` reports them):

- A page holds at most 4096 bytes, counting every section except `Retired` and
  `Sources`. Inline source links inside a claim count. Retired moves to history
  at the next smelt.
- The cap binds on history, never on conditions and exceptions.
- Pinned rulings in the Commission page (lines starting `> pinned`) count
  against the cap and are never cut to fit: smelt files, dates and links them,
  never paraphrases or retires them; only the author retires a ruling. An
  overflowing Commission page is reported as a sign that rules wait for the
  author to promote them.
- `memory/MEMORY.md` is capped separately (see Bounds).

Departments, provisional until ticket 1349 tests them on this repository: a
fixed core (Commission: the author's intent and rulings; Site practice: how
work lands here; Environment: hosts, services, external tools; History: the
journal, reports and git, never a page) plus the project's ouvrage departments
(tool or code: architecture and contracts, interfaces and compatibility,
release; analysis: data and provenance, methods, results; article: argument,
literature, venue; book: structure, voice, sources and rights; host:
services, hardware, access, monitoring). At most 8 pages per project.

## Consolidate

Apply to `memory/topics/` and `memory/MEMORY.md`:

- **Pruning:** remove outdated, irrelevant or superseded claims. Record the
  reason and the retained source references in the report; the journal episode
  stays.
- **Merging:** combine duplicate or overlapping entries into one accurate
  record, preserving source links, conditions, exceptions and unresolved
  contradictions. Quotations from manuscript sources keep their wording and
  locators; operational memory is condensed freely.
- **Refreshing:** update still-relevant context from current evidence; flag
  uncertainty when it cannot be verified.

Group related positive and negative outcomes; keep conditions, exceptions and
contradictions. A connection between episodes is not an established cause.
Present a hypothesis as such, distinct from a supported observation, and
distinguish canonical author decisions from hypotheses. A smelt may derive no
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
age ciphertext, from birth. Smelt uses the same pinned commands and the same
per-project key as capture — there is no second mechanism:

- key: `~/.config/keys/memory/<sha256(normalized origin URL)[:16]>.age`
  (scheme, user, default ports 22/443/80 and `.git` stripped, lowercased)
- recipient: `age-keygen -y <key>`
- decrypt: `age -d -i <key> <entry>.age`
- encrypt: `age -r <recipient> -o <entry>.age`

Without the key, skip `.age` entries, record the skipped count in the report
and never treat them as empty. With the key, decrypt in memory only —
plaintext is never written to the working tree — consolidate, then
re-encrypt: write the consolidated entry to a sibling temporary ciphertext
(`age -r <recipient> -o <entry>.age.new`) and only after success atomically
rename it over the original; sources preserved. `age -o` overwrites an
existing destination silently, so writing in place could destroy the
original mid-write — the temporary ciphertext is what keeps the contract
below.

Failure handling — stop and report; never leave plaintext or a partial
ciphertext in the tree:

- **authentication failure** (key missing, unreadable or wrong): treat the
  entry as unavailable — skip it, count it among the skipped, and name the
  error class in the report. Never guess content and never treat the entry
  as empty.
- **malformed ciphertext** (`age -d` fails): leave the `.age` file untouched
  and mark it unreadable in the report with its path and error class; never
  delete or overwrite it.
- **re-encryption failure** (`age -r` fails): remove the temporary
  ciphertext, keep the original `.age` entry in place untouched, and report
  the failure — that entry's consolidation is not done.

## Report

Write `memory/smelts/YYYY-MM-DD-<slug>.md` recording:

- Prompt revision, runtime and model.
- Sources examined with their git blob revisions (the ledger), the count of
  encrypted entries skipped, and unavailable sources.
- Editorial changes: what was pruned, merged or refreshed, with the reason
  and retained sources; corrections with the evidence that revised them.
- The bytes of each topic page against the cap.
- Unresolved questions and exposed contradictions.
- What the pass wrote, then a second pass over the same revision set: it
  imports nothing as new and re-examines each correction against its sources.

## Bounds

The journal is append-only: never rewrite, move or delete an entry; a
correction is a new entry linking the original. One carve-out: legacy
review-attribution records move once, by `git mv` with their bytes intact, to
`memory/evidence/attribution/`. `memory/MEMORY.md` stays at
most 40 lines, headings and blank lines counted, one line per department with
its most-used fact; check before committing.
Smelt writes only `memory/MEMORY.md`, `memory/topics/` and
`memory/smelts/` in this repository. It proposes no rule, edits no AGENTS.md
or runbook, opens no crystallisation issue and writes nothing into the
harness for another project. Commit on the smelt branch and submit a PR for
review; do not merge automatically. Only an accepted report counts as
completed processing for the runs that follow.
