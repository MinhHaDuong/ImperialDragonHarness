---
name: haduong-paper-collaboration-style
description: "Style de collaboration de l'auteur sur la rédaction du manuscrit (tête/mains, refs vérifiées)"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 0f61934e-c102-4e42-a963-03726cd52664
---

Sur la rédaction du manuscrit, l'auteur (Minh Hà-Duong) cadre les rôles :
« tu es la tête, je suis les mains » — surtout sur la prose et la rhétorique.

**Why :** la voix de l'auteur lui appartient ; il veut un avis éditorial franc,
pas une réécriture silencieuse.

**How to apply :**
- Sur le fond/argument : proposer, recommander, donner l'avis éditorial — ne pas
  substituer. Quand il dit « vas-y toi » ou colle un texte, alors appliquer.
- Références : **toujours vérifier les DOI par le web avant de citer** ; il valorise
  la précision bibliographique. Écarter une source douteuse plutôt que la deviner.
- Distinguer **vocabulaire technique vs polémique** : ne pas « nettoyer » un terme
  de métier (ex. « co-produits fatals » = inévitables, à conserver) en croyant
  adoucir le ton. Signaler la distinction.
- Figures : SVG vectoriel, **script générateur séparé** du fichier image, libellés
  **neutres et en bas-de-casse** (pas d'ALL CAPS). Acter une source unique
  (script OU svg) pour éviter l'écrasement.
- **Standard HPE pour les figures de généalogie** (fixé le 2026-07-06) : une
  flèche pleine = le texte cible dit LUI-MÊME descendre de la source (citation,
  préface) ; pointillé = historiographie nommée ; sinon retirer. Vérification
  par workflow un-agent-par-flèche : très efficace (13 flèches → 6 requalifiées,
  1 affirmation du manuscrit réfutée). Réutiliser ce patron.
- **Un fichier de travail daté (`travail-HDM-AAAAMMJJ.odt`) est FIGÉ dès qu'il
  est envoyé à Pierre.** Toute édition postérieure ouvre le fichier du jour
  (copier, mettre la date interne de la page de titre au jour, puis éditer).
  Faute du 2026-07-07 (édition du 20260706 déjà envoyé) — restauré au byte
  près en inversant l'édit connu depuis l'ODT courant : les scratchpads /tmp
  peuvent être écrits par des forks parallèles, ne jamais s'y fier pour
  restaurer.
- **Vérifier le CONTENU d'une source, pas seulement son existence** : la
  référence Simon 1978 existait bien mais ne contenait pas le passage BESOM —
  la citation précise est entrée dans le manuscrit avant d'être réfutée sur
  texte intégral, puis corrigée deux fois. Pour toute attribution issue de ma
  mémoire : lire le texte primaire AVANT de l'écrire dans le manuscrit.
- **Alan Manne est au panthéon personnel de Minh** (dit le 2026-07-07 en
  approuvant sa mise en avant dans la Figure 1). Dans les arbitrages
  éditoriaux : ne pas couper les mentions de Manne ; quand la généalogie le
  permet au standard HPE, lui donner sa place de connecteur (l'apport Cowles
  à Manne — chap. Dahan ; Häfele-Manne 1974 → MESSAGE ; MARKAL-MACRO 1992
  avec Wene ; GAMS/résolution de DICE).
- Il travaille en français, sur machine `doudou` (DISPLAY :0) — on peut lui ouvrir
  fichiers à l'écran (eog, Papers, Inkscape) avec `setsid -f`.

Voir [[oeconomia-paper-status]] et [[odt-edit-via-unzip]].
