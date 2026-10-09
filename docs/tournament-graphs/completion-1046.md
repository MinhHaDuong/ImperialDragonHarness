# Complément du rapport — couverture du ticket 1046

Date : 9 octobre 2026  
Préparé par ChatGPT prompté par Ha-Duong Minh

## Résumé exécutif

Les rapports français et anglais passent de 12 à **26 pages**. Le contenu demandé par 1046 est ajouté à partir des données publiques accessibles : grille et frontière de Pareto 3D, verdicts et distributions appariées, classes de routage, événements historiques corrigés et guide situationnel. La synthèse et ses données numériques sont conservées.

L’auteur a demandé ce complément et autorisé une **branche de revue GitHub**, sans fusion ni diffusion sur les autres canaux. Mise à jour du 9 octobre (Claude Opus 5.5) : guide relu par un relecteur Fable délégué par l’auteur, rapports cadrés, typographiés et finis, et reconstruction depuis `~/arena` sur padme. Le 9 octobre, sur padme, le dépôt récupéré au commit `5e743082` de la branche `t1046-report-finish` a régénéré figures et PDF depuis `~/arena` (`python3 scripts/tournament-graphs.py --arena ~/arena --output docs/tournament-graphs --time-value 1` puis `python3 scripts/tournament-graphs-en.py --arena ~/arena --time-value 1`). `tests.json`, `comparisons.csv`, `appendix-analysis.json`, `paired-differences.csv`, les coûts valorisés et les `.dot` sont identiques octet pour octet ; le texte des PDF est identique mot pour mot hors date de génération et placement des étiquettes. Les PDF et PNG versionnés sont ceux de padme. L’instantané public est conservé : il ne diffère de celui reconstruit que par les métadonnées comptables de Haiku 5.5, ajoutées hors générateur.

## Sommaire des ajouts

| Pages | Contenu | Preuve ou sortie reproductible |
|---|---|---|
| 13 | Résumé et sommaire du rapport complet | PDF FR/EN |
| 14 | Grille des 20 identités, médianes et Pareto 3D sur moyennes | `appendix-analysis.json` |
| 15–16 | H1, H2, axes d’effort et comparaisons inter-camps | 13 comparaisons choisies, 190 paires calculées |
| 17–21 | Distributions de Δ qualité et des log-ratios de durée/coût | `paired-differences.csv`, 130 observations |
| 22 | Analyse critique des cinq classes de la grille | `skills/route/grid.json`, valeurs de l’instantané |
| 23 | Les 19 événements historiques et leur reclassement | Journal du 6 octobre avec ses corrections |
| 24–25 | Guide : confidentialité, latence, budget, GPU, reprises, quotas et heures creuses | Tarification DeepSeek officielle vérifiée le 9 octobre |
| 26 | Sources, limites de traçabilité et critères ouverts | Aucun contenu des tickets privés exporté |

## Verdicts et précautions

- **H1** : Sol 6.1 low ne domine pas Sonnet medium sur les trois axes dans l’échantillon. Son coût moyen est inférieur et sa note moyenne supérieure, mais il est plus lent.
- **H2** : Luna a une durée moyenne inférieure aux six configurations locales. Il est plus rapide sur 10/10 tickets face à a/b/b2/b3, sur 6/10 face à c et 9/10 face à c2. La qualité dépend du comparateur ; aucune marge d’équivalence n’avait été définie et « coût négligeable » n’avait pas de seuil numérique. H2 ne peut donc pas être confirmée globalement.
- **Effort** : Sol low réduit durée et coût, sans dominance ticket par ticket en qualité. Opus low réduit durée et coût avec une qualité moyenne inférieure ; l’absence de différence significative ne prouve pas une parité.
- **Clusters** : les groupes de `grid.json` sont des catégories opérationnelles de routage, pas des classes découvertes par un clustering statistique. Leurs moyennes se chevauchent ; « assurance » ne garantit pas la fiabilité. Les notices j/k de la grille sont périmées par rapport à l’instantané final et sont signalées, sans modifier la politique de routage.
- **19 outcomes** : avant le rejeu b2, 141/160 OK et 19 non-OK ; après, 142/160 OK et 18 non-OK. Parmi neuf VOID-EMPTY historiques : un arrêt demandé pour libérer le GPU, sept incidents OpenRouter et une absence de livraison. Les sources publiques ne fournissent pas les six identifiants individuels de SpaceBunny ; le compte documenté est rapporté sans les inventer. Les cinq échecs retenus dans les séries courantes sont quatre timeouts et 0470-c2.
- **Statistiques** : les DAG conservent leur famille de 136 paires par axe. Le complément couvre les 190 paires des 20 identités, avec Holm séparément par axe ; aucune comparaison ne passe cette seconde famille non plus. Il ne s’agit pas d’une nouvelle préinscription, et les différences nominales ne suffisent pas à conclure à la supériorité ou à l’équivalence.
- **Prix** : le guide fournit des tarifs actuels, pas un recalcul des points historiques. DeepSeek documente des heures pleines du lundi au vendredi, 01–04 et 06–10 UTC, hors jours fériés chinois ; les autres périodes sont à moitié prix. Les données du tournoi restent figées. Source : [documentation officielle](https://api-docs.deepseek.com/quick_start/pricing/).

## Couverture des critères de sortie

| Critère original | Résultat de cette exécution | Restant |
|---|---|---|
| Graphes générés depuis `~/arena`, script dans le dépôt | Régénérés sur padme depuis `~/arena` au commit de la branche ; sorties numériques identiques à l’instantané | Aucun |
| Guide revu (Fable, délégué par l’auteur) | Relecteur prose-reviewer, modèle Fable : ACCEPT WITH CHANGES, huit constats appliqués (pages 24–25) | Aucun |
| Cadrage, typographie et finition PDF | message-framing (message en page 13), typography-finish (espaces insécables U+00A0 du complément français), pdf-finish (A4, 26 pages, métadonnées, aucun glyphe manquant) | Aucun |
| Analyse appariée du parent 1024 satisfaite par le rapport | Pages 14–21 : verdicts H1/H2, effort, inter-camps, distributions, 190 paires avec Holm | Le volet « verdict de routage dans STATE/ROADMAP » du critère parent relève de 1024/1052 |

Les critères de 1046 sont cochés dans le ticket. Ce complément ne clôt pas 1047 et ne modifie pas les politiques de routage.

## Reproduire

Depuis la racine du dépôt, avec les dépendances déclarées :

```bash
MPLCONFIGDIR=/tmp/tournament-mpl python3 scripts/tournament-graphs.py \
  --snapshot docs/tournament-graphs/snapshot.json \
  --output docs/tournament-graphs --time-value 1
MPLCONFIGDIR=/tmp/tournament-mpl python3 scripts/tournament-graphs-en.py \
  --snapshot docs/tournament-graphs/snapshot.json --time-value 1
```

Le premier script conserve le mode `--arena` pour une reconstruction privée. `scripts/tournament-report-completion.py` reçoit les résultats numériques des DAG pour réutiliser leurs 136 valeurs p par axe, puis calcule les 54 paires additionnelles. L’ajustement Holm du complément est refait sur l’ensemble des 190 paires, pas seulement sur les treize comparaisons illustrées.

## Validation

- Fichiers de base (`snapshot.json`, `tests.json`, `comparisons.csv` et coûts valorisés) inchangés par rapport à la base de la branche ; versions FR/EN identiques.
- Compléments FR/EN numériques identiques ; 190 paires uniques, dix tickets par paire et 130 observations dans le CSV des distributions.
- 23 tests ciblés réussis (générateur, complément, analyse, tentatives et dépendances déclarées) ; lint des scripts modifiés réussi : permutations exactes, Holm, Pareto, ratios appariés correctement réorientés, cohérence des familles et grille.
- Deux PDF de 26 pages, inspectés par rendu. Les figures d’origine sont conservées ; les cinq planches appariées par langue sont ajoutées.
- Ni conversation brute, ni clé, ni contenu des tâches privées n’est ajouté aux rapports.
