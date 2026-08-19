---
name: feedback-ligatures-cassent-le-grep-pdf
description: "Vérifier le contenu d'un PDF par grep sur pdftotext : les ligatures fi/fl cassent le motif et rendent un faux négatif indiscernable d'un contenu perdu"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 51b629ce-ad49-446f-92d1-4ed23c5d1928
  modified: 2026-08-17T15:48:49.250Z
---

Un `grep` sur la sortie de `pdftotext` rend **zéro** sur tout motif contenant
`fi` ou `fl` : LaTeX compose les ligatures, et l'extraction rend `veriﬁcation`
(U+FB01) et `proﬁt`, non `verification` et `profit`. Deux sondes de vérification
d'union ont ainsi rendu 0 lors de la relecture de la MR #145 (2026-08-17), sur du
contenu parfaitement présent.

**Why:** le faux négatif arrive exactement là où l'on cherche à prouver qu'un
merge n'a rien perdu — donc « 0 occurrence » se lit « le frère a été écrasé »
alors qu'il se lit « ma sonde ne sait pas regarder ». C'est la forme locale de la
règle générale du corpus : un garde dont l'« introuvable » est indiscernable de
« je n'ai pas su regarder » n'est pas un garde. Voir
[[feedback-merge-verifier-le-diff-pas-la-sortie]].

**How to apply:** choisir des motifs sans `fi` ni `fl`, ou replier les ligatures
avant de chercher (`sed 's/\xef\xac\x81/fi/g; s/\xef\xac\x82/fl/g'`). Un marqueur
d'union se choisit donc dans le texte, pas au hasard : préférer une phrase courte
sans ligature. Et devant un 0 inattendu, sonder d'abord un fragment plus court
avant de conclure à une perte de contenu — le même réflexe que
[[feedback-affirmation-negative-sur-source]].

**Variante du 2026-08-18, même classe, autre mécanisme : l'accent dans le
motif.** Une sonde `grep 'Bessière'` sur un `.tex` a rendu 0 pendant la
vérification d'union de la MR #174 — l'occurrence existait, la sonde échouait
sur l'encodage (è UTF-8 côté motif shell, `Bessi\`ere` échappé côté LaTeX).
Le remède qui a tranché : comparer des **comptes des deux côtés du merge** sur
un radical ASCII (`grep -ci 'bessi'` sur main ET sur la branche — comptes
égaux, union prouvée). Un marqueur d'union se choisit ASCII pur, et un zéro
sur motif accentué est une sonde aveugle avant d'être une perte.
