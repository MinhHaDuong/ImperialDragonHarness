# Legacy provenance helper retirement

During work following PR #1091, the author asked whether the extracted memory
helper handoff 1002 matched the adopted memory v8 design. The v8 dream
procedure states that dream writes project-local Markdown and does not use the
legacy shared/native-store helpers. The author then asked to retire ticket 0934
if possible.

The tracked caller audit found the dedicated tests as the only current
invocation/import sites for `skills/dream/provenance.py`. The recorded and
two-project candidate tests passed before removal as positive controls. The
helper, those dedicated tests and their coverage test were removed. The
provenance store, project-alias file, native/project notes, `read-index.py`,
`commit.py` and their tests were left unchanged. Current README, ROADMAP,
adapter/install documentation and ticket 0999 were updated to reflect v8 and
the retirement. Historical repair criteria remain in ticket 0934's record.

Ticket 1002 was closed WONTDO as superseded by v8 in PR #1099. PR #1101 closed
0934 WONTDO while removing its unused helper. Its final test run reported 1,225
passed and 2 skipped; lint reported 88 passed; all ten GitHub checks passed.
The independent panel approved correctness, consistency, scope, red-team and
documentation propagation, with reviewer-context reuse disclosed. PR #1101
merged as `6c2fa0ef`. Parent 0999 remains open for integration review; 0988
capture/integration, the 0920 pilot and later 0913 rollout remain tracked.

The shared primary checkout remains on `docs-portable-agents-plan` with local
modifications. Its status was not changed. The separate `handoff-portable-memory`
branch and the sessions implementing 0911/0917 were preserved.
