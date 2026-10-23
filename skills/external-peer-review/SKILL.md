---
metadata:
  category: writing
name: external-peer-review
description: "Obtain independent external peer reviews of a manuscript PDF; preserve dissent and synthesize verified findings."
user-invocable: true
disable-model-invocation: false
argument-hint: "<pdf-path> [reviewer needs or personas]"
---

# External peer review

Use this skill when the author explicitly requests independent external
readers. Ordinary manuscript reviews use `manuscript-review` directly. This
skill adds reviewer discovery and synthesis to that review protocol; it has
no separate review executor or credential transport.

1. **Fix the inputs, sequential-blocking.** Resolve the manuscript PDF,
   annexes, revision, author's current decisions and review question. Honor
   the author's clearance and destination constraints. Never infer clearance
   merely because an external review was requested.
2. **Discover and route reviewers, sequential-blocking.** Describe the expertise
   and independent perspectives needed, then use `route` and its decorrelation
   contract to select available readers. Record actual model identity, effort,
   route, evidence and missing perspectives. A persona or a separate session
   does not establish independence; neither does the verification pass within
   one review. If suitable independent readers are unavailable, state the
   limitation instead of relabelling a same-family or simulated panel.
3. **Run one complete review, sequential-blocking.** Follow the live
   `skills/manuscript-review/SKILL.md` contract for the selected reader, with
   explicit model, effort, route reason, clearance and input revision. Use a
   fresh run directory per reader; retain preparation, raw review, tool-use
   evidence, verification and report. Confirm the run is complete before
   starting the remaining independent readers; a non-empty response alone is
   insufficient. The current manuscript-review runner supports only the
   Claude CLI route; a model flag does not add another provider. For a required
   independent perspective beyond that route, the runtime may use another
   available mechanism that fulfills the same input, tool-use, verification
   and identity evidence contract. Otherwise report that perspective unavailable.
4. **Collect remaining reviews, parallel-background when capacity allows.**
   Each follows the same manuscript-review contract in its own run directory.
   With one slot, run them sequentially. Do not expose one reader's findings
   to another before its independent review is complete. Report failed or
   incomplete runs and uncovered manuscript parts explicitly.
5. **Synthesize, sequential-blocking after collection.** Read every completed
   review and its verification results. Attribute conclusions and evidence to
   their reader/run. Preserve dissent, unresolved criticisms and incisive
   individual findings. Weight a finding by its verified evidence and relevant
   expertise; repetition across personas is not independent corroboration and
   majority agreement cannot erase a demonstrated error. Keep coverage,
   scientific judgment and the author's disposition separate.

Return the per-reader artifacts, identity/independence evidence and limits,
verified concerns, disagreements and author decisions still needed. Reviews
are advisory; this skill neither publishes nor merges anything.
