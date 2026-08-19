---
name: feedback-fusion-au-mieux-liste-de-revue
description: "Mode d'arbitrage de vague arbitré par l'auteur — tout fusionner au mieux, livrer un PDF final et une liste de points de revue committée, plutôt qu'un arbitrage PDF par MR"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 2fc3dc8b-b805-4b6c-8808-12e722dfd4c1
  modified: 2026-08-18T11:42:23.179Z
---

**« Je préfère tout fusionner au mieux, avoir un PDF final et à côté une liste
de points à vérifier. »** Arbitrage rendu le 2026-08-18, au deuxième enfant de
la vague 0150, et tenu jusqu'au bout : douze MR de manuscrit fusionnées sans
retour à l'auteur, une seule lecture groupée à la fin.

**Why:** l'attention de l'auteur est la ressource rare. L'arbitrage sur PDF par
MR sérialise la vague sur son agenda — chaque enfant attend sa lecture. Après
un ou deux arbitrages initiaux qui établissent la confiance (0151 fut arbitré
plein : placement, titre, options), le reste de la vague coule au rythme des
exécuteurs, et la lecture humaine se fait une fois, sur l'état final, mieux
outillée.

**How to apply:**
- La liste est un fichier committé (`conception/points-revue-vague-NNNN.md`),
  pas un message de chat : chaque MR fusionnée y verse ses points-auteur,
  chaque point cite sa MR d'origine, les pages se relisent sur le PDF final.
- Un point traité se **barre et s'annote** (date + preuve), il ne disparaît
  jamais — un traité doit se voir comme traité (convention posée par une
  session sœur, adoptée).
- Les cases « validé par l'auteur sur PDF » des tickets migrent vers la liste :
  le ticket peut se fermer à la fusion, la validation vit dans la liste — sauf
  critère de sortie substantiel non tenu, auquel cas `Ticket-ref:` et le ticket
  reste ouvert (0152, garde mécanique).
- Le MOE vérifie mécaniquement chaque MR avant fusion (périmètre, CI,
  orthographe, pagination comparée, citations sur pièce) — la liste ne porte
  que ce que la machine ne peut pas juger.
- Proposer ce mode, ne jamais le présumer : c'est un arbitrage d'auteur, rendu
  en cours de vague, révocable (« Hold on 162, review started » l'a suspendu
  ponctuellement pour une MR que l'auteur voulait voir revue autrement).

Voir [[feedback-no-inverted-centaur]] (ce qui reste à l'auteur est l'arbitrage,
pas le contrôle) et [[feedback-rapports-trop-detailles]] (le détail va dans
l'artefact).
