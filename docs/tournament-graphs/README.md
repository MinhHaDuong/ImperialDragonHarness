# Comparaisons du tournoi

`comparaisons-modeles.pdf` : trois graphes de significativité, trois nuages XY (qualité/coût,
qualité/vitesse, vitesse/coût) et une page de méthode, en A4 paysage.
Les flèches vont du meilleur vers le moins bon, au seuil nominal bilatéral
p < 0,05 (Wilcoxon apparié avec permutations exhaustives des signes).
Les valeurs p ajustées de Holm par axe sont aussi fournies ; aucune paire
ne passe cette correction dans cet instantané. L'absence de flèche n'est
pas une équivalence ; un chemin n'est pas un nouveau test significatif.

Les résultats directs, y compris les flèches supprimées par réduction
transitive, restent dans `comparisons.csv` et `tests.json`. Chaque `.dot`
contient les identités complètes et les valeurs p/n des liens visibles.
Les PNG sont des aperçus, le PDF est le livrable.

Les cycles sont additifs ; SpaceBunny et les préliminaires sont exclus.
Les DNF de modèle comptent à zéro, avec leur temps et coût consommés.
GLM Flash et Mimo restent provisoires : leurs rejeux sont en cours.

Reproduction à partir de l'instantané public, sans les conversations :

```bash
MPLCONFIGDIR=/tmp/tournament-mpl python3 scripts/tournament-graphs.py \
  --snapshot docs/tournament-graphs/snapshot.json \
  --output docs/tournament-graphs
```

Dépendances : Python, NumPy, SciPy et Matplotlib. Pas de binaire Graphviz
nécessaire. Pour un nouvel instantané, omettre `--snapshot` et fournir
`--arena ~/arena`.

Référence de méthode : [SciPy Wilcoxon](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.wilcoxon.html).

Frontières XY : qualité médiane ≥ 15/30 et observations complètes requises.
Les modèles sous ce seuil restent visibles, mais ne sont pas admissibles.

Le quatrième XY valorise toute la durée à 1 USD/h : coût direct + durée/3600,
calculé par ticket avant la médiane. Paramètre reproductible : `--time-value 1`.
