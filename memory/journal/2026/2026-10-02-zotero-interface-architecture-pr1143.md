# Zotero interface architecture session — PR #1143

2026-10-02. Harness checkout. Session with the author, design conversation
through to merge.

## Context

Starting question: whether to rehome ticket 0485 (Zotero dedup) to another
project. Evolved into a full interface-architecture discussion driven by
"should we use Zoteus via MCP for the whole Zotero interface and drop our own
Zotero skills?"

## Observable events

- Web survey of the Zotero interface landscape (2026-10-02): Zoteus v1.6.x
  (local-first MCP, key-free reads via the desktop app, no hash audit, no
  merge); pyzotero v1.15.x consolidates library + CLI + optional MCP;
  zotero-native-mcp; the smaller MCP servers. Zotero 10 made the local HTTP
  API writable — the 2026-06-24 draft predates that fact.
- Discovery: the author's own search-works-for-zotero project maintains a
  Zoteus fork and upstreamed oscardvs/zoteus#25 (2026-08-28). Semantic
  retrieval is that project's lane; the harness builds nothing there.
- Design agreed with the author: principles headline section (narrow in
  domain not in mode; each skill chooses its transport; options menu for
  general work; hard invariants — no sqlite writes, client-side merges,
  backup → dry-run → apply); decision 5 rewritten from "Backend interface:
  Bash" to "Transports are chosen per skill"; one skill named `zotero` with
  verbs as arguments (precedent: the `reviewers` skill), rejecting a prefixed
  family; `index-source` to be absorbed as import-of-URL rather than renamed;
  EDM acronym retired — the discipline is Zotero-specific, named "Zotero
  management", rule file renamed rules/zotero.md; publications register
  (`Ha-Duong.bib`) named as the exception to Zotero-as-system-of-record.
- 0485 closed: the author arbitrated a sample against the regenerated
  report (266 groups live vs 269 at the 2026-09-25 census), confirming the
  hash-identified duplicates; the cure remains client-side merges
  (right-click → Merge n Items), recorded as a STATE.md author action.
  The ticket's exit criterion was met as written — no scope amendment needed.
- PR #1143 carried the doc revision, rule rename (~15 reference sites),
  0485 closure, and ticket 1018 (consolidation, open). Review panel:
  round 1 (5 seats) — consistency request-changes, six live EDM sites
  survived the "retired" claim; round 2 after the fix — correctness and
  redteam request-changes, the producer's own fix had introduced a bare
  repo-relative script path in a skills docstring that trips
  check-agnostic.sh (CI agnostic-guard). One-line fix with the `$IDH_ROOT`
  form cleared it. Merged as 254280a7 after CI green.
- The docprop seat never reported in either round despite `agent.spawn`
  returning success; it was absent from `agent.list` while its four siblings
  showed live statuses. Round-3 seats vanished from `agent.list` after the
  parent program's polling loop was interrupted. Filed as ticket 1021.
- Sweep: three live ~/.idh references survive in scripts/ (census README,
  check-primary-checkout comment, the agnostic gate's own pattern comments)
  — the gate's jurisdiction is skills/** only. Filed as ticket 1020.

## Outcome

PR #1143 merged (254280a7). 0485 closed and archived; the merge chore is one
STATE.md author action. 1018 (one `zotero` skill, backend scripts/zotero.py),
1020 and 1021 are open in the train. docs/zotero-integration.md now carries
the principles, the transport matrix, the vocabulary and a dated perishable
Annex A (interface landscape).

Decisions recorded in the doc itself; not repeated here.
