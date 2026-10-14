**Portable simplify: CLEAN.** Prior dispositions remain valid at current HEAD.

- HEAD before/after: `9bd20fa3f24f05cf8cc5030d40f44b380fe5b6c3`.
- Compared against `825b1eda84a5948705ed618101b5a799821618d1`.
- Only changed path: [docs/2026-10-14-adherence-semantic.md](/tmp/idh-raid-1080-prep/docs/2026-10-14-adherence-semantic.md).
- Prior CLEAN evidence: [1389.log](/tmp/idh-final-gazes/1389.log:4318).

Concrete candidates considered:

- **Recipe expansion:** the blank separator makes reproduction match the retained fixture diff. Clear and sufficient; no helper or framework needed.
- **Provenance wording:** labeling caller normalization and pointing to the raw verdict clarifies evidence ownership. No execution behavior changes or additional machinery.
- **Prior dispositions:** retain separate phase-3/4 mappings, small direct tests, distinct summary/worker/outer records, four minimal fixtures, and existing routing/transport reuse. Those paths are unchanged; both documentation fixes support these dispositions.

`git diff --check 825b1eda..HEAD` passed; working tree was clean. No writes, commits, pushes, or test reruns.