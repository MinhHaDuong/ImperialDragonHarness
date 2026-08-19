---
name: feedback-artefact-genere-perime-en-silence
description: Un artefact généré committé ne se garde pas aux horodatages ; seule une régénération comparée au contenu prouve sa fraîcheur
metadata: 
  node_type: memory
  type: feedback
  originSessionId: be79e9f1-77d8-4519-968a-dfbe564392eb
  modified: 2026-08-17T15:25:56.636Z
---

**`make` ne peut pas garder la fraîcheur d'un artefact généré committé.** Sa
règle peut avoir la bonne forme — cible réelle, prérequis corrects — et rester
aveugle : après un `checkout`, un `merge` ou la création d'un worktree, tous les
fichiers portent la même heure, et `make` répond « rien à faire » quelle que
soit la provenance du fichier committé.

**Why:** sur `polycentric_activity` (2026-08-17), trois commits du manuscrit HET
sont entrés par une intégration de `origin/main` ; `make complexity` n'a rien
vu ; le rapport committé annonçait 124 paragraphes pour un manuscrit qui en
avait 127. L'écart traversait une borne publiée — la part de texte dense passait
de 30,6 % à 29,9 %, franchissant le seuil autour duquel une note construisait
son argument. Le défaut est revenu **trois fois en une journée**, parce que
`main` bougeait pendant la revue.

**How to apply:** écrire un garde qui régénère et compare le CONTENU, accroché à
la passe d'adhérence et non au chemin du rendu — un instrument cassé ne doit pas
empêcher de compiler. Neutraliser ce qui change sans que le contenu bouge (date
de génération, date d'un PDF matplotlib) : un garde qui rougit tous les matins
est un garde qu'on éteint. Exercer le chemin rouge à l'installation.
Réintégrer `main` et régénérer **juste avant** la fusion, pas au début de la
revue. Référence : `scripts/check_complexity_reports.sh`, ticket 0250 pour la
figure du manuscrit.

Deux corollaires vus le même jour. Une constante recopiée d'une configuration
vers du code vieillit pareillement en silence — et un seuil lié à un *rang*
plutôt qu'à un *code* est la même faute déguisée. Et un chiffre qui bascule
d'un côté ou de l'autre d'une borne au fil des retouches ne porte aucune
conclusion : lire le percentile, qui ne dépend pas d'un seuil.

**Le garde court désormais en CI** (0280 arbitré le 2026-08-18, MR #152 :
workflow `check-adherence` sur chaque MR et chaque push de main) — et la
fréquence prédite s'est confirmée le jour même : **quatre MR de sessions
différentes sont arrivées rouges pour la même cause** (#162, #130, #171, plus
le main rouge réparé en préalable du raid), chacune un manuscrit édité sans
régénérer son rapport. La règle opérationnelle a donc changé de forme : toute
MR qui touche un manuscrit régénère `make complexity` **dans la même MR** —
c'est la première chose à écrire dans la directive d'un exécuteur de prose, et
le premier réflexe du MOE devant un `check-adherence` rouge (avant de chercher
plus loin : neuf fois sur dix c'est le rapport).

Même famille que [[feedback-merge-verifier-le-diff-pas-la-sortie]] et
[[feedback-controle-cadence-glob-etroit]] : un garde dont le « tout va bien »
est indiscernable de « je n'ai pas regardé ».
