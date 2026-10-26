# Audit de la chaîne métier recherche et publication

Date : 23 octobre 2026. Révision examinée : `b4b863c6`.
Auteur : Codex, modèle GPT-6, audit dans la session principale.

## Verdict

Les 17 skills métier couvrent les principales étapes et portent plusieurs exigences scientifiques utiles. Leur assemblage n'est cependant pas un protocole complet de revue vérifiée. Le défaut principal est dans les passages entre étapes : les mots « vérifié », « couvert », « archivé » ou « terminé » ne recouvrent pas partout les mêmes preuves.

La création d'un nouveau script de revue est justifiée. Il faut préserver l'ancien pendant l'essai et réutiliser les outils bibliographiques et documentaires après correction des défauts ci-dessous. Il serait prématuré de réécrire les 17 skills ou de leur imposer à tous une orchestration de revue de manuscrit.

Cet audit ne modifie aucun skill, script de production, routage ou règle. Il ne constitue ni un essai de lecture scientifique sur manuscrit, ni une réplication du papier King–Worthington. « Draconique » qualifie le protocole ; aucun nouveau nom de commande n'est décidé.

Le présent document conserve le constat initial. Les corrections et essais ultérieurs figurent dans [execution.md](execution.md). Pour reproduire les sondes avec les anciennes interfaces, utiliser le checkpoint d’audit `1206b23e`, dans un worktree jetable ; les sondes ne sont pas des tests de non-régression du code corrigé.

## Méthode et limites

Lecture des 17 `SKILL.md`, de leurs références et runbooks métier, des helpers de revue, de bibliographie, de décision éditoriale et de PDF annoté, des contrats Zotero, ainsi que des règles de sources, prose et compilation. Lecture des contrats transversaux `route`, `reviewers` et workflow pour évaluer les dépendances.

Contrôle des cibles des liens Markdown relatifs dans ces répertoires : aucune cible manquante dans le périmètre testé. Les chemins `runbooks/...` sont relatifs au skill ; l'absence d'un répertoire `runbooks/` à la racine n'est pas un défaut.

Huit sondes locales, conservées dans [probes.py](probes.py) et [evidence.json](evidence.json), utilisent des fichiers temporaires et de faux services. Aucun appel à un modèle, envoi de manuscrit, accès au vrai Zotero ou changement de source de production. La réponse HTTP simulée montre les limites du contrat du validateur ; elle ne prétend pas avoir découvert une mauvaise référence dans un manuscrit réel.

Onze fichiers de tests existants : **356 passed, 1 skipped**, en 36,94 s sur padme. La première exécution dans le bac à sable a produit 245 erreurs d'installation de fixtures, faute de permission de créer des sockets. La reprise avec les sockets locales autorisées a donné le résultat ci-dessus ; ces erreurs initiales ne sont pas des défauts de Zotero. Aucune mesure de qualité scientifique des modèles n'a été effectuée. Pas de relecture indépendante de cet audit.

## Inventaire : conserver, corriger ou raccorder

| Skill | Fonction et acquis | Conclusion |
|---|---|---|
| `zotero` | Métadonnées, dédoublonnage, fichiers stockés, lectures locales vivantes, indisponibilité explicite | Réutiliser le backend ; harmoniser les consignes d'import et le traitement des notes Markdown. F3. |
| `reading-note` | Lecture entière, distinction auteur/analyste, citations et folios vérifiés, statut de note | Conserver. Le statut de citations vérifiées ne certifie pas l'interprétation ; éviter d'en faire une validation scientifique globale. Raccord archivage F3. |
| `related-work-note` | Justification d'un paragraphe, alternatives, sources et méthode documentées | Conserver son périmètre. Corriger la validation et le transfert vers Zotero/BibLaTeX. F2–F3. |
| `biblio-saturation` | Diversité des recherches, vérification contradictoire, provenance, critère d'arrêt | Réutiliser pour une vraie revendication de nouveauté ; pas pour chaque référence. Clarifier résultat inconnu et limites de couverture. F6. |
| `critical-lit-review` | Objet, acteurs, controverses, hypothèses naturalisées, notes individuelles | Conserver comme travail autonome. Son appel à la saturation doit préciser les entrées et sorties attendues. F6. |
| `message-framing` | Définition de la contribution et choix par l'auteur | Conserver. Une revue peut proposer un recadrage ; elle ne remplace pas l'arbitrage de l'auteur. |
| `external-peer-review` | Routage, réception de vraies revues, indépendance déclarée, synthèse | Remplacer progressivement son moteur de revue ; le helper actuel n'exécute pas le protocole scientifique. F1. |
| `ingest-decision-letter` | Sources, segmentation, identifiants de remarques, couverture | Réutiliser ses primitives. Ajouter la disposition de chaque remarque et corriger la portée de couverture et le manifeste. F4. |
| `track-changes-pdf` | Refs Git épinglées, extraction isolée, latexdiff | Conserver ; compléter les entrées de compilation et la vérification du produit. F5. |
| `cut-prose` | Suppression avant condensation, protection des arguments et remarques | Conserver. Le futur registre doit permettre de retrouver les obligations et preuves après une coupe. |
| `pdf-finish` | Passe tardive, variantes et contrôle typographique | Réviser la frontière automatique/visuelle et isoler les variantes. F5. |
| `choose-venue` | Adéquation, coûts, ouverture, critères et dates officiels | Conserver hors du moteur central. Suggestions de revue à traiter comme propositions, puis vérifier dans ce skill. |
| `conference-submission-prep` | Lecture de l'appel, contraintes, adaptation, revue avant envoi | Conserver. Le futur moteur est un lecteur possible ; il doit recevoir les critères propres à l'appel. |
| `slides` | Message, rendu, contrôle visuel de toutes les pages, fidélité des chiffres | Conserver ; ne pas imposer ce contrat au manuscrit par analogie. Le skill distingue déjà correctement diagnostic et édition. |
| `submission-event` | Séparation travaux en cours/œuvres, registres et versions | Conserver. Le résultat d'une revue ne constitue aucun événement de soumission ou de publication. |
| `update-publist` | Préparation du dépôt, inspection du PDF, données du dépôt et confirmation avant publication | Conserver comme étape distincte. Une revue ou une finition ne vaut pas autorisation de dépôt. |
| `aap-annonce` | Lecture d'un appel, recevabilité, trois angles, instruction du dossier | Conserver comme branche distincte. Une évaluation d'AAP ne doit pas hériter sans adaptation de la grille de revue d'article. |

## F1 — La revue actuelle est un transport de prompts sommaires, sans vérification intégrée

**Priorité haute pour le nouveau script.**

Preuves : [skill](../../../skills/external-peer-review/SKILL.md), [helper à la révision auditée](https://github.com/MinhHaDuong/ImperialDragonHarness/blob/b4b863c6/skills/external-peer-review/peer_review.py), [procédure OpenRouter à la révision auditée](https://github.com/MinhHaDuong/ImperialDragonHarness/blob/b4b863c6/skills/external-peer-review/references/openrouter.md). Dans le helper : `PERSONAS`, `DEFAULT_TASK`, `build_messages`, `review_one`, `main`.

Le skill exige une revue non vide et la couverture du manuscrit. Le helper envoie une persona et une tâche courte. Il n'ajoute aucun outil de recherche web ni boucle de vérification, et n'impose pas la lecture ou la restitution d'éléments des annexes. Le repli automatique en texte conserve le même parcours alors que figures et équations peuvent ne plus être lisibles. Le mode est journalisé, mais la dégradation n'est pas un statut structuré qui borne les conclusions.

Sondes reproduites : une réponse de modèle vide, avec `finish_reason='length'`, produit un fichier avec seulement un titre et est acceptée par `review_one`. Une seconde exécution écrase le premier fichier. Le code ne contrôle pas la raison d'arrêt ; après des échecs de combinaisons, `main` journalise les échecs mais n'émet pas de code de sortie d'échec explicite. Ce dernier point est une lecture du code, pas une sonde de processus dans cet audit.

La synthèse de la référence OpenRouter considère qu'un problème repris par trois revues sur quatre prime un problème isolé. Or ses quatre combinaisons par défaut proviennent de deux modèles avec deux personas chacun : leur répétition n'établit pas quatre soutiens indépendants. Le skill principal reconnaît mieux cette limite que sa référence. Un défaut démontré dans une équation doit pouvoir primer un accord répétitif non vérifié.

**Conséquence :** des fichiers présents peuvent passer pour des revues complètes ; la synthèse peut amplifier une erreur partagée. Le nouveau script doit conserver les sorties originales et vérifier les constats avant synthèse. Cela ne demande pas d'ajouter des contrôles au vieux helper destiné au retrait.

## F2 — La chaîne bibliographique peut annoncer un contrôle incomplet et dupliquer une œuvre

**Priorité haute ; défauts reproduits et limite de contrat à distinguer.**

Preuves : [validateur](../../../scripts/validate-refs.py), fonctions `_split_entries`, `_fetch`, `main` ; [fusion](../../../scripts/bib-merge.py), fonctions `_base_key`, `merge` ; [runbook](../../../skills/related-work-note/runbooks/validate.md).

Une entrée BibTeX valide écrite sur une seule ligne n'est pas comptée par le validateur. Le parseur de fusion du même dépôt la lit : contrôle positif. Le validateur retourne pourtant zéro et « WARN: 0 of 0… ». Dans une bibliographie mixte, les entrées ignorées peuvent donc disparaître du dénominateur. Ce n'est pas une référence absente ; c'est une lecture incomplète.

Le validateur traite un HTTP inférieur à 400 comme une résolution réussie. La sonde d'une URL menant à un autre article renvoie PASS. Ce comportement correspond à un contrôle d'accessibilité : il ne vérifie ni l'identité de l'œuvre, ni le passage soutenant la citation. Le défaut d'intégration serait de transformer ce PASS en « référence scientifiquement vérifiée ».

La fusion ne compare les DOI qu'à l'intérieur d'un groupe auteur/année. Même DOI et même titre, mais 2020 contre 2021 : nouvelle entrée ajoutée. La clé de groupe ne lit que `year`, alors que le modèle de `related-work-note` prescrit `date`. Les preuves de la duplication sont donc indépendantes du cas plus large des dates BibLaTeX.

**Correction attendue :** tout ce qui ressemble à une entrée doit être analysé ou signalé comme non lu ; indexer les identifiants forts indépendamment de l'auteur/année ; accepter le format de date produit par le skill. Conserver quatre résultats distincts : accessibilité, identité, pertinence, soutien de l'affirmation. Réutiliser des primitives existantes si possible, sans ajouter un nouveau parseur artisanal.

## F3 — Archivage et rattachement à Zotero : contrats contradictoires

**Priorité de continuité documentaire.**

Preuves : [import, Duplicate handling](../../../skills/zotero/references/import.md), [backfill](../../../skills/zotero/references/backfill.md), [reading-note, Store it](../../../skills/reading-note/SKILL.md), [règle Zotero](../../../rules/zotero.md), [runbook bibliographique](../../../skills/conference-submission-prep/runbooks/bib-merge.md).

L'import conseille par défaut de recréer une notice si une œuvre trouvée n'a pas de fichier, avec fusion ultérieure. Le backfill prescrit précisément le contraire : `suggest-attachments` sur la notice existante. Le garde de `create-items` refuse par ailleurs les doublons identifiés. Suivre le chemin d'import peut donc échouer ou pousser à forcer un doublon inutile.

Les notes Markdown doivent être archivées, mais `check-staging` les exclut explicitement. Ce choix est documenté ; ce n'est pas un bug caché du backend. En revanche, une réconciliation ne couvre donc pas l'ensemble des objets que la règle exige d'archiver. `reading-note` parle d'import « URL intake » pour un fichier `.md` sans donner la commande adaptée ; l'archivage reste possible via une entrée Document et une pièce jointe, comme l'intake de cette session l'a démontré.

`related-work-note` et le runbook de fusion repoussent l'import Zotero à la soumission, alors que la règle générale en fait le système de référence dès l'intake. Le nouveau script doit pouvoir s'appuyer sur une seule chaîne d'archivage, et non inventer un deuxième gestionnaire bibliographique.

**Correction attendue :** attacher à l'existant ; rendre explicite l'archivage des notes produites et son reçu ; distinguer « réconciliation des PDF réussie » d'« ensemble des sources et notes archivé ». Le moment d'import doit être cohérent entre les skills concernés.

## F4 — Le registre R&R suit des tickets, mais pas encore les décisions scientifiques

**Priorité pour fermer le cycle de revue.**

Preuves : [skill R&R](../../../skills/ingest-decision-letter/SKILL.md), [helper](../../../skills/ingest-decision-letter/ingest_letter.py), fonctions `_ticket_ids_from_dir`, `coverage`, `archive`.

Le schéma possède texte, catégorie et tickets ; il ne représente pas une remarque rejetée avec justification, reportée ou déjà satisfaite. Une remarque sans ticket reste découverte. Ce contrat incite à traiter toute objection comme un travail à réaliser, alors que l'auteur peut légitimement la contester. Il manque aussi le lien explicite de la résolution à une modification ou une preuve ; « ticket lié » ne signifie pas « problème réglé ».

La commande recommandée utilise `--tickets-dir tickets/`, qui collecte récursivement tous les tickets, y compris clos. Une seule remarque correctement reliée au ticket de sa ronde laisse un ticket sans rapport déclaré orphelin : sonde reproduite. Le skill dit « tickets de cette ronde », mais son exemple ne fournit aucun filtre de ronde. L'option `--tickets` existante permet déjà un univers explicite ; il faut conserver à part la vérification d'existence des références.

Deux appels d'archivage dans le même dossier préservent les deux fichiers mais remplacent le manifeste par les seules entrées du second appel. Sonde reproduite : deux fichiers conservés, une entrée de manifeste. La promesse d'archive immuable et append-only n'est donc pas assurée pour ce manifeste.

**Correction attendue :** dispositions motivées, séparation couverture/résolution, univers de ronde explicite et manifeste cumulatif ou manifestes immuables par intake. Réutiliser le registre, plutôt qu'en créer un incompatible pour les revues IA. La promesse de PDF « groupé par ticket » en fin du skill R&R doit aussi être alignée sur le périmètre v1 réel de `track-changes-pdf`.

## F5 — La finition et le PDF de révision promettent plus que les contrôles exécutés

**Priorité avant livraison.**

Preuves : [pdf-finish](../../../skills/pdf-finish/SKILL.md), [typographie](../../../skills/pdf-finish/runbooks/typography-finish.md), [helper latexdiff](../../../skills/track-changes-pdf/track_changes_pdf.py), fonction `compile_pdf` ; [règle de compilation](../../../rules/manuscript-build.md).

`pdf-finish` exige des contrôles mécaniques de coupures de figures/tableaux, légendes et veuves/orphelines en balayant du texte extrait. Il ne fournit pas de helper correspondant. Un extracteur de texte sans analyse de géométrie ni rendu ne suffit pas à établir ces propriétés ; le même skill exige heureusement aussi une inspection visuelle. La correction est de préciser ce qui a été effectivement contrôlé, automatiquement et visuellement, et quelles pages ont été examinées.

Le retrait anonyme de tous les DOI et URL de dépôt, sans identifier lesquels désignent l'auteur ou sa version, est trop large : les références scientifiques ordinaires contiennent ces éléments. C'est une consigne à préciser, pas une invitation à supprimer toute référence à l'aveugle.

Le modèle de variante « transformer la source, rendre, restaurer » dépend d'une restauration fiable et peut interférer avec l'édition en cours. Une copie isolée, liée à une version source, est plus sûre pour une passe automatisée ; ce risque n'a pas été provoqué dans un projet réel.

`track-changes-pdf` vérifie le retour du compilateur et l'existence du PDF, sans analyser les références non résolues. Une sonde de faux compilateur écrit un PDF et un log avec citations indéfinies : `compile_pdf` l'accepte. Le fallback de deux passages pdflatex ne lance pas à lui seul le processeur bibliographique. Enfin `git archive` ne récupère pas une `.bib` ignorée, contrairement à ce que suggère « full tree » ; la disponibilité des entrées de compilation doit être explicite. Ces problèmes peuvent produire un PDF annoté dont la présence masque une bibliographie dégradée.

**Correction attendue :** compilation sur un paquet d'entrées complet et épinglé, contrôle du produit conformément à la règle existante, inspection visuelle déclarée, variantes isolées. Aucune raison d'appliquer des changements globaux de pagination au manuscrit pour réaliser cet audit.

## F6 — Recherche approfondie : distinguer absence de résultat et manque d'accès

**Lacune de contrat scientifique, sans mesure d'erreur sur corpus dans cet audit.**

Preuves : [saturation, phases 2–4](../../../skills/biblio-saturation/SKILL.md), [état de l'art, Build the corpus](../../../skills/critical-lit-review/SKILL.md).

La saturation demande de ne pas déclarer une antériorité quand la preuve est mince ou inaccessible. Cette prudence est bonne. Son vocabulaire final ne fournit cependant pas de résultat inconnu explicite à côté d'antériorité établie et de travail à citer. Si l'inaccessibilité est convertie en résultat négatif, une revendication de nouveauté reste trop forte. De même, un tour sans nouveau candidat ne signifie pas une saturation quand des angles n'ont pu être cherchés.

L'état de l'art appelle cette compétence pour constituer un corpus entier, alors que son contrat d'entrée décrit un registre factuel et une revendication de nouveauté. Il faut un passage explicite du cadrage à la recherche de corpus, puis une vraie saturation des revendications de lacune. Sans cela, l'orchestrateur doit inventer l'interface.

Les exigences de nombre de requêtes et de lots d'agents ne constituent pas une preuve de couverture. Les instructions `Workflow`, `ToolSearch`, `WebFetch` et `WebSearch` sont aussi propres à certains runtimes. Le nouveau script doit demander une capacité de recherche et constater son exécution, sans présumer qu'un nom de tool ou un lot de huit est disponible partout.

**Correction attendue :** restituer candidats et recherches consultés, angles empêchés, textes réellement lus et antériorités non résolues ; réserver le verdict de saturation au périmètre effectivement examiné. La recherche de références proches d'un manuscrit ne doit pas déclencher automatiquement une saturation multilingue complète.

## Ce qui doit devenir le nouveau protocole de revue

Le prompt de King–Worthington fournit un bon noyau de lecteur. Le script doit lui donner un environnement et des preuves ; copier ses instructions sans exécuter la recherche ne les satisfait pas.

1. **Fixer les entrées.** Version et empreinte du manuscrit, annexes disponibles, limites d'accès, question de l'auteur, type de document. Préparer texte paginé et pages rendues pour figures et équations ; déclarer les éventuelles pertes.
2. **Lire et chercher.** Instructions sourcées, outils réellement disponibles, lecture intégrale, recherche vérifiée, constat des limites. Une première revue complète suffit pour le premier essai ; une pluralité de lecteurs reste une option à justifier.
3. **Conserver la revue brute.** Identité effective, effort lorsque connu, prompt/version, mode d'entrée, résultats de recherche, raison d'arrêt et échecs. Une exécution possède son dossier ; une reprise ne détruit pas les précédentes.
4. **Vérifier avant restitution.** Décomposer les critiques importantes, comparer leurs descriptions au texte et aux pages, vérifier les attributions décisives dans leurs sources. Séparer factualité, gravité, jugement scientifique et proposition de révision. Une sortie tronquée ou une source non lue reste incomplète.
5. **Restituer avec preuves.** Quelques problèmes prioritaires, localisation et correction possible, incertitudes, limites de couverture et désaccords. La fréquence d'une critique n'est pas sa validité.
6. **Recueillir les décisions.** Accepté, contesté avec preuve, reporté, déjà satisfait ; garder le lien à la modification ou au motif de non-modification. L'auteur ne doit pas avoir à obtenir l'accord du lecteur sur chaque choix scientifique.
7. **Réviser puis relire la version changée.** Reprise bornée aux enjeux de la révision, conservation des points ouverts et arrêt défini avec l'auteur. Finition seulement lorsque le contenu est stabilisé ; archivage par Zotero ; publication par les compétences existantes.

Les comparaisons A/B, masques de pertinence, scores, permutations d'ordre et contrôles expérimentaux du papier sont des instruments d'évaluation du protocole. Ils peuvent devenir un mode d'essai, mais ne doivent pas alourdir chaque revue de production. Le cycle normal inclut bien la vérification ; il n'a pas besoin de reproduire toute l'expérience comparative de l'article.

## Découpage proposé après audit

Ce sont des lots proposés, pas des tickets créés ni un engagement d'implémentation dans cet audit.

| Ordre | Lot | Sortie vérifiable |
|---|---|---|
| 1 | Nouveau moteur de revue, indépendant de l'ancien — F1 | Un manuscrit réel relu avec recherche, vérification, preuves conservées et décisions d'auteur ; ancien outil intact. |
| 2 | Intégrité bibliographique et archivage — F2–F3 | Les entrées ignorées sont signalées, un DOI ne se duplique pas selon l'année, les fichiers rejoignent la bonne notice, les notes produites ont un reçu d'archivage. Peut nécessiter plusieurs petits changements. |
| 3 | Registre de revue/révision réutilisable — F4 | Contestation motivée possible, couverture limitée à la ronde, résolution prouvée et manifestes préservés. |
| 4 | Finition et PDF annoté fiables — F5 | Entrées complètes, citations résolues, variantes isolées et compte rendu de contrôle visuel. |
| 5 | Interfaces de recherche bibliographique — F6 | Inconnus et angles empêchés distincts d'un résultat négatif ; corpus de revue et saturation de nouveauté raccordés explicitement. |

Le lot 1 peut commencer en utilisant manuellement les primitives existantes et des vérifications explicites. Les autres lots ne sont pas tous des prérequis à un premier essai. Le retrait de l'ancien outil vient après une revue réelle satisfaisante et le contrôle de ses appelants, pas après la simple création d'un script.

## Rejouer les preuves

Depuis la racine du checkout, avec les dépendances de développement installées :

```sh
python docs/audits/2026-10-23-skills-metier/probes.py
```

Les sorties attendues décrivent les défauts de la révision auditée. Il ne faut pas en faire des tests de régression qui exigeraient de conserver ces défauts. Les futures corrections doivent convertir les cas utiles en tests d'acceptation de la bonne conduite.

Tests existants exécutés : `test_external_peer_review_skill`, `test_validate_refs`, `test_bib_merge`, `test_ingest_decision_letter`, `test_track_changes_pdf`, `test_zotero_import`, `test_zotero_find_work`, `test_zotero_check_staging_bib`, `test_zotero_report_duplicates`, `test_zotero_rule`, `test_zotero_backend_name`.
