---
name: No sudo — ask the user
description: Never run sudo commands; ask the user to run them and paste output.
type: feedback
originSessionId: bac3c7fd-350c-4179-9b07-72ad2c7e85b5
---
Ne jamais invoquer `sudo` directement. Si une opération requiert root (lire `/etc/snapper/configs/*`, `btrfs quota`, éditer `/etc/cron.d/`, etc.), demander à l'utilisateur d'exécuter la commande et de coller la sortie.

**Why:** l'utilisateur a explicitement rejeté un `sudo -n` et corrigé "You cannot sudo. Ask me." — il garde le contrôle des actions privilégiées.

**How to apply:** avant toute commande nécessitant root, soit proposer la commande exacte à l'utilisateur (`! sudo ...` pour qu'il la lance dans la session), soit demander la sortie. Les lectures de fichiers sous `/etc/` ou `/root/` qui échouent en non-root tombent sous cette règle.
