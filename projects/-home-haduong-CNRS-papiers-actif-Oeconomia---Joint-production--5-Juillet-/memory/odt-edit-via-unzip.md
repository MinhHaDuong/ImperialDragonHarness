---
name: odt-edit-via-unzip
description: "Comment éditer un .odt programmatiquement (unzip content.xml, rezip, régénérer le PDF)"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 0f61934e-c102-4e42-a963-03726cd52664
---

Pour éditer un manuscrit `.odt` sans LibreOffice GUI : `unzip` dans un dossier de
travail, modifier `content.xml` (texte) et `styles.xml` (polices/tailles), puis
rezip.

**Why :** ce projet est un manuscrit ODT, pas du code ; les remplacements précis
de chaînes (coquilles, références, casse) se font par script Python sur le XML.

**How to apply :**
- Localiser les chaînes avec `find`/regex sur `content.xml` ; attention aux balises
  `<text:span>` qui coupent les mots, et à l'espace fine insécable U+202F que
  LibreOffice insère avant `:` `;` `?` (typographie FR).
- Rezip **mimetype en premier, non compressé** : `zip -X dest.odt mimetype`
  puis `zip -rX dest.odt . -x mimetype`. Valider : `xml.dom.minidom.parseString`.
- Régénérer le PDF : `soffice --headless --convert-to pdf --outdir . fichier.odt`.
- **Piège** : quand l'auteur édite le .odt à la main, ré-extraire depuis le .odt
  sur disque avant d'éditer — les extractions précédentes en /tmp sont périmées et
  les réutiliser écraserait son travail.
- **Hygiène des aiguilles** (leçon du 2026-07-06, ~6 allers-retours perdus) :
  avant de construire une chaîne de remplacement, TOUJOURS `grep -o`/`repr()` la
  zone cible — apostrophes ’ vs ' vs `&apos;`, espaces insécables U+00A0/U+202F
  avant `:;?!»`, et `<text:span>` qui coupent au milieu des mots font échouer
  les needles « évidentes ». Scripts tout-ou-rien : `assert count == 1` sur
  chaque needle, `minidom.parseString` AVANT `open(...,'w')` — un assert qui
  échoue laisse alors le fichier intact (vérifié plusieurs fois ce jour).
- **Insérer une image** : fichier dans `Pictures/`, entrée dans
  `META-INF/manifest.xml`, `<draw:frame text:anchor-type="as-char">` dans un
  paragraphe dédié.
- **Figure pleine page paysage : VRAIE page paysage, jamais d'image
  pré-tournée** (« exiger un angle droit du cou, c'est dire que ce n'est pas
  la peine de lire » — MHD, 2026-07-07 ; la version pré-tournée du 6/7 était
  la solution paresseuse). Méthode : le doc LibreOffice a souvent déjà un
  master « Landscape » dans styles.xml ; sinon le créer. Ajouter
  `style:master-page-name="Landscape"` au style du paragraphe de légende
  (déclenche le saut de page paysage), image NON tournée dimensionnée pour
  l'utile couché (A4 marges 2 cm : 25,7 × 17 cm ; avec légende → ~23,7 ×
  15,8 cm), puis un style `master-page-name="Standard"` sur le paragraphe
  suivant pour revenir au portrait.

Voir [[oeconomia-paper-status]].
