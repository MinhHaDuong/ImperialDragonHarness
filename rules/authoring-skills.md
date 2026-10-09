---
paths:
  - "**/SKILL.md"
  - "**/skills/**/*.md"
last-reviewed: 2026-09-09
---
# Writing skills

Loaded when you edit a skill. These rules are enforced by
`tests/test_skill_descriptions.py` and `tests/test_skill_frontmatter.py`; the
tests are the gate, this is why.

- **A skill states a role and a need; the route skill decides the worker.**
  Write "a reviewer from another model family" or "a cheap mechanical lookup",
  never a model name, or capability-tier declaration. The choice of
  model and effort, and reviewer decorrelation, belong to `skills/route/SKILL.md`
  and its references; concrete model IDs live only there and in runtime
  configuration. Enforced by `tests/test_skill_frontmatter.py` (`skills/route/`
  is exempt: it holds the grid).
- **Name capabilities, not the tool that provides them.** "Schedule a wake-up",
  not a timer-tool name; "delegate to a subagent", not an agent-tool name;
  "merge request" not "PR", "ticket" not "issue", "forge" not "GitHub"; never
  hardcode `gh`. The harness outlives tool generations — names rot, capabilities
  don't. Enforced by `scripts/check-agnostic.sh`; a genuinely runtime-specific
  line goes behind `<!-- harness-extension-point -->`.
- **Never take a name the runtime already binds.** A skill named after a
  built-in command silently shadows it and hides its own staleness. Check the
  runtime's command list when you name one; renaming away needs no stub.
- **Discoverability first in `description:`.** The first sentence states the
  plain, unthemed function in the words a naive user would search ("Audit
  test-suite quality…"). Theming, lore and jargon come after it. Skill *names*
  may stay themed — the opening sentence is what a user scans.
- **Always quote free-text frontmatter.** `description:` and `argument-hint:`
  are wrapped in `"` (or `'` when the value contains a double quote); prose
  carries colons, leading `[` and quotes that YAML parses wrongly. Write new
  consumers strictly too: a lenient regex returns the same all-clear on broken
  documents.
- **Every multi-item step declares its concurrency** — parallel-background or
  sequential-blocking — and why. Model defaults differ across versions; the
  skill text is the contract.
- **Split a body only where a run uses one branch of many.** A skill whose
  subcommands or modes are mutually exclusive becomes a router plus
  `references/<branch>.md`, named from the router as `` `references/x.md` ``
  so `tests/test_skill_reference_pointers.py` can see it. The criterion is
  exclusivity, not length: a body whose sections are all traversed on every
  run stays whole, and splitting it only buys extra reads. Two things never
  move — a branch of two or three lines, whose pointer would cost more than
  its text, and a reference several branches share, which is one file rather
  than a copy per branch.
- **The Imperial Dragon is not a bird.** No avian analogies, in names,
  explanations or rationale. Scale, power, taxonomy.
- **A new slash-invocable automation is a skill**, not a legacy command file.
- **Test one before blasting.** A skill that fans out batch API calls dry-runs
  prompt assembly and runs one real call per regime before the full batch.
