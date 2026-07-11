---
name: Pipeline IA — règles de méthode
description: Règles absolues et contraintes de la méthode IA de génération des voix
type: feedback
originSessionId: 36d1acf3-4f7c-4c25-9343-05779577ace1
---
Règles à respecter impérativement dans le pipeline IA de génération des voix.

**Règle 1 — Aucun data leak.** Les brouillons actuels (voix-*.md) ne peuvent pas servir de référence de style, de données d'entraînement, ni de baseline comparative. Isolement total entre v0 et le pipeline IA.

**Why:** L'objectif est des voix authentiquement générées depuis les écrits originaux des figures, pas influencées par une v0 écrite par Claude.

**How to apply:** Ne jamais proposer d'utiliser voix-*.md, intro.md, ou coda.md dans le contexte du fine-tuning ou de l'évaluation. Ces fichiers sont archivés en v0 et ne participent pas au pipeline.

---

**Règle 2 — Voix-auteur dans le sweep, pas en post-traitement.** La combinaison voix-héros/voix-auteur est une dimension du sweep de génération (aux côtés de la température), pas une étape après la sélection.

**Why:** Pour que le best-of-N compare des candidats à différents niveaux de mélange — pas pour polir un texte déjà choisi.

**How to apply:** Implémenter le poids voix-auteur comme hyperparamètre du sweep. Contrainte technique à vérifier : combinaison LoRA linéaire ou ratio dataset.

---

**Règle 3 — Commencer par voix-auteur.** Premier prototype = corpus voix-auteur (banhhanoi.art + papiers curatés), avant les 13 voix héros.

**Why:** Utile quelle que soit la réponse éditoriale finale du projet. Valide aussi le pipeline sur PADME.

**How to apply:** Ticket 0014 (corpus) → ticket 0015 (prototype voix-auteur) avant ticket 0016 (sweep × 13).
