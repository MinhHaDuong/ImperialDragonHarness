# La mémoire du Dragon — conception v8

**Date :** 1 octobre 2026.
**Statut :** nouvelle direction demandée par l’auteur ; spécification, sans
changement du fonctionnement des runtimes dans cette révision.
**Rédaction :** Codex, à partir des décisions de Ha-Duong Minh.
**Prédécesseur :** [v7 conservée](2026-09-10-dragon-memory-design-v7.md).
**Livraison :** [plan v8](2026-09-11-memory-implementation-plan.md), tracker 0909.

## 1. But et décision d’architecture

La mémoire commune habite le dépôt du projet. Elle doit être lisible, recherchable
et révisable avec Markdown, Git et les outils ordinaires de l’agent. Les quatre
runtimes visés sont Claude Code, Codex, Pi et Vibe. Leurs mémoires natives restent
actives mais ne constituent pas la référence commune : le rêve les considère
comme des sources attribuées, susceptibles d’être incomplètes ou contradictoires.

V8 remplace la bibliothèque et le CLI `hoard`, le compilateur, les manifests de
publication, les snapshots partagés obligatoires, les budgets par canal et la
grammaire de prédicats par des conventions de fichiers et des instructions.
Aucun serveur de mémoire, MCP, embedding, base de données ou modèle de classement
n’est nécessaire. La recherche lexicale suffit au premier dispositif ; une
insuffisance observée pourra motiver une décision ultérieure.

Le circuit est : **capture factuelle → consolidation → revue → connaissance
acceptée**. La capture n’interprète pas l’expérience.
La consolidation peut ne produire aucune leçon ; elle ne doit pas en inventer.

## 2. Convention dans chaque dépôt

```text
AGENTS.md                         # instructions courtes et règles adoptées
CLAUDE.md -> AGENTS.md             # compatibilité si nécessaire
memory/
  MEMORY.md                       # index court, environ 100 lignes
  DREAM.md                        # prompt de consolidation versionné
  topics/
    <theme>.md                    # connaissances consolidées avec sources
  journal/
    AAAA/
      AAAA-MM-JJ-<slug>.md         # expériences factuelles, append-only
  dreams/
    AAAA-MM-JJ-<slug>.md           # rapports de traitement et provenance
```

Chaque projet possède son dossier. Les notes propres au harness restent sa
mémoire de projet ; elles n’acquièrent pas une portée générale par leur emplacement.
La référence d’installation du harness est `~/.agents`, mais ce chemin n’est pas
une API : toute consommation doit fonctionner dans un clone situé ailleurs.

Les liens sont relatifs et les noms descriptifs. Le journal reste classé par
année et date ; plusieurs épisodes le même jour reçoivent des slugs distincts.
En cas de collision, ajouter un suffixe distinctif, jamais écraser une entrée.
Le chemin conservé et l’historique Git suffisent à identifier une expérience ;
il n’y a pas d’obligation de UUID ou de schéma exécutable.

`MEMORY.md` pointe vers les thèmes utiles et le journal récent. Il ne contient
ni le corpus entier ni une copie des instructions. Environ 100 lignes et 300 mots
par expérience sont des repères éditoriaux, pas des seuils validés ou des quotas
à remplir. Un épisode simple peut tenir en quelques phrases.

## 3. Lecture commune aux runtimes

Une section courte d’AGENTS.md prescrit de :

1. Lire `memory/MEMORY.md` au début de la tâche lorsqu’il existe.
2. Ouvrir les thèmes pertinents avant l’action qu’ils peuvent éclairer.
3. Consulter le journal, y compris les expériences pas encore consolidées, avec
   `rg` ou `grep` lorsque la tâche ou un obstacle appelle une recherche.
4. Rechercher de nouveau quand la tâche change matériellement.
5. À roar, enregistrer et commiter les expériences significatives, s’il y en a.

Seul l’index est demandé systématiquement ; les thèmes et le journal sont ouverts
à la demande. Aucun hook commun ne garantit cette lecture. La consigne dans
AGENTS.md est le contrat portable ; son respect reste une propriété comportementale.
L’absence d’index ou de thème ne doit pas empêcher une tâche, et doit être signalée
si elle révèle une installation incomplète plutôt qu’un projet sans mémoire.

Claude peut employer un lien relatif CLAUDE.md vers AGENTS.md pour les installations
qui en ont besoin ; éviter un second contenu divergent. Les capacités réelles
se vérifient avec les versions installées, les dossiers de confiance et les
mécanismes de chargement propres à chaque runtime. V8 ne prétend pas que
`memory/MEMORY.md` est automatiquement injecté nativement partout.

## 4. Capture factuelle à roar

Roar sauvegarde et commite automatiquement les épisodes significatifs, positifs
comme négatifs. Les réussites, échecs, quasi-accidents, dommages évités et réussites
étonnamment faciles sont éligibles. Si rien de significatif ne s’est produit,
aucune entrée ni commit vide n’est nécessaire.

Une expérience est significative si elle introduit une nouveauté pertinente,
contredit une attente attestée, affecte matériellement le travail ou expose un
conflit entre une procédure prescrite et les circonstances rencontrées.

Ce critère est une traduction opérationnelle inspirée de la psychologie, pas
une définition consensuelle de la signification ni une mesure des émotions de
l’agent. La nouveauté et la surprise se distinguent ; les buts et la priorité
orientent la mémoire humaine. La valence positive ou négative ne donne aucune
priorité automatique. Le coût observable traduit « pénible » sans inventer
une expérience subjective de l’agent.

Une entrée contient :

- date de l’épisode et contexte ;
- ce qui s’est passé, avec l’attente préalable seulement si elle est attestée ;
- résultat observé, coût ou dommage évité s’il est connu ;
- liens vers les preuves, commits, tickets ou décisions déjà prises.

Roar ne tire pas de leçon, ne juge pas les acteurs et ne propose pas de nouvelles
règles, mémoires interprétées ou promotions. Une décision est référencée dans son
registre canonique, pas adoptée par son inscription dans le journal. Les constats
incertains ou rapportés sont attribués ; un résultat observé n’établit pas sa cause.

Le journal est append-only. Une correction prend la forme d’une nouvelle entrée
qui référence l’ancienne. La consolidation conserve les récits et leurs liens.
L’agent ne reproduit pas un diff ou un compte rendu de routine uniquement pour
remplir le journal : les artefacts ordinaires sont des preuves à citer.

### Fondements du critère de signification

- [Nouveauté et encodage épisodique](https://pmc.ncbi.nlm.nih.gov/articles/PMC8024513/).
- [Distinction entre nouveauté et surprise](https://pmc.ncbi.nlm.nih.gov/articles/PMC3858647/).
- [Mather et Sutherland, priorité et activation émotionnelle, 2011](https://pmc.ncbi.nlm.nih.gov/articles/PMC3110019/).
- [Conway et Pleydell-Pearce, mémoire autobiographique et buts, 2000](https://pubmed.ncbi.nlm.nih.gov/10789197/).

Les conflits de règles et les coûts du travail sont nos traductions d’ingénierie.
Ces travaux sur l’humain ne valident pas les seuils ni le comportement d’un agent.

## 5. Git et préservation des observations

L’écriture a lieu dans une branche de travail autorisée du dépôt du projet,
pas dans la mémoire native ni dans le checkout partagé qui sert aux pulls du
harness. Le commit regroupe les fichiers de clôture roar : capture, tickets et docs.
Les changements voisins d’une autre tâche ne doivent pas être embarqués.

Dans un workflow où roar suit la fusion, créer au plus une branche de clôture unique,
commiter ensemble épisodes, tickets et docs, puis une PR en auto-merge après
les contrôles requis. Ne pas
ajouter les souvenirs à une branche déjà fusionnée puis la supprimer. L’agent
porte les opérations de sauvegarde et d’intégration, sans demander à l’auteur
de commiter manuellement les souvenirs. Une approbation éventuellement exigée
par le dépôt reste applicable ; une capture locale n’est pas une permission de
fusionner. La relecture éditoriale de l’auteur porte sur la PR de rêve.

Un commit local rend l’observation durable sur cette machine ; son intégration
et sa synchronisation la rendent disponible aux autres sessions. Une capture
non intégrée doit être signalée avec sa branche. En cas de conflit, conserver
les deux sources et résoudre explicitement ; ne jamais choisir par date seule.
Ni stash du checkout partagé ni suppression de fichiers pour forcer un pull.
Un worktree contenant une observation non sauvée ne doit pas être supprimé.

Pour un dossier sans Git, le souvenir peut être écrit mais ne doit pas être
annoncé comme commité ; le projet doit déclarer où sa mémoire versionnée habite.
Le fonctionnement normal vise les dépôts, sans inventer un store global implicite.

Ticket 0988 porte la preuve que la capture et l’intégration préservent les notes
et laissent le harness se mettre à jour, ainsi que le signal visible d’un échec.
Le déplacement du checkout sous 0999 ne suffit pas à remplir cette obligation.

## 6. Rêve hebdomadaire et connexions

Un timer systemd hebdomadaire lance un seul runtime non interactif disponible
sur l’hôte, avec `memory/DREAM.md`. La commande et son runtime sont configurés
pour cet hôte ; ils ne deviennent pas une dépendance des trois autres lecteurs.
Le timer travaille dans un checkout isolé et sur une branche dédiée.

Le prompt lui demande de :

1. Lire AGENTS.md, le prompt versionné, les thèmes et les rapports précédents.
2. Examiner les nouvelles expériences, corrections et épisodes connexes.
3. Ingérer les notes natives disponibles comme sources attribuées, avec leur
   origine et leur révision ou empreinte ; signaler les sources indisponibles.
4. Regrouper par thèmes, rapprocher aussi les issues positives et négatives,
   rechercher les contradictions et conserver les conditions et exceptions.
5. Mettre à jour `topics/` et `MEMORY.md` lorsque l’évidence le justifie.
6. Écrire un rapport listant les sources examinées, leur révision, les jugements
   éditoriaux, les questions non résolues, sans proposition de règles.
7. Commiter le résultat sur la branche et ouvrir une PR pour relecture.

Un thème peut seulement relier des expériences partageant une caractéristique,
avec une phrase indiquant ce rapprochement et des liens aux sources. Une connexion
n’est ni une cause établie ni une règle. Un épisode peut appartenir à plusieurs
thèmes. Une hypothèse est présentée comme telle, distincte d’une connaissance
étayée ; aucune répétition ne déclenche automatiquement une généralisation.

Les thèmes sont révisables. Ils citent les sources favorables et les exceptions
pertinentes. Le retrait d’une affirmation obsolète est explicite dans la PR et
l’historique, pour qu’elle ne subsiste pas dans l’index comme conseil actuel.
Les corrections du journal doivent être consultées pendant l’analyse.

« Archiver les entrées traitées » signifie consigner leur traitement dans le
rapport accepté, pas déplacer, réécrire ou supprimer les souvenirs. Une entrée
examinée sans leçon dérivée reste une expérience utile. Un rapport sur une
branche non fusionnée ne prouve pas un traitement accepté. Au passage suivant,
consulter les rapports fusionnés pour éviter de réingérer les mêmes révisions ;
une source modifiée appelle un nouvel examen.

Conserver le texte des notes natives effectivement utilisées, adapté à l’audience,
dans le rapport ou une annexe versionnée. Une empreinte seule ne permet pas
de retrouver une note que le runtime aura ensuite réécrite.

Il n’y a ni compteur de répétitions prescriptif ni base de relations séparée.
Les connexions utiles habitent les thèmes ; Git conserve leur évolution. Les
rapports donnent la provenance du passage, y compris runtime/modèle et commit
du prompt. La prose d’un rêve n’est pas supposée reproductible à l’identique.

## 7. Cristallisation et autorité

Les projets écrivent uniquement dans leur dépôt ou leur compagnon privé
explicitement configuré. Le harnais fournit des conventions et des outils ;
il ne reçoit ni leurs souvenirs, ni leurs thèmes, ni leurs promotions. Son
propre travail peut avoir une mémoire locale lorsqu’il est le projet assigné.

Roar capture les faits. Le rêve consolide les thèmes et l’index. Aucun des deux
ne propose de règles, ne modifie AGENTS.md, ne crée de procédure, test ou issue
de cristallisation, même si une expérience semble générale ou répétée.

Toute cristallisation demande une instruction explicite de l’auteur dans une
tâche séparée, avec destination et périmètre. Accepter une PR de mémoire ne
vaut pas autoriser des règles. Les thèmes peuvent citer des décisions déjà
adoptées, sans produire de prescription concurrente. AGENTS.md reste court.

## 8. Mémoire native, confidentialité et limites

Les mémoires natives restent actives et hors du store canonique. Elles peuvent
influencer les sessions avant leur ingestion ; une instruction seule ne garantit
pas que l’agent ignore une note contradictoire. Le pilote doit éprouver cette
limite et signaler les conflits, sans prétendre à une isolation mécanique.

Une note native interprétée reste une note attribuée, pas un événement factuel
reconstitué. Le rêve la confronte aux sources disponibles. Son absence sur l’hôte
ne signifie pas qu’elle est vide ; l’ingestion est incrémentale et explicitement
incomplète. Il n’y a pas d’obligation de synchroniser quatre profils natifs.

Dans un dépôt public, ne commiter que du contenu adapté à son audience. Si le
journal doit rester privé, déclarer un dépôt compagnon privé et un pointeur
local ; `memory/` peut alors être ignoré dans le dépôt public. Un dossier ignoré
sans store versionné ne satisfait pas la sauvegarde. Une branche du même dépôt
public n’est pas un espace privé. Le clone public reste utilisable avec les
connaissances publiques, sans accès au compagnon.

Les sources historiques restent accessibles sans runtime ni installation du
harness. La semaine de retard du rêve n’empêche pas une recherche dans le journal.
Une interruption du timer conserve les commits utiles et rend l’échec visible
au prochain contrôle ; un job qui n’a pas pu lire ses sources ne rapporte pas
un passage réussi sans changement.

## 9. Pilote et critères d’acceptation

Un projet représentatif suffit au premier jalon. Ne pas migrer tout le corpus
ni désactiver les anciennes voies avant d’avoir vérifié le remplacement.

| Épreuve | Résultat attendu |
|---|---|
| Clone déplacé et liens relatifs | Index, thèmes, journal et prompt restent lisibles |
| Tâche dans chacun des quatre runtimes | Preuve de lecture de l’index et du thème pertinent avant action, versions et conditions enregistrées |
| Expérience positive, négative et quasi-accident | Capture factuelle à roar, commits vérifiés, aucune règle proposée |
| Travail de routine sans fait significatif | Aucune entrée artificielle |
| Capture après fusion et sessions concurrentes | Sources conservées, branche durable, pas de pull du harness bloqué par la capture |
| Rêve avec cas similaires aux résultats opposés | Sources et exceptions conservées ; hypothèses distinguées des faits |
| Deux passages et une source corrigée | Anciennes sources pas réimportées comme nouvelles ; correction réexaminée |
| Retrait d’une affirmation et frontière d’autorité | Index cohérent, sources accessibles, aucune proposition de règle ni écriture dans le harnais |
| Note native contradictoire ou absente | Contradiction ou limite signalée, pas de certification silencieuse |
| Timer interrompu ou intégration refusée | Travail sauvegardé et statut visible, aucun succès fictif |

Les premiers smokes sont exploratoires. Le protocole d’évaluation de 0918 est
commité avant ses essais d’acceptation ; les smokes antérieurs ne sont pas
comptés rétroactivement comme essais préspécifiés.

Les jugements de pertinence et l’adhérence aux instructions se mesurent sur des
scénarios répétés, avec les omissions et coûts observés. Un mot témoin seul ne
prouve pas que le conseil a été suivi. Les vérifications de liens, de commits,
de conservation des sources et de synchronisation restent mécaniques.

## 10. Transition depuis v7

La v7 et son plan sont conservés comme documents historiques. Les tickets
gardent leurs identités et logs ; le plan v8 indique les périmètres remplacés.
Aucune réussite des anciennes épreuves n’est présumée transférable à la nouvelle
architecture. Cette réécriture n’active ni timer ni nouveau comportement de roar.

La livraison commence par la convention et les modèles de fichiers, l’inventaire
des sources et un pilote. Elle enchaîne capture sûre, prompt et timer, preuve sur
les quatre runtimes, évaluation et migration progressive.
Les anciennes fonctions de classement, TTL destructif, promotion automatique et
écriture concurrente d’index sont retirées seulement après remplacement vérifié.

## Clarification opérationnelle : une seule branche roar

Roar crée au plus une branche de clôture pour tous ses changements : tickets,
documentation et expérience factuelle. Une seule PR regroupe le tout, passe les
contrôles requis et reçoit l’auto-merge sans nouvelle confirmation. Aucun
contournement de contrôle ; en cas d’échec, la branche est conservée et signalée.
Le rêve périodique conserve sa PR distincte pour relecture.
