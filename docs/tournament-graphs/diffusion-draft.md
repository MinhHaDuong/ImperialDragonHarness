# Textes de diffusion — version relue du 8 octobre 2026

Statut : prêts pour relecture de l’auteur, non publiés. Les liens vers les rapports et figures sur `main` doivent être utilisés après intégration des corrections associées. Les données numériques sont liées à un commit immuable incluant Haiku.

## Billet de blog

### Quel LLM pour mes tâches de recherche ? Dix tickets, qualité, vitesse et coût

Pour éclairer le choix des modèles que j’utilise dans mes projets de recherche, j’ai fait reprendre dix tickets tirés au hasard dans leur historique. Chaque configuration travaille avec Pi, les outils et les consignes du projet. Un seul modèle réalise la tâche et relit sa propre production ; trois modèles juges évaluent ensuite le résultat, sans connaître le modèle qui l’a produit, sur un total de 30 points. Ce test porte donc sur des tâches menées de bout en bout avec Pi, pas sur le workflow complet d’Imperial Dragon Harness avec revues indépendantes.

Je compare la qualité moyenne, la durée et le coût direct par ticket. Les échecs retenus comptent pour zéro en qualité, avec leurs ressources consommées. Les efforts et les politiques de reprise diffèrent selon les configurations : les résultats décrivent ces configurations dans ce petit échantillon, plutôt qu’un classement universel des modèles.

**Un compromis économique favorable à Luna.** Luna 6 medium obtient 22,20/30, avec une durée moyenne de 5,02 minutes et un coût de 0,0388 USD par ticket. Sol 6.1 low obtient 22,65/30 en 5,15 minutes pour 0,2053 USD. La proximité des moyennes de qualité et de durée, pour un coût environ 5,3 fois plus faible, rend Luna intéressant pour mes usages. Cela ne démontre pas une équivalence de qualité, ni un meilleur choix pour toutes les tâches ou toutes les valeurs du délai.

**Haiku : coût inférieur, durée supérieure à Sonnet.** Haiku 5.5 medium, ajouté le 8 octobre, obtient 21,70/30 contre 21,35/30 pour Sonnet 5.5 medium. Son coût moyen est de 0,1257 USD contre 0,3037 USD, soit environ 59 % de moins ; sa durée moyenne est de 6,11 minutes contre 2,09 minutes, soit 2,92 fois plus. Les dix tickets ont livré un résultat sans reprise candidate ni dépassement du délai ; cela ne préjuge pas de leur qualité, ni de la fiabilité sur d’autres tâches. Le test apparié de qualité ne met pas en évidence une différence au seuil nominal de 5 % (p = 0,416), et ne prouve pas l’équivalence. Les coûts des juges et du test préalable sont séparés des coûts candidats représentés.

Opus 5.5 low obtient, pour sa part, 21,45/30 en 3,03 minutes pour 0,4551 USD. Sa note moyenne proche de celle de Sonnet medium ne constitue pas ici un gain de qualité établi. Comparer une gamme et un effort simultanément ne permet pas d’attribuer les différences à un seul de ces facteurs.

**En local, une bonne moyenne au prix de l’attente.** Qwen 3.8 Flash-Next IQ3_S avec Strata, à effort xhigh, obtient la plus haute note moyenne : 26,20/30. Sa durée moyenne est de 46,11 minutes par ticket sur la workstation testée, équipée d’une RTX A4000 et d’une RTX 3060. La durée et le partage des GPU limitent l’interactif ; cette configuration est davantage une piste pour le travail asynchrone. Son avance dépend de l’échantillon : en retirant le même ticket, 0333, de toutes les séries, sa moyenne et celle de Mistral sont toutes deux de 25,78/30 sur neuf tickets. La tentative locale interrompue pour libérer le GPU est documentée et ses ressources ne sont pas incluses dans cette série.

![Qualité moyenne et coût direct moyen par ticket](https://raw.githubusercontent.com/MinhHaDuong/ImperialDragonHarness/main/docs/tournament-graphs/quality-cost.png)

*Figure 1. Moyennes par ticket, échecs retenus inclus. Le coût local couvre uniquement l’électricité, sans amortissement du matériel ; le coût hébergé couvre l’API candidate. Les anneaux indiquent la frontière de Pareto descriptive parmi les séries complètes ayant une qualité moyenne d’au moins 15/30.*

![Qualité moyenne et durée moyenne par ticket](https://raw.githubusercontent.com/MinhHaDuong/ImperialDragonHarness/main/docs/tournament-graphs/quality-speed.png)

*Figure 2. La durée dépend du modèle, de l’effort, du runtime et de l’environnement. Les durées cumulées des reprises Mistral ne représentent pas la durée calendaire d’une campagne parallélisée.*

**Mistral : deux périmètres comptables.** Mistral Large 4 atteint 24,90/30. La série « dernier succès » retient dix résultats réussis, dont le ticket 0874 via OpenRouter : 30,60 minutes et 1,7406 USD par ticket en moyenne. La série « toutes tentatives » conserve les mêmes notes et additionne les ressources de 25 tentatives directes et de ce remplacement OpenRouter : 96,32 minutes et 6,3573 USD par ticket. Elle exclut huit autres essais OpenRouter et un incident direct de configuration sur 0470, sur 35 traces conservées. Son coût n’est donc pas celui de toute la campagne. Les coûts directs sont calibrés sur une facture de 39,77 EUR ; les essais ultérieurs sont estimés à ces taux, tandis que le remplacement OpenRouter utilise son coût enregistré. Incidents d’hébergement, difficultés d’intégration et reprises empêchent d’isoler la fiabilité propre du modèle.

**Des différences descriptives, pas un palmarès statistiquement établi.** Les graphes de significativité utilisent des tests de Wilcoxon appariés bilatéraux au seuil nominal de 5 %. Aucun des 136 tests par axe ne passe la correction de Holm. Avec dix paires, le minimum possible de p est 2/1024, au-dessus du premier seuil corrigé 0,05/136. Une flèche nominale n’établit donc pas une différence après correction ; l’absence de flèche ne démontre pas une équivalence. Les dix tickets et les trois juges ne constituent pas trente observations indépendantes.

Le protocole confie orchestration, réalisation et auto-revue au même modèle. Il ne mesure pas séparément les compétences de chaque rôle ; l’hypothèse que cela pénalise Haiku ou un autre modèle reste à tester. Les panels de juges diffèrent entre les cycles conservés, et les versions de Pi ne sont pas enregistrées systématiquement : Haiku a été testé avec Pi 1.1.0. Les efforts sont relatifs aux modèles et ne constituent pas une échelle commune de calcul.

Enfin, combien vaut un résultat livré plus tôt ? Deux figures du rapport ajoutent au coût direct une valeur illustrative du délai de 1 USD ou de 0,10 EUR par ticket moyen et par heure. Ce sont des scénarios de préférence, pas des dépenses observées ni un salaire horaire. Ils permettent de discuter les choix interactifs et asynchrones.

**Rapports, données et reproduction :**

- [Rapport français, 26 pages](https://github.com/MinhHaDuong/ImperialDragonHarness/blob/main/docs/tournament-graphs/comparaisons-modeles.pdf) et [rapport anglais](https://github.com/MinhHaDuong/ImperialDragonHarness/blob/main/docs/tournament-graphs-en/model-comparison.pdf).
- [Instantané numérique figé incluant Haiku](https://github.com/MinhHaDuong/ImperialDragonHarness/blob/e352f74befe459538f11330487e8cbb517bde04f/docs/tournament-graphs/snapshot.json) et [tests appariés figés](https://github.com/MinhHaDuong/ImperialDragonHarness/blob/e352f74befe459538f11330487e8cbb517bde04f/docs/tournament-graphs/tests.json).
- [Méthode, périmètres et commande de reproduction](https://github.com/MinhHaDuong/ImperialDragonHarness/blob/main/docs/tournament-graphs/README.md), [script français](https://github.com/MinhHaDuong/ImperialDragonHarness/blob/main/scripts/tournament-graphs.py) et [script anglais](https://github.com/MinhHaDuong/ImperialDragonHarness/blob/main/scripts/tournament-graphs-en.py).
- [Audit comptable Haiku](https://github.com/MinhHaDuong/ImperialDragonHarness/blob/main/docs/tournament-graphs/haiku55-accounting.json) et [calibration Mistral](https://github.com/MinhHaDuong/ImperialDragonHarness/blob/main/scripts/tournament-mistral-invoice.json).

Retours bienvenus sur la méthode et sur vos propres compromis qualité, délai et coût.

## Tchap IA

J’ai comparé des configurations LLM sur dix tickets tirés au hasard dans mes projets : Pi et consignes des dépôts, trois juges, qualité sur 30, durée et coût par ticket. Luna 6 medium est une piste économique (22,20/30, 5,02 min, 0,0388 USD). Qwen 3.8 Flash-Next IQ3_S/Strata xhigh a la meilleure moyenne (26,20/30), mais prend 46,11 min sur ma workstation. Haiku 5.5 medium a une note moyenne proche de Sonnet medium (21,70 contre 21,35), coûte environ 59 % de moins et prend 2,92 fois plus de temps ; l’équivalence n’est pas démontrée. Mistral atteint 24,90/30, avec de nombreuses reprises ; sa série « toutes tentatives » n’inclut pas toute la campagne. Petit échantillon, efforts et reprises hétérogènes : aucune comparaison ne passe Holm. Un modèle tient tous les rôles ; il ne s’agit pas du workflow IDH complet.

[Rapport français](https://github.com/MinhHaDuong/ImperialDragonHarness/blob/main/docs/tournament-graphs/comparaisons-modeles.pdf) · [Données figées](https://github.com/MinhHaDuong/ImperialDragonHarness/blob/e352f74befe459538f11330487e8cbb517bde04f/docs/tournament-graphs/snapshot.json) · [Méthode et scripts](https://github.com/MinhHaDuong/ImperialDragonHarness/blob/main/docs/tournament-graphs/README.md)

Retours bienvenus sur la méthode et sur vos propres mesures qualité/délai/coût.

## Reddit — version anglaise, destination à approuver

Title: Ten real research tasks with Pi: quality, elapsed time and cost across my local and hosted LLM setups

I replayed ten randomly sampled tickets from my research projects using Pi, tools and each project's instructions. A single model completed each task and reviewed its own output; three blinded model judges then scored the deliverable out of 30. This evaluates end-to-end task completion, rather than the full Imperial Dragon Harness workflow with independent reviews.

Luna 6 medium looks economical in this sample: 22.20/30, 5.02 minutes and USD 0.0388 per ticket, versus 22.65/30, 5.15 minutes and USD 0.2053 for Sol 6.1 low. Local Qwen 3.8 Flash-Next IQ3_S on Strata at xhigh had the highest mean score, 26.20/30, but averaged 46.11 minutes on my A4000 + 3060 workstation. Excluding the same single ticket from all series brings its mean down to Mistral's, 25.78/30 over nine tickets.

Haiku 5.5 medium had similar mean quality to Sonnet 5.5 medium (21.70 vs 21.35/30), at USD 0.1257 vs USD 0.3037 per ticket, but took 2.92 times as long (6.11 vs 2.09 minutes). Haiku delivered all ten tasks without candidate reruns or timeouts; that does not establish high quality or general reliability. The quality comparison was not significant even at the nominal 5% threshold (paired p = 0.416), and equivalence was not demonstrated. Judge and preliminary smoke-test costs are separate from plotted candidate costs.

Mistral Large 4 scored 24.90/30. Its "last success" series averages 30.60 minutes and USD 1.7406 per ticket. The "all attempts" series averages 96.32 minutes and USD 6.3573, counting 25 direct attempts plus one successful OpenRouter replacement. Eight other OpenRouter attempts and one direct configuration incident are excluded from its 35 preserved traces: this is not the full campaign cost. Direct costs use invoice-calibrated rates, with later runs estimated; the OpenRouter replacement uses its recorded cost.

This is a small, personal benchmark, not a universal ranking. No comparison survives Holm correction across 136 tests per axis; nominal arrows do not establish corrected significance, and no arrow does not establish equivalence. The ten tasks, each scored by three judges, are not thirty independent observations. Effort settings and retry policies differ; retained judge panels differ between cycles, Pi versions were not consistently recorded (Haiku used 1.1.0), and local costs cover electricity only. Possible disadvantages from assigning every role to one model remain untested. The report also includes illustrative delay-value scenarios, rather than additional observed spending.

[English report, 26 pages](https://github.com/MinhHaDuong/ImperialDragonHarness/blob/main/docs/tournament-graphs-en/model-comparison.pdf) · [Frozen numeric snapshot](https://github.com/MinhHaDuong/ImperialDragonHarness/blob/e352f74befe459538f11330487e8cbb517bde04f/docs/tournament-graphs/snapshot.json) · [Frozen paired tests](https://github.com/MinhHaDuong/ImperialDragonHarness/blob/e352f74befe459538f11330487e8cbb517bde04f/docs/tournament-graphs/tests.json) · [Method and plotting instructions](https://github.com/MinhHaDuong/ImperialDragonHarness/blob/main/docs/tournament-graphs/README.md)

I would welcome feedback on the evaluation design and similar measurements from your own workflows.

## Décisions de publication restant à l’auteur

- Choisir la destination du billet ; les messages courts pointent directement vers les rapports, sans dépendre d’un billet encore absent.
- Choisir le subreddit et adapter le format à ses règles avant publication.
- Définir « Offinity » (destination et public), ou l’écarter de cette diffusion.
- Valider le cadrage descriptif proposé (« piste économique » plutôt que « meilleur compromis » sans poids explicites).
- Examiner les éléments encore manquants du ticket PDF 1046 et valider le guide de choix ; le ticket 1047 reste bloqué par 1046.
- Donner le feu vert explicite aux textes et aux canaux retenus. Aucune publication ni approbation n’est enregistrée par cette relecture.
