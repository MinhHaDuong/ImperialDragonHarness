---
name: reference-verifier-liens-pdf
description: Voir les URL d'un PDF — pdftotext et un grep de /URI sont tous deux aveugles ; mutool show <pdf> grep les voit
metadata:
  type: reference
---

Un lien de PDF vit dans une **annotation**, pas dans le texte. Trois sondes,
une seule qui voit :

| Sonde | Ce qu'elle voit | Verdict |
|---|---|---|
| `pdftotext f.pdf - \| grep -c "https\?://"` | le texte d'ancre seul | aveugle aux liens |
| `grep -ao "/URI" f.pdf` | rien si les objets sont compressés | aveugle en pratique |
| `mutool show f.pdf grep \| grep /URI` | toutes les annotations | **voit** |

`qpdf --qdf --object-streams=disable` marche aussi, mais échoue en écrivant
hors d'un répertoire autorisé — préférer `mutool`, qui lit sans écrire.

Mesuré le 2026-09-09 sur les dossiers éditeurs : `pdftotext` et le grep brut
disaient 0 ; `mutool` a compté 7 liens dans la version envoyée et 37 dans la
version annotée. L'écart, 30, est exactement le nombre de liens portés par
les notes éditeur que le filtre retire.

Contrôle positif indispensable : lancer la sonde sur un fichier dont on sait
qu'il contient des liens. Voir [[feedback-grep-documents-faux-negatifs]].
