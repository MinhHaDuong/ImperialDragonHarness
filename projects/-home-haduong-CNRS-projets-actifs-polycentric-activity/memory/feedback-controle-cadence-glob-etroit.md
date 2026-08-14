---
name: feedback-controle-cadence-glob-etroit
description: un contrôle de fraîcheur non récursif alarme sur les fichiers les mieux tenus et laisse les dormants invisibles
metadata: 
  node_type: memory
  type: feedback
  originSessionId: fc808437-1012-4355-b3b2-fa45b753a253
  modified: 2026-08-14T12:03:51.255Z
---

`warn-stale-rules.sh` balayait `rules/*.md` sans récursion et sautait tout
fichier sans marqueur. Mesure (harness, 2026-08-14) : les deux alarmes les plus
bruyantes visaient `workflow.md` et `git.md`, soit 50 et 21 commits depuis leur
dernier tampon — les deux fichiers les mieux entretenus du dépôt — pendant que
`edm.md` et `pdf-finishing.md`, sans marqueur, étaient exemptés à vie et que
sept règles en sous-répertoire dépassaient le seuil depuis 38 jours sans un mot.

**Why:** le marqueur mesure les passes de revue délibérées, pas les éditions, et
rien ne le bouge quand une règle est amendée sur place. Un fichier très édité
déclenche donc l'alarme alors qu'il est à jour ; un fichier dormant — ce qu'un
contrôle de cadence existe précisément pour attraper — reste muet s'il tombe
hors du glob ou n'a pas de marqueur. Le signal est anti-corrélé à ce qu'il
prétend mesurer.

**How to apply:** vérifier qu'un contrôle de fraîcheur couvre tout son objet
(récursion, et fichier sans marqueur traité comme un défaut plutôt que comme une
exemption) avant de croire son silence. Une alarme ancienne est une preuve
faible de pourriture ; l'absence d'alarme n'est aucune preuve de santé. Même
famille que le piège d'`AGENTS.md` : un contrôle dont le « rien à signaler » est
indiscernable du « je n'ai pas pu regarder » n'est pas un contrôle. Corollaire
tiré du même passage : ne jamais tamponner « revu » un fichier qu'on n'a pas lu
— le marqueur devient un mensonge que rien ne détecte.
