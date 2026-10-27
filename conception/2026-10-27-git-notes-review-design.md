# IDH — Revue hunt/gaze fondée sur Git

**Note de conception et étude d’impact — brouillon révisé du 27 octobre 2026**  
Préparé par ChatGPT prompté par Ha-Duong Minh

## Synthèse

Le projet conserve les demandes de revue, plans, rapports et synthèses dans des **Git notes attachées aux commits examinés**. Il préserve les mécanismes actuels d’exécution, de routage et d’observation.

Les responsabilités sont :

- **`hunt`** formule la demande et traite les suites.
- **`gaze`** choisit le plan, organise la revue et publie les rapports et la synthèse.
- **Les reviewers** produisent leurs rapports sans devoir publier dans Git.
- **`verify-gate`** décide de l’admissibilité à l’intégration selon les règles existantes.

Le principal risque pratique est le transport des données entre **doudou, padme, ChatGPT Work et Claude Code Web**. Une branche disponible ne garantit pas que les notes associées soient présentes. Un essai entre ces quatre environnements précède donc la migration du harnais.

**Sommaire :** 1. Périmètre · 2. Workflow · 3. Données et identités · 4. Revue incrémentale · 5. Exécution et observation · 6. Usage entre environnements · 7. Étude d’impact · 8. Migration et validation.

## 1. Périmètre et référence

L’inspection statique porte sur `MinhHaDuong/ImperialDragonHarness`, branche `main`, commit :

`dafe25f65a60c35fc69906012495dbd27b5f7eb4`

Elle couvre les skills, leurs références, les scripts, règles, adaptateurs, workflows et tests associés. Le parcours proposé n’a pas encore été validé par exécution.

Deux objectifs sont distincts :

1. **Découpler la revue de la forge** : demande, rapports et résultats circulent par Git.
2. **Permettre le parcours complet sans forge** : gate, intégration, clôture et bilans disposent également de ce fonctionnement.

La réalisation du premier objectif ne suffit pas à garantir le second.

## 2. Workflow

### 2.1. Demande par `hunt`

Après avoir commité les changements, `hunt` attache au HEAD soumis une demande comprenant :

- **What** : sortie de `git request-pull` ;
- **Why** : *body* décrivant le problème, la motivation, les choix et le résultat attendu ;
- les coordonnées du périmètre et des tickets ;
- les liens vers les tours précédents, le cas échéant.

Lorsque la question de revue est plus étroite que l’ensemble des changements, la demande précise aussi son **intention** : « vérifier telle correction parce que telle observation était bloquante ».

Le What présente les changements ; l’intention précise la question à examiner. Le plan appartient à `gaze`.

### 2.2. Planification et exécution par `gaze`

`gaze` lit la demande et les résultats antérieurs pertinents. Elle choisit la méthode proportionnée : script, reviewer unique ou panel.

Elle conserve les mécanismes actuels :

1. écrire le manifeste avant les lancements ;
2. attribuer missions et budgets ;
3. recueillir les rapports ;
4. comparer le plan à la réalisation ;
5. vérifier les observations avant de les retenir ;
6. produire la synthèse.

Le routage des modèles reste assuré par le mécanisme existant.

### 2.3. Publication centralisée par `gaze`

Chaque reviewer produit son rapport dans un fichier ou par son canal de retour habituel. **`gaze` assure la publication durable de l’ensemble du panel.**

Cette organisation évite d’exiger des droits Git de chaque reviewer et permet de contrôler la correspondance entre manifeste, rapports et publications.

L’auteur du contenu et le processus qui publie sont enregistrés séparément.

La synthèse conserve notamment :

- `result: REVIEWED | FINDINGS | ESCALATE` ;
- `seats: panel | self-only` ;
- `reviewed_head_sha` ;
- intention, couverture et limites ;
- plan, réalisation et écarts ;
- observations et listes non résolues ;
- attribution, durées et télémétrie.

**`gaze` ne rend jamais `APPROVED`.** Elle ne corrige pas le code, ne lance pas de boucle de correction et ne fusionne pas.

### 2.4. Gate et intégration

`verify-gate` conserve ses résultats :

`APPROVED | REROLL | ESCALATE | NEEDS-AUTHOR`.

Le caller conserve la responsabilité des suites. Le gate puis l’intégration utilisent les preuves publiées, avec les contrôles de HEAD et les règles de réutilisation existants.

## 3. Données et identités

### 3.1. Familles de notes

| Famille logique | Auteur du contenu | Publication |
|---|---|---|
| `refs/notes/review-request` | `hunt` | `hunt` |
| `refs/notes/review-plan` | `gaze` | `gaze` |
| `refs/notes/review-report/<reviewer>` | Reviewer | `gaze` |
| `refs/notes/review-answer` | `gaze` | `gaze` |
| Famille de verdicts à définir | `verify-gate` | Gate ou son contrôleur |

Le suffixage exact reste à fixer. Il doit permettre plusieurs demandes ou exécutions portant sur un même commit sans écraser leurs résultats.

### 3.2. Identités distinctes

| Identifiant | Fonction |
|---|---|
| `review_id` | Demande d’intégration suivie dans la durée |
| `request_id` | Version de la demande de `hunt` |
| `run_id` | Exécution particulière de `gaze` |
| `seat_id` | Mission dans cette exécution |
| `gate_session_id` | Séquence de gate existante |

Les coordonnées comprennent les SHA `base` et `head`, la branche cible et son SHA, l’intention et les liens vers les antécédents.

Une synthèse référence les versions précises des rapports utilisées. Une modification ultérieure d’un rapport ne change pas rétroactivement le résultat rendu.

Une vue « dernière synthèse » peut faciliter l’usage, mais reste dérivée de l’historique conservé.

## 4. Revue incrémentale

Après correction, `hunt` crée une nouvelle demande sur le nouveau HEAD, avec :

- les liens vers la demande et la synthèse précédentes ;
- les changements supplémentaires ;
- les réponses aux observations, identifiées de manière stable ;
- le motif de la nouvelle revue ;
- les coordonnées du périmètre complet.

Le résumé d’intégration de `request-pull` et le delta depuis le tour précédent sont distingués.

`gaze` détermine les corrections, ajouts et interactions à réexaminer. Elle explicite les conclusions antérieures reprises et peut élargir la revue.

**Une revue incrémentale ne devient pas automatiquement une revue complète du nouveau HEAD.** La synthèse indique ce qui a été vérifié, repris et laissé hors couverture.

Une observation ancienne ne disparaît pas parce que le dernier tour ne la mentionne pas. Les règles existantes sur le bookkeeping et la réutilisation des preuves sont conservées.

## 5. Exécution, observation et reprise

### 5.1. Supports de travail

Les manifests, fichiers de rapports, statuts, horloges et traces restent les supports du monitoring en direct. Les notes constituent la publication durable.

La publication intervient avant la suppression des seuls exemplaires des rapports. Son échec doit laisser les résultats récupérables et être signalé explicitement.

Le contrat de fermeture doit organiser :

1. la conservation des rapports ;
2. leur publication et sa vérification ;
3. le nettoyage ;
4. la publication de la synthèse finale, incluant le résultat du nettoyage.

### 5.2. Informations conservées

| Dimension | Données |
|---|---|
| Participation | Missions prévues, réalisées, échouées et ignorées |
| Identité | Runtime, modèle observé, famille, route, effort et indépendance disponibles |
| Temps | Durée globale, phases, missions, attentes et dépassements |
| Couverture | Intention, périmètre, preuves et limites |
| Résultats | Observations, dispositions et corrections |
| Ressources | Tokens et coût lorsqu’ils sont mesurés |
| Environnement | Hôte ou environnement pertinent, commande et dépendances nécessaires |
| Provenance | Exécution, contexte reviewer, SHA et références des artefacts |

Une identité demandée n’est pas une identité observée. Une mesure absente reste absente.

### 5.3. Reprise après interruption

Chaque exécution dispose d’un état explicite et de son propre emplacement de travail.

La reprise distingue :

- les rapports conservés ;
- les missions terminées, interrompues ou dont l’état est inconnu ;
- une synthèse finale d’un état partiel.

Un ancien fichier ne prouve pas qu’un processus distant travaille encore. Une nouvelle exécution conserve les tentatives précédentes et ne relance pas automatiquement tout le panel.

## 6. Usage entre doudou, padme et les environnements web

### 6.1. Répartition envisagée

| Environnement | Rôle envisagé | Exigence |
|---|---|---|
| **doudou** | Développement interactif et pilotage | Retrouver et reprendre une revue simplement |
| **padme** | Tests lourds et reviewers locaux | Exécuter sans dépendre d’une session ouverte sur doudou |
| **ChatGPT Work** | Analyse, développement ou revue déléguée | Tester la récupération et la publication des notes ; le clonage a fonctionné dans la session d’étude |
| **Claude Code Web** | Développement ou revue déléguée | Tester les accès aux références de notes et leur persistance |

Cette répartition est un scénario de travail, pas une obligation de routage.

### 6.2. Transmission explicite

Une transmission fournit au minimum :

**dépôt + `review_id` + `head`**

Un helper commun récupère les données nécessaires et vérifie leur cohérence. Les agents ne reconstruisent pas les conventions de références dans leurs prompts.

Les opérations suivantes illustrent l’interface attendue ; leurs noms restent indicatifs :

| Opération | Fonction |
|---|---|
| `review show <id>` | Afficher l’état, le HEAD et les résultats |
| `review run <id>` | Exécuter `gaze` |
| `review sync <id>` | Publier et récupérer les données |
| `review history <id>` | Consulter demandes, exécutions et observations |

La complexité des références reste interne à cet outillage.

### 6.3. Synchronisation et livraison

La synchronisation périodique convient aux clones durables de doudou et padme. Pour une session web, la livraison exige une publication vérifiée avant sa fin.

Il faut distinguer :

- travail terminé ;
- données publiées ;
- données récupérables par le prochain environnement.

Un résultat terminé mais non publié reste une livraison incomplète.

### 6.4. Place de padme

Padme est un exécuteur privilégié pour les besoins lourds, sans devenir une dépendance générale.

Une vérification exigeant ses GPU, données ou dépendances est nommée dans le plan. Si elle n’a pas été exécutée, elle reste manquante ; elle n’est pas remplacée par un résultat obtenu dans un environnement différent.

### 6.5. Transport, provenance et conservation

Le bootstrap doit récupérer les branches de code et les références de revue.

La conservation couvre également les commits examinés après rebase ou suppression des branches. La synchronisation doit préserver les écritures locales concurrentes.

La provenance doit être définie explicitement : l’identité déclarée dans un rapport et l’auteur Git de sa note ne remplacent pas automatiquement une identité de forge précédemment vérifiée.

## 7. Étude d’impact sur le harnais

| Composant | Adaptation |
|---|---|
| **`hunt`** | Construire la demande Git et remplacer le parcours de revue spécifique sans forge |
| **`gaze`, `gaze_setup.py`** | Accepter une demande Git ; conserver la résolution par PR en entrée ; isoler les exécutions |
| **`review-anchor.py`** | Ancrer le checkout sur les SHA de la demande |
| **`gaze_close.py`** | Publier rapports, attribution et synthèse ; préserver les artefacts lors des échecs |
| **`raid`** | Lire les résultats Git ; conserver vagues, budgets, escalades et politique de reprise |
| **`verify-gate`** | Lire les observations et l’historique des gates sans dépendre des commentaires de PR ; conserver le plafond global de deux tours |
| **`review_evidence.py`** | Lire les notes en préservant les critères de fraîcheur, réutilisation et provenance |
| **`merge`** | Ajouter une recette locale avec gate, HEAD figé, preuve d’intégration et lecture de contrôle |
| **`merge-gate.py`, `main_sweep.py`** | Réutiliser les preuves existantes dans `refs/notes/gate` ; adapter les hypothèses de remote au parcours local |
| **Attribution : record, query, backfill** | Étendre les formats et jointures centrés sur les numéros de PR ; conserver toutes les tentatives |
| **`roar`, capture, clôture** | Lire les notes et les preuves d’intégration ; capturer l’attribution sans forge |
| **`enumerate-merges.py`** | Réduire la dépendance aux sujets et messages au format GitHub |
| **Dashboard, sitrep, `project-state.py`** | Présenter les demandes locales ; distinguer absence et échec de lecture |
| **Durées et analyses de traces** | Préserver les mesures ; étendre les jointures fondées sur les PR |
| **`lair`, `molt`, `yawn`, housekeeping** | Préserver et synchroniser les données avant nettoyage |
| **Producteurs de branches et revue de prose** | Utiliser le parcours commun ; adapter notamment l’appel de `conference-submission-prep` |
| **Diagnostics et tests** | Reconnaître les nouvelles entrées, publications, preuves et échecs |

### Modifications de contrat nécessaires

- **`rules/git.md`** impose actuellement branche + PR : autoriser un parcours sans forge exige une évolution explicite de cette politique.
- **Lecture seule de `gaze`** : autoriser précisément les commits de notes tout en interdisant les modifications du code examiné.
- **Contrôle des collisions** : remplacer, pour le parcours local, l’énumération des PR ouvertes par celle des changements en cours.
- **Hooks et adaptateurs** : vérifier les droits de publication des notes et les contrats projetés affectés.
- **Documentation interne** : réconcilier les références anciennes à l’organisation de `gaze` avec son contrat actuel.

Le mécanisme de gate utilise déjà des notes : c’est un point d’appui, sans assimiler preuves mécaniques et rapports de revue.

## 8. Migration et validation

### 8.1. Première étape : essai de transport

Avant de migrer les skills :

1. doudou publie une demande ;
2. padme la récupère et publie un rapport ;
3. ChatGPT Work récupère l’ensemble et publie une synthèse ;
4. Claude Code Web récupère cette synthèse et publie un complément ;
5. doudou retrouve l’historique après suppression des worktrees temporaires.

Si un environnement ne peut pas publier les notes avec ses accès habituels, ce résultat devient une contrainte d’architecture. Un relais existant ou un stockage sur branche dédiée peuvent alors être évalués. Aucun de ces mécanismes n’est retenu à ce stade.

### 8.2. Suite de la migration

Après validation du transport :

1. fixer les identifiants, formats et conventions de références ;
2. fournir les helpers communs ;
3. adapter `hunt`, `gaze` et leur publication ;
4. migrer `raid`, le gate et l’intégration ;
5. migrer observation, attribution et nettoyage ;
6. activer le parcours complet sans forge après adaptation des règles.

### 8.3. Cas de validation déterminants

- Plusieurs exécutions sur un même HEAD restent distinctes.
- Les observations et leur disposition survivent aux corrections.
- Une intention étroite n’élargit pas implicitement la couverture.
- Les missions absentes ou échouées restent visibles.
- Une nouvelle session ne réinitialise pas le budget de gate.
- Une publication échouée conserve les rapports.
- Une interruption permet une reprise sans relance aveugle.
- Rebase et nettoyage ne détruisent pas les preuves.
- Les bilans restituent participants, temps, version et environnement.
- Le parcours sans forge va de `hunt` à l’intégration puis à `roar`.
- Les preuves historiques restent lisibles pendant la transition.

**État :** design proposé et impacts inspectés ; aucune modification du harnais réalisée. La prochaine décision repose sur l’essai de transport entre les quatre environnements.
