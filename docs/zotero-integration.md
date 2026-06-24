# Zotero Integration — IDH Architecture

**Status**: Draft — 2026-06-24  
**Principle**: KISS and YAGNI at all layers.

---

## Reference use cases

Five concrete use cases drive what capabilities actually matter.

**archiveCIRED** — institutional archive, 686 items, French academic papers 1970–2013, scanned PDFs. Needs: bulk enrichment (HAL, OpenAlex, CrossRef), OCR, dedup, multi-library access (own library + group library).

**Publications list** — personal list of research outputs (homepage, CV). Needs: keep bibLaTeX (`refs.bib`), HAL deposits, and Zotero citation keys in sync after each new publication. Zotero is the authoritative source; `update-publist` and `bib-merge` are downstream consumers.

**AEDIST** — energy transition statistical analysis paper. Needs: bibliography management for a manuscript in progress (`refs.bib`), source provenance tracking. `related-work-note` + `refs.bib` already covers this. Zotero adds value only if the manuscript bibliography grows too large to manage by hand.

**CIRED.digital** — RAG over CIRED research corpus. Needs: clean metadata export (title, authors, year, abstract, type, DOI, URL) for ingestion into a retrieval index. Zotero is the source; the RAG pipeline is the consumer. Blocked on index schema.

**Periodic activity report** — annual or biennial researcher activity report (rapport d'activité CNRS/HCERES). Needs: filtered export of recent publications by year/type, formatted for the report template. Zotero is the source; the report is the output.

---

## Backend interface: Bash

All Zotero operations go through Bash-callable Python scripts. No MCP dependency.

**Why Bash, not MCP:**
- The safety contract (backup → dry-run → apply) is expressed as script flags. MCP write tools have no natural slot for this — calls are immediate and opaque.
- Autonomous sessions (`raid`, `nightbeat`, `beat`) run headless; an MCP server may not be up. A script always works.
- The read pattern here is batch (fetch all items, process, emit JSON), not interactive item-by-item queries where MCP shines.

MCP (`zotero-mcp-server`) is a useful optional overlay for HITL sessions — ad-hoc queries, interactive dedup — but the harness never depends on it for correctness.

**API layer**: Zotero Web API v3 (REST, JSON). No wrapper library — stdlib HTTP suffices.  
**Local reads**: Zotero SQLite via `?immutable=1` (works while Zotero is running). Already in `~/.claude/scripts/zotero-import.py`.  
**Credentials**: `~/.config/keys/<project>.env` as `KEY=VALUE`.

---

## Safety contract (every mutating skill)

1. Fetch and save current state to a timestamped JSON backup before writing.
2. Write with `If-Unmodified-Since-Version` — reject on concurrent edit.
3. Dry-run by default. `--apply` requires `--backup` path.

---

## Existing skill

`zotero-import` — PDF → metadata extraction → RIS → `xdg-open`. Entry point for new items.

---

## Capabilities to add (by use case, in order of concrete need)

| Capability | Use case | Trigger |
|---|---|---|
| **Lint** — normalize field formats (date, DOI, pages, language) | archiveCIRED | First normalization ticket |
| **Enrich** — fill missing fields from CrossRef / HAL / OpenAlex | archiveCIRED | Tickets 0022–0023 |
| **Find PDF** — Unpaywall lookup + attach | archiveCIRED | Ticket 0030 |
| **OCR** — scanned PDF → text attachment via Mistral | archiveCIRED | Ticket 0006 |
| **Export (metadata)** — filtered JSON/CSV export by collection/tag/year | CIRED.digital, activity report | RAG schema finalized or report cycle starts |
| **Key sync** — keep citation keys consistent across Zotero / refs.bib / HAL | Publications list | Next homepage refresh |
| **Dedup** — candidate pairs + HITL merge | archiveCIRED, publications list | When second project triggers it |

Each capability: one script, one skill, no shared framework.

---

## Not in scope

- pyzotero — stdlib covers all needs
- MCP server — nothing blocks on it now
- AEDIST — `related-work-note` + `refs.bib` covers it; no Zotero integration needed unless manuscript bibliography exceeds ~100 items

---

## Open questions (for the review)

1. Should client functions (pagination, rate-limit retry, credential loading) move to a harness-level script now, or only when a second project needs them?
2. Does the activity report need a dedicated skill or is a parameterized export enough?
3. What does "Base R2DS read access" concretely require?
