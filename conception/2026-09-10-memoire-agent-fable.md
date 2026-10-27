# Mémoire des agents — rapport d'étude (Fable, 2026-09-10)

> **NON NORMATIF.** Rapport d'étude, enregistré pour information. Rien ici
> n'est décidé, adopté ni applicable au harness. Aucune règle, aucun agent et
> aucun outil ne doit s'y référer comme à une prescription : la section
> « Proposition pour ImperialDragonHarness » est une suggestion de l'auteur du
> rapport, pas une architecture retenue. Les normes du harness vivent dans
> `rules/`, `CLAUDE.md` et les tickets — pas dans `docs/`.

**Auteur :** Fable. **Enregistré le :** 2026-09-10, verbatim.
Les affirmations chiffrées et les références sont celles de l'auteur et n'ont
pas été revérifiées à l'enregistrement.

Premier des trois rapports sollicités indépendamment sur la même question :
[`2026-09-10-memoire-agent-perplexity.md`](./2026-09-10-memoire-agent-perplexity.md),
[`2026-09-10-memoire-agent-chatgpt.md`](./2026-09-10-memoire-agent-chatgpt.md).
Voir aussi [`dream-research.md`](./dream-research.md) (note de recherche
`/dream`, 2026-05-13) et [`VISION-original.md`](./VISION-original.md).

Les trois rapports ont été sollicités **avant** la rédaction du document de
conception
[`2026-09-10-dragon-memory-design.md`](./2026-09-10-dragon-memory-design.md)
(arrivé par la PR #887) : ce sont des entrées amont, pas des relectures de ce
document. C'est lui qui porte la proposition du harness, pas ceux-ci ; la
calibration des seuils est dans
[`2026-09-10-portable-agent-memory-calibration.md`](./2026-09-10-portable-agent-memory-calibration.md).

---

## Cadre stabilisé (2025-2026)

Deux distinctions font désormais consensus. D'abord contexte (mémoire de travail, dans le prompt) vs mémoire longue (magasin externe) ; ensuite, au sein de la mémoire longue, la taxonomie épisodique / sémantique / procédurale, adoptée par LangMem, Letta et Mem0. Le survey le plus utile est Du (2026, arXiv 2603.07670), qui formalise la mémoire comme une boucle écrire–gérer–lire couplée à la perception et à l'action, avec une taxonomie sur trois axes : portée temporelle, substrat de représentation, politique de contrôle. Le point décisif pour votre question : la difficulté n'est pas le stockage mais l'étape « gérer » — fusionner, arbitrer les contradictions, oublier.

## Familles d'architectures

| Famille | Représentants | Apport | Limite |
|---|---|---|---|
| Contexte hiérarchique « OS » | MemGPT/Letta (blocs core éditables + archive paginée, *sleep-time compute*) | Le modèle gère lui-même sa pagination | Dérive des blocs, peu de contrôle sur l'oubli |
| Stores gérés par LLM | Mem0 (add/update/delete décidés par LLM), Zep/Graphiti (graphe bitemporel), A-MEM (Zettelkasten auto-lié) | Supersession et liens explicites | Coût par écriture, décisions opaques |
| Mémoire expérientielle / procédurale | Reflexion, ExpeL, Voyager ; puis ReasoningBank, Memp, ReMe, ACE | Apprendre des trajectoires, y compris des échecs | Qualité de la distillation ; pollution du pool |
| Politiques apprises (RL) | Memory-R1, « Agentic Memory » (Yu et al. 2026) | Write/forget optimisés sur tâche aval | Peu reproductible localement |
| Bio-inspiré | Human-Inspired Memory Architecture (2605.08538) | Mécanismes d'oubli explicites | Encore peu validé |

La troisième famille est celle qui répond à « se souvenir des expériences ». ReasoningBank distille des stratégies de raisonnement réutilisables, apprend spécifiquement des échecs, et annonce jusqu'à 20 % d'amélioration relative et 16 % d'interactions en moins. Memp transforme les trajectoires en instructions pas-à-pas et en scripts abstraits, avec un régime qui corrige et déprécie continûment le contenu. ReMe (ACL 2026) est le plus abouti sur la gestion du cycle de vie : distillation multi-facettes (succès, déclencheurs d'échec, insights comparatifs), réutilisation adaptée au contexte, et raffinement par utilité qui ajoute les mémoires validées et élague les obsolètes ; un Qwen3-8B ainsi équipé dépasse un Qwen3-14B sans mémoire. Côté bio-inspiré, l'architecture de mai 2026 combine consolidation en phase de sommeil, oubli par interférence, maturation des engrammes, reconsolidation à la lecture, graphe d'entités et retrieval multi-indices, chaque mécanisme visant un mode d'échec précis de l'accumulation naïve.

## Évaluation et limites connues

Les benchmarks sont passés du rappel statique à des tests agentiques couplant mémoire et action (MemBench, MemoryAgentBench, MemoryArena) ; les gains restent modestes sur les contradictions temporelles et le raisonnement multi-sauts. Sécurité : une étude 2026 sur l'empoisonnement de mémoire trouve plus de 90 % des agents testés vulnérables, avec 100 % de rechute quand on tente de corriger par conversation. Les défis ouverts listés par Du sont exactement les vôtres : consolidation continue, retrieval causalement fondé, réflexion fiable, oubli appris.

## Principes pour ne pas accumuler à l'infini

1. Trois niveaux de rétention à règles distinctes : trace brute (immuable, jamais chargée, rétention par âge) ; épisodes distillés (TTL, promotion possible) ; connaissance curée (plafond de taille, pas de TTL).
2. Filtrer à l'écriture, pas seulement à la lecture. Critères explicites : surprise (écart à l'attendu), coût de redécouverte, généralité, stabilité à un mois. Une mention isolée ne s'écrit pas ; une récurrence si.
3. Consolider hors ligne, jamais par append : fusion des doublons, généralisation épisodes → règle, contradiction résolue par supersession datée (« X, précédemment Y »). C'est le schéma que j'utilise ici : passe de fond après chaque tour, fichiers plafonnés, réorganisation obligatoire à l'approche du plafond.
4. Oublier par utilité, pas par âge seul : score = rappels ayant effectivement changé une décision × récence × généralité ; démotion vers archive avant suppression.
5. Bitemporalité (valid_time / transaction_time) et provenance par ligne (stated / observed / inferred) — indispensables pour l'audit et contre l'empoisonnement. Corollaire : la mémoire est une donnée, jamais une instruction.

## Proposition pour ImperialDragonHarness

*[Note d'enregistrement — non de l'auteur du rapport : ce qui suit est
une proposition soumise à l'étude, non un état des lieux du harness ni
un plan approuvé.]*

Substrat : markdown + frontmatter YAML, versionné dans git (le diff devient le journal de consolidation gratuit). Un index (chemin + description d'une ligne) toujours chargé ; contenu à la demande.

- `log/` : JSONL par session, rotation 90 j (restic si besoin).
- `episodes/` : une note par tâche (objectif, ce qui a marché, échecs, correction), 10–20 lignes, générée en fin de session par un modèle local Ollama ; TTL 60–90 j sauf promotion.
- `knowledge/` (projets, conventions) et `procedures/` (playbooks, avec compteurs `uses`, `successes`, `last_used`) : plafond par fichier.
- Processus en ligne : extraction fin de session sous critères. Processus hors ligne : cron nocturne local qui consolide episodes → knowledge/procedures, score, archive, et ouvre une PR git pour revue humaine des changements de `procedures/` (seule ligne de défense sérieuse contre l'empoisonnement).
- Lecture hybride : SQLite FTS5 + embeddings Ollama, fusion RRF.
- Métriques de pilotage : taille totale ; taux de rappel utile (mémoire chargée et effectivement mobilisée) ; taux de redécouverte (même erreur deux fois, traçable via git-erg) ; tokens de mémoire par session.

Options classées : (1) fichiers + git + consolidation locale — standard, auditable, sans verrou ; (2) ajouter Graphiti (open source, bitemporel) si beaucoup d'entités liées et requêtes temporelles, au prix d'un Neo4j/FalkorDB à opérer ; (3) Letta ou Mem0 OSS — clé en main, mais décisions d'écriture cachées derrière l'abstraction. À éviter : vector store seul en append-only ; fine-tuning continu, opaque et non auditable.
