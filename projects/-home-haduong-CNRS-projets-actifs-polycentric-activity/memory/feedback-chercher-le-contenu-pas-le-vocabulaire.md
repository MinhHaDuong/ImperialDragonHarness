---
name: feedback-chercher-le-contenu-pas-le-vocabulaire
description: Un grep de vocabulaire ne décide pas si une source porte un théorème ; ce papier repose précisément sur des énoncés dont les mots manquent
metadata: 
  node_type: memory
  type: feedback
  originSessionId: fabedda1-8499-450e-be83-824460d60108
  modified: 2026-08-18T09:12:35.319Z
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

Récidive le 2026-08-18, sous une autre forme : dans La Porte (éd. 1770), un
chercheur a grepé « arbitrage » (7 occurrences OCR), classé l'exemple p. 627
(une route, deux dates) et affirmé qu'aucun cycle fermé n'existait « dans tout
le volume ». Le « Roulement de Lettre » p. 626 — la page d'en face, un circuit
fermé France→Londres→Amsterdam→France avec test explicite de perte/gain — ne
contient pas le mot, et seul le vérificateur qui lisait la section sur l'image
l'a vu.

**How to apply:** poser la spécialisation à la main — quelles variables, quelles
formes, que devient le cône annulateur — avant de conclure quoi que ce soit sur
une source. Un grep sert à *localiser* un passage à lire, jamais à rendre un
verdict d'absence. Corollaire : quand une source est déclarée muette, la
question à se poser est « qu'ai-je cherché ? », parce qu'un balayage lexical qui
ne trouve rien est indiscernable d'un balayage qui ne pouvait pas trouver. Voir
[[feedback-grep-context-audit]], [[feedback-affirmation-negative-sur-source]] et
[[feedback-piste-secondaire-lue-sur-piece]].
