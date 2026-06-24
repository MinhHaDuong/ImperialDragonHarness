# Zotero Integration — IDH Architecture

**Status**: Draft — 2026-06-24
**Principle**: KISS and YAGNI at all layers.

---

## Reference use cases

Five concrete use cases drive what capabilities matter.

**archiveCIRED** — institutional archive, 686 items, French academic papers 1970–2013, scanned PDFs. Needs: bulk enrichment (HAL, OpenAlex, CrossRef), OCR, dedup, multi-library access, field linting and normalization.

**Publications list** — personal list of research outputs (homepage, CV). Needs: keep `Ha-Duong.bib`, HAL deposits, and Zotero citation keys in sync after each new publication.

**AEDIST** — energy transition analysis. Manage information sources HITL, periodically discovers, harvest, index, store relevant documents on energy transition and infrastructure in target countries. May scale up.

**CIRED.digital** — RAG over CIRED research corpus. Needs: import from HAL with fulltext, metadata export with fulltext for ingestion into a retrieval index.

**Periodic activity report** — CNRS/HCERES rapport d'activité. Needs: filtered publication export by year/type, contents organization, summarization and presentation.

---

## Structural decisions

### 1. Source of truth: `CNRS/html/Ha-Duong.bib`

`Ha-Duong.bib` is the authoritative bibliography. Zotero and HAL are downstream consumers. Sync direction: bib → Zotero (import), bib → HAL (deposit via `update-publist`). Zotero is not written to derive the bib; the bib is written to populate Zotero.

This has worked for 30+ years. Do not reconsider until a concrete pain point forces it.

### 2. Shared mutation format: RIS

RIS is the interchange format across all skills. Every mutating skill is a pure function: items in → corrected RIS out. A single apply step diffs the RIS against current Zotero state and writes the delta (PATCH/PUT with `If-Unmodified-Since-Version`).

Skills compose by piping RIS: `lint | enrich | apply`. No shared framework needed beyond that contract.

### 3. Export format: RIS or CSL-JSON only

No custom formats. CSL-JSON is richer (use for RAG and activity report). RIS is simpler (use when Zotero import/export is the destination). Choose per consumer; never invent a third format.

### 4. Harness-level extraction trigger: dream-time

Client functions stay in the project (`reconcile_zotero.py`) until `/dream` finds two projects using them. Dream already promotes project-level patterns to the harness when a threshold is crossed — this is that mechanism. No explicit hook needed.

### 5. Backend interface: Bash

All Zotero operations go through Bash-callable Python scripts. No MCP dependency.

**Why Bash, not MCP:**
- The safety contract (backup → dry-run → apply) is expressed as script flags. MCP write tools have no natural slot for this.
- Autonomous sessions (`raid`, `nightbeat`, `beat`) run headless; an MCP server may not be up.
- The read pattern here is batch, not interactive item-by-item queries.

MCP (`zotero-mcp-server`) is a useful optional overlay for HITL sessions but the harness never depends on it for correctness.

**API layer**: Zotero Web API v3 (REST, JSON). No wrapper library — stdlib HTTP suffices. 
**Local reads**: Zotero SQLite via `?immutable=1`. Already in `~/.claude/scripts/zotero-import.py`. 
**Credentials**: `~/.config/keys/<project>.env` as `KEY=VALUE`.

### 6. Multi-library access

Own library: `users/{uid}`, writes allowed.

Foreign group (Base R2DS, archiveCIRED group): `groups/{gid}`, **read-only**. Group-scoped API key required. Writes are always guarded to `users/{uid}`. Validate library string format early; fail fast on malformed input.

---

## Safety contract

Every mutating skill must:

1. Fetch and save current state to `outputs/zotero-backups/<skill>-<ISO8601>.json` before writing.
2. Output a RIS file of desired state; never write directly.
3. Apply with `If-Unmodified-Since-Version` — reject on concurrent edit.
4. Dry-run by default; `--apply` requires the backup path.
5. In autonomous/background sessions: auto-apply only high-confidence changes; write low-confidence proposals to the RIS ledger and stop. Never block waiting for input.

---

## Existing skill

`zotero-import` — PDF → metadata extraction → RIS → `xdg-open`. Entry point for new items.

---

## Capabilities to add (by use case, in order of concrete need)

| Capability | Use case | Trigger |
|---|---|---|
| **Lint** — normalize field formats (date ISO 8601, DOI prefix, pages en-dash, language code) | archiveCIRED | First normalization ticket |
| **Enrich** — fill missing fields from CrossRef / HAL / OpenAlex; outputs RIS | archiveCIRED | Tickets 0022–0023 |
| **Upload PDF** — attach local archive files to existing Zotero stubs (authorize → multipart → register, idempotent on md5) | archiveCIRED | Ticket 0030 |
| **Find PDF** — Unpaywall lookup + attach; jurisdiction gate before grey-web | archiveCIRED | Ticket 0037 |
| **OCR** — scanned PDF → text attachment via Mistral | archiveCIRED | Ticket 0006 |
| **Export** — filtered CSL-JSON or RIS by collection/tag/year | CIRED.digital, activity report | RAG schema finalized or report cycle starts |
| **Key sync** — import `Ha-Duong.bib` citation keys into Zotero Extra field | Publications list | Next homepage refresh; `update-publist` is the sanctioned write path |
| **Dedup** — candidate pairs + HITL merge; auto-apply DOI-exact matches only | archiveCIRED, publications list | When second project triggers it |

Each capability: one script, one skill, no shared framework beyond the RIS contract.

