# Secretariat - Memory

## Structure

~/CNRS/secretariat/ est organisé en 10 dossiers thématiques (voir README.md).
Convention de nommage : minuscules, tirets, français.

## Réorganisation effectuée (mars 2026)

- Ancien `Rapport/` avec 30+ sous-dossiers `sent-*` classés en 5 types dans `rapports-d-activite/`
- CRAC (2003-2010) convertis en PDF et fusionnés dans `RIBAC/` (série complète 2003-2025)
- `PublicationAnalysis` frozen supprimé (94MB), code vit dans `~/CNRS/code/activity_report_writer/PublicationAnalysis/` (tag git `v2024-09-frozen`)
- `contrib/` + `procedures/` scindés en 3 : `logos/`, `references/`, `procedures/`
- `courrier/` déplacé vers `~/CNRS/gens/archive/courrier`
- Nommage harmonisé : navigo->transport, positions->carriere, tickets-restau->restauration

## Nettoyage effectué

- Doublons identiques (MD5) supprimés
- Fichiers éditables >5 ans supprimés quand PDF existe
- 12 fichiers obsolètes supprimés de references/ (AERES, conventions expirées, etc.)
- 4 fichiers obsolètes supprimés de procedures/ (CIRAD, véhicule 2009, SMASH FAQ 2006)
- Instructions évaluation vague déplacées de vague/2025/contrib/ vers references/evaluation-vague/

## Code associé

~/CNRS/code/activity_report_writer/ contient 3 sous-projets :
- PublicationAnalysis/ (git, tag v2024-09-frozen)
- ribac-check/ (git, pyproject.toml + uv)
- activity-analysis/ (git initialisé cette session)

## Préférences utilisateur

- Langue de travail : français
- Décisions rapides, peu de discussion préalable
- Préfère supprimer plutôt qu'archiver
- Conserve les documents CIRED et les RIB même anciens
- Section CNRS : 40 (anciennement 37 avant 2024)
