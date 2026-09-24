---
name: feedback_changement_de_decision_reecrire_les_actions
description: "Quand l'auteur change une décision d'outillage sur un ticket ouvert, réécrire ses actions — pas seulement son titre"
metadata:
  type: feedback
---

Ticket 0711 présupposait Quarto pour les deux papiers JETP ; l'auteur a tranché
LaTeX simple. Retitrer aurait laissé un ticket incohérent : trois de ses quatre
actions étaient de forme Quarto (variables `{{< meta >}}` + `-vars.yml`,
fragments markdown `\input`és, extension de `test_render_placeholders.py` dont
l'oracle *est* le résolveur de Quarto et dont les modes de défaillance
`?meta:` / `?@fig-` / `(clé?)` n'existent pas en LaTeX).

**Why:** un ticket encode sa décision d'outillage dans ses actions, son test et
ses invariants, pas seulement dans son titre. Un ticket à moitié converti se lit
comme cohérent et n'explose qu'à l'exécution, quand l'exécutant découvre un par
un les couplages que personne n'a nommés.

**How to apply:** à chaque changement de décision sur un ticket ouvert, relire
Actions / Test / Verification / Invariants en se demandant lesquels ne tiennent
que par l'ancienne décision ; nommer dans le Context le coût du changement (ici :
le dépôt passe d'une chaîne de rendu à deux) plutôt que de le laisser découvrir.
Puis balayer l'unité logique complète — le tracker parent et les notes de
conception répétaient la même présupposition. Marqueur de PR : le ticket reste
ouvert, donc `**Ticket-ref:**`, voir [[feedback_pr_creates_ticket_no_close]].
