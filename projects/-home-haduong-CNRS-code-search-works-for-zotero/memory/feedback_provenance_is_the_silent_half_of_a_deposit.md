---
name: feedback-provenance-is-the-silent-half-of-a-deposit
description: "A memory deposit has three parts and only two are visible — files and MEMORY.md lines can be complete while provenance is 0/N, and the slug is the filename stem, not the frontmatter name"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 3cdf4883-8bf7-4ffa-8060-2e328114969d
  modified: 2026-09-16T11:14:24.752Z
---

Depositing a memory lot writes three things: the `.md` files, the `MEMORY.md`
pointer lines, and a record per entry in
`~/.claude/memory/.provenance.json`. The first two are visible in every
session — they load into context. The third is visible to nothing, so a lot can
look fully deposited and be two-thirds deposited.

**Why:** on 2026-09-16 a twelve-entry lot was carried as an open task. All
twelve files existed, all twelve `MEMORY.md` lines were present and resident in
the session prompt. Provenance held **0 of 12**. Nothing anywhere would have
said so; the entries simply would not have counted toward the ≥2-project
promotion gate, silently, forever.

**Two traps in the fix.**

First, the slug is the **filename stem with underscores**
(`feedback_line_citations_rot`), not the kebab-case `name:` in the file's own
frontmatter (`feedback-line-citations-rot`). The store is 888 underscore keys to
96 kebab, and every sibling entry for this project is underscore. Recording the
frontmatter form creates orphan entries that match nothing and are
indistinguishable from a successful deposit.

Second, `provenance.py record SLUG PROJECT` takes only those two arguments and
writes to an absolute path, so it runs fine from any worktree — the `--root`
that harness ticket 0934 reports missing belongs to `backfill` and `usage`, not
to `record`. "Deposit from the main checkout" is not a constraint here.

**How to apply:** verify the deposit by reading the store, never by reading
`MEMORY.md`, which is the one part that cannot fail silently:

```python
json.load(open(os.path.expanduser('~/.claude/memory/.provenance.json')))['entries']
```

and check each slug is present **with this project in its `projects` list** —
presence alone is not enough, since a promoted harness-level entry exists
without naming any project. The project key is the directory slug with its
leading dash: `-home-haduong-CNRS-code-search-works-for-zotero`.

Same family as [[feedback_a_checkbox_needs_its_procedure]]: a deposit "done"
box that names no command is tickable while a third of the work is missing.
