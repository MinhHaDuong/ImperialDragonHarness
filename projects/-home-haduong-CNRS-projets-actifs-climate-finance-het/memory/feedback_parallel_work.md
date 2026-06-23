---
name: User works in parallel
description: User actively works in their terminal alongside the chat — never assume they haven't done something just because it wasn't pasted in chat
type: feedback
---

When the user says they did something (tested podman, wrote a file, etc.), trust them. They work in their VSCode terminal in parallel with the conversation. Claude cannot see that terminal.

**Why:** User was told they hadn't done something they clearly had. Being contradicted felt dismissive ("gaga"). The Dockerfile was already written and merged while the conversation was ongoing.

**How to apply:** Before asserting "you haven't done X" or "X doesn't exist yet", check the actual filesystem/git state first. If evidence confirms the user's claim, acknowledge it immediately. Never assume the conversation is the only source of truth about what happened.
