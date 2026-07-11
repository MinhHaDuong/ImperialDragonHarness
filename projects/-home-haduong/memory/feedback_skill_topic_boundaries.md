---
name: Skill files are topic-bounded; split mixed rules
description: When drafting harness rules, keep each skill file (git/coding/state/workflow) to its own topic and split rules that span two topics across files
type: feedback
originSessionId: f363f3c5-63e5-4b4d-a38c-cc6f2533aed7
---
Harness skill files ([git.md](.claude/skills/harness-rules/git.md), [coding.md](.claude/skills/harness-rules/coding.md), [state.md](.claude/skills/harness-rules/state.md), [workflow.md](.claude/skills/harness-rules/workflow.md)) are organized by topic, not by chronology or use case. When a rule has consequences in more than one area, split the rule across files at the topic boundary instead of putting the whole thing in one file with a cross-reference in the body.

**Why:** user corrected me after I put a rule about the analysis/writing build split into git.md because its *consequence* was about commit-vs-gitignore. The root cause was build structure (coding.md) and the git behaviour was downstream. The user wanted two short bullets, one per file.

**How to apply:** before writing a bullet, ask "what topic is this rule's root cause?" and place it there. If the rule also has a consequence in another topic, write a second, shorter bullet in that file — don't bundle. Cross-link with a relative path so readers can navigate.
