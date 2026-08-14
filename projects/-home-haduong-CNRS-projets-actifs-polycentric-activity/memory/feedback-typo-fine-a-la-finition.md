---
name: feedback-typo-fine-a-la-finition
description: "La typographie fine s'applique à la finition, jamais à la rédaction, et dépend de la langue du texte ET du langage de balisage"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d656551a-8f4e-4a1d-b7f0-2ea8536cf852
  modified: 2026-08-14T08:43:19.885Z
---

La typographie fine (espaces insécables, guillemets « », fines avant `; ? !`)
s'applique **à la finition**, pas à la rédaction. Elle dépend de deux axes,
pas d'un seul : la **langue du texte** ET le **langage de balisage** — de
préférence un balisage qui supporte UTF-8. Un brouillon non rendu ne la porte
pas ; un livrable rendu la porte au moment où son contenu est gelé.

**Why :** appliquer la typographie pendant la rédaction paie un coût certain
pour un bénéfice qui ne s'encaisse qu'au rendu, et souvent jamais. Dans
polycentric_activity (arbitrage auteur du 2026-08-14), les 41 notes
`conception/*.md` totalisaient 3 633 sites candidats pour **un seul** fichier
conforme ; les manuscrits sont en anglais et en LaTeX, où `babel` produit les
insécables tout seul. La clause Markdown de `lang/fr.md` n'avait donc aucune
cible réelle. L'auteur a explicitement refusé le rétro-port : « pas de sed
mécanique qui bouzille tout » — et il avait raison au sens strict, les quatre
faux positifs du fichier conforme étaient tous du math (`$G(i,j) := …$`,
`$H_0 : f = 0$`) qu'un `sed` aurait corrompus.

**How to apply :** en rédaction, écrire en espaces ordinaires et ne pas
s'en soucier. Au moment de la finition d'un livrable *rendu*, décider la passe
typographique en croisant langue et balisage : LaTeX + babel → ne rien taper à
la main ; Markdown ou HTML rendu en UTF-8 → passe manuelle sur le livrable ;
texte non rendu → aucune passe. Ne jamais rétro-porter sur les brouillons
sources d'un livrable : la passe se fait sur le livrable. Le câblage projet vit
dans `<repo>/.claude/rules-map.toml`, qui ne porte que des mappings
chemin → axes. Voir [[project-het-hand-pagination]] pour l'autre décision de
finition différée de ce dépôt.
