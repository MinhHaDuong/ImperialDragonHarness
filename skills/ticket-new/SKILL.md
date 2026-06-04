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

**Input:** anything — a title, a sentence, a JSON blob from the forge CLI, a
paste from a conversation. Extract the intent and normalize to a single
imperative title.

## Steps

1. **Normalize the title.** Distill the free-form input into one imperative
   title (e.g. "Add retry logic for failed API requests"). Drop noise; keep
   the intent. This is the only piece you craft by hand.

2. **Create the file atomically:**
   ```bash
   ERG=${ERG:-tickets/erg}
   $ERG new "<normalized title>"
   ```
   `erg new` allocates the next free ID, kebab-cases the title into a slug,
   and writes a valid `%erg 0.1` file (preamble headers + a `created` log
   line + an empty body) in one race-safe step. It prints
   `CREATED NNNN-slug.erg` — note that filename for the next step. Never
   compute the ID or slug yourself.

3. **Edit the body in place.** Open the file `erg new` just printed and fill
   in the body section with these sections:
   ```markdown
   ## Context
   {why this work exists}

   ## Actions
   1. {concrete step}

   ## Test
   {first test to write — TDD red step}

   ## Exit criteria
   {definition of done}
   ```
   Leave the preamble headers and log section as `erg new` wrote them.

4. **Validate the file** (pass the specific file, not the directory):
   ```bash
   $ERG validate tickets/<new-file>.erg
   ```
   Fix any errors before committing.

5. **Run corpus check** to catch dangling refs:
   ```bash
   $ERG check tickets/
   ```
   Fix any errors before committing.

6. **Commit the ticket file.**

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
