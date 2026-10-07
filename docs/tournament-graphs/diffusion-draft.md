# Brouillons de diffusion — à relire avant publication

## Billet de blog

Titre proposé : Quel LLM pour mes tâches de recherche ? Dix tickets, qualité, vitesse et coût

Pour choisir les modèles que j’utilise dans mes projets de recherche, j’ai fait reprendre dix tickets tirés au hasard dans leur historique. Chaque configuration travaille avec Pi, les outils et les consignes du projet ; trois modèles jugent le résultat sur 30. Je compare la qualité, le temps jusqu’au résultat et les dépenses directes. Le rapport, les données numériques et les scripts permettent de refaire les figures.

Luna 6 medium ressort comme le meilleur compromis observé : sa qualité et sa vitesse moyennes sont proches de Sol 6.1 low, pour un coût inférieur. Chez Claude aussi, monter en gamme tout en réduisant l’effort n’offre pas ici d’avantage net : Opus 5.5 low n’apporte pas de gain de qualité établi face à Sonnet 5.5 medium, qui est plus rapide et moins cher.

En local, Qwen 3.8 Flash-Next IQ3_S avec Strata, à effort xhigh, obtient la meilleure note moyenne : 26,2/30. Mais il faut attendre en moyenne 46 minutes par ticket sur ma workstation, et les tâches partagent les GPU. C’est une option pour le travail asynchrone, moins commode en interactif. Son avance dépend aussi de l’échantillon : retirer un ticket suffit à rejoindre la moyenne de Mistral.

Mistral Large 4 est prometteur en qualité. Les incidents d’hébergement et les difficultés d’intégration ont toutefois imposé des reprises, parfois longues et coûteuses. Deux séries distinguent les dix réussites retenues et une comptabilité élargie des tentatives. Cette dernière ne couvre pas tous les essais OpenRouter ; le périmètre est explicité dans le rapport.

Ce sont dix tickets de mes projets, avec des configurations choisies selon mes usages. Les efforts diffèrent, les coûts locaux ne comprennent que l’électricité et les reprises ne suivent pas un protocole uniforme. Les graphes de significativité donnent des comparaisons nominales à 5 % ; ils ne garantissent pas un classement global. Le test confie aussi orchestration, codage et revue à un seul modèle, alors que mes workflows peuvent répartir ces rôles.

Au-delà du classement, une question m’intéresse : combien vaut un résultat livré plus tôt ? Deux figures ajoutent au coût direct une valeur du délai de 1 USD ou de 0,10 EUR par erg et par heure. Elles permettent de distinguer un choix interactif d’un choix asynchrone.

[Insérer une figure qualité/coût, une figure qualité/vitesse et les liens vers le PDF et les données figées.]

## Tchap IA

J’ai comparé les configurations LLM que j’utilise pour la recherche sur dix tickets tirés dans mes projets : même runtime Pi, trois juges, qualité sur 30, durée et coût. Luna 6 medium offre le meilleur compromis observé ; Qwen 3.8 Flash-Next IQ3_S/Strata xhigh atteint la meilleure qualité moyenne en local, mais prend environ 46 minutes par ticket sur ma workstation. Mistral Large 4 est prometteur, avec un coût important des reprises. Échantillon petit et protocoles de reprise hétérogènes : les limites sont détaillées. PDF, données et scripts : [lien du billet]. Retours bienvenus sur la méthode et sur vos propres compromis qualité/délai/coût.

## Reddit — version anglaise à adapter au subreddit

Title: Ten real research tasks with Pi: quality, latency and cost across my local and hosted LLM setups

I replayed ten randomly sampled tickets from my research projects, using Pi and each project’s instructions, with three model judges scoring the deliverables. Luna medium was the best observed compromise in this sample. Local Qwen 3.8 Flash-Next IQ3_S on Strata at xhigh had the highest mean quality, but averaged 46 minutes per ticket on my workstation. Mistral Large 4 showed promising quality, alongside substantial retry overhead.

This is my own small benchmark, not a universal ranking. Effort settings and retry policies differ; local costs cover electricity only. The report explains failures, accounting exclusions and sensitivity to one ticket. PDF, numeric snapshot and plotting scripts: [blog link]. I would welcome feedback on the evaluation design and similar measurements from your own workflows.

## Canal à préciser

Offinity : destination et public à confirmer avant adaptation.
