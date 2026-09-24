---
name: feedback_runs_longs_en_nohup_sur_la_machine_cible
description: Un travail autonome long se lance en nohup depuis la machine qui doit l'exécuter, jamais télécommandé par ssh depuis la session locale.
metadata:
  type: feedback
---

Instruction explicite de l'auteur, 2026-09-11 : « À lancer en nohup depuis
padme, pas à la main en mode télécommande ici. La session locale doudou est en
fin de vie. »

**Pourquoi.** Un agent local qui pilote la machine cible par `ssh` meurt avec
la session locale, et emporte le travail en cours. Le processus doit être
enfanté *sur* la cible et détaché d'elle.

**Comment l'appliquer.** `ssh <cible> "cd <repo> && setsid nohup claude -p
'/hunt <N>' --model opus --permission-mode bypassPermissions > ~/<log> 2>&1
< /dev/null &"`. Vérifier ensuite que le `ppid` du processus vaut **1** —
c'est la preuve du détachement, pas le simple fait que `nohup` ait été tapé.
Le client ssh, lui, restera bloqué sur le canal ouvert : le tuer par `timeout`
est normal et ne touche pas le processus distant.

Trois choses manquaient à la cible et auraient fait échouer le run en silence :
son `main` avait huit commits de retard, le code source à porter n'existait
pas sur elle, et les tirages archivés non plus. Avant de détacher, vérifier
que la machine cible a tout ce que le ticket nomme — un agent détaché ne peut
plus rien demander.

Voir [[project_jetp_strate_de_climate_finance_het]].
