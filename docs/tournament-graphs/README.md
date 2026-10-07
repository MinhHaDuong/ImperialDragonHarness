# Comparaisons du tournoi — beta 1

Rapport du 7 octobre 2026, révisé après la beta 0 (PR #1243) et la revue Astra.
Les changements de présentation et de discussion ont été ratifiés par l’auteur.
L’instantané numérique et les comparaisons statistiques restent inchangés.

Le PDF A4 paysage contient 12 pages : présentation, table des résultats, cinq nuages XY,
trois DAG de significativité et deux pages de méthode. La perspective du benchmark
de mai est intégrée à la méthode, sans page de discussion séparée.
Les PNG sont des aperçus du PDF. Les cycles sont additifs ; SpaceBunny et les
préliminaires sont exclus.

## Reproduire les figures

Depuis la racine du dépôt, avec Python et les dépendances de `requirements-dev.txt` :

```bash
MPLCONFIGDIR=/tmp/tournament-mpl python3 scripts/tournament-graphs.py \
  --snapshot docs/tournament-graphs/snapshot.json \
  --output docs/tournament-graphs --time-value 1
```

NumPy, SciPy et Matplotlib sont nécessaires ; Graphviz ne l’est pas.
L’instantané public suffit : aucune conversation ni clé API n’est requise.
Pour reconstruire un nouvel instantané depuis les archives privées, omettre
`--snapshot` et fournir `--arena ~/arena` ; cela change les données de référence.

## Lire les figures

Les nuages représentent les moyennes arithmétiques par ticket de qualité,
durée et coût. Les échecs retenus valent zéro, avec leurs ressources consommées.
Les anneaux orange indiquent la frontière de Pareto parmi les séries complètes
ayant une qualité moyenne d’au moins 15/30. Une série à 9 réussites sur 10 peut
être complète : son dixième résultat est un échec comptabilisé.

Les deux derniers XY ajoutent une valeur du délai de 1 USD/(erg·h) et de
0,10 EUR/(erg·h). Chaque ticket représente un erg moyen. Le coût total est
calculé par ticket, puis moyenné : coût direct + valeur du délai × durée en heures.
La conversion commune est 1,08 USD pour 1 EUR ; le local ne compte que
l’électricité, sans amortissement du matériel.

Les flèches des DAG vont vers le résultat moins juste, plus lent ou plus cher.
Le seuil nominal est p < 0,05, avec un test de Wilcoxon apparié bilatéral
et permutations exhaustives des signes. La réduction transitive retire les
flèches redondantes. L’absence de flèche ne prouve pas l’équivalence ; un chemin
indirect n’est pas un test supplémentaire. L’épaisseur indique l’intensité de l’effet.
Qwen 3, Qwen 3.6 et GPT-6 Sol restent dans les nuages mais sont exclus des DAG.

Holm est calculé séparément sur les 120 comparaisons de chaque axe. Avec dix
paires, le minimum possible de p bilatéral est 2/1024, supérieur au premier
seuil 0,05/120 : aucune comparaison ne peut franchir cette correction dans ce
protocole. Les tests nominaux n’établissent donc pas un classement global à 95 %.
Les comparaisons, y compris les flèches retirées, figurent dans `comparisons.csv`
et `tests.json` ; les `.dot` donnent les liens visibles et leurs valeurs p/n.

## Périmètre Mistral et reprises

`mi` (Mistral Idéal) retient le dernier succès jugé de chaque ticket, dont le
succès OpenRouter de 0874. `mr`, affiché mβ (Mistral beta), additionne les coûts
et durées de 25 tentatives directes conservées et de ce remplacement OpenRouter,
avec la meilleure note réussie par ticket. Les deux séries comptent 35 tentatives
préservées dans la table, mais neuf sont hors du périmètre des ressources beta :
huit autres essais OpenRouter et un incident direct de configuration sur 0470.
Il ne s’agit donc pas du coût exhaustif de la campagne.

Les coûts directs répartissent la facture de 39,77 EUR proportionnellement aux
tokens de chaque catégorie : entrée 12,23 EUR, cache 25,58 EUR, sortie 1,96 EUR.
La calibration et ses sources sont dans `scripts/tournament-mistral-invoice.json`
et `snapshot.json`. Les essais ultérieurs utilisent les taux calibrés comme
estimations ; le remplacement OpenRouter utilise son coût Pi enregistré.
Les coûts Pi d’origine sont conservés pour audit. Les durées cumulées par ticket
ne sont pas la durée calendaire d’une campagne parallélisée.

« Tentés » compte les traces préservées, y compris les incidents d’infrastructure,
sans garantir un historique exhaustif. « Réussis » compte les tickets livrés.
Les tokens moyens suivent les runs utilisés dans chaque série. Les reprises
n’étant pas uniformes, les lignes ne mesurent pas toutes la fiabilité au premier essai.
Les cinq 9/10 sont expliqués sous la table. La reprise b2 interrompue pour libérer
le GPU et la sensibilité au retrait de 0333 sont décrites dans les limites du PDF.

## Documents associés

- [Identités des configurations et versions enregistrées](configurations.md).
- [Idées optionnelles et candidats pour un prochain cycle](candidats-cycle-suivant.md).
- [Méthode du test de Wilcoxon (SciPy)](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.wilcoxon.html).
- [Présentation du benchmark de mai 2026](https://minh.haduong.com/files/HaDuong-2026-EconomIA-BeyondRAG.pdf), discutée à la fin du rapport.
