---
name: project_bareme_fiches_acteur
description: "Grading rubric and house rules for the IEE \"fiche acteur\" assignment (Jussieu cohort)"
metadata: 
  node_type: memory
  type: project
  originSessionId: f77cf02a-4622-426d-977c-7beec792cfe6
---

Barème de la **fiche acteur** (UE Introduction aux enjeux environnementaux, Sorbonne/Jussieu), controverse « éoliennes en mer ». Note chiffrée **/20** = somme de 7 critères : Expression (0–2), Description de l'acteur (0–3), Arguments mobilisés (0–3), Positionnement (0–3), Pouvoir d'agir (0–3), Liens avec les autres acteurs (0–3), Bibliographie (0–3).

**Règles maison (overrides) explicitées par l'enseignant, à appliquer strictement :**
- **Expression = 0** s'il manque, *sur le document lui-même*, le titre OU le nom de l'auteur OU la date de rédaction. L'identité connue via Moodle/le nom de fichier ne compte pas. Une date de *consultation* de source ou un label « année scolaire » ne compte pas comme date.
- **Expression ≤ 1** s'il manque les numéros de page OU si le format n'est pas un PDF (.docx/.odt plafonnés à 1). Vérifier la pagination **visuellement** (rendu image), pas via pdftotext qui rate les pieds de page.
- **Note réflexive sur l'usage de l'IA** : obligatoire (répété par l'enseignant) mais **hors-barème** → 2 colonnes séparées : `IA présence` (Oui/Non) + `IA clarté` (0–3 : 0 absente, 1 vague, 2 claire = outils nommés+comment+vérification, 3 exemplaire = prompts/comparaison/vérif sources). Un refus argumenté d'utiliser l'IA = présence Oui, clarté 1.
- **Fiches multiples** (étudiant ayant rendu plusieurs acteurs) : additionner les points **par critère**, plafonné au max du critère.

Livrable type : un CSV (séparateur `;`, UTF-8 BOM) avec Groupe, Nom, Prénom, N° étudiant, les 7 notes + motif Expression, Total /20 (hors IA), colonnes IA, Remarques. Voir aussi [[feedback_group_codes]] (codes groupes complets SVCST). Corpus 2026 : `~/CNRS/missions/actif/2026 cours Jussieu/Fiches acteur/notes_fiches_acteur.csv`.
