# Train métier 1198 — exécution et preuves

Autorisation auteur : train complet sous supervision MOE autonome ; validation des skills par Astra et Fable avec KISS. Push et brouillon GitHub explicitement autorisés après le refus automatique initial. PR 1633 ; tracker 1198 ouvert jusqu’à la revue d’intégration après fusion.

## Résultat métier

Un lecteur complet, une vérification bornée des critiques majeures, puis les décisions de l’auteur dans le registre R&R existant. Le protocole de production adapte Appendix C ; les scores, masques et comparaisons expérimentales restent hors parcours. Les17skills ont été examinés ; les corrections ciblent les six constats initiaux, sans réécriture générale ni nouveau catalogue documentaire.

Les lots bibliographie, Zotero/notes, révision, PDF et recherche sont livrés. L’essai public complet est réussi ; le candidat de retrait est adopté seulement après ce succès. Ancien exécuteur et référence OpenRouter supprimés, appelants migrés ; la revue externe indépendante reste un contrat explicite, avec limite réelle du runner actuel à un CLI. Le lecteur de provider encore utilisé par la sonde mémoire est extrait sans framework ; le SDK inutilisé et ses dépendances exclusives sont retirés. Voir retirement-inventory.md.

## Validations et identités

- Exécutants : Codex natif, gpt-6.1-sol/medium, worktrees isolés ; supervision gpt-6.1-sol/low. Même famille, aucune indépendance scientifique revendiquée.
- Astra : gpt-6-astra/high confirmé dans turn_context. Conception `1206b23e`, constats `0121b6a6`, corrections validées e3233985, reprise18e2a29f et candidat final b9c27de5587d303b52c7a55e5e539676ebdb2eca.100 tests ciblés réussis,1 sonde live optionnelle ignorée. Même fournisseur que le superviseur.
- Fable : claude-fable-5-1 confirmé par modelUsage, high demandé sans attestation indépendante de l’effort. Conception `1206b23e`, validation `0121b6a6` avec corrections bornées, puis validation finale b9c27de5 sans constat bloquant. Relecture de fidélité à Appendix C : aucun écart matériel. La première lecture du PDF hors espace autorisé avait été refusée ; une copie publique dans le worktree a permis cet addendum. Les limites de lecture sont conservées dans son avis.
- Les quatre constats initiaux Astra sont résolus : critiques omises du registre, sources décisives non contrôlées, atomiques entre rondes, import Zotero retardé. Le texte WebFetch est explicitement une sortie potentiellement traitée, pas les octets originaux.
- Simplifications Fable : recherche gratuite du vérificateur supprimée ; category laissé vide, gravité conservée dans review/verify ; identifiants existants conservés car la couverture utilise round. Pas de nouvelle taxonomie ou architecture. Le blanc EOF signalé par Astra est supprimé sans changement fonctionnel après b9c27de5.

Avis bruts et métadonnées dans reviews/. La validation des skills ne remplace ni l’essai réel ni gaze/verify-gate.

## Essai public réel

Source : King–Worthington,22 octobre 2026 ; manuscrit 15 pages et supplément 23 pages. Les PDF originaux et le protocole sont déjà archivés sous Zotero user:5IWA45WQ, note source CA22TVTN. Empreinte du supplément confirmée par le superviseur ; les procédures de jugement des annexes D/E ne sont pas copiées dans la production.

| Tentative | Résultat conservé |
|---|---|
|1|Incomplète : vérificateur natif terminé avec lectures/récupérations, mais absence de WebSearch alors exigée sans nécessité. Contrat corrigé.|
|2|Lecteur validé,11 remarques ; vérification refusée pour extraits assemblés.|
|3|Lecteur 2 réutilisé, nouveau vérificateur ; extraits continus corrects, mais contrôle canonique rejetant un article effectivement récupéré après redirections. Diagnostic corrigé après examen des traces.|
|4|Cycle complet sous le contrôle corrigé, auteur en attente ; lecteur 2 revalidé et conservé, nouveau vérificateur.|

Le correctif des redirections suit seulement les sauts natifs observés avec URL exacte, borne et refus des cycles/ambiguïtés. Le contrôle de sous-chaîne reste strict. Le format indenté réel est couvert par deux régressions reproduites rouges puis vertes. Une revalidation en lecture seule de 3 passe les cinq contrôles ; son statut historique reste incomplet.

Le cycle 4 fournit11 remarques. Le vérificateur confirme quatre critiques majeures et signale la cinquième comme mauvaise lecture, ramenée mineure. Ces jugements restent advisory, sans arbitrage scientifique humain. Les 11 dispositions sont nulles ; la couverture du registre indique 11 attentes et aucun enregistrement invalide. Aucun manuscrit réécrit, aucune décision inventée.

trial-attempts.json conserve entrées, empreintes, vrais appels/outils et identités ; trial3-revalidation.json décrit le contrôle en lecture seule ; trial-ledger-handoff.json constate le transfert au registre. Deux lectures ont été produites, les deux reprises réutilisent la deuxième ; ce ne sont pas quatre revues indépendantes. Les coûts des lecteurs réutilisés ne doivent pas être additionnés comme nouveaux appels.

## Archivage et contrôles

La note complète avec revue originale et vérification séparée est Zotero user:QVBRSPVZ, pièce jointe Markdown F5AJGQH2. L’archive des quatre tentatives, incluant sources, images, prompts et streams bruts, est jointe CZVL4QLQ. Deux lectures vivantes par storageHash confirment les octets importés ; type Document et abstractNote de provenance vérifiés par API locale. archive-receipt.json conserve les empreintes, clés et limites. Les fichiers complets restent dans Zotero, pas sur GitHub ; aucune matière privée de doudou utilisée.

make check complet du candidat `b9c27de5` : **2 179 réussis, 4 ignorés**, 33,50 s. Les contrôles intermédiaires et régressions de chaque lot sont dans les tickets et avis. Le premier contrôle documentaire avait rencontré trois erreurs de fixture Zotero 401 ; les contrôles suivants passent, cause initiale non isolée. Pas de réparation backend opportuniste.

Coarse-ink 1.9.6 a été examiné à la demande de l’auteur : décision de ne pas remplacer ce moteur par un pipeline aux garanties différentes, aucune dépendance ajoutée. Voir coarse-ink.md. Un essai comparatif éventuel reste distinct de la production.

Prochaine utilisation : un projet d’article de doudou choisi avec une révision et un périmètre de diffusion explicites. Le runner hébergé refuse le contenu non autorisé ; une perspective ou un backend non disponible reste déclaré indisponible. La qualité scientifique et l’amélioration du manuscrit ne sont pas établies par cet essai opérationnel.
