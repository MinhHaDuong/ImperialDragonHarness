---
name: feedback-affirmation-negative-sur-source
description: Une affirmation négative sur une source est la plus fragile du manuscrit ; le texte peut citer les pages mêmes qui la démentent
metadata: 
  node_type: memory
  type: feedback
  originSessionId: fabedda1-8499-450e-be83-824460d60108
  modified: 2026-08-14T17:52:28.317Z
---

Dans un papier d'histoire de la pensée, la phrase la plus exposée n'est pas
celle qui attribue, c'est celle qui **nie** : « the converse is not written »,
« the words appear nowhere », « nowhere registers », « no author of the
communities ». Une attribution fausse se corrige ; une négation fausse détruit
la crédibilité de tout l'appareil, parce qu'un referee qui trouve **une seule**
contre-instance sait que personne n'a regardé.

Deux formes, inégalement dangereuses :

- **La négation bornée** — « cette conférence ne mentionne pas Kantorovitch,
  n'ayant aucune bibliographie ». Elle porte sa propre preuve et se vérifie.
- **La négation universelle** — « l'appareil de Koopmans n'enregistre nulle
  part le programme viennois ». Portée sur un corpus entier, invérifiable en
  pratique, indéfendable en cas de contre-exemple.

**Why:** le §3.6 affirmait de Gallai que « the converse is not written ». C'était
faux deux fois — le télescopage est écrit p. 404, l'équivalence complète p. 433 —
et le manuscrit **citait déjà `\citep[pp.~431--433]{Gallai1958}` vingt lignes
plus loin**. Il renvoyait donc le lecteur aux pages qui le démentaient. Le défaut
n'a été vu qu'en ouvrant Gallai, jamais en relisant le manuscrit (PR #127,
2026-08-14).

**How to apply:** traiter toute négation comme une dette de lecture. Avant de
l'écrire, ouvrir la source ; avant de la garder à la finition, la rouvrir. Borner
la portée — « dans les articles fondateurs de 1956 et 1958 » plutôt que
« jamais » — car une négation datée est vraie et ajoute un fait, là où une
négation universelle est un pari. Et vérifier qu'aucune citation voisine ne
pointe vers ce que la phrase nie : c'est le tell mécanique, et le seul qui se
grep. Le garde du ticket 0130 couvre la forme tabulaire ; la forme en prose
n'est pas mécanisable, elle se lit. Voir [[feedback-grep-context-audit]] et
[[feedback-ligne-sans-clause-disculpatoire]].
