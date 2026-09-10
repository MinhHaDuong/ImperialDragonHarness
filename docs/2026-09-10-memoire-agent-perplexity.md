# Mémoire des agents — rapport d'étude (Perplexity, 2026-09-10)

> **NON NORMATIF.** Rapport d'étude, enregistré pour information. Rien ici
> n'est décidé, adopté ni applicable au harness. Aucune règle, aucun agent et
> aucun outil ne doit s'y référer comme à une prescription : les sections
> « Architecture recommandée pour un harnais » et « Ce que je mettrais en
> œuvre en pratique » sont des suggestions de l'auteur du rapport, pas une
> architecture retenue. Les normes du harness vivent dans `rules/`,
> `CLAUDE.md` et les tickets — pas dans `docs/`.

**Auteur :** Perplexity. **Enregistré le :** 2026-09-10, verbatim.
Les affirmations chiffrées et les références sont celles de l'auteur et n'ont
pas été revérifiées à l'enregistrement.

Deuxième des trois rapports sollicités indépendamment sur la même question :
[`2026-09-10-memoire-agent-fable.md`](./2026-09-10-memoire-agent-fable.md),
[`2026-09-10-memoire-agent-chatgpt.md`](./2026-09-10-memoire-agent-chatgpt.md).
Voir aussi [`dream-research.md`](./dream-research.md) (note de recherche
`/dream`, 2026-05-13).

---

# Idée centrale

La mémoire agentique n'est pas une « base de conversations » que l'on interroge plus tard. C'est une **politique de gestion d'état** : décider quoi observer, quoi conserver, sous quelle forme, quand le rappeler, quand le réviser et quand l'oublier.

L'état de l'art converge vers une architecture en couches combinant mémoire de travail, mémoire épisodique, mémoire sémantique et mémoire procédurale, avec un cycle :

\[
\text{observer} \rightarrow \text{évaluer} \rightarrow \text{encoder} \rightarrow \text{rappeler} \rightarrow \text{agir} \rightarrow \text{consolider} \rightarrow \text{oublier}
\]

La difficulté principale n'est plus le stockage. C'est la **sélection**, la **consolidation**, la **gestion des contradictions** et l'oubli sélectif. Une enquête récente décrit précisément ce déplacement : la mémoire devient le substrat de l'auto-amélioration des agents, et non plus seulement une couche RAG passive. [arxiv](https://arxiv.org/abs/2602.06052)

## 1. Taxonomie actuelle

### Mémoire de travail

C'est l'état actif de la tâche :

- objectif courant ;
- plan ;
- sous-tâches terminées et restantes ;
- observations récentes ;
- résultats des outils ;
- hypothèses en cours ;
- erreurs non encore résolues.

Elle doit rester petite, lisible et facilement remplaçable. Il ne faut pas y conserver toute la trace d'exécution.

### Mémoire épisodique

Elle conserve des événements situés :

> « Pour installer ce projet sur Ubuntu, l'agent a dû ajouter le dépôt X, puis corriger l'erreur Y. »

Elle est utile pour retrouver des expériences analogues, mais elle ne doit pas devenir un journal infini. Les épisodes doivent être résumés, dédupliqués et finalement transformés en connaissances plus générales.

### Mémoire sémantique

Elle contient des faits relativement stables :

- conventions d'un projet ;
- préférences de l'utilisateur ;
- contraintes institutionnelles ;
- relations entre entités ;
- décisions confirmées ;
- faits vérifiés.

Un fait doit être atomique, daté et traçable :

```yaml
id: project.python.version
value: "Python 3.12"
scope: project-x
source: "pyproject.toml"
confidence: 0.98
observed_at: 2026-09-10
valid_until: null
status: active
```

Les systèmes modernes de type Mem0 suivent une logique proche : extraire des faits atomiques puis décider `ADD`, `UPDATE` ou `DELETE`, plutôt que d'empiler les tours de conversation. [arxiv](https://arxiv.org/html/2606.06448v1)

### Mémoire procédurale

Elle encode les méthodes qui ont fonctionné :

> « Pour publier un logiciel de recherche, lancer les tests, construire le paquet, vérifier le dépôt Git, puis créer l'archive DOI. »

C'est probablement la couche la plus importante pour un harnais de recherche ou de programmation. Elle doit prendre la forme de **compétences exécutables**, de check-lists ou de playbooks, et non de simples souvenirs textuels.

### Mémoire de référence

Elle contient les documents externes : documentation, articles, fichiers du projet, logs, dépôts, corpus. Elle ne doit pas être confondue avec la mémoire des expériences de l'agent.

Cette distinction est essentielle :

| Type | Question à laquelle elle répond | Durée typique |
|---|---|---|
| Travail | Que suis-je en train de faire ? | Minutes à heures |
| Épisodique | Qu'est-il arrivé ? | Jours à semaines |
| Sémantique | Que savons-nous maintenant ? | Longue durée |
| Procédurale | Comment réussir cette opération ? | Longue durée |
| Référence | Où trouver la preuve ou le document ? | Selon la source |

## 2. Les grandes familles d'architecture

On peut distinguer quatre familles, allant de la plus simple à la plus agentique :

1. **Contexte long** : conserver l'historique brut et le renvoyer au modèle.
2. **RAG plat** : index lexical ou vectoriel de fragments.
3. **RAG structuré** : extraction de faits, entités, relations ou résumés.
4. **Mémoire contrôlée par l'agent** : l'agent décide quand lire, écrire, mettre à jour ou supprimer.

Cette dernière famille est flexible, mais coûteuse et difficile à contrôler. Une étude système de 2026 décompose le pipeline en ingestion, construction, stockage, retrieval, assemblage du prompt, génération et maintenance. Elle montre aussi que les systèmes diffèrent fortement par le coût déplacé vers l'écriture ou vers la lecture. [arxiv](https://arxiv.org/html/2606.06448v1)

Le point important pour un harnais est donc de séparer :

- **l'exécution** ;
- **la mémoire de session** ;
- **la mémoire persistante** ;
- **la maintenance**.

Il ne faut pas demander à l'agent principal de faire tout cela dans le même contexte.

## 3. Architecture recommandée pour un harnais

Je recommanderais une architecture à cinq services logiques, même si elle est d'abord implémentée dans un seul programme.

### A. Journal brut temporaire

Conserver la trace complète de l'exécution, mais avec une durée de vie limitée :

```text
runs/
  2026-09-10T14-32Z/
    events.jsonl
    tool-calls.jsonl
    artifacts/
    final-result.md
```

Ce journal sert à l'audit et au débogage, pas à être injecté dans chaque session.

Il peut être supprimé après 7, 30 ou 90 jours selon le besoin. Les artefacts importants doivent être promus vers une mémoire durable.

### B. État de tâche

Un fichier ou objet structuré, court et toujours chargé :

```yaml
goal: "Publier la version 2 du corpus"
status: in_progress
constraints:
  - "Ne pas modifier les fichiers sources"
  - "Préserver les métadonnées HAL"
next_actions:
  - "Valider le schéma JSON"
  - "Exécuter les tests"
blocked_by: null
decisions:
  - "Utiliser JSONL plutôt que CSV"
```

Cette mémoire de travail doit être reconstruite à chaque reprise à partir de checkpoints. Elle ne doit pas croître avec le nombre d'appels d'outils.

### C. Banque d'expériences

Chaque expérience est un objet court et orienté décision :

```yaml
id: exp-2026-09-10-0042
task_type: hal_deposit
context:
  repository: corpus-climate
action:
  - "Préparer le dépôt avec le script deposit.py"
outcome: failure
error: "Le champ affiliation manquait dans le métadonnée XML"
lesson: "Valider les affiliations avant génération XML"
confidence: 0.85
reuse_when:
  - "Dépôt HAL"
  - "Génération XML"
  - "Erreur affiliation"
source_run: 2026-09-10T14-32Z
created_at: 2026-09-10
last_retrieved_at: 2026-09-10
utility: 0.7
status: active
```

Le point essentiel est de ne pas enregistrer « toute l'expérience », mais sa **leçon réutilisable**.

### D. Banque de connaissances et de décisions

Séparer au moins trois namespaces :

```text
memory/
  user/
  project/
  system/
  procedures/
  experiments/
  decisions/
```

Cette séparation évite qu'une préférence personnelle, une convention de projet et une leçon générale soient traitées de la même manière.

Exemples :

- `user/` : préférences et contraintes de l'utilisateur ;
- `project/` : état et conventions du dépôt courant ;
- `system/` : règles du harnais ;
- `procedures/` : compétences réutilisables ;
- `experiments/` : épisodes utiles ;
- `decisions/` : choix approuvés et leur justification.

### E. Service de consolidation

Un processus asynchrone examine les épisodes et décide :

- supprimer ;
- fusionner ;
- remplacer ;
- généraliser ;
- promouvoir en procédure ;
- archiver ;
- invalider.

C'est cette étape qui empêche l'accumulation infinie.

## 4. Une politique d'écriture

Le harnais ne devrait jamais écrire automatiquement chaque observation dans la mémoire longue durée. Il devrait appliquer un filtre de valeur.

### Test de mémorisation

Pour chaque événement, produire une décision structurée :

```json
{
  "store": true,
  "type": "procedural",
  "memory": "Avant un dépôt HAL, valider les champs affiliation et licence.",
  "scope": "hal_deposit",
  "confidence": 0.86,
  "evidence": ["run:2026-09-10T14-32Z"],
  "replace": null,
  "expires": null
}
```

Une information mérite d'être persistée si elle satisfait au moins un des critères suivants :

- elle sera probablement utile dans une autre tâche ;
- elle corrige une erreur récurrente ;
- elle exprime une préférence ou une contrainte stable ;
- elle documente une décision explicite ;
- elle améliore une procédure ;
- elle évite un coût ou un risque important ;
- elle est confirmée plusieurs fois.

Elle ne devrait généralement pas être mémorisée si elle est :

- purement transitoire ;
- facilement recalculable ;
- spécifique à un seul tour ;
- incertaine et non vérifiée ;
- sensible sans nécessité ;
- redondante avec un document de référence.

## 5. Éviter l'accumulation infinie

### 1. Déduplication sémantique

Avant d'ajouter un souvenir, rechercher les entrées proches :

```text
nouveau souvenir
  → recherche lexicale
  → recherche vectorielle
  → filtrage par scope
  → détection de contradiction
  → ADD / UPDATE / MERGE / DELETE
```

La recherche vectorielle seule ne suffit pas. Il faut aussi rechercher les termes exacts, les identifiants et les noms de fichiers. Pour un harnais de code ou de recherche, une combinaison BM25 + embeddings + filtres structurés est souvent préférable.

### 2. Mise à jour plutôt qu'ajout

Mauvais modèle :

```text
L'utilisateur utilise Python 3.10.
L'utilisateur utilise Python 3.11.
L'utilisateur utilise Python 3.12.
```

Meilleur modèle :

```yaml
subject: project-x.python_version
current_value: "3.12"
history:
  - value: "3.10"
    valid_until: 2025-06
  - value: "3.11"
    valid_until: 2026-01
  - value: "3.12"
    valid_from: 2026-01
```

La mémoire doit représenter l'état courant et conserver l'historique uniquement lorsqu'il a une valeur explicative ou d'audit.

### 3. Consolidation épisodique vers sémantique

Après plusieurs épisodes similaires :

```text
Épisode 1 : l'installation échoue à cause de Python 3.10.
Épisode 2 : l'installation échoue à cause d'une dépendance Python.
Épisode 3 : Python 3.12 résout le problème.
```

Consolidation :

> « Ce projet requiert Python ≥ 3.12 ; vérifier la version avant d'installer les dépendances. »

Les épisodes individuels peuvent ensuite être supprimés ou archivés.

### 4. Promotion vers une procédure

Si une leçon est confirmée et répétée :

```text
expériences répétées
  → règle locale
  → procédure testée
  → compétence versionnée
```

Une procédure devrait avoir un taux de réussite :

```yaml
name: validate-python-environment
version: 2
successes: 14
failures: 2
last_used: 2026-09-10
applies_to:
  - project-x
  - project-y
```

Cela transforme la mémoire en bibliothèque de compétences plutôt qu'en collection de récits.

### 5. Oubli par budget

Définir un budget explicite par espace :

```yaml
budgets:
  working_memory_tokens: 6000
  active_project_facts: 500
  episodic_memories: 2000
  procedures: 300
  user_preferences: 100
```

Le nombre d'entrées n'est pas le seul budget. Il faut aussi limiter :

- tokens injectés dans le prompt ;
- nombre de résultats récupérés ;
- nombre de niveaux de graphes traversés ;
- coût de maintenance ;
- latence de récupération.

Une mémoire de dix mille entrées peut être acceptable si seulement cinq sont injectées. Inversement, deux cents résumés longs peuvent déjà saturer le contexte.

### 6. Score de rétention

Un score pratique peut combiner plusieurs signaux :

\[
R(m) =
w_u U(m)
+ w_r \log(1 + \text{retrievals}(m))
+ w_c C(m)
+ w_s S(m)
- w_a A(m)
- w_d D(m)
\]

où :

- \(U(m)\) = utilité observée ;
- \(R(m)\) = fréquence de récupération ;
- \(C(m)\) = niveau de confirmation ;
- \(S(m)\) = importance ou criticité ;
- \(A(m)\) = ancienneté ;
- \(D(m)\) = redondance.

Mais il faut éviter une règle naïve du type « supprimer les souvenirs peu récupérés ». Une information rare peut être critique : une procédure de restauration, une contrainte juridique ou une décision institutionnelle.

Je distinguerais donc :

- **TTL automatique** pour les observations et épisodes ;
- **expiration avec validation** pour les faits évolutifs ;
- **conservation indéfinie** pour les décisions et procédures approuvées ;
- **suppression immédiate** pour les données sensibles ou explicitement révoquées.

## 6. Récupération : ne pas tout injecter

La récupération devrait être conditionnée par la tâche, pas seulement par la similarité sémantique.

### Pipeline recommandé

```text
requête courante
  → classification de la tâche
  → choix des namespaces
  → recherche lexicale + vectorielle
  → filtres scope/date/statut
  → résolution des contradictions
  → reranking par utilité
  → compression
  → injection limitée
```

Exemple :

- pour une erreur de compilation : chercher d'abord les procédures et expériences techniques ;
- pour une question sur l'utilisateur : chercher les préférences ;
- pour un dépôt HAL : chercher les décisions et procédures du dépôt ;
- pour une revue de littérature : chercher les sources et non les anciennes stratégies d'agent.

Le harnais devrait aussi savoir répondre :

> « Je n'ai pas assez de confiance pour utiliser cette mémoire. »

L'abstention est aussi importante que le rappel. Les benchmarks récents évaluent désormais la rétention, l'apprentissage en ligne, la généralisation, les conflits et l'oubli sélectif, plutôt que le seul rappel d'un fait. [iclr](https://iclr.cc/virtual/2026/10012519)

## 7. Gestion des contradictions

Chaque mémoire devrait avoir :

- une portée ;
- une date d'observation ;
- une source ;
- un niveau de confiance ;
- un statut ;
- éventuellement une période de validité.

Les conflits doivent être traités explicitement :

```text
if same_subject and same_scope:
    if new_fact is newer and better_supported:
        supersede(old_fact)
    elif facts_are_contextual:
        keep_both_with_conditions()
    else:
        flag_for_confirmation()
```

Il faut distinguer :

1. **Contradiction temporelle** : Python 3.11 puis Python 3.12.
2. **Contradiction de portée** : une règle pour le projet A, une autre pour le projet B.
3. **Contradiction d'incertitude** : deux hypothèses non vérifiées.
4. **Contradiction réelle** : deux faits incompatibles sans explication.

Une erreur fréquente consiste à faire confiance au souvenir le plus récent. Le plus récent n'est pas toujours le plus fiable ; la source et la confirmation doivent également compter.

## 8. Ce que je mettrais en œuvre en pratique

Pour un harnais personnel ou de recherche, je commencerais sans graphe de connaissances sophistiqué :

```text
SQLite/PostgreSQL
  - memories
  - procedures
  - decisions
  - runs
  - artifacts
  - memory_events
```

Puis :

- recherche BM25 pour les mots exacts ;
- embeddings pour la paraphrase ;
- métadonnées structurées pour scope, date, statut et type ;
- fichiers Markdown versionnés pour les procédures et décisions importantes ;
- un worker de consolidation différé ;
- un journal d'audit de chaque mutation mémoire.

Schéma minimal :

```sql
CREATE TABLE memories (
    id TEXT PRIMARY KEY,
    namespace TEXT NOT NULL,
    kind TEXT NOT NULL,
    content TEXT NOT NULL,
    scope TEXT,
    source TEXT,
    confidence REAL,
    utility REAL,
    created_at TIMESTAMP,
    last_used_at TIMESTAMP,
    valid_from TIMESTAMP,
    valid_until TIMESTAMP,
    status TEXT NOT NULL
);
```

Cycle de fin de tâche :

```text
1. Produire le résultat.
2. Évaluer succès, échec et incertitudes.
3. Extraire au maximum 0–5 souvenirs candidats.
4. Comparer chaque candidat aux souvenirs existants.
5. Mettre à jour ou fusionner.
6. Promouvoir les leçons répétées en procédures.
7. Déprécier les épisodes obsolètes.
8. Écrire un checkpoint court.
```

La limite « 0–5 souvenirs candidats par tâche » est utile : elle force le modèle à exercer une sélection et empêche le memory writer de transformer chaque interaction en nouvelle entrée.

## 9. Évaluer le harnais

Il faut mesurer le système mémoire indépendamment de la qualité générale du modèle.

### Tests essentiels

- rappel exact d'un fait ancien ;
- raisonnement sur plusieurs épisodes ;
- mise à jour d'un fait ;
- non-utilisation d'un fait obsolète ;
- résolution d'une contradiction ;
- réutilisation d'une procédure ;
- abstention en cas d'incertitude ;
- suppression effective d'une donnée ;
- coût de construction ;
- latence de récupération ;
- taille moyenne du contexte injecté.

Une métrique utile est la précision de mémoire réellement utilisée :

\[
\text{Memory Precision}
=
\frac{\text{souvenirs pertinents injectés}}
{\text{souvenirs injectés}}
\]

À compléter par :

\[
\text{Memory Utility}
=
\frac{\text{tâches améliorées par la mémoire}}
{\text{tâches où la mémoire a été consultée}}
\]

et par une mesure d'obsolescence :

\[
\text{Stale Usage Rate}
=
\frac{\text{réponses s'appuyant sur une mémoire invalide}}
{\text{réponses nécessitant cette mémoire}}
\]

Les résultats disponibles montrent que les systèmes actuels sont généralement meilleurs pour retrouver des informations que pour savoir lesquelles oublier ou invalider ; cette dernière capacité reste un point faible central. [arxiv](https://arxiv.org/abs/2604.20006)

## Conclusion opérationnelle

Pour éviter l'accumulation infinie, je construirais le harnais autour de quatre principes :

1. **Journaliser largement, mais persister parcimonieusement.**
2. **Séparer épisodes, faits, procédures, décisions et documents.**
3. **Mettre à jour et consolider plutôt qu'ajouter.**
4. **Traiter l'oubli, l'expiration et l'invalidation comme des opérations de première classe.**

Le bon modèle mental n'est donc pas « une mémoire qui se remplit », mais une **mémoire qui se transforme** :

```text
trace brute
  → épisode court
  → leçon validée
  → fait ou procédure
  → consolidation
  → expiration, archivage ou suppression
```

Pour un harnais de recherche ou de code, une architecture hybride fichiers + base structurée + recherche BM25/embeddings + worker de consolidation constitue probablement le meilleur compromis actuel entre inspectabilité, sobriété, coût et robustesse.
