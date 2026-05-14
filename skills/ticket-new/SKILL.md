---
name: ticket-new
description: Create a local %erg 0.1 file for agent coordination.
# Model-invocable: parses free-form input (title, sentence, JSON blob, paste) into %erg 0.1.
# Side effects are file-only — no branch, no PR — so autonomous capture is safe.
# Contrast start-ticket (disable-model-invocation: true), which creates worktree + branch + PR.
disable-model-invocation: false
user-invocable: true
argument-hint: [title]
---

# Create local ticket

**Input:** anything — a title, a sentence, a JSON blob from `gh`, a paste
from a conversation. Extract the intent and normalize to `%erg 0.1`.

## Steps

1. Determine the next ID:
   ```bash
   ERG=${ERG:-tickets/erg}
   $ERG next-id tickets/
   ```
   Always use `erg next-id` — never compute or guess the ID manually.

2. Choose a slug: lowercase kebab-case, ASCII only (`[a-z0-9-]`), derived from the title.

3. Create `tickets/{ID}-{slug}.erg` with this exact structure:
   ```
   %erg 0.1
   Title: {imperative title}
   Created: {YYYY-MM-DD}
   Author: {agent or user}

   --- log ---
   {YYYY-MM-DD}T{HH:MM}Z {author} created

   --- body ---
   ## Context
   {why this work exists}

   ## Actions
   1. {concrete step}

   ## Test
   {first test to write — TDD red step}

   ## Exit criteria
   {definition of done}
   ```
   Note: no `Status:` header — `erg validate` rejects it.

4. Validate the new ticket (pass the specific file, not the directory):
   ```bash
   $ERG validate tickets/<new-file>.erg
   ```
   Fix any errors before committing.

5. Run corpus check to catch dangling refs:
   ```bash
   $ERG check tickets/
   ```
   Fix any errors before committing.

6. Commit the ticket file.

Format spec: `tickets/spec-erg-v1.md` (or global rule `tickets.md`).

## Required sections for handoff documents

When creating a ticket as a handoff document, ensure it includes these sections
so a new agent has complete context:

```markdown
## Context
What problem or need this addresses. Why now.

## Relevant files
- `path/to/file.py` — role in this task

## Actions
1. Concrete step
2. Concrete step

## Test
- What test to write first (red step of TDD)

## Verification
- [ ] How to confirm each action worked

## Invariants
- What must not break (tests, build, existing behavior)

## Exit criteria
- Definition of done — when is this ticket complete?
```

## Tracking ticket convention

When investigation spawns sub-tickets:

1. Original ticket becomes the **tracking ticket** — leave it open.
2. Create each sub-ticket referencing the tracker.
3. Edit tracking ticket to list each child.
4. Tracking ticket closes only after integration review (see `/celebrate` step 7).
