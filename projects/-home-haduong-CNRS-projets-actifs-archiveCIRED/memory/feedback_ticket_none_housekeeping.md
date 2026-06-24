---
name: feedback_ticket_none_housekeeping
description: "PRs de housekeeping (créer/rouvrir un ticket) doivent utiliser Ticket: none, pas **Ticket:**"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 860a097b-73e1-4765-a22f-9cdf8896643c
---

Pour un PR qui crée ou rouvre un ticket sans compléter son travail, utiliser `Ticket: none` dans le corps du PR.

**Why:** `erg-pr-merge` ferme et archive inconditionnellement tout ticket nommé dans une ligne `**Ticket:**`. Un PR de housekeeping (réouverture, création) avec `**Ticket:** tickets/NNNN` ferme le ticket au merge — le travail reste orphelin. S'est produit deux fois en une session (PR #54 et #55, 2026-06-24).

**How to apply:** Dès qu'un PR ne *complète* pas le ticket mais seulement le crée, déplace ou documente : `Ticket: none`. Utiliser `Ticket-ref:` si on veut citer le ticket sans le fermer.
