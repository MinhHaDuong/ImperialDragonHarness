# Mémoire des agents — rapport d'étude (ChatGPT, 2026-09-10)

> **NON NORMATIF.** Rapport d'étude, enregistré pour information. Rien ici
> n'est décidé, adopté ni applicable au harness. Aucune règle, aucun agent et
> aucun outil ne doit s'y référer comme à une prescription : les sections
> « L'architecture que je recommande pour votre harnais » et « Implémentation
> minimale et évaluation » sont des suggestions de l'auteur du rapport, pas
> une architecture retenue. Les normes du harness vivent dans `rules/`,
> `CLAUDE.md` et les tickets — pas dans `docs/`.

**Auteur :** ChatGPT, prompté par Ha-Duong Minh.
**Enregistré le :** 2026-09-10, verbatim.
Les affirmations chiffrées et les références sont celles de l'auteur et n'ont
pas été revérifiées à l'enregistrement.

Troisième des trois rapports sollicités indépendamment sur la même question :
[`2026-09-10-memoire-agent-fable.md`](./2026-09-10-memoire-agent-fable.md),
[`2026-09-10-memoire-agent-perplexity.md`](./2026-09-10-memoire-agent-perplexity.md).
Voir aussi [`dream-research.md`](./dream-research.md) (note de recherche
`/dream`, 2026-05-13).

Les trois rapports ont été sollicités **avant** la rédaction du document de
conception
[`2026-09-10-dragon-memory-design.md`](./2026-09-10-dragon-memory-design.md)
(arrivé par la PR #887) : ce sont des entrées amont, pas des relectures de ce
document. C'est lui qui porte la proposition du harness, pas ceux-ci ; la
calibration des seuils est dans
[`2026-09-10-portable-agent-memory-calibration.md`](./2026-09-10-portable-agent-memory-calibration.md).

---

# Mémoire agentique : apprendre sans accumuler indéfiniment

*10 septembre 2026 — Préparé par ChatGPT prompté par Ha-Duong Minh*

## Synthèse exécutive

**Je recommande une mémoire externe, sélective et vérifiable : peu de contexte résident, des expériences récupérées à la demande, des leçons consolidées sous contrôle, et une véritable politique de suppression.** L'objectif n'est pas de conserver la conversation : c'est de conserver ce qui améliore les décisions futures.

La littérature a dépassé le simple « historique + recherche vectorielle ». Elle explore maintenant la structuration des souvenirs, leur transformation en procédures, la résolution des contradictions, l'oubli sélectif et l'apprentissage des politiques de gestion. Mais une mise en garde importante ressort des travaux récents : **résumer continuellement ses expériences peut dégrader un agent, parfois sous sa performance sans mémoire**. Une bonne architecture doit donc préserver certaines preuves originales et tester les abstractions qu'elle en tire. ([arXiv][1])

Pour Imperial Dragon, mon arbitrage serait : **conserver les décisions, sélectionner les épisodes, mettre les leçons à l'épreuve, transformer les apprentissages robustes en tests ou procédures, supprimer les représentations devenues inutiles.**

*Sommaire : 1. Les distinctions utiles · 2. L'état de l'art · 3. Les limites empiriques · 4. L'architecture proposée · 5. Le cycle d'apprentissage · 6. L'oubli et les budgets · 7. L'implémentation et l'évaluation.*

## 1. Les distinctions utiles

### La mémoire n'est ni le contexte, ni la bibliothèque

Le **contexte** est ce que le modèle voit maintenant. La **mémoire persistante** contient ce qui peut être mobilisé plus tard. La **bibliothèque documentaire** conserve les sources du travail. Ces objets peuvent partager les mêmes outils de recherche, mais n'ont pas la même fonction : consulter un article n'est pas apprendre qu'une méthode employée hier a échoué dans certaines conditions. La frontière avec le RAG est donc fonctionnelle, pas une opposition entre technologies. ([arXiv][2])

La synthèse de Hu et collaborateurs distingue trois supports : mémoire **explicite en tokens**, mémoire **paramétrique** dans les poids, et mémoire **latente** dans des représentations internes. Elle distingue aussi les fonctions factuelle, expérientielle et de travail. ([arXiv][1])

Pour un harnais portable entre modèles et clients, je privilégierais nettement la mémoire explicite : son contenu peut être inspecté, corrigé, transféré et soumis à des tests indépendamment du modèle.

### Retenir une expérience n'est pas encore apprendre

Je distinguerais trois degrés :

**L'épisode** : « Dans cette situation, cette action a produit ce résultat. »

**La leçon** : « Dans cette classe de situations, cette action semble préférable, sous telles conditions. »

**La procédure** : « Voici comment agir, avec des préconditions et un moyen de vérifier le résultat. »

Le passage de l'un à l'autre est une **inférence**, non une simple compression. C'est précisément là qu'il faut placer le contrôle qualité.

## 2. L'état de l'art : les avancées qui comptent

### 2.1. Hiérarchiser la mémoire et charger à la demande

**MemGPT, en 2023**, formalise une mémoire virtuelle : un espace actif limité, des mémoires externes et des opérations permettant de déplacer l'information entre niveaux. L'apport durable est de dissocier la capacité de stockage du contenu immédiatement présenté au modèle. Cela ne résout toutefois pas, à lui seul, la sélection des souvenirs à conserver. ([arXiv][3])

Les pratiques d'ingénierie prolongent cette idée : conserver des identifiants légers — chemins, requêtes, références — puis charger les données utiles au moment opportun. Anthropic distingue ainsi compaction du contexte, prise de notes structurées et délégation à des sous-agents. **Un pointeur pertinent peut remplacer des milliers de tokens résidents.** ([Anthropic][4])

### 2.2. Apprendre de l'expérience sans modifier les poids

**Reflexion** conserve un retour formulé en langage naturel sur les essais précédents. **ExpeL**, publié à AAAI 2024, extrait des enseignements à partir d'expériences et rappelle à la fois ces enseignements et des exemples antérieurs. Il s'agit d'une adaptation par le contexte, pas nécessairement d'un entraînement du modèle. ([arXiv][5])

**Voyager** apporte un autre résultat conceptuel important : la mémoire d'expérience peut être une bibliothèque de code exécutable et composable, plutôt qu'un ensemble de souvenirs narratifs. En revanche, sa bibliothèque est conçue pour croître ; ce n'est pas une solution générale à la mémoire bornée. ([arXiv][6])

**Conséquence pour un harnais de chercheur : une expérience utile peut finir comme test, script, modèle de document ou protocole, et non comme paragraphe dans `MEMORY.md`.**

### 2.3. Structurer les souvenirs, leur temporalité et leur provenance

Trois directions se complètent :

| Direction                              | Travaux représentatifs       | Apport                                                                                               |
| -------------------------------------- | ---------------------------- | ---------------------------------------------------------------------------------------------------- |
| Notes atomiques reliées                | **A-MEM**, NeurIPS 2025      | Des notes contextualisées, des liens et une évolution des représentations, inspirés du Zettelkasten. |
| Extraction et mise à jour des faits    | **Mem0** ; **Zep/Graphiti**  | Sélection des informations saillantes ; gestion des relations et, chez Zep, de leur temporalité.     |
| Séparation des statuts de connaissance | **Hindsight**, décembre 2025 | Distinction entre faits du monde, expériences de l'agent, synthèses et croyances.                    |

Ces architectures évitent de traiter tous les fragments comme des passages interchangeables. Elles ne dispensent cependant pas de décider lesquels sont fiables, périmés ou superflus. ([arXiv][7])

Pour votre usage, **séparer observation et interprétation me semble plus prioritaire que choisir entre une base vectorielle et un graphe**.

### 2.4. Consolider sans réécrire toute la mémoire

**ACE — Agentic Context Engineering**, en 2025, identifie notamment le risque d'érosion des détails lors de réécritures successives. Il propose des mises à jour localisées d'un ensemble de stratégies, avec curation et déduplication, plutôt que la réécriture monolithique d'un grand résumé. ([arXiv][8])

**SimpleMem**, en janvier 2026, combine compression structurée, consolidation et récupération adaptée à la requête. **FadeMem**, également en janvier, étudie explicitement l'oubli, avec une rétention modulée par pertinence, fréquence d'accès et temporalité. Ces travaux rendent la gestion du cycle de vie centrale, au-delà du seul moteur de recherche. ([arXiv][9])

L'industrialisation suit cette direction : la fonctionnalité **« dreaming »** présentée par Anthropic en mai 2026 examine des sessions et des mémoires entre les tâches pour en extraire des régularités, avec possibilité de revue des changements. C'est un mécanisme de maintenance de mémoire ; son existence ne constitue pas une validation générale de l'auto-amélioration. ([Claude][10])

### 2.5. Apprendre la politique de mémoire elle-même

**Memory-R1** apprend des opérations telles que `ADD`, `UPDATE`, `DELETE`, `NOOP`. **AgeMem** intègre stockage, récupération, résumé et suppression dans une politique entraînée par renforcement. La mémoire devient ainsi un espace d'actions, dont on cherche à optimiser l'effet sur le résultat final. ([arXiv][11])

Une prépublication d'août 2026, **Dual-Layer Agentic Memory**, pousse la sélection vers l'écriture : ne rien enregistrer, créer ou mettre à jour, puis éventuellement transférer certains acquis dans les paramètres du modèle. Les auteurs signalent encore des coûts de consolidation, des conflits temporels et de l'interférence paramétrique. **Je retiendrais le filtrage à l'entrée, mais pas l'entraînement paramétrique comme première étape pour Imperial Dragon.** ([arXiv][12])

## 3. Les limites empiriques à prendre au sérieux

### Une mémoire consolidée peut devenir nuisible

La prépublication **Useful Memories Become Faulty When Continuously Updated by LLMs**, déposée en mai et révisée le 29 août 2026, observe des trajectoires où l'utilité de la mémoire augmente puis diminue. Les auteurs attribuent notamment cette dégradation aux mauvaises généralisations et aux distinctions perdues pendant la consolidation. Des mémoires d'épisodes restent compétitives face aux abstractions produites. ([arXiv][13])

Il ne faut pas en conclure « ne jamais consolider ». Il faut en conclure : **ne pas confondre résumé plausible et connaissance validée**. L'étude porte sur des environnements et modèles déterminés ; elle ne démontre pas une impossibilité universelle. ([arXiv][14])

### Savoir oublier une information fausse est distinct de savoir la retrouver

**LongMemEval**, publié à ICLR 2025, teste déjà les mises à jour de connaissances, le raisonnement temporel et l'abstention. **Memora**, en avril 2026, ajoute une évaluation pénalisant explicitement l'utilisation de souvenirs invalidés. Ses résultats montrent que disposer d'anciens souvenirs sans bien appliquer leurs mises à jour peut amplifier les incohérences. ([arXiv][15])

### Les classements ne suffisent pas

Les comparaisons restent sensibles au modèle de base, aux métriques, aux juges et au coût de construction des mémoires. Les gains en lecture peuvent masquer des dépenses importantes d'extraction et de maintenance. **MemoryBench** cherche justement à aller au-delà du rappel conversationnel pour mesurer l'apprentissage à partir du retour utilisateur. ([arXiv][16])

Mon critère de décision serait donc : **l'agent refait-il moins les mêmes erreurs, avec une dépense totale maîtrisée ?**

## 4. L'architecture que je recommande pour votre harnais

Je séparerais les rôles suivants, sans imposer nécessairement une nouvelle arborescence :

| Compartiment                   | Contenu                                                      | Politique                                                                  |
| ------------------------------ | ------------------------------------------------------------ | -------------------------------------------------------------------------- |
| **Constitution du harnais**    | Règles, permissions, conventions stables                     | Petite, explicitement validée ; pas réécrite par l'apprentissage ordinaire |
| **État courant du projet**     | Objectif, décisions applicables, blocages, prochaine action  | Remplacé et actualisé, pas alimenté comme un journal                       |
| **Mémoire épisodique**         | Cas sélectionnés : situation, action, résultat, preuves      | Récupérée à la demande ; rétention bornée                                  |
| **Leçons et faits consolidés** | Enseignements conditionnels, connaissances locales vérifiées | Fiches atomiques, sourcées, révisables                                     |
| **Mémoire procédurale**        | Skills, scripts, tests, protocoles                           | Maintenance comme du code ou de la documentation de référence              |

**Les transcriptions brutes sont un tampon de diagnostic, pas un sixième réservoir éternel.**

Les articles, données et livrables scientifiques restent dans leurs dépôts documentaires. La mémoire du harnais doit principalement conserver **où ils sont, pourquoi ils comptent et ce qui a été appris en les utilisant**, plutôt que les recopier.

Je séparerais aussi les périmètres : mémoire personnelle privée, mémoire générale validée du harnais, mémoire de chaque projet. Une leçon locale ne devient globale qu'après examen de sa transférabilité. Les agents travaillant en parallèle proposent des modifications ; ils ne réécrivent pas concurremment le même résumé.

## 5. Le cycle d'apprentissage : sélectionner, vérifier, transformer

### À l'écriture : autoriser explicitement « rien à retenir »

Une fin de session ne doit pas obligatoirement produire une leçon. Je déclencherais une candidature mémoire lorsqu'il y a une correction humaine, une erreur coûteuse, une méthode vérifiée, une décision durable ou une découverte difficile à reproduire.

À l'inverse, je n'enregistrerais pas un succès banal, une reformulation du plan ou une information facilement relisible dans la configuration. **Le bon objet est le changement de connaissance, pas le compte rendu de l'activité.**

Une fiche devrait permettre de répondre à ces questions : dans quel périmètre vaut-elle, que s'est-il effectivement passé, quelle interprétation en tire-t-on, quelle preuve la soutient, quand doit-elle être rappelée, et qu'est-ce qui la rendrait caduque ?

Exemple **fictif** :

```yaml
type: lesson
scope: projet-analyse
status: candidate
trigger: reprise d'une extraction de données
observation: une modification de format a invalidé le parseur
recommendation: vérifier le schéma avant de réutiliser les résultats
evidence: référence vers le test et l'extrait d'entrée conservés
validity: version du format effectivement testée
review_on: changement du format source
```

Il faut distinguer **« le test a échoué »**, une observation, de **« il a échoué à cause de X »**, une explication parfois encore hypothétique.

### À la consolidation : produire une modification vérifiable

Je privilégierais une consolidation ciblée : plusieurs incidents apparentés, une contradiction, une fiche trop volumineuse, ou un quota proche de saturation. Pas un grand résumé de toutes les mémoires après chaque interaction.

Le consolidateur proposerait une modification localisée, avec les épisodes qui la justifient. La validation vérifierait notamment la conservation des conditions d'application, des exceptions, des versions et des contre-exemples.

**Une règle générale doit rester reliée à quelques cas concrets représentatifs.** Ceux-ci peuvent être des extraits minimaux plutôt que des sessions entières. Si leurs preuves disparaissent, il faut le signaler ; la leçon ne doit pas continuer à se présenter comme aisément vérifiable.

Cela reprend le résultat prudent des travaux sur la dégradation des mémoires : conserver des épisodes comme preuves et ne pas forcer toute expérience à devenir une abstraction. ([arXiv][17])

### À la maturation : transformer la leçon en mécanisme

C'est, à mon sens, le principal moyen d'éviter l'inflation.

Une erreur récurrente de format devient un **validateur**. Une séquence fiable devient un **script testé**. Un oubli méthodologique devient une **vérification dans le protocole**. Un arbitrage durable rejoint le **registre des décisions**.

La fiche narrative peut alors être réduite à un pointeur et à une justification courte. Il ne faut pas conserver parallèlement cinq formulations de la même règle dans les souvenirs, les instructions, le skill, la documentation et les notes de session.

**Le harnais apprend véritablement lorsque son fonctionnement s'améliore, pas seulement lorsque son récit s'allonge.**

### À la lecture : rechercher aussi les conditions et les exceptions

La récupération devrait d'abord filtrer par projet, statut et validité, puis combiner recherche exacte et sémantique. Elle devrait chercher les échecs et les contre-exemples pertinents, pas seulement les réussites ressemblantes.

Des approches comme Hindsight combinent plusieurs modes de recherche et un filtrage par budget de tokens ; SimpleMem adapte la profondeur de récupération à la requête. Cela fournit des modèles utiles, sans imposer leur infrastructure complète. ([arXiv][18])

Je chargerais en deux temps : quelques intitulés et recommandations, puis les preuves des fiches effectivement utiles. Une recherche infructueuse doit pouvoir aboutir à **« aucune expérience pertinente retrouvée »**, sans compléter par invention.

## 6. Comment oublier sans tout perdre

### Distinguer quatre opérations

**Compresser** réduit une représentation. **Invalider** indique qu'elle n'est plus applicable. **Retirer de la mémoire active** évite son rappel ordinaire. **Supprimer** élimine réellement les données.

Déplacer tous les anciens éléments dans `archive/` ne résout pas l'accumulation : cela la déplace.

Il existe ici une contrainte logique : avec un stockage strictement borné et un flux indéfini d'informations nouvelles, on ne peut pas garantir la restitution exacte de tout le passé. Il faut choisir quelles pertes sont acceptables. Pour votre harnais, je sacrifierais d'abord les détails redondants et reproductibles, pas les décisions structurantes ni les preuves rares.

### Oublier selon l'utilité attendue, pas seulement selon l'âge

Je raisonnerais avec une fonction de valeur de ce type :

$$
V(m)=
P(\text{réutilisation})\times
\text{coût évité}\times
\text{fiabilité}
-\text{coût de maintenance}
-\text{redondance}.
$$

Ce n'est pas une formule empirique établie, mais un principe d'arbitrage. Sous contrainte de budget, on privilégie la valeur marginale par unité de place, tout en réservant une protection aux informations critiques.

La fréquence de consultation ne suffit pas : une fiche peut être souvent récupérée parce qu'elle est trop générale. Il faut distinguer **récupérée**, **utilisée**, et **utile au résultat**.

De même, ancien ne veut pas dire faux. Une décision méthodologique peut rester pertinente dix ans ; une observation sur une version logicielle peut devenir caduque demain. Je donnerais donc aux fiches des conditions de réexamen, pas seulement une date d'expiration.

### Imposer des plafonds exécutoires

Voici une **politique initiale à tester**, et non des seuils issus de la littérature :

| Ressource                          | Point de départ proposé                                       |
| ---------------------------------- | ------------------------------------------------------------- |
| Mémoire injectée au démarrage      | **1 500–3 000 tokens**, hors outils et documents de travail   |
| Souvenirs récupérés pour une tâche | **4 000 tokens supplémentaires** par défaut                   |
| Fiches d'expérience actives        | **200 par projet**, avec un plafond global distinct           |
| Traces brutes                      | **30 jours ou 1 Go**, première limite atteinte                |
| Consolidation                      | Budget explicite en tokens, appels et volume traité par passe |

Un quota par projet ne suffit pas si le nombre de projets croît indéfiniment. Il faut également un plafond global en octets, couvrant les preuves conservées, les index, les anciennes versions et les instantanés.

**Ces limites doivent être appliquées par le programme, pas laissées à la bonne volonté du modèle.** Le modèle propose les fusions et suppressions ; le programme vérifie les quotas, les protections et les dépendances. Lorsque le budget protégé est saturé, il faut un arbitrage explicite, pas une suppression silencieuse.

Enfin, une suppression réelle doit tenir compte des copies et historiques. Je ne placerais donc pas les traces brutes ou sensibles dans un dépôt destiné à conserver indéfiniment toutes ses versions.

## 7. Implémentation minimale et évaluation

### Commencer simple et indépendant des fournisseurs

Pour Imperial Dragon, je commencerais par des fiches texte structurées, un index local reconstructible et trois points d'intégration : **charger l'état au démarrage, proposer les apprentissages à la fin d'un épisode significatif, effectuer une maintenance bornée**.

Le stockage canonique resterait indépendant de Claude Code, Codex ou Pi ; les adaptateurs serviraient à présenter le même contenu et les mêmes opérations. J'éviterais plusieurs mémoires natives concurrentes qui se recopient mutuellement.

Je n'introduirais un graphe complet ou une politique entraînée par renforcement qu'après avoir mesuré une limite concrète du système simple.

La frontière de confiance est essentielle : une mémoire issue d'un document ou d'un résultat d'outil reste une donnée, pas une instruction autorisée à modifier les règles du harnais. Les attaques MINJA montrent que des interactions peuvent contaminer une mémoire et influencer les actions ultérieures. **La promotion vers une instruction ou un skill doit donc être contrôlée.** ([arXiv][19])

### Tester l'apprentissage, et pas seulement le rappel

Je constituerais un petit banc d'essai chronologique de vos workflows, en comparant :

1. **État courant seul**, sans mémoire d'expérience.
2. **État courant + épisodes sélectionnés**.
3. **État courant + épisodes + leçons consolidées**.

La troisième configuration doit justifier son surcoût et ne pas dégrader les tâches précédemment maîtrisées. Il faut également tester après plusieurs cycles de maintenance, et pas seulement après la première consolidation.

Les cas décisifs seraient : reprendre un projet ancien, ne pas répéter une erreur, appliquer une décision révisée, retrouver une exception, reconnaître qu'un souvenir n'est plus valable et s'abstenir lorsque les preuves manquent. La séparation temporelle entre apprentissage et évaluation est indispensable pour ne pas mesurer une simple restitution des cas utilisés pour fabriquer la mémoire.

Je suivrais surtout **le taux d'erreurs répétées, l'usage de souvenirs périmés, le temps de reprise d'un projet et le coût total lecture–écriture–maintenance**. Le volume stocké serait une contrainte, pas un indicateur de progrès.

### Mon ordre de priorité

**D'abord :** séparer état courant, épisodes, leçons et procédures ; rendre provenance et validité explicites.

**Ensuite :** imposer les budgets, la récupération sélective et une consolidation avec tests de non-régression.

**Enfin :** automatiser davantage la sélection et la consolidation, uniquement là où l'évaluation en montre le bénéfice.

**Le signe d'un harnais qui mûrit ne devrait pas être un `MEMORY.md` toujours plus gros. Ce devrait être moins d'erreurs récurrentes, des reprises de projet plus rapides et davantage de savoir-faire vérifiable, pour une charge de mémoire stabilisée.**

[1]: https://arxiv.org/abs/2512.13564 "[2512.13564] Memory in the Age of AI Agents"
[2]: https://arxiv.org/html/2512.13564v2 "Memory in the Age of AI Agents: A SurveyForms, Functions and Dynamics"
[3]: https://arxiv.org/abs/2310.08560?utm_source=chatgpt.com "MemGPT: Towards LLMs as Operating Systems"
[4]: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents "Effective context engineering for AI agents \ Anthropic"
[5]: https://arxiv.org/abs/2303.11366?utm_source=chatgpt.com "Reflexion: Language Agents with Verbal Reinforcement Learning"
[6]: https://arxiv.org/abs/2305.16291?utm_source=chatgpt.com "Voyager: An Open-Ended Embodied Agent with Large Language Models"
[7]: https://arxiv.org/abs/2502.12110 "[2502.12110] A-MEM: Agentic Memory for LLM Agents"
[8]: https://arxiv.org/html/2510.04618v1 "Agentic Context Engineering: Evolving Contexts for Self-ImprovingLanguage Models"
[9]: https://arxiv.org/abs/2601.02553?utm_source=chatgpt.com "SimpleMem: Efficient Lifelong Memory for LLM Agents"
[10]: https://claude.com/blog/new-in-claude-managed-agents "New in Claude Managed Agents: dreaming, outcomes, and multiagent orchestration | Claude by Anthropic"
[11]: https://arxiv.org/abs/2508.19828?utm_source=chatgpt.com "Memory-R1: Enhancing Large Language Model Agents to Manage and Utilize Memories via Reinforcement Learning"
[12]: https://arxiv.org/abs/2608.22215 "[2608.22215] Dual-Layer Agentic Memory with Fast Write Routing and Slow Consolidation"
[13]: https://arxiv.org/abs/2605.12978 "[2605.12978] Useful Memories Become Faulty When Continuously Updated by LLMs"
[14]: https://arxiv.org/html/2605.12978v1 "Useful Memories Become FaultyWhen Continuously Updated by LLMs"
[15]: https://arxiv.org/abs/2410.10813 "[2410.10813] LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory"
[16]: https://arxiv.org/html/2602.19320v2 "Anatomy of Agentic Memory: Taxonomy and Empirical Analysis of Evaluation and System Limitations"
[17]: https://arxiv.org/html/2605.12978v2 "Useful Memories Become FaultyWhen Continuously Updated by LLMs"
[18]: https://arxiv.org/html/2512.12818v1 "Hindsight is 20/20: Building Agent Memory that Retains, Recalls, and Reflects"
[19]: https://arxiv.org/abs/2503.03704?utm_source=chatgpt.com "A Practical Memory Injection Attack against LLM Agents"
