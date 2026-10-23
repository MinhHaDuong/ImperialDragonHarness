# Train métier 1198 — exécution MOE

Base commune de la première vague : `1206b23e`. Tracker 1198, enfants 1199–1205. Autorisation auteur : train complet, exécution autonome sous supervision MOE, validation des skills par Astra et Fable avec KISS.

## Conception

- Astra : `gpt-6-astra`, OpenAI, high, route native avec contexte neuf ; identité confirmée par turn_context. Avis de conception reçu, pas validation finale.
- Fable : `claude-fable-5-1`, Anthropic, high demandé, porte `claude -p --model fable`, outils Read/Glob/Grep seulement, permission dontAsk ; identité confirmée par modelUsage. Avis reçu, pas validation finale. Coût rapporté par le CLI : 4,9408085 USD.
- Les deux avis portent sur `1206b23e`. Sources originales déjà acquises et archivées avant ce train. Les sorties Fable et leur métadonnée sont conservées dans `reviews/` ; l’avis Astra est consigné avec sa provenance.

Décisions MOE : une seule revue complète avant toute multiplication des lecteurs ; conservation des recherches réellement exécutées ; schéma R&R commun ; protocole de production distinct des comparaisons expérimentales ; aucun framework ni nouvelle gestion de credentials.

Champs R&R convenus avec 1202 : round, disposition (accepted/rejected/deferred/already_addressed/null), reason, resolution (open/resolved), evidence (références). Les constats factuels et extraits restent dans les artefacts de vérification auxquels evidence renvoie. Les deux vocabulaires proposés par les lecteurs ne seront pas implémentés en parallèle.

## Exécutants

Tous les exécutants ci-dessous : `gpt-6.1-sol`, OpenAI, medium, contexte neuf, code ordinaire borné ; worktrees distincts ; aucune autorité de fusion. Validation finale des skills encore à obtenir.

- 1200 bibliographie : t1200-biblio-integrity ; réutilisation de bibtexparser, tests des défauts avant correction.
- 1202 registre de révision : t1202-revision-ledger ; contrat additif convenu avant le moteur.
- 1203 finition/PDF : t1203-pdf-product ; contrôles du produit, entrées explicites épinglées, pas d’analyseur de mise en page.

Les barrières du dépôt sont conservées : tests métier puis gate complet, revue et verify-gate avant fusion. Les erreurs de sockets ou caches dues au bac à sable ne sont pas requalifiées en défaut de code ni en passage réussi.

## Première composition vérifiée

- 1200 intégré par c3ba3a68 ; 1202 par 3f19a22c ; 1203 par e8c94112.
- Gate complet sur cette composition : **2130 passed, 4 skipped**, 32,76 s. Le premier gate sur la base documentaire avait rencontré trois erreurs de fixture Zotero401 ; les gates suivants des lots et de leur composition passent. Cause de cet incident initial non isolée ; aucun changement Zotero opportuniste.
- Lecture de code intermédiaire par Luna/OpenAI/medium : aucun constat dans les trois lots, sans nouvelle exécution des tests. Même famille que les exécutants ; ne remplace pas la validation Astra/Fable.
- 1201 intégré par eb865394 ; 1204 par dcb6a99b. Backend Zotero inchangé ; contrôles documentaires et35tests existants réussis côté exécutant.
- 1199 en implémentation dans son worktree, selon les deux avis KISS et le schéma de1202. Essai réel et validation des skills finaux toujours ouverts.

## Publication en attente d’autorisation

Le contrôle automatique a refusé le push de la branche et la création d’une demande de fusion brouillon vers le dépôt GitHub, au motif d’une absence d’autorisation explicite pour ce contenu et cette destination. Une question précise a été transmise à l’auteur. Aucun contournement ni seconde tentative ; le travail se poursuit localement. Le refus ne concerne pas les relectures Astra/Fable explicitement demandées.

## Reprise et validation finale initiale

Push et demande de fusion brouillon explicitement autorisés par l’auteur ; PR1633 créée. Le refus automatique antérieur est levé par cette autorisation, pas contourné.

Validation des skills sur0121b6a6 : Astra relève trois défauts mécaniques bloquants du moteur/registre et une contradiction Zotero ; Fable valide l’architecture avec limites et relève cette même contradiction et la nécessité de qualifier les passages WebFetch comme sorties potentiellement traitées. Avis et métadonnées dans reviews/. Coût CLI Fable final4,57409425USD, modèle observéclaude-fable-5-1. Les correctifs restent bornés, sans juge supplémentaire ni couche d’adaptation.

Essai public1 : article King–Worthington et annexe,38pages. Lecteur exécuté,12constats produits. Vérificateur :76lectures texte/image et4WebFetch, mais pas deWebSearch. Exécution native terminée avec succès ; moteur retourne incomplete car son contrat exigeait encore recherche et récupération à chaque passe. L’essai reste inchangé, ne constitue pas un cycle achevé. Correction retenue : recherche obligatoire du lecteur ; vérificateur borné aux sources décisives, recherche lorsque nécessaire, couverture des récupérations conservée. Nouvel essai requis avec les champs corrigés ; aucune sortie simulée présentée comme preuve métier.

Bibliographie1200 close sur critères fonctionnels/testés et avis sans constat restant de parsing ; intégration globale1198/1205 encore ouverte. Les logs historiques restent inchangés.

Composition après corrections Astra/Fable : e3233985, make check complet **2156 passed,4 skipped**,31,28s. Astra a recontrôlé les quatre constats et exécuté57tests : tous résolus, validation bornée sans constat restant. L’essai2 et le retrait de l’ancien moteur restent des preuves distinctes en cours.

## Retrait préparé, non encore intégré

Les commits locaux cfb59cf6 et68150364 préparent le retrait : suppression de l’ancien exécuteur et de sa référence de transport, orchestration externe conservée comme contrat de lecteurs indépendants, préparation conférence raccordée au nouveau parcours ordinaire, extraction minimale du lecteur de provider encore consommé par la sonde mémoire, suppression du SDK inutilisé et de ses dépendances exclusives.90tests ciblés réussis,1sonde live optionnelle ignorée ;35contrôles de skills réussis. Le runner actuel ne sait appeler que le CLIClaude : aucune exécution multi-famille ou compatibilité Albert nouvelle n’est prétendue. Un autre mécanisme doit conserver les mêmes preuves, sinon perspective indisponible.

Ces commits restent hors de la branche d’intégration jusqu’au succès du nouvel essai public ; le tracker demeure ouvert.

Essai2 : lecteur validé,11constats ; vérificateur terminé mais contrôle refusé pour extraits assemblés avec points de suspension et source présentée accessible malgré une redirection seule. Les deux tentatives et leurs empreintes figurent dans trial-attempts.json. Le contrôle reste strict. Astra accepte une reprise bornée de la seule vérification dans un nouveau dossier, avec lecteur original revalidé et épinglé ; aucune réussite déclarée avant cet essai.
