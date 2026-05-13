---
name: nightbeat-risk-review
description: Interactively de-risk nightbeat by reviewing logs for risky-ticket patterns.
user-invocable: true
argument-hint: "[--hours N]"
---

# Nightbeat Risk Review — interactive triage

Run this skill before starting a new nightbeat window to flag and de-risk structurally problematic tickets.

## Steps

1. **Collect the raw report.**

   Run:
   ```bash
   python3 ~/.claude/scripts/nightbeat-report.py --full --hours 72
   ```
   Accept `--hours N` from the skill argument and substitute it (default: 72 = 3 nights).
   Capture and read the full output.

2. **Extract risk signals.**

   For each run in the report, extract the picked ticket ID (look for `PICK: NNNN` in the result text).
   Flag a ticket if **any** of:
   - `total_cost_usd > 2.0` — parallel fanout risk
   - `stop_reason` is `None` or absent — budget kill or crash
   - Same ticket ID picked ≥ 2 times in the window with no new commits between picks — repeated pick, no progress
   - Result text contains "Access Denied" or "permission denial"
   - `num_turns < 5` and `total_cost_usd > 1.0` — expensive but fast, parallel agents died early

3. **Present risk table.**

   Display a ranked table (worst signals first):

   ```
   | Ticket | Project | Attempts | Max Cost ($) | Signals |
   |--------|---------|----------|--------------|---------|
   ```

   If no tickets are flagged, print "No risk signals detected in the window." and stop.

4. **Interactive triage.**

   For each flagged ticket (in risk-rank order), present signals and offer:

   a. **sweep-skip** — tag the ticket deferred:
      ```bash
      erg tag NNNN deferred tickets/
      erg log NNNN "claude note sweep-skip: scope-too-large, deferred after risk review" tickets/
      ```

   b. **note** — append an explanation without tagging:
      ```bash
      erg log NNNN "claude note <reason>" tickets/
      ```

   c. **open sub-ticket** — split into a smaller ticket: invoke `/ticket-new` to create the sub-ticket with a focused scope.

   d. **skip** — leave unchanged, move to next.

   Record every action taken.

5. **Housekeeping commit.**

   After triage, commit all modified ticket files:
   ```bash
   git add tickets/
   git commit -m "chore(tickets): nightbeat risk-review triage $(date +%Y-%m-%d)"
   ```
   If no files were changed (all `skip`), print "No changes to commit."
