---
name: check-docs-staging-before-inaccessible
description: "Avant de déclarer une source primaire « inaccessible », vérifier le staging EDM local docs/ du dépôt — huit fois sur dix le PDF y était déjà"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 31e0f615-0318-44e3-867d-b6d3561e018f
  modified: 2026-08-11T07:31:27.396Z
---

Dans les dépôts de papiers (discipline EDM : `docs/` = staging des sources,
git-ignoré), les agents de recherche déclarent « inaccessible » des sources
dont le PDF est déjà en staging, parce qu'ils cherchent en ligne sans lister
`docs/` d'abord.

**Coût observé (polycentric_activity, HET, 2026-08-10)** : huit instances en
une session — le « showstopper » E1 (Enke 1951 « hors scan » alors que lu
depuis docs/), puis Enke+Samuelson re-déclarés inaccessibles par la note A2,
puis le balayage /roar en a trouvé cinq de plus (Afriat 1967, Walley 1991,
de Finetti 1937, Galichon 2016, Varian 1982) — dont un faux showstopper et
trois « actions humaines requises » fictives que l'auteur aurait faites à la
main.

**Why:** le staging EDM est invisible pour un agent qui raisonne « recherche
web → payant → inaccessible » ; `docs/` n'est pas dans git, donc pas dans les
greps du dépôt.

**How to apply:** tout prompt d'agent de vérification de sources commence par
« liste `docs/` (et les variantes du nom de l'auteur) **puis interroge
Zotero** avant toute recherche en ligne » ; et toute phrase « resté
inaccessible » dans une note de conception se relit contre `ls docs/` + une
requête Zotero. Un scan sans couche texte n'est pas inaccessible :
`ocrmypdf` est installé. **Règle promue dans `~/.claude/rules/edm.md`**
(directive auteur 2026-08-11, PR harnais `edm-zotero-check`).
