# Legacy executor retirement preparation

Ticket 1205, prepared 2026-10-23 in the isolated métier-contract worktree.
Integration is conditional on the parent's successful public manuscript trial;
this preparation does not establish that prerequisite or retire the train's
executor on its own.

The raw repository search was `rg -n 'peer_review\.py|external-peer-review|_keystore_value|resolve_credential'`.
The live consumers and changes are:

| Consumer | Minimal migration |
|---|---|
| `skills/external-peer-review/SKILL.md` and optional transport reference | Keep the requested independent-reader capability; use the live manuscript-review contract per routed reader with separate artifacts and dissent. Delete the old executor and transport instructions. |
| `skills/conference-submission-prep/SKILL.md` | Ordinary PDF review uses manuscript-review. Explicit independent review uses the external skill. |
| `scripts/probe-memory-symlink.py` | Extract the existing isolated-shell provider reader into `scripts/keystore.py`; import it instead of the review executor. No model, credential transport or backend framework added. |
| `tests/test_external_peer_review_skill.py` | Remove obsolete executor/persona/SDK requirements. Preserve provider guard regressions in `tests/test_keystore.py`, exercising the extracted reader in disposable subprocesses without site-packages. |
| `tests/test_probe_memory_symlink.py` | Retain the real provider-reader positive control and all probe guards; update the simulated loader-failure label. |
| `tests/test_deps_declared.py` | Keep the live YAML positive control; replace the deleted SDK import control with a direct lazy-import scanner test. |
| `pyproject.toml`, `uv.lock` | No remaining production OpenAI SDK imports. Remove its dependency and regenerate the lock offline; eleven packages are removed in total. |
| `skills-catalog.md` | Regenerate the changed external-review description. |

Historical audit/discussion, ticket, coaching benchmark and memory mentions
remain evidence about past implementations. They are not executable consumers
and are deliberately unchanged. The separate HAL shell resolver and coaching
shell reader remain active implementations in their own scopes; this task does
not consolidate them.

The unused OpenRouter environment-first resolver is removed with the executor.
The probe still asks its explicit trusted provider file for its fixed credential
name; it never inherited that resolver's environment-first behavior. The
extracted reader retains regular-file and size checks, clean-shell sourcing,
scalar-only values, CRLF handling, UTF-8 validation and no secret output, and
now validates credential-shaped names at its own entry point.

Scoped verification: 55 passed, 1 optional live probe skipped across keystore,
memory probe and dependency tests; 35 existing skill checks passed. Ruff,
relative link checks for changed skills, agnostic checks, catalog drift and
diff hygiene passed. No live credential or model call was made. The parent's
composition gate, public trial and final Astra/Fable validation remain separate.
The installed resolver generated lock revision 3 from revision 5 while pruning
the SDK's exclusively used dependency tree; package versions retained are unchanged.
