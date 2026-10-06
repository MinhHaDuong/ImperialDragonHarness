# 0887 adapter activation: live state regressed by a pre-merge install mid-transition

Date: 2026-10-05 · project: .agents (harness) · session: Mistral Vibe, branch t0887-activate-adapter, PR #1211

Context: ticket 0887's operator act ran on the reference machine: live
`~/.claude/settings.json` hooks key removed at 21:37, adapter link placed
(`~/.claude/skills/claude-code`), guard confirmed firing from the plugin in a
real session (dirty `git reset --hard` denied, denial attributed by Claude Code
to "the claude-code@skills-dir plugin"; SessionStart confirmed by the
`sync-local-main.last` side effect). Probe case D (broken symlink does not
fire) measured on Claude Code 2.1.289.

Observable events: during the same evening, a model-tournament replay session
worked in parallel from pre-merge historical checkouts. At 21:40 — three
minutes after activation — `~/.claude/settings.json` again carried the three
managed hooks, with the adapter link still active: an `idh install` run from
a checkout whose canonical still had hooks had merged them back
(fingerprint: the `register_settings` merge signature and the
`~/.local/state/idh/links.json` receipt mtime). Every guard would have fired
twice per session. The PR's own review panel (round 1, four seats
independently) detected it from the live machine state.

Outcome and decisions: the live file was remediated twice (hooks key removed
again); the state is detectable by design now — the merged absence-mode
registration check refuses a live settings file carrying harness hooks, and
`idh install` from a merged checkout removes exactly those commands
(command-granular, refusing when the plugin link or payload is broken, so
zero guards is never an install outcome). The review panel also caught three
escalating variants of the fail-open class across its rounds: a vacuous
launch check that blessed the double-fire state, install-order stranding on
zero guards, and a payload-blind readiness gate that proved the switch rather
than the source.

A review seat incident is on record: during an end-to-end reproduction the
seat failed to override HOME and clobbered the real `~/.claude/settings.json`;
it restored the hooks-less pre-install state (sha-verified against the idh
backup) and preserved the clobbered copy at
/tmp/settings.json.clobbered-by-review-seat-20261005. Post-incident
verification: live file hooks-free, adapter ACTIVE, `idh check: ok`.

References: PR #1211 (merge 89004cff), tickets/closed/0887-*.erg log entries
2026-10-05T19:37Z, review rounds 1-3 posted as PR reviews, STATE.md caveat
(self-expiring), tests test_install_refuses_to_strand_a_machine_on_zero_guards
and test_install_refuses_removal_when_the_plugin_payload_is_broken.

Pending capture (roar step 6): the review-attribution record for PR #1211
could not be written. The runtime exposes no verbatim provider-qualified
model id to the session (provider masked as "configured", session_metadata
active_model null, no model field in any session log), the attribution
contract forbids reconstructing an id from an alias, and the validator
refuses placeholders. Fifteen reviewer attempts are nameable with full
status and findings (draft preserved at
memory/pending-capture-pr1211.md.txt; the durable trail is the three
synthesis reviews on PR #1211), but the writer line cannot be established.
Filed as a follow-up ticket.
