# Memory v8 convention and templates

These are documentary resources for tickets 0911 and 0917, based on the
[current design](../2026-09-10-dragon-memory-design.md) and
[delivery plan](../2026-09-11-memory-implementation-plan.md). They install no
runtime behavior. The harness is the candidate pilot because its assigned work
already has repository memory; activation and audience verification belong to
0920. Do not copy another project's memories into it.

## Adopting the convention

Resolve the assigned project repository first. Merge the
[reading section](templates/AGENTS.md) into its existing AGENTS.md during pilot
setup; never replace its other instructions. Copy the [index](templates/memory/MEMORY.md)
and adapt its relative links to actual files. The
[journal template](templates/memory/journal/2026/2026-10-01-example.md) and
[topic template](templates/memory/topics/example.md) are examples, not experiences
to import. Remove their instructional placeholders when creating real files.
A relative CLAUDE.md symlink to AGENTS.md may provide compatibility; verify each
runtime's loading rather than claiming automatic injection.

```text
memory/MEMORY.md
memory/DREAM.md
memory/topics/<theme>.md
memory/journal/YYYY/YYYY-MM-DD-<slug>.md
memory/dreams/YYYY-MM-DD-<slug>.md
```

DREAM.md and the accepted-report convention are delivered under 0916, not by
these templates. Journal files stay in their original year directory. Choose a
new descriptive slug or distinguishing suffix on collision; never overwrite.
Corrections are new entries linking to the original, which remains unchanged.
Concurrent captures preserve both files and resolve conflicting claims explicitly.
No UUID, mandatory frontmatter or executable schema is required.

## Capture and consolidation boundaries

Capture a significant novelty, an attested surprise, a material consequence or
a conflict between procedure and circumstances. Positive results, failures,
near misses and unexpectedly easy successes qualify on the same basis. Routine
work needs no entry. Around 300 words is guidance, not a quota. Record context,
observations, known cost or avoided damage, and evidence; attribute uncertainty.
An observation does not establish its cause. Do not invent an earlier expectation,
judge actors, derive lessons or propose rules. Cite already adopted decisions.

Capture goes into the project's authorized work branch. A post-merge roar uses
at most one closure branch and one PR bundling factual capture, tickets and docs;
required checks precede auto-merge. Preserve and report any unintegrated branch.
No native-store or harness fallback, unrelated staging, shared-checkout stash,
or removal of unsaved worktrees. A non-Git capture cannot be called committed.

DREAM separately prunes obsolete consolidated claims, merges overlapping themes
with their sources and exceptions, and refreshes still-relevant context. It
checks coherence between indexed memories and applicable harness rules, which
it reads without changing. Resolve conflicts only where evidence and authority
are clear; otherwise expose the contradiction. Preserve journal sources and
trace withdrawals in a reviewed report. Neither roar nor DREAM proposes rules
or crystallisation. The index is at most 100 lines, including blank lines and
headings; move detail to themes. Check with `wc -l memory/MEMORY.md` before commit
and ensure the file ends in a newline.

After completing its work, lair suggests a separate DREAM invocation when at
least five new experiences remain uncovered by accepted reports, including on
a session with no new commit. It does not ask, wait or launch. No timer.
A pending report does not consume experiences; changed source revisions need
re-examination. Counting and live validation remain under 0910/0916.

## Audience and source handling

The candidate pilot's tracked material has a public repository audience, not a
certificate of privacy clearance. Review each source before including text.
For private material, configure a versioned private companion and a local pointer;
an ignored directory or a branch in a public repository is insufficient.
Unavailable native sources are unknown, not empty. Interpreted native notes stay
attributed notes, never reconstructed factual journal entries. See the
[source inventory](source-inventory.md) before selecting pilot material.
