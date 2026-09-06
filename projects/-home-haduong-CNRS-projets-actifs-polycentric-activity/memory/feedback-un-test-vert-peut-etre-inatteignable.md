---
name: feedback-un-test-vert-peut-etre-inatteignable
description: "un test peut passer parce que le défaut qu'il nomme ne peut pas l'atteindre ; seule la mutation le dit"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 51594d4e-b4b5-4060-a112-a50aed5d0ece
  modified: 2026-08-19T20:22:42.959Z
---

Le test de traversée de `knowledge_hints.py` est passé **deux fois de suite**
contre un défaut vivant (2026-08-19).

Première version : il cherchait un fichier `escape`, alors que le code suffixe
`.{id}` — l'échappée réelle s'appelait `escape.het-field-map`, un nom que
l'assertion ne pouvait trouver ni avec ni sans le défaut. Deuxième version,
réécrite en balayage : le `TMPDIR` de la sonde était si haut que l'échappée
atterrissait *au-dessus* de l'arbre inspecté. Vert les deux fois, et la
désinfection pouvait être supprimée sans que rien ne rougisse.

Trouvé en mutant : retirer le garde, relancer, exiger le rouge. Sur six gardes,
quatre discriminaient, deux non — et ces deux-là pour une raison qui n'était pas
un oubli : l'enveloppe qui empêche toute sortie non nulle rend le comportement
planté identique au comportement gardé, donc **aucune épreuve en boîte noire ne
peut les séparer**. Elles ont reçu un test à la fonction.

**Why:** c'est la version côté test de la leçon que ce corpus porte déjà côté
outil ([[feedback-un-controle-rouge-accuse-parfois-le-controle]]) : un vert ne
prouve que le vert. Un test qui nomme un garde sans pouvoir échouer sans lui
est une décoration, et il est *plus* dangereux qu'une absence de test, parce
qu'il éteint la question.

**How to apply:** pour tout test écrit contre un défaut de sécurité ou de
confinement, muter le garde et exiger le rouge avant de committer. Et committer
*avant* de muter : la boucle de mutation fait `git checkout --`, qui a effacé
ici quatre correctifs non commités ([[feedback-checkout-ref-ecrase-l-index]]).
