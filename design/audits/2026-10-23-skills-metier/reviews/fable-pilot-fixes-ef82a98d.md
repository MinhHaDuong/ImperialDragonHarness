# Fable — final bounded review

Reviewed commit: ef82a98deb3d2e51b8d94839eeca649a5cc40edb. Pasted technical diff only; no tools, tests or manuscripts inspected. Model identity comes from native modelUsage, not response text. Not a merge authorization.

`[→ Verify] · model not self-attested per request · MOE N+2 — government by intention via team leads; I filter, verify, surface, advise.`

No worktree created: the cwd is `/tmp`, not a project checkout, and the review is of pasted text only.

**Verdict: CLEAR.** No blockers in the four scoped areas.

- **Cache normalization.** The chain requires absolute, lexically under the cache root, equal to its own resolve, resolve under the resolved root, exact `tool-results` and session parent names, `webfetch-` prefix, no symlink at any ancestor, regular file. Any `..` component or symlink in the path fails `cache != cache.resolve()` before the per-ancestor symlink check even runs. Fail-closed on both vectors.
- **Record linkage.** The receipt is parsed from the fetch record for the accepted URL as returned by the redirect walker, not from a text match. The read must name that exact path, carry no limit or offset, and sit after that fetch's result line. The `same-content-other-url` case rejects because the read precedes the linked fetch, which is the correct discriminator against equal-string matching.
- **Duplicate-heading restriction.** The `len(canonical) != len(blocks)` check runs only when some finding lacks a text field. All-text payloads keep the legacy substring check, and the legacy test asserts the payload is returned unmodified.
- **Negative tests.** The twelve cases cover the receipt, path, session, ordering, page selection, image count, cache mutation and symlink paths. The `unread` case confirms a passage on an unread page is rejected even though the PDF is pinned.

Two observations, neither blocking:

- **Symlinked home rejects everything.** If the user's home or cache root is itself a symlink, every legitimate receipt fails the resolve equality check. That is fail-closed, so it only costs evidence, never admits bad evidence.
- **Block regex ignores H1.** A canonical block ends at the next `##` or `###` heading only. A `#` heading after a finding would be absorbed into its text. Cosmetic for the ledger, no security effect.
