# Reprise sur doudou — 2026-10-07

Projet : MinhHaDuong/ImperialDragonHarness. Beta 1 fusionnée dans PR1246 ; réorganisation finale fusionnée dans PR1247, main 59ddd1b8bf8875877f45623ee2386246e027d574. Rapport français : 12 pages, table en page 2, discussion intégrée à la méthode.

Travail enregistré sur la branche docs/tournament-english-diffusion : version anglaise, scripts/tournament-graphs-en.py, scripts/tournament-english.json et docs/tournament-graphs-en/. Douze pages inspectées ; tests.json identique à la version française ; Ruff passe. Ces fichiers sont versionnés dans le dépôt.

Diffusion : brouillon docs/tournament-graphs/diffusion-draft.md à relire. Rien publié. Destinations envisagées : blog, Tchap IA, Reddit ; destination du blog et sens de « Offinity » encore à préciser. User veut seulement comparer les modèles effectivement utilisés ; visualisateur 3D de sensibilité gardé comme nice-to-have.

Pour reprendre : cloner/synchroniser le dépôt, puis récupérer la branche docs/tournament-english-diffusion. Relire le brouillon de diffusion avant publication. Générer avec : MPLCONFIGDIR=/tmp/tournament-mpl python3 scripts/tournament-graphs-en.py --snapshot docs/tournament-graphs/snapshot.json --time-value 1. Le PDF anglais est docs/tournament-graphs-en/model-comparison.pdf.

Aucune conversation brute ni clé API dans ces fichiers.
