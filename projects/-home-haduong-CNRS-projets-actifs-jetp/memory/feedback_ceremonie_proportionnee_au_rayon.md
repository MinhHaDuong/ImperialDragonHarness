---
name: feedback_ceremonie_proportionnee_au_rayon
description: "L'auteur calibre la cérémonie sur le rayon d'action : un changement de texte (ticket, prose) se commite et se merge directement, sans panel de revue"
metadata:
  type: feedback
---

Sur une réécriture de ticket, l'auteur a coupé court : « Aller aller on commite,
on merge, c'est un changement de texte pas une refonte du kernel ». Le gate
`/gaze` et son panel de reviewers sont pour le code, pas pour un `.erg` ou de
la prose.

**Why:** la machinerie de vérification du harnais (gaze, verify-gate, panel
décorrélé) est dimensionnée pour du code qui peut casser un build ou une
science. L'appliquer à un changement de texte coûte du temps d'auteur pour un
risque nul, et le signal « ce PR mérite un examen » se dilue.

**How to apply:** rayon = texte (ticket, note de conception, README, prose de
manuscrit) → branche, commit, PR, merge, sans gate. Rayon = code, données,
build → gate complet. En cas de doute, demander en une ligne plutôt que de
supposer la version chère. Voir [[feedback_decide_dont_micromanage]].
