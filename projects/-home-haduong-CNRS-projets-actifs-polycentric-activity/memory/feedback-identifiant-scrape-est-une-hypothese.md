---
name: feedback-identifiant-scrape-est-une-hypothese
description: Un DOI ou arXiv extrait du texte d'un PDF est souvent celui d'un ouvrage cité, pas du document ; le résoudre donne une fiche propre et fausse
metadata:
  type: feedback
---

Un identifiant récupéré par expression régulière dans le texte d'un PDF est une
**hypothèse**, jamais une trouvaille : la page contient la bibliographie, donc
le DOI trouvé est fréquemment celui d'un ouvrage **cité**. Résolu chez Crossref
il rend une fiche bien formée, complète, confiante — et fausse. Rien en aval ne
la conteste.

Mesuré sur le versement de `docs/` (19/08/2026, 158 PDF) : sur 116 fiches
construites automatiquement à partir des identifiants et de `refs.bib`,
**77 ont dû être corrigées** une fois relues contre le document. Trois exemples
où la fiche automatique désignait un tout autre travail : un mémoire de Cottle
classé comme un article d'Albers sur Ronald Graham, un Parise-Ozdaglar classé
Diaconis & Janson 2007, un Le Cadre classé Foti 2018.

**Why:** la vraisemblance d'une fiche ne prouve rien sur son appartenance au
document. C'est la même famille que [[feedback-affirmation-negative-sur-source]]
et [[feedback-grep-context-audit]] : la pièce dit ce qui est, le registre dit
seulement ce qu'il a.

**How to apply:** avant d'accepter une métadonnée résolue, vérifier que le titre
et le nom du premier auteur figurent dans les premières pages du document
(`corroborate()` dans `zotero-import.py` le fait et rend
corroborated/weak/contradicted/unchecked). Sur `contradicted`, jeter la
résolution et reconstruire depuis le texte, le nom de fichier et une recherche.
Croiser avec `refs.bib` — curé par l'auteur, donc corroborant — sans le
substituer à la lecture de la page. Une année discordante ne suffit pas à
conclure : la date d'une fiche peut être celle d'une réédition ou d'une
traduction (Kantorovitch 1942 enregistré 2004).
