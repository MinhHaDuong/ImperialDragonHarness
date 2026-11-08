# Smelt — consolidation detail

The editorial layer every project used to copy into its own `memory/SMELT.md`
(earlier `DREAM.md`, `HOARD.md`). It is generic and lives here once (ticket
1451); a project keeps no prompt. Its local facts, such as where its rules,
native store or import annex live, are one or two lines in its
`memory/MEMORY.md` or in a `SOURCES.md` that index links. SKILL.md holds the
contract (the three functions, coherence, lanes, procedure, authority); this
file holds the operational detail it points to.

## Read

1. `memory/MEMORY.md`, every `topics/` file it indexes, previous accepted
   reports in `memory/smelts/`, and the entries of `memory/journal/YYYY/`:
   all of them are evidence for the rebuild; an accepted report is a ledger
   of what was examined, not a reason to skip an entry. Attribution records
   (`*review-attribution-*`) are skipped: they are route-grid telemetry, they
   live in `memory/evidence/attribution/`, and a project that has not moved
   its records yet still holds some in the journal.
2. Applicable rules as authority sources: the project's `AGENTS.md`, the
   rules locations its index names, and the harness `rules/`. Read, never
   edited.
3. Native notes only as attributed sources when available, at the location
   the index names; report an unavailable source as unknown, not empty.

A source revision (git blob) already examined by an accepted report is
processed: cite its revision, do not re-import its content as new. A changed
revision is re-examined. Record every examined source in the report ledger,
one line each:

- <path> blob <40-hex git blob id>

## Rebuild

A smelt re-derives every topic; it does not append to it. Each page is written
fresh from the previous page plus the journal episodes that page links and any
new ones, under the caps below. A claim survives only if current evidence
supports it. Preserve rulings’ substance and context, including later author
edits, using § Ruling register and retirement.

Work by department: one topic at a time, loading only the journal episodes
that topic links plus entries not yet linked anywhere, and never the whole
journal at once. Files linked by several topics are re-read per topic.

Net change is measured, never estimated, from the harness against the
selected project:

```bash
python3 "$IDH_ROOT/scripts/memory_sizes.py" "$PROJECT/memory/topics" --before <git ref of the previous accepted state>
```

It prints bytes before and after per page and the total; the ref resolves in
the project's own repository. Rulings count. A page or a store that grows
is explained in the report; shrinking needs no reason.

## Job of a topic and caps

A topic is the as-built guide to one department of the project: what is true
now, in the present tense, each claim with its scope and a link to the journal
episode that supports it. It is a guide to the journal, not a replacement for
it. When a claim and its source episode disagree, the episode wins and the
claim is corrected or retired. A superseded claim leaves the page: the journal
and git keep the history; never annotate it in place, and never split a page
by date.

Ordinary topic shape: current guidance, hazards, open questions, Sources
(journal links), and a fallback box emptied at each smelt. No topic retains a
Retired or Newly retired section; retirement records belong in the journal.
The ruling register uses the separate format below.

Caps, in UTF-8 bytes (`memory_sizes.py` reports them):

- A page holds at most 4096 bytes, counting every section except `Sources`.
  Inline source links inside a claim count.
- Keep conditions and exceptions; move historical detail to the journal.
- An overflowing `user-rulings.md` is reported without failing the size check
  or directing promotion. Preserve reviewed rulings rather than cutting them
  merely to fit the budget.
- `memory/MEMORY.md`: one line per department with its most-used fact, plus
  the project's local location facts, within the 40-line cap SKILL.md states.

## Ruling register and retirement

Each selected project's `memory/topics/user-rulings.md` has a project-identifying
title and useful subject headings containing active rulings in ordinary,
blank-separated paragraphs. Keep each ruling's context, scope, qualifications,
and sources beside it. Rulings are contextual jurisprudence: preserve substance
and author edits, not immutable wording. Dates stay in sources unless chronology
matters. Journal narratives use `[context]`; preserved note text uses
`[smelt annex: note identifier]` linked to its actual repository annex.

This register is exempt from the ordinary topic template. Add no introductory
policy, generic Hazards/Open questions/Fallback sections, pinned-date prefixes,
summary blockquotes, Shared provenance inventory, or pending intentions.
Proposals stay in their journal sources until ruled on. Use the selected
project's decisions; the harness register illustrates format, not content to copy.

Brood primarily integrates rulings and retires those fully integrated, without
an additional author-approval gate. Preserve active rulings through Smelt
rebuilds and Brood edits. For a retirement, remove the ruling from the topic and
retain it in the selected project's append-only journal, grouped by cause:
verified integration into rules/skills/documentation (name the destination),
supersession, retraction, or historical completion/observation. Keep the ruling,
sources, and reason. Completed work or dated observations do not establish
integration. Reuse an existing source record when it already records the
retirement; otherwise append a new linked record. Never rewrite old journal
entries or accepted reports, or duplicate retirements on later passes.

Memory pages: the ruling register plus department topics with a fixed core (Site
practice: how work lands here; Environment: hosts, services, external tools;
History: the journal, reports and git, never a page) plus the project's
ouvrage departments (tool or code: architecture and contracts, interfaces and
compatibility, release; analysis: data and provenance, methods, results;
article: argument, literature, venue; book: structure, voice, sources and
rights; host: services, hardware, access, monitoring). At most 8 pages per
project.

## Consolidate

Beyond the three functions SKILL.md states: group related positive and
negative outcomes; keep conditions, exceptions and contradictions. A
connection between episodes is not an established cause. Present a hypothesis
as such, distinct from a supported observation, and distinguish canonical
author decisions from hypotheses. A smelt may derive no lesson at all; it must
not invent one.

## Encrypted entries (.age)

Material not cleared for the repository audience stays in the project
repository as age ciphertext, from birth. Smelt uses the same pinned commands
and the same per-project key as capture; there is no second mechanism:

- key: `~/.config/keys/memory/<sha256(normalized origin URL)[:16]>.age`
  (scheme, user, default ports 22/443/80 and `.git` stripped, lowercased)
- recipient: `age-keygen -y <key>`
- decrypt: `age -d -i <key> <entry>.age`
- encrypt: `age -r <recipient> -o <entry>.age`

Without the key, skip `.age` entries, record the skipped count in the report
and never treat them as empty. With the key, decrypt in memory only (plaintext
is never written to the working tree), consolidate, then re-encrypt: write the
consolidated entry to a sibling temporary ciphertext
(`age -r <recipient> -o <entry>.age.new`) and only after success atomically
rename it over the original; sources preserved. `age -o` overwrites an
existing destination silently, so writing in place could destroy the original
mid-write; the temporary ciphertext is what keeps the failure contract below.

Re-encryption applies to consolidated entries under `memory/topics/` only: an
encrypted journal entry is read, never rewritten.

Failure handling: stop and report; never leave plaintext or a partial
ciphertext in the tree.

- **authentication failure** (key missing, unreadable or wrong): treat the
  entry as unavailable: skip it, count it among the skipped, and name the
  error class in the report. Never guess content and never treat the entry as
  empty.
- **malformed ciphertext** (`age -d` fails): leave the `.age` file untouched
  and mark it unreadable in the report with its path and error class; never
  delete or overwrite it.
- **re-encryption failure** (`age -r` fails): remove the temporary ciphertext,
  keep the original `.age` entry in place untouched, and report the failure:
  that entry's consolidation is not done.

## Report

Write `memory/smelts/YYYY-MM-DD-<slug>.md` recording:

- Skill revision (`git -C "$IDH_ROOT" log -1 --format=%H -- skills/smelt`),
  runtime and model.
- Sources examined with their git blob revisions (the ledger), the count of
  encrypted entries skipped, and unavailable sources.
- Editorial changes: what was pruned, merged or refreshed, with the reason and
  retained sources; corrections with the evidence that revised them.
- The bytes of each topic page against the cap, and the net change per page
  and in total (§ Rebuild), with the reason for any growth.
- Unresolved questions and exposed contradictions, each with its ticket.
- The native-note triage table and the case-note changes (SKILL.md lanes).
- Native notes actually used: their text, adapted to the project's audience,
  in the report or a versioned appendix; a fingerprint alone cannot preserve a
  mutable note.
- What the pass wrote, then a second pass over the same revision set: it
  imports nothing as new and re-examines each correction against its sources.
  It also compares each previous page with its rebuild: every caveat,
  condition or exception of the previous page is still present or has a
  sourced retirement record (§ Ruling register and retirement). Confirm that
  the second pass appends no duplicate retirement records.
