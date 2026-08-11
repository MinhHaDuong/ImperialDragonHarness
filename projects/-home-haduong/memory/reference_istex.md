---
name: istex-access-token
description: "Jeton ISTEX (licences nationales, plein texte) dans ~/.config/keys/istex.env — à essayer d'office pour tout article sous péage"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 31e0f615-0318-44e3-867d-b6d3561e018f
  modified: 2026-08-11T08:06:41.235Z
---

ISTEX (https://api.istex.fr) : archive plein-texte des licences nationales
françaises. Jeton dans `~/.config/keys/istex.env` (`ISTEX_ACCESSTOKEN`),
header `Authorization: Bearer …`. Ne jamais afficher la valeur.

Requêtes : `GET /document/?q=…` (Lucene : `doi:"…"`, `title:"…"`,
`host.title:"…"`, `author.name:…`), plein texte via
`/document/{id}/fulltext/pdf`. Utiliser `curl -G --data-urlencode` (les
guillemets nus dans l'URL font échouer la requête).

À essayer **avant** de conclure « accès institutionnel requis » pour un
article sous péage — après docs/ et Zotero ([[check-docs-staging-before-inaccessible]],
règle `~/.claude/rules/edm.md`). L'auteur l'a rappelé lui-même le
2026-08-11 (« Did you try my ISTEX token? »).

Couverture non uniforme : *JRSS-B* n'y commence qu'en 1997 (vérifié
2026-08-11, chasse Smith 1961 — négatif) ; les backfiles anciens varient
par éditeur. Fonds Elsevier riche et récent : *JME* 2016 tiré en plein
texte le 2026-08-11 (Shiozawa, premier usage productif — le PDF servi par
`/fulltext/pdf` est l'édition éditeur native). Autres clés d'accès documentaire voisines dans
`~/.config/keys/` : `hal.env`, `openalex.env`, `semanticscholar.env`,
`zotero.env` ([[Zotero library]]).
