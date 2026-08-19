---
name: feedback-affirmation-negative-sur-source
description: Une affirmation négative sur une source est la plus fragile du manuscrit ; le texte peut citer les pages mêmes qui la démentent
metadata: 
  node_type: memory
  type: feedback
  originSessionId: fabedda1-8499-450e-be83-824460d60108
  modified: 2026-08-18T10:32:59.157Z
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

**Un marqueur de provenance ne couvre pas une négation, et c'est la forme
récidivante.** Le 2026-08-17 le même défaut a été retrouvé vivant dans
`conception/note-non-unicite-sept-champs.md` l. 437 — « Gallai n'énonce que le
sens suffisant », marqué `[vu, texte intégral]` — alors que la réfutation était
déjà sur main dans le corps de 0150. La légende définit `[vu]` par « le texte
primaire a été ouvert et le passage lu ». Or **une affirmation positive se
vérifie là où elle se trouve, une négative là où elle se réfuterait** : le
*Hilfssatz* est p. 402 et l'équivalence p. 433, dans une section de conclusion
qu'un lecteur venu chercher le lemme n'ouvre pas. Le marqueur a fait son travail
et la négation est passée quand même. Ticket 0210, MR #138.

**Troisième forme, sur le registre et non sur une source : « aucun ticket ne
couvre ceci ».** Le 2026-08-17 le ticket 0220 affirmait que quatre passages du
manuscrit « ne figurent dans aucun des cinq enfants » de l'épique 0150. Faux pour
trois d'entre eux, relevé au gate de la MR #137 : le 0151 listait déjà le
`§3.1 l. 596-714` et `l'introduction l. 78-113`. La négation avait été déduite du
**rayon d'explosion de l'épique**, qui ne les nommait effectivement pas, sans
ouvrir les enfants. Or le rayon dit ce qu'il a mesuré, pas ce que les enfants
couvrent — exactement le rapport entre registre et pièce.

Ce qui a sauvé le fond est une distinction que la correction a fait apparaître :
**lister un intervalle n'est pas en couvrir le contenu.** Le 0151 listait bien le
§3.1, mais son périmètre est le *statut* de la section, non les affirmations
d'unicité qu'elle contient. Le défaut réel n'était donc pas « hors du rayon »
mais « sans propriétaire », ce qui est plus juste et plus utile. Voir
[[feedback-intervalle-liste-nest-pas-perimetre]].

**Quatrième forme, la négation sur un lot de sources dont une n'a pas été
lue — et la garantie qui l'aggrave.** Le 2026-08-17 la § 10 de
`conception/checklist-venue-ejhet.md` affirmait « zéro occurrence sur les sept
articles » d'EJHET. Le relevé n'établissait ce négatif que sur six : le corps de
`10.1080/09672567.2026.2628536` passe par un widget PDF rendu côté client
(`<div id="embedded-pdf-target">` vide, un seul `NLM_sec` contre cinq sur le
contrôle `2569327`), et ni le proxy de rendu ni le HTML brut ne le restituent —
seuls résumé, déclaration d'intérêts et notes reviennent. Relevé au tour 1 d'un
`/gaze`, corrigé au tour 2 (MR #139).

**Le signal était dans ma propre sortie et je suis passé à côté :** le lot avait
rendu **25 581 octets pour cet article contre 68 à 138 Ko pour les six autres**.
Dans une récupération en lot, la valeur aberrante de taille *est* la source non
lue. C'est le tell mécanique de cette forme, et il se trie.

Ce qui rend le défaut plus grave que les trois précédents : le paragraphe de
méthode **se vantait** d'avoir écarté la collision « rien trouvé / pas pu
regarder » en relisant le HTML brut. Une garantie affichée dispense le lecteur
de vérifier, donc elle transforme un trou en angle mort. Une méthode qui
proclame son garde-fou doit énumérer ses exceptions, sinon le garde-fou est un
argument d'autorité.

Forme du correctif, à réemployer : restreindre le compte aux pièces
effectivement lues, donner à la source inatteignable **sa propre ligne** nommant
la cause, le contrôle positif et la date de re-vérification, et écrire « non
vérifié par ce canal » et non « non lu » — car l'auteur a peut-être lu l'article
sur papier, et affirmer son absence de lecture reproduirait le défaut qu'on
répare. La ligne invite à nommer le canal, ce qui ramènerait le compte à sept.

**Cinquième forme, la négation d'accès : « resté inaccessible » établi sur un
403.** Le 2026-08-18 un chercheur a conclu « l'édition Rebstock est restée
inaccessible (ResearchGate 403) » — alors que sa propre recherche avait fait
remonter `jphogendijk.nl/ZGAIW/vol22.pdf`, le même dépôt libre à un numéro de
volume près ; `vol10.pdf` y était, et son contenu a renversé le verdict de la
piste. Un 403 est la réponse par défaut d'un hôte aux agents, pas un constat
d'indisponibilité de l'œuvre. Deux obstacles avaient masqué la ressource :
fichier au-dessus de la limite WebFetch (prendre curl) et scan sans couche de
texte (océriser, puis lire les pages décisives sur l'image). Fait réutilisable :
la ZGAIW est intégralement en libre accès sur `jphogendijk.nl/ZGAIW/`.

**How to apply:** dans une récupération en lot, trier les sorties par taille et
ouvrir la plus petite **avant** de conclure quoi que ce soit ; un plancher par
source est le garde mécanique. Traiter toute négation comme une dette de
lecture. Avant de
l'écrire, ouvrir la source ; avant de la garder à la finition, la rouvrir. Borner
la portée — « dans les articles fondateurs de 1956 et 1958 » plutôt que
« jamais » — car une négation datée est vraie et ajoute un fait, là où une
négation universelle est un pari. Et vérifier qu'aucune citation voisine ne
pointe vers ce que la phrase nie : c'est le tell mécanique, et le seul qui se
grep. Le garde du ticket 0130 couvre la forme tabulaire ; la forme en prose
n'est pas mécanisable, elle se lit. Voir [[feedback-grep-context-audit]] et
[[feedback-ligne-sans-clause-disculpatoire]].
