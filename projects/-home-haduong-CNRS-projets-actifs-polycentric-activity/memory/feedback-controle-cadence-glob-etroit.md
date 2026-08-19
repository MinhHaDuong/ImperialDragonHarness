---
name: feedback-controle-cadence-glob-etroit
description: un contrôle de fraîcheur non récursif alarmait sur les fichiers les mieux tenus et laissait les dormants invisibles ; la récursion est corrigée, l'exemption sans marqueur reste et est désormais assumée
metadata: 
  node_type: memory
  type: feedback
  originSessionId: fc808437-1012-4355-b3b2-fa45b753a253
  modified: 2026-08-19T10:15:29.647Z
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

**Récursion corrigée, vérifié sur pièce le 2026-08-19.** `scripts/warn-stale-rules.sh`
balaie désormais `rules/*.md` **et** `rules/*/*.md` — le commentaire en tête du
fichier cite explicitement « a narrow rules/*.md glob left seven subdirectory
rules unmonitored » comme le défaut corrigé. Le second défaut n'a pas bougé :
`[ -z "$date_str" ] && continue` saute toujours silencieusement tout fichier
sans marqueur. Ce n'est plus un angle mort tu : `rules/README.md` § Review
cadence l'énonce maintenant en toutes lettres — « A file without a marker is
skipped, not flagged, so absence buys permanent silence » — donc le risque est
documenté au lieu d'être caché, même s'il subsiste dans le code.

**How to apply:** vérifier qu'un contrôle de fraîcheur couvre tout son objet
(récursion, et fichier sans marqueur traité comme un défaut plutôt que comme une
exemption) avant de croire son silence. Une alarme ancienne est une preuve
faible de pourriture ; l'absence d'alarme n'est aucune preuve de santé. Même
famille que le piège d'`AGENTS.md` : un contrôle dont le « rien à signaler » est
indiscernable du « je n'ai pas pu regarder » n'est pas un contrôle. Corollaire
tiré du même passage : ne jamais tamponner « revu » un fichier qu'on n'a pas lu
— le marqueur devient un mensonge que rien ne détecte. Un nouveau fichier de
règle a donc besoin de son marqueur dès la création, pas après coup : c'est la
seule façon de sortir de l'exemption plutôt que de la découvrir un jour au
mauvais moment.
