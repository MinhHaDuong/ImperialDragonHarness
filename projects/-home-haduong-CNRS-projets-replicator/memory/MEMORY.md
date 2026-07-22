# Replicator Project Memory

## Objectif
Agent IA qui replique des papiers en economie pour les Replication Games (I4R).

## Plans
4 fichiers dans `plans/` :
- `overview.plan` — decisions arretees, abstractions, tech choices, risques, milestones
- `phase-a.plan` — Part A dataset assembly (**implemente**, 156 tests)
- `phase-b.plan` — Part B agent replicateur (pas commence)
- `phase-c.plan` — Part C boucle d'evaluation (pas commence)

## Code implemente (Part A)
156 tests passent. Package installable via `uv sync --extra dev`.
- `cli.py` — `replicator dataset {fetch,ingest,link,stats,extract,repair,rebuild}`
- `blobs.py` — blob store SHA-256, atomique, URL→hash cache (load_manifest_index)
- `schema.py` — Paper (avec link_confidence, original_reference), paper_families (paper_pairs supprime)
- `db.py` — CRUD, FTS, WAL, family ops (create_family, find_family_original, find_family_members)
- `extract.py` — 3 niveaux (text/structure/markdown), idempotent, ecritures atomiques
- `download.py` — async httpx + curl fallback (NBER/SSRN), retry, rate-limit, validate_pdf
- `sources/` — 6 decouverte (i4r, ideas, econstor, osf, github, rr) + 3 resolution (crossref, unpaywall, scihub)
- `build_dataset.py` — fetch, ingest, link_originals (LLM-first), rebuild, repair

## Modele Familles (remplace Paires)
- paper_families = 1 conversation : original + N replications + N responses + N commentaries
- paper_type enrichi : original | replication_report | discussion_paper | response | commentary
- Classification heuristique (regex) + LLM (paper_role) a l'etape de linking
- paper_pairs deprecated (DDL conserve, code supprime)

## Link originals pipeline (LLM-first)
1. Classifier le type (reanalysis/response/commentary) — skip linking si response/commentary
2. LLM extrait metadonnees original (titre, auteurs, DOI, reference verbatim, paper_role)
3. Snippet : premiers 2000 + derniers 2000 chars ; retry 8000 si need_bibliography
4. Resolution DOI : LLM DOI direct → Crossref title search → DOI extraction texte (fallback)
5. Anti-meta filter (_is_comment_or_replication) + author matching
6. Download : Unpaywall → NBER → SSRN → Publisher (skip paywall) → Sci-Hub → HITL
7. Creation famille + original Paper + family_id sur les deux

## Architecture future (noter, pas implemente)
Pipeline async avec queues fichier/repertoires :
- Ingestion note les metadonnees du papier source
- Linker parcourt la DB, sort liste de references a telecharger
- Service download trouve les papiers (ou non)
- Service ingestion decouvre les PDFs, OCR, extraction, versement en famille
- Possibilite de queues en fichier texte + repertoires watched

## Prochaine etape
- Valider le switch familles : re-link en cours, verifier avec audit
- Verifier type reanalysis a l'ingestion (pas au linking)
- Part B : agent replicateur (voir phase-b.plan)

## Notes techniques
- marker-pdf en extra optionnel (`pip install replicator[marker]`) — pin anthropic<0.47
- Extraction fallback pymupdf4llm fonctionne bien
- Pas de licence Stata — MVP sur R/Python/Julia
- I4R AJAX: `page` et `per_page` (pas `paged`) — 412 entries
- Sci-Hub bloque depuis la France (403), fonctionne avec VPN
- curl necessaire pour NBER/SSRN (TLS fingerprinting bloque httpx)

## Protocole I4R (6 etapes)
1. Reproduction computationnelle  2. Inspection du code  3. Scoping
4. Robustesse (multiverse)  5. Pre-analysis plan  6. Validite externe

## Workflow git
- Ne JAMAIS travailler sur `main` — toujours creer une branche
- Branches courtes (feature branches)
- Avant commit : tests, ruff check, ruff format, sync docs

## Langue
L'utilisateur communique en francais.
