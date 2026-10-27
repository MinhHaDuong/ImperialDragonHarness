# Model-service transmission authorization

On 23 October 2026, during preparation of the REL outline and initial HET
submission review pilots, the user explicitly authorized the transmissions
necessary for the tests and requested that blocking of sends to Claude,
Codex and OpenRouter be disabled, remembered and committed.

The harness guards (`rules/guards.md`, and for Codex and Pi the
session-start context) now record standing
authorization for task-necessary model-service transmissions to those three
destinations, preserving explicit local-only restrictions, confidentiality
obligations, credential protections and agreed task budgets.

The local Codex configuration was read: its existing value was
`approvals_reviewer = "user"`. This session nevertheless exposed
`approvals_reviewer = "auto_review"` as managed execution policy. No local
configuration value was changed or invented: the agent cannot replace the
active managed policy through repository instructions. This commit records
the user's authorization; it does not claim to disable the managed reviewer.

After the explicit authorization, the REL hosted review launch was accepted.
No blanket permission for unrelated publication, people-directed messages,
merges or arbitrary network destinations was inferred.

Configuration reference:
https://learn.chatgpt.com/docs/security

Verbatim user instructions establishing persistence beyond the immediate
test: “Je disable le bloquage automatique des envois vers Claude, Codex et
OpenRouter”, then “Modifie les réglages du bloquage, mémorise et commite.”
These are direct authorization and a separate implementation request, not
an inference from the original test request.

Cross-family review via Claude CLI requested Opus/medium. The encrypted/local
material exception was made explicit after review. Official documentation
URL was fetched and its redirect observed. CLI modelUsage: claude-opus-5-5; effort requested, not independently attested.

Placement revised on 2026-10-27 at the author's choice: first drafted in the
harness AGENTS.md, which no other repository loads.
