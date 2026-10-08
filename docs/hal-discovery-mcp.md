# HAL Discovery MCP — optional discovery transport

Verified against [HAL documentation](https://doc.hal.science/mcp/) on 2026-10-08.
HAL describes this official service as experimental.

## Scope and use

HAL Discovery exposes public HAL metadata, including abstracts, through ten
MCP tools: topic publications; author lookup, publications and affiliations;
structure lookup, publications and topics; ANR/European project lookup and
publications; and a free-form Solr search (`hal_solr_search`). The latter returns
its query and a link for rerunning it. It does not retrieve document full text
or deposit or modify publications.

Use it optionally for interactive literature discovery, French theses and gray
literature, and exploration of research actors and funded projects. It can feed
`biblio-saturation`, `related-work-note` and `critical-lit-review`; it does not
replace their screening, independent search angles or identifier verification.
Save the query, retrieval date and HAL identifiers/URLs in the task's search
record. Follow the existing full-text retrieval and Zotero intake workflows.
Profiles and affiliations reflect deposited records and bounded samples, not a
complete career history. HAL coverage is not exhaustive scholarly coverage.

## Explicit activation only

Endpoint: `https://api.archives-ouvertes.fr/mcp`. HAL requires no authentication
and charges no access fee; the assistant provider may impose subscription or
connector restrictions. Configure the remote HTTP connector only when the
session needs it, using the active runtime's supported MCP interface.

This reference is loaded on demand. IDH does not register the server in default
MCP configuration, install it, import this document into resident rules, or load
its tool schemas at session start. Reading a skill pointer does not activate it.
Keep any trial configuration scoped to the research project/session rather than
a user-wide default, and remove it when the trial ends. No new skill is needed.

## Fallback and verification

If MCP is unavailable, use the [HAL API](https://api.archives-ouvertes.fr/docs/)
directly. HAL recommends direct API calls for data processing, statistics and
visualizations; retain reproducible queries and pagination for batch work.
Verify identifiers, dates, author matches and source records before reuse.
Full text still requires separate retrieval. `update-publist` retains its
existing SWORD deposit and payload-review workflow.

Setup instructions and current tool parameters belong to the
[official guide](https://doc.hal.science/mcp/), not resident harness context.
