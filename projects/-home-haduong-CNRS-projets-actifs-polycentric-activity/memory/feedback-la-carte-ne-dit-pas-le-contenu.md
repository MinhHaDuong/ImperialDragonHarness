---
name: feedback-la-carte-ne-dit-pas-le-contenu
description: "la mise en garde d'un artefact injecté sert à distinguer lu de rapporté, pas à refuser les mauvaises inférences"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 51594d4e-b4b5-4060-a112-a50aed5d0ece
  modified: 2026-08-19T10:38:59.648Z
---

La carte du champ ([[project-carte-du-champ-handbook]]) porte une mise en garde
dans son en-tête *et* dans le pointeur de `CLAUDE.md` : une notice ou une arête
absente renseigne sur le classement de 2016, jamais sur l'idée.

**Ce qu'elle ne sert pas à faire.** À l'épreuve, le modèle *sans aucun accès*
refuse déjà les deux inférences fautives, et les argumente bien (« l'absence
d'un renvoi éditorial à l'absence d'un concept commet une confusion de
niveau »). La mise en garde n'achète donc pas la prudence inférentielle : un
modèle correct l'a sans elle.

**Ce qu'elle sert à faire.** Un agent muni de la carte a signalé de lui-même que
deux de ses réponses reposaient sur la carte et non sur une page ouverte, en
citant la règle en retour — « citer la page et non la carte » — pour dire
lesquelles seraient fragiles si elles devenaient portantes. C'est la distinction
entre *lu* et *rapporté*, qu'un simple relevé de noms aurait effacée.

**Why:** on écrit ces garde-fous en craignant la crédulité inférentielle, qui
est le risque le mieux couvert par le modèle lui-même. Le risque réel est plus
sourd : la source d'une affirmation se perd en route, et rien ne le signale.

**How to apply:** rédiger la mise en garde d'un artefact injecté autour de la
provenance (« router, ouvrir la page, citer la page ») plutôt qu'autour de
l'inférence (« ne concluez pas de l'absence »). Et l'éprouver sur un agent qui
*possède* l'artefact — un bras témoin sans accès ne peut pas montrer ce que la
mise en garde ajoute. Voir aussi
[[feedback-un-controle-rouge-accuse-parfois-le-controle]].
