---
name: project-cnrs-filing-convention
description: "Convention de rangement de ~/CNRS — projets/ = atelier git, papiers/ = un répertoire par manuscrit, sorties gelées en sous-dossiers datés"
metadata: 
  node_type: memory
  type: project
  originSessionId: ceb24c88-cdf1-479e-986b-08d286b1acfc
  modified: 2026-07-28T15:39:51.120Z
---

Convention validée par l'auteur (session feuille de route, 2026-07-28),
modèle : climate-finance-het / Oeconomia.

- **`projets/actifs/<programme>`** = l'atelier : le dépôt git, tout ce qui
  s'édite (code, données, tickets, sources des manuscrits et slides).
- **`papiers/actif|sent/<manuscrit>`** = un répertoire **par manuscrit**
  (pas par programme), contenant **uniquement des sorties gelées** : un
  sous-dossier daté par événement d'expédition (`2026-06-16 HAL et
  homepage/`, `2026-01-14 Special Issue/`…), jamais de `.git`, `.tex`,
  `.md`, `.py` éditables. L'article et le rapport technique d'un même
  programme peuvent être « la même chose » (pratique de l'auteur : l'article
  est la substance distillée du rapport).
- Rangements dormants : `papiers/grenier/`, `projets/placard/` (ressortable
  si bonnes nouvelles), `projets/finished/`, `missions/annulees/`.
- **Chaque artefact gelé doit être l'authentique**, vérifié contre sa source
  (mail via [[reference-mail-archive]], HAL, `html/files/`), au hash près —
  voir [[feedback-authentic-artifacts-not-reconstructions]].

**Why:** garder le brouillon sous `papiers/` invite à l'éditer là et fait
proliférer les dossiers (AEDIST était éclaté en 3 emplacements à racines git
disjointes avant consolidation).

**How to apply:** à la création d'un manuscrit ou d'une release, créer le
sous-dossier daté côté `papiers/` et y copier la sortie gelée ; tout le reste
va dans l'atelier. Instances restantes de la classe (signalées, non
déplacées, décision auteur) : Fuzzy Corpus, Cadens, livre-milliards-climat,
polycentric_activity — dépôts git encore sous `papiers/actif/`.
