# Mistral Large 4 entre dans notre arène de travail

*Brouillon du 6 octobre 2026 — premier résultat, série complète en cours.*

Mistral Large 4 est disponible en préversion publique depuis aujourd’hui. Nous lui avons immédiatement confié une tâche de notre arène de travail : il obtient **27 points sur 30 en 15 minutes et 18 secondes**. C’est un premier résultat encourageant, qui mérite maintenant une comparaison sur la totalité de notre échantillon.

Mistral présente un modèle multimodal à mélange d’experts de plus de mille milliards de paramètres totaux. L’API est accessible ; la publication des poids est annoncée pour la fin du mois. Nous testons aujourd’hui le service hébergé, pas une installation locale. Les chiffres de performance publiés par le constructeur sont ses propres évaluations. [Annonce de Mistral](https://mistral.ai/news/mistral-large-4/).

Notre premier essai a été évalué par trois juges indépendants issus de familles différentes : Gemini, Grok et MiniMax. Les notes sont **7, 10 et 10**. La bonne note totale ne masque donc pas un désaccord : le premier juge relève une affirmation d’impossibilité erronée. La qualité d’un agent se joue aussi dans sa capacité à reconnaître correctement ce qu’il peut accomplir.

L’identité testée est **Mistral Large 4 par l’API native, avec Pi indiquant `off`**. Dans cette version de Pi, le modèle n’est pas référencé au catalogue et le paramètre API `reasoning_effort` est omis. Un test direct donne la même réponse lorsque ce paramètre est omis ou réglé sur `none` ; l’API accepte aussi `high` et rejette `low`. Cela ne permet pas d’assimiler notre série à un test de la configuration `high`, ni de conclure à une absence de raisonnement interne.

Les tarifs ordinaires annoncés sont de **1,36 USD en entrée et 4,18 USD en sortie par million de tokens**. Le tarif de préversion affiché aujourd’hui est de **0,68 USD par million de tokens d’entrée**, **0,07 USD pour les entrées en cache** et **2,09 USD pour les sorties**. En appliquant ces trois composantes aux compteurs de notre premier essai, le coût estimé est d’environ **0,23 USD**, hors évaluation par les juges. À cela s’ajoute le temps : avec notre convention de **1 USD par heure de durée**, cet essai représente environ **0,49 USD de coût total**. Ce sont des estimations à partir des tokens enregistrés, pas une facture du fournisseur. [Fiche officielle du modèle](https://docs.mistral.ai/models/mistral-large-4-0).

Nous avons lancé les **neuf autres tâches en parallèle**, sur les mêmes bases de code historiques et avec les mêmes critères que les autres modèles. Le premier résultat est conservé. Chaque production sera évaluée à l’aveugle ; nous comparerons ensuite qualité, durée et coût ticket par ticket. Un dépassement du budget de temps compte comme un échec ; une panne de fournisseur exige un rejeu.

Cette série nous dira si Mistral Large 4 trouve une place sur la frontière qualité/coût de nos outils de travail. À ce stade, nous avons un premier résultat et une expérience en cours. Le classement attendra les dix tâches.
