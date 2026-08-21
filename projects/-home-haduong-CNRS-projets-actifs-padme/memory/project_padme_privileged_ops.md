---
name: project-padme-privileged-ops
description: "Un agent ne peut pas exécuter de commande privilégiée sur padme — sudo y demande un mot de passe, donc toute étape root se rend à l'auteur."
metadata: 
  node_type: memory
  type: project
  originSessionId: 0dd7065c-e3cf-4dae-a477-8dae7737aa9a
  modified: 2026-08-21T11:01:51.407Z
---

`sudo -n` échoue sur padme (« il est nécessaire de saisir un mot de passe »).
Aucune opération root n'est donc réalisable depuis une session agent : déployer
des unités systemd, lancer restic, lire `/var/log/p620-checks/*` en écriture,
`apt upgrade`, redémarrer.

**Why:** la moitié du travail utile sur cette machine est privilégiée. Découvert
en pleine réparation d'urgence le 2026-08-21 (7 timers morts, 72 jours sans
sauvegarde), où la seule chose que je pouvais livrer était le correctif plus des
commandes prêtes à coller.

**How to apply:** structurer le livrable pour ça dès le départ — préparer un
script idempotent et vérifiable plutôt qu'une séquence de commandes à copier une
par une, et le faire échouer proprement en non-root (`id -u` en tête). Annoncer
explicitement « je ne peux pas le faire moi-même » plutôt que de laisser croire
que l'étape est faite. Ce qui reste faisable sans sudo : lecture du journal
(`journalctl` utilisateur), `systemctl show/is-active/is-enabled/list-timers`,
`git` dans `~/padme`, `curl` sur les ports locaux. Voir
[[project-padme-remote-access-netbird]] pour l'autre contrainte d'accès.
