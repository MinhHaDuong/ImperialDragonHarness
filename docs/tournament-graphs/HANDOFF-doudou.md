# Reprise sur doudou — 2026-10-08

Projet : MinhHaDuong/ImperialDragonHarness. Tout est sur `main` : rapports français et anglais (12 pages chacun, table en page 2), scripts `scripts/tournament-graphs.py`, `scripts/tournament-graphs-en.py` et `scripts/tournament-english.json`, figures dans `docs/tournament-graphs/` et `docs/tournament-graphs-en/`, brouillons de diffusion. Haiku 5.5 (série n) est intégré (PR #1253 pour les données, #1252 pour les rapports). Les séries Mistral s'appellent « dernier succès » et « toutes tentatives ». La branche `docs/tournament-english-diffusion` n'existe plus ; il n'y a rien à récupérer en dehors de `main`.

Diffusion : brouillon `docs/tournament-graphs/diffusion-draft.md` (billet de blog, Tchap IA, Reddit) à relire. Rien publié. Le ticket 1047 attend le feu vert de l'auteur ; la destination du blog et le sens de « Offinity » restent à préciser. Le visualisateur 3D de sensibilité reste un nice-to-have (`docs/tournament-graphs/candidats-cycle-suivant.md`). Le ticket 1061 (différé) couvre un futur banc d'essai qui teste séparément orchestrateur, codeur et relecteur.

Pour reprendre : cloner ou synchroniser le dépôt (`main`), relire le brouillon, puis publier. Régénérer les figures : `MPLCONFIGDIR=/tmp/tournament-mpl python3 scripts/tournament-graphs-en.py --snapshot docs/tournament-graphs/snapshot.json --time-value 1` (version française : `scripts/tournament-graphs.py` avec `--output docs/tournament-graphs`). Le PDF anglais est `docs/tournament-graphs-en/model-comparison.pdf`, le français `docs/tournament-graphs/comparaisons-modeles.pdf`.

Aucune conversation brute ni clé API dans ces fichiers.
