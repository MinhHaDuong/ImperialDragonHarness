# Zotero Integration — IDH Architecture

**Status**: Draft — 2026-06-24, revised 2026-10-02

## Principles

- **Narrow, specialized skills** — narrow in domain, not in mode: one discipline per skill, verbs as arguments, modes share the machinery (harness precedent: the `reviewers` skill). The target surface is one `zotero` skill, not a prefixed family.
- **Each skill chooses the transport best suited to its task** — local database read, local HTTP API, Web API, or a transport bundled with an MCP overlay — judged on liveness requirement, blast radius, durable artifacts, and dependency footprint.
- **For general work outside the skills**, the harness documents the interface options and lets the session choose. No option is a required dependency.
- **Hard invariants, regardless of transport**: never write `zotero.sqlite`; merges happen in the desktop client; every mutation follows backup → dry-run → apply with durable artifacts.
- **KISS and YAGNI at all layers.**

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

### 5. Transports are chosen per skill

Zotero exposes three surfaces; a transport is the path a skill takes to them:

| Surface | Client up? | Auth | Writes |
|---|---|---|---|
| Local `zotero.sqlite`, read via `?immutable=1` | No | none | never (invariant) |
| Local HTTP API `127.0.0.1:23119/api/` | Yes | key-free reads; user-granted key for writes | yes, since Zotero 10 (new since this doc's first draft) |
| Web API v3 (cloud) | No | API key, rate-limited | yes, but **no merge endpoint anywhere** |

The zotero skill chose sqlite reads + Web API writes through Bash-callable Python
scripts. That is a choice, not a rule — but it is the right one for it:

- The safety contract (backup → dry-run → apply) is expressed as script flags; the
  outputs are durable RIS/report artifacts, not ephemeral tool calls.
- Autonomous sessions (`raid`, `nightbeat`, `beat`) run headless; the sqlite path
  needs no running client and no network.
- The read pattern here is batch, not interactive item-by-item queries.

Stdlib HTTP over a wrapper library is likewise the current choice, not a rule:
`pyzotero` (v1.15.x) reaches the Web API *and* the local API (`local=True`), ships
a CLI, and an optional MCP server — a legitimate alternative transport for a
future skill that wants its maintenance offloaded.

An MCP server (recommended overlay: **Zoteus** — see Annex A) is useful for
interactive HITL retrieval: search, PDF passages, CSL citations, add-by-DOI.
It never appears in a skill's correctness path.

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

## Skills

One skill named `zotero`, verbs as arguments — the command surface mirrors the backend script's subcommands. Narrowness is the domain, not the verb count.

| verb | does | backed by (today) |
|---|---|---|
| `import <pdf-or-url>...` | file or URL intake → new items with attachments | `inject`, `probe`, `match`, `sync-index`; URL probing via `probe-url.py` |
| `enrich` | fill missing fields on existing items | `enrich`, `write` |
| `audit` | report staging ↔ library drift | `audit` |
| `reconcile` | repair the correspondence | `reconcile` |
| `dedup-report` | hash-dedup report, library against itself | `dedup-report` (ticket 0485) |
| `attach` | attachment upload to existing stubs | `attach` (MR #760); declared, created on first need |

This surface ships as one skill — `zotero` (ticket 1018, landed 2026-10-03), driving `scripts/zotero.py`. The former two skills — zotero-import (file intake) and index-source (URL intake) — are consolidated into it. A URL is an input to `import`, not a separate verb or skill.

The dedup cascade consults keys strongest-first — file content hash (`storageHash`), then persistent identifier (DOI, ISBN, arXiv, handle), then attachment filename, then first-author/year/normalised-title, with title Jaccard as last resort — and stops at the first key that fires. Scope defaults to the **user library**, since that is where `inject` writes; a copy sitting in a read-only group library does not count as already present. The verdict distinguishes `match` / `ambiguous` / `none` / `unchecked`, so "found nothing" and "could not look" stay apart. The RIS file is still written as the durable artifact and remains the fallback when no read-write key resolves.

## Vocabulary

- **Zotero management** (formerly "EDM") — the discipline in `rules/zotero.md` is Zotero-specific: source documents, notes, and project `.bib` files are all staging flowing into Zotero, the system of record. The bare acronym EDM (elsewhere: Electronic Dance Music) is retired. Exception — the publications register: `Ha-Duong.bib` is its own master with Zotero downstream (decision 1); project `refs.bib` files are staging, `Ha-Duong.bib` is not.
- **import** — intake into the library; a URL is an input, not a distinct concept. **index** is reserved for retrieval indexing — search-works-for-zotero's lane.
- **hash-dedup report** — the attachment-content-hash duplication audit (`dedup-report`); "dedup" alone is ambiguous.
- **attachment upload** — the `attach` capability; "attach" alone is a generic verb.

Prose names a skill's operation precisely; command names stay as they are, scoped by the script or skill that carries them.

---

## Capabilities to add (by use case, in order of concrete need)

| Capability | Use case | Trigger |
|---|---|---|
| **Lint** — normalize field formats (date ISO 8601, DOI prefix, pages en-dash, language code) | archiveCIRED | First normalization ticket |
| **Enrich** — fill missing fields from CrossRef / HAL / OpenAlex; outputs RIS | archiveCIRED | Unbacked — file on demand |
| ~~**Upload PDF**~~ — attach local archive files to existing Zotero stubs (authorize → multipart → register, idempotent on md5) | archiveCIRED | **Done 2026-08-19** — `zotero.py attach --parent <itemKey> <file>...` (MR #760, delivered under the backend's former name). Exposes the three-step upload `upload_attachment()` already implemented; the repair for an `audit` verdict of `work_present_no_file`, where `inject` would mint a duplicate. |
| **Find PDF** — Unpaywall lookup + attach; jurisdiction gate before grey-web | archiveCIRED | Unbacked — file on demand |
| **OCR** — scanned PDF → text attachment via Mistral | archiveCIRED | Unbacked — file on demand |
| **Export** — filtered CSL-JSON or RIS by collection/tag/year | CIRED.digital, activity report | RAG schema finalized or report cycle starts |
| **Key sync** — import `Ha-Duong.bib` citation keys into Zotero Extra field | Publications list | Next homepage refresh; `update-publist` is the sanctioned write path |
| **Dedup** — candidate pairs + HITL merge; auto-apply hash- and DOI-exact matches only | archiveCIRED, publications list | **Triggered 2026-08-14** — ticket 0485. See also ticket 0570: the same 269 clusters make `classify_matches()`'s untie-broken `exact` tier report one parent and drop the rest in silence. 269 clusters where one file md5 sits under distinct parents in the user library, none of them visible to Zotero's own Duplicate Items pane (it matches title/DOI/ISBN + creators + year, same item type, and never the file hash). Detection reads the local DB; the **merge belongs to the desktop client** — the Web API has no merge endpoint, and a Zotero merge is a client-side composite (move children, union collections and tags, trash the losers, write `dc:replaces` on the master; the library already carries 436 such relations). Ticket 0485 closed 2026-10-02: detector and report delivered and live-validated, sample arbitrated; residue — author merges in the client, right-click → Merge n Items. |

Each capability rides one backend script; the library capability is the
one `zotero` skill (verbs, reference files), no shared framework beyond the
RIS contract.

The former ticket references in this table (0006, 0022–0023, 0037) were dead — those IDs name unrelated work in both the harness and search-works-for-zotero trackers — and are removed (2026-10-02).

---

## Annex A — Interface landscape, surveyed 2026-10-02

Perishable inventory: tool names and versions rot; re-verify before relying on any entry. Frontends are transports to the three surfaces in decision 5 — what matters is which surface they reach and what they leave behind.

**MCP servers** (interactive HITL retrieval; never a correctness dependency)
- **Zoteus** (`@oscardvs/zoteus`, TypeScript, MIT, v1.6.x, very active) — the recommended overlay: local-first, key-free reads via the desktop app's local API, versioned reversible writes, semantic search over PDFs, CSL citations, add-by-DOI. No attachment-hash audit, no merge composite. The author maintains a fork under search-works-for-zotero and has upstreamed hardening (oscardvs/zoteus#25, 2026-08-28).
- `54yyyu/zotero-mcp` (Python, FastMCP) — sqlite reads, Zotero 10 local writes; ships a companion `zotero-cli`.
- `zotero-native-mcp` — writable local API only, nothing networked.
- danielostrow/zotero-mcp-server, cookjohn, lit-lake, pyzotero's built-in optional MCP — smaller or less current.

**Python libraries**
- **pyzotero** (canonical, active) — Web API + local API (`local=True`), CLI, optional MCP server; one dependency covering three frontends.
- pyzolocal (local sqlite) — stale.

**CLI clients**
- pyzotero-cli (chriscarrollsmith) — pitched as the MCP alternative when shell access exists, since MCP schemas load into context.
- 54yyyu's `zotero-cli`; older edtechhub/jbaiter clients (web-API era, stale).

**Web clients**
- Raw HTTP against Web API v3 — what the harness scripts do.
- Zotero's translation-server for identifier→metadata lookups.

**Semantic retrieval** is search-works-for-zotero's lane (`~/CNRS/code/search-works-for-zotero`): requirements, experiments, and upstream contributions toward semantic search in Zotero. The harness builds nothing there and consumes the result through whatever transport wins.


