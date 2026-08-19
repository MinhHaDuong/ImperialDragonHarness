---
name: reference-doifetch
description: "L'outil DOIfetch existe (~/CNRS/code/DOIfetch) — chaîne DOI→PDF complète (Crossref, Unpaywall, HAL, ISTEX, Sci-Hub optionnel), à utiliser au lieu de refaire la chaîne en curl ad hoc"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 2fc3dc8b-b805-4b6c-8808-12e722dfd4c1
  modified: 2026-08-19T10:15:53.659Z
---

**`~/CNRS/code/DOIfetch`** — outil personnel de l'auteur pour l'acquisition de
fulltexts par lot. Dépôt git autonome, Python, `uv run fetch.py`.

- **Entrées** : DOI (chaîne Crossref → Unpaywall → HAL → ISTEX → Sci-Hub, dans
  cet ordre), ISBN (Library Genesis), URL directes ; fichiers de références en
  Excel/CSV/texte dans `references/`.
- **Sélection de canal** : `--source crossref|unpaywall|hal|istex|…` — pour une
  passe strictement licite, énumérer les canaux voulus et NE PAS laisser courir
  jusqu'à Sci-Hub : le choix du canal d'acquisition revient à l'auteur (règle
  EDM).
- **Dédoublonnage Zotero** automatique quand `ZOTERO_DB_PATH` est posé ;
  `ISTEX_ACCESSTOKEN` attendu en environnement (jeton dans
  `~/.config/keys/istex.env`).
- Multithread, retries, rotation de domaines, mise à jour du statut dans le
  fichier d'entrée.
- **Limite connue : `fetch_ezproxy.py` (EZPROXY_BASE + cookies.txt) ne
  fonctionne pas sur BibCNRS.** La passerelle `bib.cnrs.fr` est une SPA en
  JavaScript (ticket par session, rien de rendu côté serveur) et un `requests`
  rejoué ne peut pas l'exécuter — indépendamment de la fraîcheur des cookies.
  Détail et contournement (navigateur piloté, cookies tirés de
  `recovery.jsonlz4`) : [[feedback-bibcnrs-ezticket-pas-de-cookies-txt]].

**Why:** le 2026-08-18, trois agents ont réimplémenté cette chaîne à la main en
curl (Kreps/ISTEX, Mundell/archive.org, la passe de re-sourcing
CrossRef+Unpaywall) sans savoir que l'outil existait — il n'est ni dans le
PATH ni dans le dépôt projet, et la question de l'auteur (« on a un script
doifetch ? ») a révélé l'angle mort.

**How to apply:** pour toute passe d'acquisition ou de re-sourcing, commencer
par `~/CNRS/code/DOIfetch` avec les canaux licites explicités ; ne revenir au
curl ad hoc que pour un cas que l'outil ne couvre pas (et le signaler comme
extension candidate). Voir [[reference_zotero]] pour l'API et la collection.
