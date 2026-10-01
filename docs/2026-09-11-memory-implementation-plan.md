# Plan de livraison de la mémoire v8

**Date :** 1 octobre 2026. **Phase :** plan, aucune activation de runtime.
**Contrat :** [conception v8](2026-09-10-dragon-memory-design.md).
**Historique :** [plan v7](2026-09-11-memory-implementation-plan-v7.md).

## Premier jalon

Un dépôt pilote possède un journal factuel commité, des thèmes avec provenance,
un index de 100 lignes maximum et un prompt DREAM.md. Un rêve suggéré par lair puis invoqué séparément produit une
branche et une PR. Les quatre runtimes peuvent lire les mêmes fichiers et
rechercher le journal avec leurs outils ordinaires.

Aucun package hoard, schéma exécutable, compilateur, embedding, base de données,
MCP, snapshot partagé obligatoire ou budget par canal ne précède ce jalon.
Les IDs et logs restent stables ; les fichiers des tickets gardent leur ancien
slug. Leur titre, corps et dépendances expriment le nouveau périmètre.

## Tickets et dépendances

| Ticket | Livraison v8 | Prérequis |
|---|---|---|
| 0911 | Convention Markdown et modèles de capture/lecture | — |
| 0917 | Inventaire et provenance des sources existantes | — |
| 0920 | Un projet pilote, index, thèmes, journal annuel | 0911, 0917, 0999 |
| 0988 | Capture factuelle à roar, commit et intégration sûrs | 0920 |
| 0916 | Prompt DREAM.md et consolidation avec sources conservées | 0920 |
| 0910 | Suggestion finale lair au seuil de 5, puis rêve distinct et PR | 0916, 0988 |
| 0923 | Premier smoke de lecture/capture/rêve, runtime choisi et déclaré | 0910 |
| 0924 | Preuves sur les trois autres runtimes, dont Vibe | 0923 |
| 0925 | Différé : cristallisation sur demande explicite seulement | Hors livraison automatique |
| 0918 | Évaluation de lecture, rappel, capture et consolidation | 0924 |
| 0913 | Migration progressive et retrait des mécanismes remplacés | 0918 |
| 0909 | Revue du résultat intégré et clôture du programme | 0913, 0988 |

0991, qui prescrit un scoring EU et une purge dans l’ancien rêve, est aussi
différé pendant la transition ; 0913 réévaluera ses constats utiles après le
pilote, sans réintroduire automatiquement son mécanisme.

0999 garde l’installation portable et l’enregistrement des runtimes. 0934 garde
la correction des outils hérités tant qu’ils ont des consommateurs ; leur
retrait éventuel se décide après le pilote, sans confondre ce défaut avec 0988.

## Périmètres abandonnés ou différés

Les tickets 0908, 0912, 0914, 0915, 0919, 0921 et 0922 sont marqués `deferred`
et supersédés par v8, pas déclarés implémentés. Leur ancien périmètre reste dans
Git et le plan historique. Ils ne bloquent pas la livraison et ne doivent pas
être exécutés contre v7. Toute réactivation exige une nouvelle décision :

- 0908 : import des marqueurs inactifs couvert par inventaire/pilote si nécessaire.
- 0912 : découverte automatisée distincte couverte par le rêve éditorial.
- 0914/0915 : grammaire de prédicats et admission exécutable abandonnées.
- 0919 : annotations de qualité systématiques abandonnées.
- 0921 : loader orientation/recent et overlay G/C abandonnés.
- 0922 : moteur de rappel dédié abandonné ; lecture et rg/grep dans la convention.

## Ordre et preuves

1. Écrire les modèles, inventorier les corpus et choisir un pilote et son audience.
2. Mettre en place le dossier versionné sans effacer les anciens récits.
3. Réviser roar pour capturer et commiter seulement des faits significatifs,
   positifs et négatifs ; prouver intégration et absence de pull bloqué.
4. Livrer le prompt et la proposition lair : sources attribuées, rapports de traitement,
   branche isolée et PR, aucune fusion automatique de connaissance proposée.
5. Vérifier les quatre runtimes avec leurs versions et limites réelles, puis
   les scénarios comportementaux et la frontière d’écriture avant élargissement.
6. Migrer par projets, retirer seulement les anciennes voies remplacées et
   revoir l’ensemble intégré avant de fermer 0909.

Les répétitions de scénario servent à mesurer les oublis et les effets des
mémoires natives contradictoires. Fixer protocole et critères avant les essais,
puis enregistrer résultats, coûts, omissions et limites. Les vérifications
mécaniques portent sur sources, liens, commits, seuil, suggestion finale, intégration et visibilité
des échecs ; elles ne certifient pas la qualité sémantique.

## Limites de cette révision

Le journal reste append-only dans journal/AAAA/. Les entrées traitées sont
référencées dans les rapports de rêve fusionnés, pas déplacées. Un modèle de
300 mots par expérience est un repère éditorial ; l’index a une limite stricte
de 100 lignes, titres et lignes vides compris.
Un compagnon privé demande sa propre convention d’accès et de versionnement.
Les sources natives absentes sont signalées, pas supposées vides.

La réécriture initiale v8 conservait les skills existants. La clarification
ci-dessous corrige leurs instructions ; les profils restent inchangés.
Aucun test live ni clôture de ticket d’implémentation n’est annoncé.

## Frontière d’autorité — clarification du 1 octobre 2026

Les sorties d’un projet restent dans son dépôt ou son compagnon privé explicite.
Roar ne propose aucune règle ; dream ne propose ni ne réalise de cristallisation.
0925 est différé et ne bloque plus le programme. Une demande explicite future
ouvre une tâche distincte. Les instructions actuelles roar/dream/memory-sweep
sont corrigées dès cette clarification ; la proposition lair et le pilote restent à éprouver.

Lair termine puis suggère dream en conclusion à partir de 5 nouvelles
expériences. Il n’attend ni ne lance rien ; dream est un follow-up distinct.
Le seuil de 5 est choisi par l’auteur.

DREAM consolide par pruning, merging et refreshing des thèmes et de l’index.
Le journal reste append-only ; les sources et motifs des retraits sont tracés.
