---
name: feedback-paraphrase-derive-en-session-longue
description: "Avant de déclarer un passage du manuscrit fautif, le rouvrir — une source lue en début de session est reparaphrasée de mémoire cinq heures plus tard, et la paraphrase dérive"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 0d11987a-f98d-4cfd-9894-7ed2b7812d33
  modified: 2026-08-18T09:01:49.254Z
---

Rouvrir le passage **avant** d'écrire qu'il se trompe. Pas le relire dans ses
propres notes : le rouvrir dans le fichier.

**Why:** le 2026-08-17, une note de généalogie a accusé le §2.1 du manuscrit HET
de dater l'héritage partagé de « by 1937, 1951, and a fortiori 1979 » et de se
tromper ainsi de quinze ans. La phrase ne date pas l'héritage : elle date les
trois énoncés de **cône** que le paragraphe *Grading* gradue — de Finetti 1937,
Koopmans 1951, Harrison-Kreps 1979 — et affirme qu'à chacune de ces dates la
séparation convexe était déjà monnaie courante. Elle est juste.

Le défaut n'est pas celui de [[feedback-grep-context-audit]], et c'est ce qui le
rend traître : **le paragraphe avait bien été lu en entier, en début de session.**
Il a été reparaphrasé de mémoire cinq heures plus tard, et la paraphrase a dérivé
d'un énoncé sur trois découvertes vers un énoncé sur une chronologie. L'accusation
a survécu à la rédaction de la note, à son commit, à la rédaction du corps de la
merge request, et n'est tombée qu'au contrôle de fond demandé juste avant le
merge. Coût : trois commits de correction, et une note qui aurait envoyé l'auteur
modifier une phrase correcte d'un manuscrit dont le §3 est paginé à la main.

**How to apply:** toute phrase de la forme « le manuscrit se trompe / dit à tort
/ sous-estime » déclenche un `sed -n` sur le passage entier, y compris son
`\paragraph{}` d'accueil, immédiatement avant de l'écrire. Le test qui tranche :
*de quoi cette phrase parle-t-elle, dans l'économie de son paragraphe ?* Ici les
trois dates étaient celles des trois découvertes graduées, ce que la seule ligne
extraite ne pouvait pas montrer.

Corollaire sur les documents datés : la numérotation de section d'un rapport de
relecture vaut à sa date. Le rapport du panel EJHET du 8 juillet renvoie à un
« §8, régime de stricte positivité » que la restructuration a déplacé en §5.1 ;
reprendre sa numérotation telle quelle a produit, dans la même note, deux renvois
morts. Le rapport reste juste et ne doit pas être corrigé — c'est le lecteur qui
doit revérifier la structure courante.

Deuxième instance, en écriture cette fois (2026-08-18, MR #162) : le motif vaut
aussi pour toute phrase qui **décrit ce qu'une autre section fait** — pas
seulement pour celles qui l'accusent. Une passe locale au §2.3 a écrit « the
name this paper weighs in Section 6.1 attaches to the network instance » sans
rouvrir sec:naming, dont la proposition étend le nom aux huit vocabulaires,
niveau cône compris. Deux rapporteurs indépendants l'ont classée « majeur » ;
le correctif a réconcilié (le sans-nom est l'instance, dans ses huit
vocabulaires). Le déclencheur s'élargit donc : « le manuscrit se trompe » ET
« la section X propose/fait Y » exigent tous deux le `sed -n` sur pièce avant
d'écrire.
