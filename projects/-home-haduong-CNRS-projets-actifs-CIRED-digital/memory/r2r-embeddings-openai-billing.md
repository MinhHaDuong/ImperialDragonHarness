---
name: r2r-embeddings-openai-billing
description: "Cirdi's R2R uses OpenAI for embeddings, so the OpenAI key is the whole app's single billing dependency"
metadata: 
  node_type: memory
  type: project
  originSessionId: d85d05f6-f79f-4dc3-923c-6868021a8cf6
---

Cirdi's R2R is configured with `openai/text-embedding-3-small` for embeddings (`[embedding]` in the R2R config). Every user query is embedded *first* (the retrieval step), so if the OpenAI account is out of quota the whole RAG request returns HTTP 500 — even though generation runs on Mistral (`mistral/mistral-small-latest` in prod, per `src/frontend/settings.js`).

On 2026-06-22 the app was down with exactly this: OpenAI 429 `insufficient_quota`. A top-up of the *same* key needs nothing. A key *swap* needs the new key in `secrets/env/r2r-full.env`, pushed via `deploy/ops/push_secrets.sh`, then the r2r container **recreated** — `cd ~/cired.digital/deploy && docker compose up -d --no-deps --force-recreate r2r` (or `deploy/ops/up.sh --remote`).

**Gotcha that cost an hour:** `docker restart cidir2r-r2r-1` does NOT re-read `env_file` — it bounces the process with the env baked in at container *creation*. A swapped key only loads on `docker compose up` (recreate), never on `restart`. During the 2026-06-22 rotation, repeated `docker restart` kept serving the old key; it only *appeared* fixed because the old key had been topped up. After the old key was revoked it 401'd, and only `--force-recreate` loaded the new key. Verify a swap with a **novel** query (forces a fresh embedding) — a repeated query can return 200 from a cached embedding and mask a broken key. Confirm the loaded key by `docker exec cidir2r-r2r-1 sh -c 'printf %s "$OPENAI_API_KEY" | tail -c 4'` (last 4 chars only).

Second gotcha: in `r2r-full.env` the key must be a real assignment `OPENAI_API_KEY=sk-proj-...`. A hand-edit once left the new key as a bare value (no `OPENAI_API_KEY=` prefix) → variable undefined.

**Why:** "App broken" looked like a Mistral/Claude problem at first, but the failing dependency was OpenAI embeddings. Anthropic offers no embeddings API, so Claude console funds cannot cover this step.

**How to apply:** When Cirdi queries 500 but health is "ok", check the OpenAI account quota first. Set a budget alert on the OpenAI project. Switching embedding providers is NOT a hotfix — the 1199 stored vectors are tied to `text-embedding-3-small` and would need full re-embedding. Related upstream risk: [[r2r-upstream-dormant]].
