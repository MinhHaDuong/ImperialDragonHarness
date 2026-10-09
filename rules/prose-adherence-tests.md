---
paths:
  - "**/tests/**/*.py"
  - "**/test_*.py"
  - "**/docs/editorial-brief.md"
last-reviewed: 2026-10-09
---
# Prose adherence tests — pin defects, never phrasings

Loaded when any test file or the editorial brief is touched. It binds only in a
repo that has a manuscript; in a repo without one, stop reading here.
Promoted from two projects that reached the same rule independently
(ticket 0375).

- **Pin only negative guards and mechanical checks.** A prose test may forbid a phrasing (overclaim signature, banned register) or check a mechanical property (a number re-derived from a committed artifact, structural presence, a density ratchet). It never asserts that an authorial sentence appears.
- **Why the asymmetry holds:** a defect reads the same in every draft; good prose does not, so a positive pin breaks on each legitimate rewrite and forces test-chasing edits.
- **Allowed narrow exception: loose structural anchors** — a section-scoped marker class, or fixed *external* terminology the author does not own — never a sentence the author wrote.
- **Conditional negatives bridge editorial decisions to CI:** "if figure X appears in the conclusion, its caveat accompanies it" guards a decision without pinning its wording.
- **Positive intent lives in the editorial brief** (`docs/editorial-brief.md`), one entry per standing decision, checked at review time by `/review-pr-prose`, which owns the entry schema.
- **Pure prose tickets carry no red test.** TDD assumes a machine-checkable positive outcome and prose has none; verification is the rebuilt artifact plus the prose review panel. Add a test only to pin a newly observed defect class.
- **Close a defect class with a sweep, not a guard.** Fix every instance, then sweep the whole tree for the class; write a standing guard only if the class recurs after a sweep cleared it. A text pattern is always one synonym behind.
- **If a guard earns its place, key it on the distinguishing feature, not topic vocabulary**, and check the span bounds between pattern parts — a too-narrow window silently skips a sibling instance.
