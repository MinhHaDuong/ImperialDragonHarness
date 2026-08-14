---
name: feedback-chercher-le-contenu-pas-le-vocabulaire
description: Un grep de vocabulaire ne décide pas si une source porte un théorème ; ce papier repose précisément sur des énoncés dont les mots manquent
metadata: 
  node_type: memory
  type: feedback
  originSessionId: fabedda1-8499-450e-be83-824460d60108
  modified: 2026-08-14T18:29:07.911Z
---

Pour savoir si une source ancienne porte le théorème, **lire l'énoncé et le
spécialiser**. Ne jamais trancher sur la présence ou l'absence du vocabulaire
— *cycle*, *circuit*, *potential*, *tension*, *network* — dans une extraction.

La raison est propre à ce papier et rend l'erreur inexcusable : **sa thèse est
que le théorème a été énoncé huit fois sans nom commun**, et le §3.6 insiste que
chez Gallai « the words "potential" and "tension" appear nowhere » alors que
l'énoncé y est. Un grep de vocabulaire cherche donc le mot exactement là où le
manuscrit explique que le mot manque. L'instrument nie la thèse qu'il sert.

**Why:** le 2026-08-14, j'ai balayé les 58 pages de Ky Fan (AM-38, 1956) pour
ces mots, trouvé zéro occurrence, et rapporté que sa source « ne peut pas porter
l'équivalence ». Faux. Son Théorème 1 p. 100 dit qu'un système est consistant ssi
toute combinaison non négative annulant les formes annule aussi les seconds
membres — et sur un graphe les combinaisons annulatrices **sont** les
circulations, dont les rayons extrêmes sont les circuits. Les trois cases y
étaient, le circuit sous forme de cône. Gallai lui-même le cite deux fois pour
cela, p. 100, dans sa section finale.

**How to apply:** poser la spécialisation à la main — quelles variables, quelles
formes, que devient le cône annulateur — avant de conclure quoi que ce soit sur
une source. Un grep sert à *localiser* un passage à lire, jamais à rendre un
verdict d'absence. Corollaire : quand une source est déclarée muette, la
question à se poser est « qu'ai-je cherché ? », parce qu'un balayage lexical qui
ne trouve rien est indiscernable d'un balayage qui ne pouvait pas trouver. Voir
[[feedback-grep-context-audit]], [[feedback-affirmation-negative-sur-source]] et
[[feedback-piste-secondaire-lue-sur-piece]].
