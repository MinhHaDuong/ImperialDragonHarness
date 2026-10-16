# Zotero Integration — IDH Architecture

**Status**: Draft — 2026-06-24, revised 2026-10-16

## Principles

- **Narrow, specialized skills** — narrow in domain, not in mode: one discipline per skill, verbs as arguments, modes share the machinery (harness precedent: the `reviewers` skill). The target surface is one `zotero` skill, not a prefixed family.
- **Each skill chooses the transport best suited to its task** — the local HTTP API or a transport bundled with an MCP overlay — judged on liveness requirement, blast radius, durable artifacts, and dependency footprint.
- **For general work outside the skills**, the harness documents the interface options and lets the session choose. No option is a required dependency.
- **Hard invariants, regardless of transport**: never write `zotero.sqlite`; merges happen in the desktop client; edits to existing items are reported unless `--edit` is passed; creating items is previewed first (`--dry-run`); Zotero itself is the durable record of what was created (ticket 1116 dropped the RIS artifact).
- **Local-only and stateless helper** (decided 2026-10-15, ticket 1113): `scripts/zotero.py` reaches no cloud service and keeps no cache, index or record between runs. Its only stored state is the local API key Zotero grants it (`~/.config/keys/zotero-local.env`, mode 600).
- **API only, never sqlite** (decided 2026-10-16, ticket 1113): every library read goes through the running client's local API; the helper never opens `zotero.sqlite`. When Zotero is not up the helper tries to launch it; if it cannot, it does nothing. In a container it does nothing.
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

### 2. Shared mutation format: entries JSON and edit rows

New items travel as entries JSON (`create-items`), created in Zotero directly through the local API; the RIS writer was dropped (ticket 1116, 2026-10-16), since an item Zotero holds needs no second artifact. Suggested edits to existing items travel as `{itemKey, field, old, new}` rows (`suggest-edits`, `suggest-attachments`, `check-staging`). Applying a delta to existing items is the author's step in the desktop client unless `--edit` is passed. No shared framework needed beyond those two contracts.

### 3. Export format: RIS or CSL-JSON only

No custom formats. CSL-JSON is richer (use for RAG and activity report). RIS is simpler (use when Zotero import/export is the destination). Choose per consumer; never invent a third format.

### 4. Harness-level extraction requires an authorized task

Whether a shared function belongs in the harness is decided by a separately
authorized task, not a Hoard run. Hoard consolidates project memory; it does
not promote code. Brood may implement project improvements and nominate a
change to a named, authorized harness, but does not authorize harness
implementation. Harness work remains a separate task under the existing
authorization.

### 5. Transports are chosen per skill

Zotero exposes these surfaces on the author's machine; a transport is the path a skill takes to them:

| Surface | Client up? | Auth | Writes |
|---|---|---|---|
| Local `zotero.sqlite` (not used by the helper) | No | none | never (invariant) |
| Local HTTP API `127.0.0.1:23119/api/` | Yes | key-free reads, once the user enables "Allow other applications on this computer to communicate with Zotero" (Settings > Advanced); writes need a local API key granted in the client (Allow / Always Allow / Deny) | yes, since Zotero 10.0 (the helper writes only through this surface) |

The zotero skill chose the local API for reads and writes through
Bash-callable Python scripts (pyzotero's local client), and no cloud surface
(ticket 1113; reads moved from sqlite to the local API on 2026-10-16, and
writes from the connector to the local API under the plan-A decision the same
day):

- The safety contract is expressed as script flags (`--dry-run`, an explicit
  `--apply` opt-in, `--edit` for changes to existing items); the outputs are JSON reports, not
  ephemeral tool calls.
- Every read is live: the duplicate guard sees what the client saved a second
  ago, where a sqlite snapshot of a running client could lag it.
- Reads and writes need Zotero running. The helper launches it when it is
  not (never in a container or headless runner, nor with `ZOTERO_NO_LAUNCH`
  set) and waits up to 90 s; when it
  still does not answer, the helper stops the client it launched, the
  command does nothing, exits 75 (`EX_TEMPFAIL`),
  and `check-staging` reports verdict `zotero_unavailable` with exit 0 so an
  unattended sweep reads it as a clean no-op. Autonomous sessions in a
  container therefore never check staging.
- Zotero 10 is the floor for the whole helper (decided 2026-10-16, ticket
  1116): its item JSON reports each stored file's md5, and its local API
  takes writes. Lookups ask Zotero's own search (`q`, `qmode=everything`)
  per key and check the md5 of each work found, so only `report-duplicates`
  lists every attachment, which makes the client hash every stored file: not
  measured on the author's library yet. A read Zotero does not finish in
  time is its own verdict (`zotero_slow`, exit 74), never "unavailable".

The helper uses `pyzotero` (1.16) in local mode for every read and write, so it
hand-rolls no Zotero interface. Writes need a key: on the first write, or on a
401, Zotero shows an Allow / Always Allow / Deny dialog; the helper accepts and
stores only an "Always Allow" key (ticket 1116), and refuses a one-time
"Allow" answer before writing anything. An attachment counts as a stored file only
when Zotero reports its md5 or size: Zotero sends a file URL for every
stored-file attachment, one created without its file included.

An MCP server (recommended overlay: **Zoteus** — see Annex A) is useful for
interactive HITL retrieval: search, PDF passages, CSL citations, add-by-DOI.
It never appears in a skill's correctness path.

### 6. Multi-library access

The default destination and dedup scope is the user library. `create-items --library
<groupID>` or `--collection <key>` targets another editable library, e.g. a
group the author can write to: the item is created directly in the target library (the collection's own
library for `--collection`), whatever the Zotero window shows. A
read-only group cannot be a destination. Validate the library selector early;
fail fast on malformed input.

---

## Safety contract

Every mutating skill must:

1. Never edit an existing item unless `--edit` is passed (`suggest-edits`, `suggest-attachments`, `check-staging --apply --edit`); without it the helper changes no stored item, so there is nothing to back up.
2. Report every item it creates (its key, per entry) in its JSON output.
3. Edits to existing items are reported (item key, field, old → new) by default; they are written only with `--edit`, or applied by the author in the client.
4. Preview before creating (`create-items --dry-run`); unattended creation requires the project opt-in (`check-staging --apply` with `.zotero-reconcile.json`).
5. In autonomous/background sessions: create only high-confidence new items; write low-confidence proposals to a JSON proposal file (the entries) and stop. Never block waiting for input.

---

## Skills

One skill named `zotero`, verbs as arguments — the command surface mirrors the backend script's subcommands. Narrowness is the domain, not the verb count.

| verb | does | backed by (today) |
|---|---|---|
| `import <pdf-or-url>...` | file or URL intake → new items with attachments | `extract-metadata`, `find-work`, `create-items`; URL probing via `probe-url.py` |
| `suggest-edits` | report missing fields on existing items | `suggest-edits` |
| `check-staging` | report staging ↔ library drift, `.bib`-linked files or one directory; repair it with `--apply` | `check-staging` (merges the former two verbs, ticket 1116) |
| `report-duplicates` | hash-dedup report, library against itself, JSON | `report-duplicates` (ticket 0485) |
| `suggest-attachments` | by-hand attachment of a file to an existing stub | `suggest-attachments` (reports only since ticket 1113) |

Ticket 1116 (2026-10-16) gave every subcommand a name that says what it does, with no alias for the former ones: `probe` split into `extract-metadata` (input-format dependent, never needs Zotero) and `find-work` (the library lookup, local API only, which also absorbed `match`); `audit` and `reconcile` became `check-staging`; `attach`, `inject`, `enrich` and `dedup-report` became `suggest-attachments`, `create-items`, `suggest-edits` and `report-duplicates`; `write` (RIS) was dropped. The project opt-in file `.zotero-reconcile.json`, the lair helper `skills/lair/zotero-reconcile-trigger` and the script's internal function names keep their old words on purpose: no command answers to them, and renaming the opt-in file would silently disable existing projects' opt-ins.

This surface ships as one skill — `zotero` (ticket 1018, landed 2026-10-03), driving `scripts/zotero.py`. The former two skills — zotero-import (file intake) and index-source (URL intake) — are consolidated into it. A URL is an input to `import`, not a separate verb or skill.

The duplicate lookup asks Zotero's own search, key by key, strongest first — persistent identifier (DOI, ISBN, arXiv, handle), then the first author's works scored for title similarity with rapidfuzz — and stops at the first key that fires; each work found is checked for a stored file with the same md5 (`storageHash`), which makes the hit exact (ticket 1116 replaced the in-memory cascade over a whole-library read, and dropped its attachment-filename key: Zotero's search does not see attachment filenames). Scope defaults to the **user library**, since that is where `create-items` writes; a copy sitting in a read-only group library does not count as already present. The verdict distinguishes `match` / `ambiguous` / `none` / `unchecked`, so "found nothing" and "could not look" stay apart. When Zotero is not running, nothing is created and the command says so.

## Vocabulary

- **Zotero management** (formerly "EDM") — the discipline in `rules/zotero.md` is Zotero-specific: source documents, notes, and project `.bib` files are all staging flowing into Zotero, the system of record. The bare acronym EDM (elsewhere: Electronic Dance Music) is retired. Exception — the publications register: `Ha-Duong.bib` is its own master with Zotero downstream (decision 1); project `refs.bib` files are staging, `Ha-Duong.bib` is not.
- **import** — intake into the library; a URL is an input, not a distinct concept. **index** is reserved for retrieval indexing — search-works-for-zotero's lane.
- **hash-dedup report** — the attachment-content-hash duplication audit (`report-duplicates`); "dedup" alone is ambiguous.
- **attachment** — the `suggest-attachments` capability: filing a document under an existing item; "attach" alone is a generic verb.

Prose names a skill's operation precisely; command names stay as they are, scoped by the script or skill that carries them.

---

## Capabilities to add (by use case, in order of concrete need)

| Capability | Use case | Trigger |
|---|---|---|
| **Lint** — normalize field formats (date ISO 8601, DOI prefix, pages en-dash, language code) | archiveCIRED | First normalization ticket |
| **Enrich** — fill missing fields from CrossRef / HAL / OpenAlex; outputs suggested edits, written only with `--edit` | archiveCIRED | Unbacked — file on demand |
| ~~**Upload PDF**~~ — attach local archive files to existing Zotero stubs (authorize → multipart → register, idempotent on md5) | archiveCIRED | **Done 2026-08-19, reduced 2026-10-15** — `zotero.py suggest-attachments --parent <itemKey> <file>...` (MR #760, renamed in ticket 1116). The repair for a `check-staging` verdict of `work_present_no_file`, where `create-items` would mint a duplicate. Since ticket 1113 it checks the item and the file and reports the attachment; `--edit` stores it through the local API (Zotero 10.0 or later). |
| **Find PDF** — Unpaywall lookup + attach; jurisdiction gate before grey-web | archiveCIRED | Unbacked — file on demand |
| **OCR** — scanned PDF → text attachment via Mistral | archiveCIRED | Unbacked — file on demand |
| **Export** — filtered CSL-JSON or RIS by collection/tag/year | CIRED.digital, activity report | RAG schema finalized or report cycle starts |
| **Key sync** — import `Ha-Duong.bib` citation keys into Zotero Extra field | Publications list | Next homepage refresh; `update-publist` is the sanctioned write path |
| **Dedup** — candidate pairs + HITL merge; auto-apply hash- and DOI-exact matches only | archiveCIRED, publications list | **Triggered 2026-08-14** — ticket 0485. See also ticket 0570: the same 269 clusters make `classify_matches()`'s untie-broken `exact` tier report one parent and drop the rest in silence. 269 clusters where one file md5 sits under distinct parents in the user library, none of them visible to Zotero's own Duplicate Items pane (it matches title/DOI/ISBN + creators + year, same item type, and never the file hash). Detection reads the library through the local API; the **merge belongs to the desktop client** — no programmatic surface has a merge endpoint, and a Zotero merge is a client-side composite (move children, union collections and tags, trash the losers, write `dc:replaces` on the master; the library already carries 436 such relations). Ticket 0485 closed 2026-10-02: detector and report delivered and live-validated, sample arbitrated; residue — author merges in the client, right-click → Merge n Items. |

Each capability rides one backend script; the library capability is the
one `zotero` skill (verbs, reference files), no shared framework beyond the
entries JSON and edit-row contracts.

The former ticket references in this table (0006, 0022–0023, 0037) were dead — those IDs name unrelated work in both the harness and search-works-for-zotero trackers — and are removed (2026-10-02).

---

## Annex A — Interface landscape, surveyed 2026-10-02

Perishable inventory: tool names and versions rot; re-verify before relying on any entry. Frontends are transports to the three surfaces in decision 5 — what matters is which surface they reach and what they leave behind.

**External discovery** (optional, separate from library access)
- [HAL Discovery MCP](hal-discovery-mcp.md) — official experimental public
  metadata discovery for topics, authors, structures and funded projects.
  Explicit session/project activation only; no default registration or tool
  loading. Full text, Zotero intake and HAL deposit retain their existing paths.

**MCP servers** (interactive HITL retrieval; never a correctness dependency)
- **Zoteus** (`@oscardvs/zoteus`, TypeScript, MIT, v1.6.x, very active) — the recommended overlay: local-first, key-free reads via the desktop app's local API, versioned reversible writes, semantic search over PDFs, CSL citations, add-by-DOI. No attachment-hash audit, no merge composite. The author maintains a fork under search-works-for-zotero and has upstreamed hardening (oscardvs/zoteus#25, 2026-08-28).
- `54yyyu/zotero-mcp` (Python, FastMCP) — sqlite reads, Zotero 10 local writes; ships a companion `zotero-cli`.
- `zotero-native-mcp` — writable local API only, nothing networked.
- danielostrow/zotero-mcp-server, cookjohn, lit-lake, pyzotero's built-in optional MCP — smaller or less current.

**Python libraries**
- **pyzotero** (canonical, active) — cloud and local API (`local=True`), CLI, optional MCP server; one dependency covering three frontends.
- pyzolocal (local sqlite) — stale.

**CLI clients**
- pyzotero-cli (chriscarrollsmith) — pitched as the MCP alternative when shell access exists, since MCP schemas load into context.
- 54yyyu's `zotero-cli`; older edtechhub/jbaiter clients (web-API era, stale).

**Web clients**
- Raw HTTP against the desktop connector — not used by the harness scripts since ticket 1113.
- Zotero's translation-server for identifier→metadata lookups.

**Semantic retrieval** is search-works-for-zotero's lane (`~/CNRS/code/search-works-for-zotero`): requirements, experiments, and upstream contributions toward semantic search in Zotero. The harness builds nothing there and consumes the result through whatever transport wins.


