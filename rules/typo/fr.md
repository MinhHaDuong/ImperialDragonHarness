<!-- last-reviewed: 2026-08-14 -->
# Typographie fine — français, livrable rendu

Passe de **finition**, sur un livrable que quelque chose rend. Elle croise deux
axes : la langue du texte et le langage de balisage. Elle présuppose un contenu
gelé — pendant la rédaction, elle est du bruit. Un brouillon que rien ne rend
n'en doit rien, et la passe se fait sur le livrable, jamais rétroactivement sur
le brouillon source.

- **LaTeX : ne rien taper à la main.** `babel`/`polyglossia` française pose les espaces insécables ; les mettre en dur double la correction.
- **Markdown ou HTML rendu en UTF-8 : passe manuelle sur le livrable**, insécable U+00A0 (ou `&nbsp;`), à la finition seulement.
- **Espace insécable avant `: ; ? !`** et à l'intérieur des guillemets « comme ceci ».
- **Séparateur de milliers : espace insécable** (10 000) — jamais le point ni la virgule.
- **Ne pas toucher au mode math** : `$H_0 : f = 0$`, `$G(i,j) := …$` — un `sed` mécanique sur les `:` y produit du faux (polycentric_activity, 2026-08-14 : les quatre faux positifs du seul fichier conforme étaient tous du math).
- **Rendu non UTF-8 ou sortie texte brut : ne rien poser** — l'insécable y devient un octet parasite.
