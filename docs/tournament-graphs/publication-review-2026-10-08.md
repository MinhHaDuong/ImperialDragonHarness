# Revue technique et décisions avant diffusion du tournoi LLM

Date : 8 octobre 2026  
Préparé par ChatGPT prompté par Ha-Duong Minh

## Mise à jour du 9 octobre

L’auteur a choisi de compléter les éléments demandés par 1046 et autorisé une branche GitHub de revue, sans fusion ni diffusion. Le rapport est porté à 26 pages ; les lacunes listées ci-dessous décrivent la version de 12 pages examinée le 8 octobre et sont remplacées par [completion-1046.md](completion-1046.md). La validation du guide par l’auteur et le réaudit privé restent ouverts.

## Sommaire

1. Résumé exécutif
2. Affirmations quantitatives
3. Périmètre comptable et statistiques
4. Incohérences et corrections
5. Critères des tickets
6. Décisions éditoriales et publication
7. Validation et limites de la revue

## 1. Résumé exécutif

Les trois textes ont été relus et complétés dans [diffusion-draft.md](diffusion-draft.md). Les données FR/EN concordent et les principaux chiffres sont exacts. Les corrections portent sur l’interprétation : proximité des moyennes plutôt qu’équivalence Haiku/Sonnet, coûts Mistral partiels, comparaisons nominales sans significativité après Holm. Les figures et liens disponibles remplacent les emplacements réservés.

Les PDF, le générateur et les notices sont corrigés pour rester cohérents avec les brouillons. Un lien dit « figé du 8 octobre » menait auparavant à des données sans Haiku ; le nouveau lien fige les données effectivement examinées. Les textes sont prêts pour relecture de l’auteur. La revue ne satisfait pas à elle seule tous les critères du rapport 1046 et n’autorise aucune publication.

Base examinée : [`e352f74befe459538f11330487e8cbb517bde04f`](https://github.com/MinhHaDuong/ImperialDragonHarness/tree/e352f74befe459538f11330487e8cbb517bde04f). Les identifiants 1046 et 1047 désignent les tickets `.erg`, **pas** les numéros de PR GitHub portant ces nombres.

## 2. Affirmations quantitatives

Moyennes arithmétiques par ticket, sur les dix tickets, avec échecs retenus inclus. Coûts candidats ; dépenses des juges séparées.

| Configuration | Note /30 | Minutes | USD/ticket |
|---|---:|---:|---:|
| Luna 6 medium | 22,20 | 5,02 | 0,0388 |
| Sol 6.1 low | 22,65 | 5,15 | 0,2053 |
| Sol 6.1 medium | 21,90 | 8,38 | 0,3883 |
| Sonnet 5.5 medium | 21,35 | 2,09 | 0,3037 |
| Haiku 5.5 medium | 21,70 | 6,11 | 0,1257 |
| Opus 5.5 low | 21,45 | 3,03 | 0,4551 |
| Opus 5.5 medium | 23,70 | 9,07 | 1,5578 |
| Qwen b2, IQ3_S/Strata xhigh | 26,20 | 46,11 | 0,1145 |
| Mistral dernier succès | 24,90 | 30,60 | 1,7406 |
| Mistral toutes tentatives | 24,90 | 96,32 | 6,3573 |

Haiku/Sonnet : coût ×0,413955 (−58,60 %), durée ×2,921631. La moyenne Sonnet exacte est 21,35, affichée 21,4 dans l’ancien résumé. Employer les centièmes évite une ambiguïté d’arrondi. Haiku livre dix résultats en dix tentatives candidates, sans reprise ni timeout observé. Livré ne signifie pas « de haute qualité » : les notes individuelles vont de 7 à 30/30. Coût candidat total : 1,2571 USD ; juges : 1,483838195 USD ; smoke : 0,00028389 USD. L’audit conserve aussi le total de session non arrondi, 1,257252575 USD ; cet écart d’arrondi n’est pas une erreur du tableau.

Qwen b2/Mistral : retirer **0333 dans toutes les séries** donne 25,777778/30 pour chacun sur neuf tickets. Ce contrôle est une sensibilité descriptive, pas un nouvel échantillon indépendant. Une tentative b2 interrompue pour libérer le GPU est exclue du coût et de la durée de la série retenue.

Les formulations historiques du contexte de 1047 (« Opus à parité », « Sol low strictement dominant », « local bat Sol ») doivent être lues comme observations de l’échantillon ou tests nominaux. Elles ne démontrent ni équivalence, ni supériorité statistique corrigée, ni doctrine causale sur l’effort.

## 3. Périmètre comptable et statistiques

### Mistral

- Dernier succès : dix succès retenus, incluant 0874 via OpenRouter ; dernier et meilleur succès coïncident pour les trois tickets à plusieurs succès jugés.
- Toutes tentatives : 25 tentatives directes et le succès OpenRouter de 0874, soit 26 tentatives. Total retenu : 63,5727440884 USD et 57 789,4 secondes.
- Comptage des tentatives : 35 traces conservées. Huit autres tentatives OpenRouter et un incident direct de configuration sur 0470 sont exclus des ressources de la série. « Toutes tentatives » est donc un nom de série au périmètre restreint, pas un coût exhaustif de campagne.
- Calibration directe : 12,23 EUR d’entrée + 25,58 EUR de cache + 1,96 EUR de sortie = 39,77 EUR. Allocation proportionnelle par catégorie de tokens, puis estimation des essais ultérieurs aux taux calibrés. Conversion : 1,08 USD/EUR. OpenRouter utilise le coût enregistré de son remplacement.
- Les reprises ne sont pas traitées uniformément entre séries ; la durée cumulée des tentatives ne représente pas le temps calendaire d’une campagne parallèle. Le test n’isole pas la fiabilité propre de Mistral des incidents du fournisseur ou de l’intégration.

### Comparaisons appariées

Les 136 comparaisons de chaque axe utilisent un Wilcoxon bilatéral avec permutation exhaustive des signes, différences nulles omises et rangs liés conservés ; l’hypothèse de symétrie des différences sous H0 reste une condition d’interprétation. Holm est appliqué **séparément par axe**, pas globalement aux trois axes.

| Axe | Comparaisons | Différences nominales p < 0,05 avant réduction transitive | Différences après Holm |
|---|---:|---:|---:|
| Qualité | 136 | 12 | 0 |
| Durée | 136 | 99 | 0 |
| Coût | 136 | 100 | 0 |

Dix paires donnent au mieux p = 2/1024 = 0,001953125, au-dessus de 0,05/136 = 0,000367647. Les égalités réduisent le nombre de différences non nulles et peuvent relever ce minimum. L’absence de résultat corrigé ne prouve pas l’équivalence.

| Qualité, paire | p nominal | p Holm |
|---|---:|---:|
| Haiku medium / Sonnet medium | 0,416015625 | 1 |
| Luna medium / Sol 6.1 low | 0,75390625 | 1 |
| Opus low / Sonnet medium | 0,845703125 | 1 |
| Opus medium / Opus low | 0,515625 | 1 |
| Sol 6.1 low / medium | 0,9453125 | 1 |
| Qwen b2 / Sol 6.1 medium | 0,0234375 | 1 |

Les trois juges produisent une note agrégée par ticket, pas trois réplications indépendantes. Les panels conservés diffèrent entre cycles ; « même runtime Pi » n’implique pas une version ou un environnement identiques. Haiku est documenté avec Pi 1.1.0, les autres versions ne le sont pas systématiquement. L’hypothèse d’un désavantage de Haiku lié aux rôles cumulés n’a pas été testée.

## 4. Incohérences et corrections

| Élément | Constat | Correction |
|---|---|---|
| Blog/Tchap/Reddit | Figures et liens laissés en attente | Figures du dépôt et liens directs vers PDF, données figées, tests et scripts |
| Blog/Reddit et PDF page 1 | Haiku « égale/matches » Sonnet | Moyennes proches, équivalence non établie ; ratios exacts |
| DAG, légendes FR/EN | « Significatives deux à deux » sans qualification immédiate | Seuil nominal ; zéro comparaison après Holm, 136 tests/axe |
| PDF page 1, Qwen et Mistral | Équivalence locale et fiabilité du modèle suggérées au-delà du protocole | Moyennes descriptives ; incidents de la configuration distincts de la fiabilité propre |
| PDF anglais page 1 | Deux signes dollar interprétés comme balises mathématiques, espaces et signes supprimés | Monnaie écrite « USD », rendu vérifié |
| PDF page 11 | Lien figé `433c6fd…` : instantané du 7 octobre sans N | Lien `e352f74…`, incluant N et correspondant à cette revue |
| README français | Figures annoncées antérieures à Haiku, 120 tests | Artefacts courants incluant N, 136 tests |
| Configurations | Ligne N dupliquée ; régénération annoncée non faite | Doublon retiré et notice actualisée |
| Périmètre Mistral | Brouillon moins précis que le rapport | 26 tentatives comptées sur 35 traces, neuf exclusions explicitement décrites |

Les données numériques, les notes et les périmètres de coût sont conservés. Les corrections du résumé n’imposent pas un choix de modèle, de pondération du délai ou de destination de publication.

## 5. Critères des tickets

### Ticket 1046 : PDF

Le rapport courant est une synthèse de douze pages avec table, cinq nuages, trois DAG et deux pages de méthode. Les critères du ticket restent décochés. Il ne faut pas déclarer ce ticket terminé à partir de la présence du PDF.

| Exigence du ticket | État établi par la revue |
|---|---|
| Graphes reproductibles à partir des données arena | Générateur présent et reproduction à partir de l’instantané public vérifiée ; archives privées `~/arena` inaccessibles ici, provenance brute non réauditée |
| Distributions des différences appariées par hypothèse | Tests numériques présents, mais distributions absentes des douze pages |
| Grille, verdicts H1/H2, axes d’effort, inter-camps ; 19 outcomes en trois classes | Table par configuration présente ; ces analyses et cette typologie ne sont pas présentées intégralement dans le PDF courant |
| Analyse des clusters et classes | Pas de section dédiée correspondant au contenu demandé |
| Guide situationnel : heures creuses, quotas/caps, confidentialité, GPU, budget et latence | Coûts et latence discutés, mais guide complet absent ; aucune revue du guide par l’auteur n’est établie |
| Cadrage, typographie et finition PDF | Défauts factuels et de rendu identifiés corrigés ; validation de l’auteur et des critères complets reste à faire |
| Critère parent 1024 « paired analysis written up » | Les tests apportent une preuve partielle ; leur présence ne justifie pas de cocher ce critère au titre du rapport sans revue de couverture |

Décision nécessaire : compléter le rapport selon le ticket initial, ou approuver explicitement un périmètre de publication plus court et traiter séparément le contenu restant. La revue ne réécrit ni ne ferme les critères.

### Ticket 1047 : diffusion

| Critère | État |
|---|---|
| Brouillons français référant au rapport et aux figures | Blog et Tchap complétés ; Reddit anglais également préparé |
| Egress : specs/notes publiques, aucun contenu des projets | Textes relus : résultats agrégés, identifiants de tickets et environnement de test ; aucune tâche privée, conversation brute ou clé ajoutée. Les seules données liées sont les instantanés déjà présents dans le dépôt |
| Revue et feu vert de l’auteur | Non obtenus ; rien publié |
| Dépendance 1046 | Conservée ; critères PDF encore ouverts |

## 6. Décisions éditoriales et publication

Corrections techniques effectuées : chiffres et arrondis, statistique, périmètre comptable, lien immuable, doublon, notices et défaut de rendu anglais.

Choix proposés à l’auteur :

1. Employer « piste économique » pour Luna dans la diffusion ; le titre « meilleur compromis observé » du rapport est conservé comme cadrage antérieurement ratifié et reste à confirmer pour publication. « Meilleur compromis » nécessite des priorités explicites sur qualité/coût/délai ; Sonnet reste plus rapide et Qwen b2 a une meilleure moyenne de qualité.
2. Conserver un billet analytique avec deux figures et les précautions explicites, puis des messages courts pointant directement vers les rapports.
3. Choisir la destination du blog et le subreddit. Le format Reddit reste à adapter à ses règles ; aucun canal n’a été présumé.
4. Définir « Offinity » ou l’écarter.
5. Décider du complément requis pour 1046 avant le feu vert de 1047.
6. Approuver les textes et canaux retenus, puis seulement publier. L’intégration d’une correction technique ne vaut pas accord de diffusion.

Avant diffusion : intégrer les corrections des rapports sur `main`, vérifier une dernière fois les liens du billet sur la destination choisie et les règles du subreddit, puis obtenir le feu vert explicite. Aucun message, commentaire de réseau social ni billet n’a été envoyé.

## 7. Validation et limites de la revue

- Moyennes recalculées depuis les jambes de l’instantané ; ratios Haiku/Sonnet et sensibilité sans 0333 recalculés.
- 408 valeurs p recalculées par le générateur depuis les paires ; Holm et les fichiers statistiques vérifiés par régénération.
- Instantanés, tests et CSV français/anglais identiques ; résultats numériques conservés après correction des textes.
- PDF FR/EN régénérés ; douze pages chacun. Vérification textuelle, liens PDF et inspection visuelle des pages retouchées et des figures.
- Sept fonctions de test du générateur exécutées directement et réussies (pytest absent de l’environnement) : Wilcoxon exact comparé à SciPy, Holm, réduction transitive et cycles, Pareto, coût valorisé.
- Aucun réexamen du travail privé livré, des tarifs courants des fournisseurs ou des factures originales : les coûts sont ceux enregistrés/calibrés dans les artefacts du tournoi, pas des promesses de prix futurs.

Sources primaires : [rapport FR](comparaisons-modeles.pdf), [rapport EN](../tournament-graphs-en/model-comparison.pdf), [snapshot](snapshot.json), [tests](tests.json), [audit Haiku](haiku55-accounting.json), [calibration Mistral](../../scripts/tournament-mistral-invoice.json), [ticket 1046](../../tickets/1046-model-tournament-pdf-report-graphs-paret.erg), [ticket 1047](../../tickets/1047-model-tournament-blog-posts-to-dissemina.erg).
