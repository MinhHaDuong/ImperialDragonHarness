---
name: project-zotero-dois-manquants
description: "Neuf items Zotero n'avaient pas le DOI que refs.bib porte — écart refermé ; l'enrichissement d'un item existant reste en MR ouverte, pas encore sur main"
metadata: 
  node_type: memory
  type: project
  originSessionId: 277b597a-6ee8-4d6c-8821-ab09a6962263
  modified: 2026-08-19T10:15:43.193Z
---

Mesuré le 2026-08-18 : sur les entrées de `refs.bib` munies d'un DOI et
rapprochables d'un item Zotero par titre normalisé, **neuf items n'avaient pas
ce DOI**. `Koopmans1949`, puis `AngerisEvansChitraBoyd2022`,
`BoldyrevKirtchik2017`, `DanosEtAl2021`, `Dorfman1984`, `Koopmans1960note`,
`Leontief1937`, `Leontief1970`, `WangEtAl2022`.

**Écart refermé le jour même : la mesure rejouée rend 0.**

Ce que ces neuf ont révélé compte plus que les neuf : le skill `zotero-import`
savait **créer** un item, pas **enrichir** un item existant. `match` signalait
l'item comme présent et le flux s'arrêtait là, si bien qu'une fiche incomplète
le restait indéfiniment — un système de référence moins complet que le staging
qu'il remplace. Une sous-commande `enrich` a été proposée (harnais, PR #758)
mais **reste ouverte, non mergée** — vérifié sur `origin/main` le 2026-08-19 :
`scripts/zotero-import.py` n'y a ni `enrich` ni aucune trace du mot. Tant que
la PR n'atterrit pas, une fiche incomplète reste incomplète — comme au
2026-08-18.

**Why:** l'écart ne bloquait aucune fusion et ne changeait aucun rendu, puisque
c'est `refs.bib` que le manuscrit imprime — donc sous le plancher de sévérité,
rapporté et non ticketé. Mais la règle EDM fait de Zotero le système de
référence, et c'est cette règle-là qui rendait l'écart anormal.

**How to apply:** pour refaire la mesure, rapprocher `refs.bib` et Zotero par
titre normalisé puis **revérifier chaque candidat via l'API** — la base locale
`zotero.sqlite` ne reflète pas les écritures tant que le client de bureau n'a
pas synchronisé, si bien qu'une fiche corrigée le matin ressort comme un trou
l'après-midi. Et vérifier tout DOI avant de l'écrire, par la page
d'atterrissage et non le code retour : recopier depuis `refs.bib` propagerait
l'erreur qui s'y trouve. Un 403 de l'ACM sur une requête HEAD est un blocage
anti-robot, pas un DOI irrésolu — le noter comme tel.
