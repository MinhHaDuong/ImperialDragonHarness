# PADME Project Memory

## Commit practices
- Always commit policy docs (main-logbook.md) together with their implementing scripts — they are a unit.
- Never say "prêt à commit" without actually committing. Either commit directly or ask if the user wants to commit.

## Entries

- [Opérations privilégiées](project_padme_privileged_ops.md) — `sudo -n` échoue sur padme : toute étape root se rend à l'auteur, livrer un script idempotent plutôt qu'une liste de commandes
- [Accès distant par netbird](project_padme_remote_access_netbird.md) — `wt0` est le seul chemin hors LAN ; un upgrade de netbird/network-manager coupe le lien, donc `apt` sous tmux
- [Vérifier le prédicat, pas seulement le résultat](feedback_verifier_le_predicat_pas_seulement_le_resultat.md) — un « rien à signaler » indistinguable d'un « je n'ai pas su regarder » ; éprouver le contrôle contre un cas connu positif
