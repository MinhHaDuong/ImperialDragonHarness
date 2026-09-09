---
name: capture-source
description: "Archive a web source that blocks automated fetching (403 from Cloudflare, Akamai, publisher bot walls) into a durable citable artifact. Turns a browser print-to-PDF into a reconstituted PDF with reflowed paragraphs, the article's own figures, and a provenance block printed inside the document; verifies coverage sentence by sentence against the capture, then files both PDFs in Zotero with an access date. Third case of the EDM workflow, beside index-source (fetchable URL) and zotero-import (PDF in hand)."
---

# Archiver une source que la machine ne peut pas atteindre

`index-source` suppose une URL récupérable. `zotero-import` suppose un PDF déjà
en main. Ce skill couvre le troisième cas : **la page existe, elle est vivante,
et elle renvoie 403 à tout client automatisé.** Cloudflare, Akamai, les murs
anti-robot des éditeurs. Un navigateur passe ; `curl` avec la meilleure
signature de navigateur du monde ne passe pas.

Le réflexe — « lien suspect, à vérifier à la main » — laisse la source hors du
système de record. Deux ans plus tard elle est morte et il ne reste qu'une URL.

## Quand l'appliquer

Une passe anti-bitrot classe un lien **SUSPECT 403/401/429**, et la
vérification machine échoue dans les deux sens : requête directe, signature de
navigateur, API de l'éditeur sans clé, Internet Archive. Ce n'est pas un lien
mort ; c'est un lien que seule une personne peut ouvrir.

**Ne pas confondre avec un 404.** Un mur anti-robot renvoie une page — défi
Cloudflare (« Just a moment… ») ou refus Akamai (« Access Denied ») —, pas une
absence. Lis le corps de la réponse avant de conclure.

## La chaîne

1. **L'auteur bascule la page en mode lecture, désactive les en-têtes et pieds
   de page d'impression, et imprime en PDF.** Seule étape humaine, dix
   secondes. Le mode lecture n'est pas un confort : c'est lui qui fait la
   qualité de tout ce qui suit (règle 1). Ne pas sauvegarder la « page
   complète » — son répertoire d'accompagnement ne sert à rien (règle 1).
2. **Lire les métadonnées de la page sauvegardée** : `rel="canonical"`,
   `og:url`, `article:published_time`, `og:title`. Voir règle 2.
3. **Reconstituer** avec `~/.claude/skills/capture-source/scripts/reconstitute.py build`.
4. **Vérifier** avec `~/.claude/skills/capture-source/scripts/reconstitute.py verify`, puis regarder le rendu.
5. **Classer** dans Zotero : les deux PDF en pièces jointes du même item, plus
   `accessDate`. Voir règle 5.

## Cinq règles, toutes payées

### 1. C'est le mode lecture qui fait le tri, pas l'impression

**Imprimer depuis le mode lecture du navigateur, jamais depuis la page telle
qu'elle s'affiche.** Le mode lecture jette la navigation, les bandeaux, les
encarts, les vignettes de recommandation, et ne garde que le titre, le texte
et les figures de l'article.

Mesuré sur un article du World Economic Forum : **9 120 mots dans le HTML
complet, 763 dans la capture en mode lecture.** 92 % de la page écartés, et ce
92 % est exactement ce qu'un nettoyage écrit à la main tenterait de retirer.
Côté images, le répertoire de la sauvegarde « page complète » contenait six
fichiers, tous décoratifs, chacun en avif et en webp et en quatre tailles ; la
capture en mode lecture en contenait un, le graphique de données que l'article
commente.

D'où la règle opératoire : **les figures se prennent avec `pdfimages` sur la
capture**, jamais dans un répertoire d'accompagnement — qu'il vaut mieux ne pas
sauvegarder du tout. Un premier passage qui trie les images à la main embarque
les six mauvaises et manque la bonne : 8 pages et 9,8 Mo au lieu de 3 et 184 Ko.

**Corollaire de scope, honnête.** Si la capture est bonne, `build` n'a presque
plus rien à nettoyer, et la valeur du skill se déplace : elle est dans le bloc
de provenance, le contrôle du `rel=canonical`, la date de consultation et le
classement, pas dans le reflux de paragraphes. Une capture prise sans mode
lecture, elle, demande tout le nettoyage — c'est le cas dégradé, pas la norme.
Des extensions de lecture apaisée impriment peut-être plus proprement encore
que le mode lecture natif ; non vérifié.

### 2. Le `rel=canonical` corrige les attributions

Une republication garde dans son `<head>` l'adresse de l'original. C'est ce qui
révèle que la page citée n'est pas la source.

Mesuré sur le même article : le manuscrit créditait le World Economic Forum
d'un texte dont le `rel=canonical` désignait **Reuters**, 15 mai 2023. Et
l'URL citée redirigeait vers une autre forme, le site ayant réorganisé ses
chemins. Deux corrections bibliographiques réelles, obtenues d'un `grep` dans
le fichier sauvegardé.

### 3. La provenance va dans le document, pas seulement à côté

Le PDF reconstitué s'ouvre sur un bloc « Provenance et méthode » : source, date
de publication, URL — canonique, actuelle, et celle citée dans le manuscrit si
elles diffèrent —, date de consultation, et **ce que le document n'est pas**.

La phrase de méthode dit que c'est une reconstitution, d'où vient le texte,
pourquoi la page était inaccessible, et où se trouve la capture d'origine. Un
lecteur qui ouvre le fichier dans trois ans sait ce qu'il vaut sans rien
d'autre. Un sidecar YAML, lui, se perd au premier déplacement.

### 4. La vérification se fait phrase à phrase, apostrophes normalisées

`verify` compare les phrases de contenu de la capture à celles du reconstitué,
en écartant l'habillage de page et ce que l'on a retiré exprès. La cible est
zéro manquante.

**Normaliser les guillemets typographiques avant de comparer.** Un moteur TeX
transforme `'` en `’` : une recherche sur `Vietnam's` échoue sur un texte qui
contient `Vietnam’s`, et l'on croit à une perte de contenu. Même piège avec un
`grep` sur une seule ligne quand le texte source est coupé à 80 colonnes. Deux
faux négatifs dans la même session, tous deux annoncés avant d'être compris —
c'est la discipline générale du harnais sur les résultats nuls, appliquée ici :
une sonde qui ne voit pas ne produit pas de constat.

Et le regard humain reste requis pour ce qu'aucun script ne voit : rendre la
première page en image et la lire.

### 5. Deux fichiers, pas quatre

On conserve **la capture navigateur** et **le PDF reconstitué**. Le markdown
intermédiaire et les images séparées sont des sous-produits : ils partent.

Les deux PDF s'attachent au **même** item Zotero — la capture est la preuve, le
reconstitué est l'exemplaire de travail. Et `accessDate` se renseigne par
`zotero-import.py enrich`, le champ n'ayant pas de place dans le format RIS.

## Le script

```bash
S=~/.claude/skills/capture-source/scripts/reconstitute.py
"$S" build  --capture page_capture.pdf --meta meta.json --out page_reconstitue.pdf
"$S" verify --capture page_capture.pdf --reconstituted page_reconstitue.pdf \
            --ignore 'Have you read' 'published in collaboration'
```

`meta.json` :

```json
{
  "title": "PDP8: Vietnam's $135 billion power plan for 2030",
  "meta": [["Source", "World Economic Forum — republication d'un article Reuters"],
           ["Auteur d'origine", "Reuters"],
           ["Date de publication", "15 mai 2023"],
           ["URL canonique", "https://www.reuters.com/business/energy/..."],
           ["Consulté le", "9 septembre 2026"]],
  "note": "Reconstitution. Le texte et la figure sont extraits d'une capture navigateur…",
  "drop": ["^PDP8: #Vietnam"],
  "drop_blocks": ["^Have you read"],
  "headings": ["Gas, wind and coal"],
  "figure_captions": ["Vietnam's energy mix — sources projetées. Source : gouvernement vietnamien, graphique Reuters."]
}
```

`build` reflue les paragraphes, dédoublonne la ligne répétée au saut de page,
recoud les phrases coupées entre deux pages, rétablit les puces, et place
chaque figure là où le texte l'annonce. `--min-px` écarte les vignettes
résiduelles (400 px par défaut).

Sur une capture en mode lecture avec en-têtes d'impression désactivés, la
plupart de ces traitements ne trouvent rien à faire, et c'est le signe que la
capture est bonne. Les motifs `drop` et `drop_blocks` restent utiles pour ce
que le mode lecture garde et que l'on ne veut pas — une banque de liens
« Have you read? » au milieu de l'article, par exemple.

`verify` sort en code 1 s'il manque une phrase.

## Nommage

`Source_Année_Sujet_capture.pdf` et `Source_Année_Sujet_reconstitue.pdf`, dans
le `docs/` du projet — staging, git-ignoré **en entier**, sous-répertoires
compris. Un motif par extension ne suffit pas : une capture arrive avec son
répertoire d'images.

## Voir aussi

`index-source` (URL récupérable), `zotero-import` (PDF en main),
`rules/edm.md` (Zotero système de record, `docs/` en staging),
`rules/pdf-finishing.md` (vérification scriptée d'un PDF livrable).
