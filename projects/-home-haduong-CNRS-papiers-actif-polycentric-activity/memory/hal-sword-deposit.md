---
name: hal-sword-deposit
description: "Recette de dépôt/mise à jour HAL par l'API SWORD — clés, format AOfr, pièges (202 vs 201, statuts)"
metadata: 
  node_type: memory
  type: reference
  originSessionId: d4618d42-d464-427b-998e-0b3f1d5a765a
---

Dépôt HAL scriptable via SWORD : `POST/PUT https://api.archives-ouvertes.fr/sword/hal[-ID]`,
auth basic depuis `~/.config/keys/hal.env` (`HAL_ID`/`HAL_PASSWORD`), corps =
ZIP {meta.xml AOfr + PDF}, en-têtes `Packaging: http://purl.org/net/sword-types/AOfr`,
`Content-Type: application/zip`, `Content-Disposition: attachment; filename=meta.xml`.
Dry-run avec `X-test: 1` avant tout envoi réel.

**Pièges vécus (2026-07-06) :**
- Sans `<editionStmt><edition><ref type="file" subtype="author" target="doc.pdf"/>`
  pointant le fichier, HAL crée une notice SANS fichier (réponse 202 ; un dépôt
  avec fichier répond 201). Annexe : `<ref type="annex" target="slides.pdf"/>`.
- `GET /sword/hal-ID` (authentifié) donne le statut réel du dépôt : `accept`
  (validé), `verify` (en modération), `update` (renvoyé au déposant — invisible
  du public, facile à rater pendant des mois : hal-05558422 y est resté 4 mois
  parce que le PDF déposé était la version anonyme pour review).
- Référentiels : CIRED = `#struct-1380080`, idHAL `minh-ha-duong`. pdftotext
  laisse des \f (control chars) qui cassent le XML — les strip avant escape().
- hal.science est derrière Anubis (anti-bot) : vérifier les notices par l'API
  (`api.archives-ouvertes.fr/search/?q=halId_s:...`), pas par la page web.

Scripts réutilisables : `make_meta.py` (COMM) et `make_meta_preprint.py` dans
le tmp du job du 2026-07-06 (régénérables au besoin).
