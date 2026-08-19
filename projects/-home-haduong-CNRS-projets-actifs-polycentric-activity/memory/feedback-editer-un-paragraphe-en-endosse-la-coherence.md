---
name: feedback-editer-un-paragraphe-en-endosse-la-coherence
description: "Éditer un paragraphe, même d'une ligne, fait perdre la défense « je diffère la décision » sur tout ce paragraphe"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 1d55babc-872f-4c21-989e-895dee45f553
  modified: 2026-08-17T13:35:03.202Z
---

Différer une décision d'architecture est légitime ; continuer d'éditer le
paragraphe qui la porte ne l'est plus. Toucher une seule ligne d'un paragraphe
en endosse la cohérence entière, et « je n'ai touché qu'une ligne » ne défend
pas contre une contradiction que le reste du paragraphe crée avec ce qu'on
vient d'écrire ailleurs.

**Why:** PR #136 (HET, 2026-08-17) clarifiait l'appendice sur le problème du
transport — la condition de cycle retrouve son contenu sur le graphe résiduel
d'un plan de fret — tout en différant explicitement la décision brut/résiduel
que le 0153 veut uniforme sur les cinq lignes de réseau. Mais la même PR
ajoutait un renvoi dans le paragraphe de raffinements, dont la phrase voisine
affirmait toujours que la moitié cycle ne mord « only once the objects are
rates rather than freights ». Le gate a bloqué là-dessus, à raison : la
défense de report ne couvre pas un paragraphe que la PR édite. Le manuscrit
portait de plus son propre contre-exemple sans le voir — le §3.1 cite le
cross-haulage de Samuelson, qui est exactement un cycle résiduel négatif à
frets tous positifs.

**How to apply:** Avant de clore une PR de prose, relire *en entier* chaque
paragraphe touché, en chassant les affirmations d'exclusivité — « only »,
« never », « always », « seul », « jamais » — que le reste du changement
dément. Puis chercher dans le document ses propres contre-exemples : la
discipline de [[feedback-affirmation-negative-sur-source]] appliquée aux
sources, retournée vers le texte qu'on écrit soi-même. Deux issues seulement :
étendre la correction à tout le paragraphe, ou ne pas y toucher du tout.

Conséquence encore ouverte, à verser au 0153 quand il se débloquera : lire la
ligne planification sur le graphe résiduel fait porter la réduction sur un
graphe **dérivé** `G(x)` et non sur le graphe des données `G`, alors que le
§2.3 revendique que les cinq énoncés réseau se ramènent au théorème « without
residue » et que l'appendice définit « essentially the same » comme le même
certificat sur l'instance restreinte. Changer de graphe n'est pas changer de
noms. Voir [[project-test-de-vacuite-du-cycle]].
