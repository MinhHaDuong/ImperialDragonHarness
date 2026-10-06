# Mistral Large 4 entre dans notre arène de travail

*Brouillon du 6 octobre 2026 — premier résultat, série complète en cours.*

Mistral Large 4 est disponible en préversion publique depuis aujourd’hui. Nous lui avons immédiatement confié une tâche de notre arène de travail : il obtient **27 points sur 30 en 15 minutes et 18 secondes**. C’est un premier résultat encourageant, qui mérite maintenant une comparaison sur la totalité de notre échantillon.

Mistral présente un modèle multimodal à mélange d’experts de plus de mille milliards de paramètres totaux. L’API est accessible ; la publication des poids est annoncée pour la fin du mois. Nous testons aujourd’hui le service hébergé, pas une installation locale. Les chiffres de performance publiés par le constructeur sont ses propres évaluations. [Annonce de Mistral](https://mistral.ai/news/mistral-large-4/).

Notre premier essai a été évalué par trois juges indépendants issus de familles différentes : Gemini, Grok et MiniMax. Les notes sont **7, 10 et 10**. La bonne note totale ne masque donc pas un désaccord : le premier juge relève une affirmation d’impossibilité erronée. La qualité d’un agent se joue aussi dans sa capacité à reconnaître correctement ce qu’il peut accomplir.

L’identité testée est **Mistral Large 4 par l’API native, avec Pi indiquant `off`**. Dans cette version de Pi, le modèle n’est pas référencé au catalogue et le paramètre API `reasoning_effort` est omis. Un test direct donne la même réponse lorsque ce paramètre est omis ou réglé sur `none` ; l’API accepte aussi `high` et rejette `low`. Cela ne permet pas d’assimiler notre série à un test de la configuration `high`, ni de conclure à une absence de raisonnement interne.

L’annonce donne **1,36 USD en entrée et 4,18 USD en sortie par million de tokens**. Notre plan de test a fixé un scénario de préversion à **0,68 USD en entrée, 0,07 USD pour les entrées en cache et 2,09 USD en sortie**. Les taux réduits figurent sur la fiche publique du modèle et sur la promotion OpenRouter ; nos essais passent toutefois par l’API native Mistral. Nous n’avons pas encore rapproché ces compteurs d’une facture native. Aux taux préenregistrés, le premier essai représente environ **0,23 USD**, hors juges, ou **0,49 USD en ajoutant la durée à 1 USD/h**. Pi a enregistré 0,1549 USD avec un autre triplet de prix ; cette valeur ne peut pas servir telle quelle au classement économique. [Fiche officielle du modèle](https://docs.mistral.ai/models/mistral-large-4-0).

Nous avons lancé les **neuf autres tâches en parallèle**, sur les mêmes bases de code historiques et avec les mêmes critères que les autres modèles. Le premier résultat est conservé. Chaque production sera évaluée à l’aveugle ; nous comparerons ensuite qualité, durée et coût ticket par ticket. Un dépassement du budget de temps compte comme un échec ; une panne de fournisseur exige un rejeu.

Cette série nous dira si Mistral Large 4 trouve une place sur la frontière qualité/coût de nos outils de travail. À ce stade, nous avons un premier résultat et une expérience en cours. Le classement attendra les dix tâches.

*Actualisation pendant le test : cinq tâches ont abouti par l’API native ; les cinq autres ont été interrompues par des erreurs de service. Elles sont relancées en parallèle via OpenRouter, qui ne propose actuellement que Mistral comme fournisseur pour ce modèle. Nous distinguerons les deux routes dans les résultats : disponibilité du service et qualité du modèle sont deux mesures différentes.*
