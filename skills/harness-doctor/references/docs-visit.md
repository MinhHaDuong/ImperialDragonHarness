# Docs visit: the whole doc set as the patient

The other visit inputs are incremental: the complaint, or what changed since
the last entry. This one reads the whole doc set at a pinned commit, to
find what no per-change check can see.

## Input

Name the commit (`git rev-parse HEAD`) in the report, then read:

- the root docs: `README.md`, `INSTALL.md`, `AGENTS.md`, `CONTRIBUTING.md`,
  `ROADMAP.md`, `STATE.md`, `RTK.md`;
- `rules/`, its `README.md` table included;
- `conception/README.md`, the index, but not the frozen records it lists;
- the skill references, `skills/*/references/*.md`, read against the SKILL.md
  that cites them.

## Questions

- **One home per fact.** Is each fact stated in exactly one place? A second
  statement is a finding unless it is a pointer.
- **Pointers, not restatement.** Does a document that needs another's fact
  link to it rather than paraphrase it? A paraphrase drifts when the home
  changes.
- **Role held.** Does each document still contain what its role says (its
  title, its opening line, the index entry that describes it)?
- **Overlap and gaps.** Do two documents cover the same ground? Is a topic
  the others point to missing its home?
- **Dead pointers.** Does every path a document names exist?

Findings name both sides (`path:line`) and follow the floor of
`SKILL.md` § Findings and report.

## Journal and trigger

The entry is `memory/journal/YYYY/YYYY-MM-DD-docs-visit-<slug>.md`. The
slug differs from `-harness-doctor-` so that a docs visit does not move the
default input of the next regular visit. Lair suggests a docs visit 30 days
after the newest `-docs-visit-` entry, or when a ROADMAP workstream closes.
