---
name: project_jetp_strate_de_climate_finance_het
description: JETP n'est plus un projet autonome — c'est une strate de climate-finance-het, pilotée par le tracker 0708 ; ~/CNRS/projets/actifs/jetp/ n'est qu'un sas non versionné.
metadata:
  type: project
---

Décidé par l'auteur le 2026-09-10. Le programme JETP (avec Christophe Cassen,
CIRED) est devenu une strate de `climate-finance-het` : même donnée OCDE CRS,
une seule machinerie à entretenir. Tracker **0708**.

`~/CNRS/projets/actifs/jetp/` **n'est pas un dépôt git** — aucune PR n'y est
possible, rien n'y a d'historique. C'est un sas. Tout travail versionné passe
par `climate-finance-het`.

État au 2026-09-11 :

- **0709, 0710, 0712 fermés.** Notes atterries dans `conception/` et
  `conception/jetp/` (42 fichiers + README d'inventaire).
- **0713 ouvert** — portage du pipeline CRS du papier court sous DVC. Doit
  tourner sur **padme** (`~/Climate_finance`), jamais sur doudou : padme est
  l'autorité des données, doudou ne pousse jamais.
- **0711 ouvert** — livrables ; l'auteur a fait réécrire le ticket en LaTeX,
  il ne veut pas de Quarto pour ces papiers.
- **45 fichiers redondants de `jetp/` sont en `.bak` lecture seule.** La copie
  vivante est celle de het. Exception : `cr-reunion-2026-09-08-christophe.md`
  a divergé et reste écrivable — voir
  [[feedback_reverifier_juste_avant_l_acte_destructif]].

Restent hors périmètre, explicitement : le papier 1 (working paper CIRED 2024,
rangé dans `~/CNRS/papiers/published/Reports/JETP at two/`) et le dossier
AFD-Sénégal, en pause (chiffre central 670 M€ non vérifié).

Constat utile et contre-intuitif : `climate-finance-het` n'a **aucun** pipeline
CRS — pas de code CRS suivi en git, pas d'étape CRS dans `dvc.yaml`.
`data/book/riomarkers/` (504 Mo sur padme) n'est qu'un dépôt de zips bruts pour
le chapitre de livre. Il n'y avait donc jamais deux pipelines à réconcilier.
