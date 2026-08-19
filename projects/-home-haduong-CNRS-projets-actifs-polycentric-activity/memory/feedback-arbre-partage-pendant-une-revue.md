---
name: feedback-arbre-partage-pendant-une-revue
description: "Ne pas éditer un worktree pendant qu'une porte ou une revue y tourne — elles peuvent restaurer l'arbre et effacer le travail non commité"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: be79e9f1-77d8-4519-968a-dfbe564392eb
  modified: 2026-08-17T15:14:12.555Z
---

**Committer avant de lancer une revue, et ne rien éditer tant qu'elle tourne.**
Une porte de vérification et un agent de revue lisent le même arbre de travail
que la session qui corrige. Sur `polycentric_activity` (2026-08-17), la porte a
lu des modifications en cours comme des écritures illégitimes de son propre
sous-agent, et a lancé `git checkout -- <fichier>` **deux fois** sur du travail
vivant non commité. Il n'y a pas de reflog pour ce qui n'a jamais été commité :
le contenu n'a survécu que parce que je l'ai refait.

**Why:** l'affordance est le défaut, pas le moment où quelqu'un s'en sert. Une
porte spécifiée comme instrument de lecture seule, mais qui *peut* atteindre une
commande mutante, finira par en lancer une. Et trois rôles — porte, revue,
correcteur — dans un seul worktree sans séparation de voies, c'est la condition
qui rend la collision possible.

**How to apply:** committer l'état courant avant d'invoquer `/gaze`,
`/verify-gate` ou `/review-pr` ; attendre leur verdict avant de rééditer. Si un
correctif doit partir pendant qu'une revue tourne, le faire dans un worktree
distinct. Après le retour d'une porte, **vérifier que ses propres correctifs
sont toujours là** (`git status`, un `grep` sur un motif du correctif) avant de
committer — ils peuvent avoir disparu sans message.

Voir aussi [[feedback-checkout-ref-ecrase-l-index]] : la même commande, le même
silence. Je l'ai déclenchée moi-même le même jour en restaurant un TOML pour
défaire un test, ce qui a effacé les éditions non commitées du même fichier.
Restaurer par édition ciblée, jamais par `git checkout --`.
