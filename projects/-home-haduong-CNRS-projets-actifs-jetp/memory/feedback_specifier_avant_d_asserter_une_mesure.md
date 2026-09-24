---
name: feedback-specifier-avant-d-asserter-une-mesure
description: Une mesure dont le chiffre bouge avec sa spécification n'est pas un résultat tant que la spécification n'est pas énoncée.
metadata:
  type: feedback
---

Sur le papier court JETP (2026-09-11), j'ai asserté **trois fois** un résultat
à quatre pays, et je me suis trompé trois fois. Chaque fois, la cause était un
choix de spécification non examiné, et chaque fois c'est l'auteur qui l'a vu.

1. **Population.** Filtrer `instr == "pret"` semblait dire « prêts ». Cela
   disait en réalité « APD seule », donc excluait les prêts IBRD — et avec eux
   l'*Eskom Just Energy Transition Project*, principal prêt-projet du JETP
   sud-africain. Le filtre retenait à sa place une opération AFD codée C01 mais
   décaissée à 100 % l'année de son engagement. D'où un « 87 % sud-africain »
   présenté comme une inversion de la thèse : un artefact.
2. **Dénominateur.** Rapporter le décaissé aux engagements signés ou au paquet
   annoncé ne mesure pas la même chose. Le JETP est une promesse : c'est le
   paquet annoncé.
3. **Horizon.** Les quatre JETP n'ont pas été signés la même année. Un horizon
   uniforme les comptait inégalement.

**Why:** un chiffre obtenu d'un `groupby` a l'air d'une observation. Il est en
fait la sortie d'une chaîne de choix — population, dénominateur, horizon — dont
aucun n'apparaît dans le résultat. Le chiffre se présente donc avec l'autorité
d'une mesure et la fragilité d'une convention.

**How to apply:** avant d'annoncer un chiffre tiré d'un filtre, énoncer les
trois choix et vérifier qu'un cas connu se trouve du bon côté du filtre —
ici, chercher nommément l'Eskom JET Project aurait suffi. Et quand le chiffre
se déplace avec la spécification, le dire : cette sensibilité est un résultat,
et elle justifie qu'un papier porte sur l'étalon plutôt que sur un nombre.
Parent de [[feedback-reverifier-juste-avant-l-acte-destructif]] : dans les deux
cas, un contrôle fait « en gros » ne protège pas de l'acte précis.
