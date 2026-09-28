---
name: dossier-vacations-jussieu
description: "État du dossier de recrutement vacataire Sorbonne (cours IEE 2025-26) — rempli le 2026-06-04, deux points en attente"
metadata: 
  node_type: memory
  type: project
  originSessionId: 8866a629-6115-446d-999e-dd0c57db788a
---

Dossier de paiement des vacations « Introduction aux Enjeux Environnementaux » (Sorbonne Université, FSI, Cycle d'intégration), demandé par Robin Chevalier (robin.chevalier@sorbonne-universite.fr) le 2026-05-27.

**Fait (2026-06-04)** : formulaire rempli + signé (signature bleue) → `Formulaire_Agent public_25_HA-DUONG.docx/.pdf` ; 7 pièces PDF dans `pièces/`. Scripts régénérables : `/tmp/formulaire/fill.py` (chirurgie XML) + `finish.py` (python-docx) — pipeline : fill → finish → soffice convert.

Services déclarés : 2 groupes TD × 8 séances × 2 h = 32 h TD, du 22/01 au 07/05/2026, + correction de 45 copies d'examen mutualisé.

**Cumul** : la loi a changé — le CNRS ne délivre plus d'autorisation de cumul pour l'enseignement (art. L. 411-3-1 code de la recherche) : simple déclaration. Déclaration déposée sur la plateforme CNRS le 2026-06-04 (montants : dossier local, tier-2). Capture en ruban : `pièces/8 - Déclaration de cumul CNRS.pdf`. L'Annexe 1 papier est probablement caduque.

**Finalisation (2026-06-04 soir)** : Annexe 1 alignée à 48 h TD ; note « Services assurés » (2×16 h TD + 45 copies) en petit italique ; le PDF du formulaire ne contient que les 2 premières pages (le docx garde tout). Lettre explicative du régime déclaratif (`Lettre régime déclaratif cumul.pdf/.docx`) signée, renvoyant à la pièce 8.

**En attente** : réponse de R. Chevalier (volume 48 h et acceptation du régime déclaratif) ; envoi du dossier complet.

Sources des données (chemins locaux vers pièces d'état civil et de paie) : tier-2, dans `~/.config/harness/private/`.
