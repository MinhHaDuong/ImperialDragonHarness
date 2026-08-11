---
name: adversarial-pair-verification
description: "Pour tout théorème produit par agent, apparier un développeur et un referee adversarial à bases de code indépendantes (arithmétique exacte) avant insertion au manuscrit"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 70bfdabf-9d99-4812-9990-ad845b0097d4
  modified: 2026-08-11T09:33:20.054Z
---

Sur la session pépite MIMO (polycentric_activity, 2026-08-10/11), chaque bloc
mathématique destiné au manuscrit est passé par une paire : agent développeur
(V1, V2) puis referee adversarial (V1b, V2b) briefé pour CASSER les preuves,
avec interdiction de réutiliser le code du développeur — vérification
réécrite from scratch en arithmétique exacte (fractions stdlib), balayages
exhaustifs, et sondes ciblées sur les pas compressés.

**Why:** le motif a confirmé tous les théorèmes ET trouvé deux vrais trous de
preuve (la « faille du bloc-source » dans les théorèmes C/D de la théorie ι —
exhibit TRIPLE_M réalisant la configuration déclarée impossible) plus une
clause redondante et une hypothèse manquante, qu'aucune relecture simple d'un
seul agent n'aurait vus. La décorrélation des bases de code est ce qui fonde
le verdict (même modèle ≠ même code ≠ mêmes angles morts).

**How to apply:** avant d'insérer un théorème d'agent dans un manuscrit,
lancer un referee adversarial dédié avec (1) l'énoncé et la preuve verbatim
dans le prompt, (2) interdiction de réutiliser le code du développeur,
(3) sondes explicites sur les pas fragiles (cas dégénérés, quantificateurs,
comptages), (4) un balayage indépendant critère-contre-vérité-terrain. Ne pas
argumenter de fenêtres de paramètres par échantillonnage de chambres de
signes : la validité d'un plan n'y est pas constante (piège ASSEM) — exiger
un certificat explicite pour le possible et Fourier–Motzkin/quantification
jointe pour l'impossible. Voir [[skill-topic-boundaries]] pour où ranger ce
genre de règle.
