# Project memory index

One line per memory. Content lives in the linked file, never here.

- [R2R upstream dormant](r2r-upstream-dormant.md) — Cirdi's RAG engine is abandonware since ~Nov 2025; SciPhi pivoted to Event Horizon Labs; pin v3.6.6, sustainability risk
- [R2R embeddings on OpenAI](r2r-embeddings-openai-billing.md) — OpenAI key is the app's single billing dependency; quota-exhaustion 500s every query even though generation is Mistral
- [Outer repo local-only, secrets gitignored](outer-repo-local-only-secrets.md) — CIRED.digital outer repo has no remote; secrets/ purged from history + gitignored, managed via push_secrets; cired.digital is a bare gitlink not a submodule
- [Verify via real code path, not cache](feedback-verify-real-codepath.md) — confirm fixes with input that forces the real path; a cached/repeated query gave a false "fixed" after a key rotation
