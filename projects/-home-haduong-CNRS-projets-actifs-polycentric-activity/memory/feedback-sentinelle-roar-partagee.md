---
name: feedback-sentinelle-roar-partagee
description: La sentinelle roar est globale au dépôt ; en sessions parallèles une autre session avance la vôtre et absorbe vos merges
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 1e742b5d-6433-44f8-b6a3-8dbb03a621ba
  modified: 2026-08-18T11:34:53.943Z
---

La sentinelle `roar-last-sha` vit dans le git-dir commun, donc **toutes les
sessions du dépôt la partagent**. En travail parallèle, la première qui roare
avance la sentinelle jusqu'à `origin/main` et absorbe dans sa télémétrie les
merges des autres. Vérifier le journal avant de logger.

**Why:** le 2026-08-17, `/roar` sur ma MR #138 a trouvé la sentinelle déjà à
`a8b1fc8`, le tip courant : une session parallèle avait roaré entre mon merge et
le mien. L'énumération renvoyait vide, ce qui aurait déclenché le repli agrégé du
skill et créé un doublon. Le journal montrait mon `t0210-negatifs-formels-marqueurs,
commits=3` déjà consigné avec la bonne attribution — par leur roar. Il montrait
aussi `het-2-1-sans-chapeaux` deux fois, à 14:54 et 15:10 : un vrai doublon de
roars parallèles. Sous le plancher de sévérité, donc rapporté et non ticketé.

**How to apply:** avant l'étape 2, lire `~/.claude/telemetry/celebrations.jsonl`
et chercher sa propre branche. Présente avec le bon compte de commits, ne rien
logger et ne pas toucher la sentinelle. Absente et l'énumération vide, le repli
agrégé est correct. Et ne jamais avancer la sentinelle plus loin qu'elle n'est :
le faire volerait la plage d'une autre session.

Corollaire pour l'étape 2 en session parallèle : le chemin de la sentinelle se
calcule avec `git -C <repo> rev-parse --path-format=absolute --git-common-dir`.
Sans `--path-format=absolute`, `git -C` renvoie un chemin relatif et le `cat`
échoue sur « Not a directory » sans que rien ne le signale. Voir
[[feedback-roar-enumerate-merges-head]] pour l'autre piège de cette étape.

**« Sentinelle relue, inchangée » ne remplace pas la lecture du journal.**
Le 2026-08-18, une session a sauté l'étape « lire `celebrations.jsonl` et
chercher sa propre branche » et l'a remplacée par « relire le fichier
sentinelle juste avant d'écrire, vérifier qu'il n'a pas bougé depuis la
première lecture ». Ça n'attrape pas la même course : une session parallèle
peut avoir déjà *loggé* votre branche via son propre balayage sentinelle→HEAD
(qui traverse plusieurs merges d'un coup) sans avoir encore *avancé* le
fichier sentinelle — la fenêtre entre son log et son écriture du fichier.
Dans ce cas le fichier relu est identique aux deux lectures, l'écriture
passe, et l'entrée est dupliquée dans le journal sans qu'aucun des deux
contrôles ne l'ait vu. Cette fois-ci le résultat était correct (une seule
entrée, un seul autre roar en vol), mais par absence de collision, pas par
la vérification effectuée. Les deux contrôles sont complémentaires, pas
substituables : le fichier protège contre l'écrasement de l'avancée d'autrui,
le journal protège contre le doublon de votre propre entrée.
