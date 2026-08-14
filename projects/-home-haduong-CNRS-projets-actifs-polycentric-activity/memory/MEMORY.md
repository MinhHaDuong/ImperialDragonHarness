# Memory index — polycentric_activity

## Key insights

- **Vérifier sur pièce, jamais sur la foi d'un intermédiaire.** Le corpus redécouvre la même leçon sous quatre formes : un candidat classé secondaire dans un ticket, une occurrence de grep sans son contexte, un `.blg` non lu après une purge de bibliographie, une typographie rétro-portée sans relire la langue du texte. La pièce dit ce qui est ; le registre dit seulement ce qu'il a.
- **La sortie « clean » d'un outil n'est pas une preuve.** Un merge dit « clean » sur une base périmée, un scan qui ne peut pas regarder rend le même vide qu'un scan qui n'a rien trouvé, une table de preuves se contredit d'une colonne à l'autre. Tout garde dont l'« tout va bien » est indiscernable de « je n'ai pas regardé » doit être éprouvé sur un cas positif connu.
- **L'état courant se date, il ne se suppose pas.** Sessions parallèles et worktrees font que le fichier qu'on lit peut avoir des jours de retard, qu'une branche peut avoir été réécrite sous nos pieds, qu'un `erg-pr-merge` peut avoir déjà poussé son commit de fermeture. `git log -S`, la sonde d'ancêtre et le diff sont les instruments ; l'inférence ne l'est pas.
- **La charge de vérification revient à l'agent, jamais à l'auteur.** Pas de centaure inversé, pas de corvée résiduelle, pas de fichier à renommer à la main : ce qui reste à l'auteur est l'arbitrage, c'est-à-dire la décision qu'il est seul à pouvoir prendre — pas le contrôle que la machine pouvait faire.
- **Les contraintes de forme du manuscrit sont des invariants mesurables.** Pagination du §3 HET, typographie fine réservée à la finition, un seul `manuscrit.pdf` canonique : ces règles se vérifient par construction comparée avant/après, pas à l'œil, et se signalent avec des options plutôt que se tranchent seules.

## Entries

- [No version-suffix filenames](feedback-no-version-suffix-filenames.md) — one canonical manuscrit.pdf; git holds history
- [erg-pr-merge stale-worktree bounce](feedback-ergprmerge-stale-worktree-after-api-push.md) — gaze API-pushes leave executor worktrees behind; recover via detached cherry-pick + ff push, never rerun
- [Grep sans contexte n'est pas un audit](feedback-grep-context-audit.md) — toujours une fenêtre de contexte avant de qualifier une occurrence
- [Après un merge, vérifier le diff pas la sortie](feedback-merge-verifier-le-diff-pas-la-sortie.md) — `git diff origin/main --stat` ne doit montrer que vos fichiers ; le merge dit « clean » même sur base périmée
- [Purge de bib partagée casse les frères](feedback-purge-bib-partagee-casse-les-freres.md) — refs.bib sert 3 manuscrits ; après purge ou conflit, construire tous les frères et lire les .blg
- [Rejouer ou reconstruire une branche](feedback-rejouer-ou-reconstruire-une-branche.md) — deux commits qui s'annulent : reconstruire l'état final sur origin/main, pas rebaser
- [Typo fine à la finition](feedback-typo-fine-a-la-finition.md) — jamais en rédaction ; dépend de la langue du texte ET du balisage ; pas de rétro-port mécanique
- [Piste secondaire lue sur pièce](feedback-piste-secondaire-lue-sur-piece.md) — le candidat « secondaire » d'un ticket peut être le support principal ; tirer tous les candidats avant de rédiger
- [Ligne sans clause disculpatoire](feedback-ligne-sans-clause-disculpatoire.md) — dans une table de preuves, la ligne qui ne dit pas ce que ses sœurs disent est le défaut
- [Worktree périmé sert l'ancienne version](feedback-worktree-perime-sert-une-version-ancienne.md) — dater un changement avec `git log -S`, jamais conclure « c'est le nouveau » depuis le worktree d'une autre session
- [Sortie rtk — pipes corrigés en v0.45.0, écart résiduel non isolé](feedback-rtk-sortie-git-non-fiable.md) — le test empirique tranche et non la lecture du code amont ; vérifier par effet, jamais en analysant une sortie
- [Folio imprimé, pas offset d'extraction](feedback-folio-imprime-pas-offset-extraction.md) — une page citée se lit sur la page, jamais interpolée depuis un `pdftotext` du document entier
- [Contrôle de cadence au glob trop étroit](feedback-controle-cadence-glob-etroit.md) — le check de fraîcheur alarmait sur les fichiers les mieux tenus et exemptait les dormants ; ne jamais tamponner « revu » sans lire
- [Pas de centaure inversé](feedback-no-inverted-centaur.md) — ne jamais laisser à l'auteur une corvée de vérification résiduelle
- [Boucle dictée-arbitrage prose](project-boucle-dictee-arbitrage.md) — circuit registre sur main pour les arbitrages de prose dictés
- [Pagination manuelle HET §3](project-het-hand-pagination.md) — tout ajout déborde une page ; signaler avec options, arbitrage groupé après la dernière PR, repagination à la finition
- [Zotero injection auto (implémentée)](project-zotero-injection-auto.md) — le skill zotero-import injecte via l'API (PR harness #718) ; RIS en repli
- [Email professionnel de l'auteur](user-professional-email.md) — adresse pour manuscrits et correspondance
