---
name: project-padme-remote-access-netbird
description: "L'accès distant à padme passe uniquement par netbird (wt0) — un upgrade de netbird ou network-manager peut couper la session en plein dpkg."
metadata: 
  node_type: memory
  type: project
  originSessionId: 0dd7065c-e3cf-4dae-a477-8dae7737aa9a
  modified: 2026-08-21T11:02:03.491Z
---

`ssh padme` résout `100.93.160.120`, portée par l'interface **`wt0`** (netbird,
`100.93.0.0/16`). La machine a aussi `wlp4s0` en `192.168.0.131/24`, mais elle
n'est joignable hors LAN que par le tunnel.

**Why:** `netbird`, `netbird-ui`, `network-manager` et `libnm0` figurent
régulièrement dans les upgrades. Le redémarrage du démon fait tomber `wt0`. Si
la coupure arrive pendant `apt upgrade`, elle n'interrompt pas une session mais
**dpkg**, et laisse une base à réparer à la main. Constaté le 2026-08-21 : le
lien est bien tombé pendant l'upgrade des 42 paquets, et n'est revenu que
plusieurs dizaines de secondes plus tard.

**How to apply:** avant tout `apt upgrade` sur padme, lire la liste des paquets
et chercher `netbird`, `network-manager`, `libnm`, `openssh`. Si l'un y est,
faire lancer l'opération dans `tmux` (`tmux new -s upgrade`) : apt survit à la
coupure et l'auteur se rattache. Vérifier après coup que netbird est
`active` **et** `enabled` — c'est ce qui décide si la machine reste joignable au
prochain redémarrage. Corollaire : préférer un upgrade de netbird pendant que
l'auteur peut encore brancher un écran, jamais en son absence. Voir
[[project-padme-privileged-ops]].
