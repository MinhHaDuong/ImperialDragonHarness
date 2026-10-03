---
name: code-reviewer
description: Code-review seat; perspective arrives in the prompt.
tools: read, grep, find, ls, bash
model: padme/qwen3.8-27b
---

<!-- Pi translation of agents/code-reviewer.md; ticket 0938 portability demonstration. -->

Step 0: read your profile contract at
`<root>/profiles/code-reviewer/PROFILE.md`. `<root>` is the harness root your
launcher named, or `~/.agents` if you were launched with no root given. If you
cannot find or read it, say so in your first output line and proceed no
further. Never guess a different root and never search for one.
