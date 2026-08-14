---
name: feedback_verify_each_before_batch_action
description: "When a sweep buckets multiple items as \"the same,\" verify each individually before committing to a batch action — per-item inspection repeatedly contradicts the batch framing"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a95551ca-2f8f-4b22-8ca0-859f7bf1e1c2
  modified: 2026-08-14T13:57:35.630Z
---

When a sweep or audit groups several items under one label ("these N repos all
have the same stale footprint", "discard all these stale edits"), **inspect each
item before acting on the batch as one.** The shared framing is a hypothesis, not
a finding.

**Why:** In the 2026-06-08 fleet erg-footprint sweep this bit three times in one
session:
- "fuzzy-corpus's edits are stale leftovers, discard them" → per-file diff showed
  they were *migration-in-progress*, more correct than HEAD (mtimes actively
  misled; only diffing content against the binary's own `erg spec` settled it).
- "all three remaining repos have the same stale footprint, do all three" → on
  inspection only Climate_finance matched; aedist was skills-only with an
  *accurate* CLAUDE.md, padme was already clean.
- The advisor caught two scope over-reaches that flowed directly from the batch
  framing (a cherry-fixed verb line; reducing aedist's accurate, deliberately
  maintained docs).

Each wrong batch framing cost a re-ask or a reverted edit. The cheap per-item
check would have pre-empted all of them.

**How to apply:**
- Treat a sweep's bucket as a list of candidates, not a decided action. Before a
  batch edit/delete/commit, open each item and confirm it actually matches.
- Distrust timestamps as evidence of intent — verify by content against the
  authoritative source (the tool's own `spec`/`--help`, the binary, the test),
  not by mtime or by another stale doc.
- An *accurate* artifact that merely carries a stale marker is not stale; don't
  strip maintained content for cosmetic uniformity unless explicitly asked.
- This is the per-item complement to "sweep results are decisions": the sweep
  tells you *where* to look; it does not pre-authorize the *same* action everywhere.

**Recurrence 2026-08-14, twice in one PR-queue drain — and the second form is
worse, because the batch had only one visible member.**
- « Ces deux consolidations dream sont périmées par celle qui a fusionné
  depuis » → vérification fichier par fichier : 3 des 7 sur main, **4 absents**,
  plus 1 des 2 de la sœur. Les fermer aurait perdu cinq entrées de mémoire.
- « Le fichier sale du checkout est identique à origin/main, l'écarter ne perd
  rien » → vrai **du fichier que j'avais regardé**, faux du checkout : il y en
  avait trois, dont un plus récent que tout ce que j'avais commité, portant une
  leçon qu'aucune de mes versions n'avait. La commande que j'avais donnée à
  l'auteur l'aurait détruite.

Le second cas généralise la règle : le piège n'est pas seulement « N items
groupés sous un label », c'est **inférer d'un échantillon vers un ensemble dont
on n'a pas établi la taille**. Un instantané de statut du début de session, un
`git status` d'il y a une heure, un diff sur le seul fichier qu'on a pensé à
regarder — tous donnent un « lot » de taille 1 qui n'est pas le lot réel. Avant
d'écarter ou d'écraser quoi que ce soit, **énumérer l'ensemble à cet instant**,
pas se fier au dernier dénombrement connu.

Corollaire opérationnel gagné le même jour : depuis une session isolée en
worktree, cette énumération est impossible — voir
[[feedback_isolated_session_cannot_read_shared_checkout]]. La réponse correcte
est alors de sortir du worktree, pas d'extrapoler.

See [[reference_git_erg_adopter_canonical_shape]] (the sweep this came from) and
the harness "Rename/refactor sweeps cover the full logical unit" rule — that says
sweep *widely*; this says verify each hit *before* acting.
