# Dragon memory design — revue (ChatGPT, 2026-09-10)

> **NON NORMATIF.** Une revue, enregistrée pour information. Rien ici n'est
> décidé ni adopté. Son verdict, ses critères de sortie corrigés et son ordre
> de livraison sont les recommandations du relecteur sur un brouillon, pas la
> politique du harness. Les normes vivent dans `rules/`, `CLAUDE.md` et les
> tickets — pas dans `docs/`.

**Auteur :** ChatGPT, prompté par Ha-Duong Minh.
**Enregistré le :** 2026-09-10, verbatim depuis le fichier fourni par l'auteur.
Les chiffres et les références sont ceux du relecteur et n'ont pas été
revérifiés à l'enregistrement.

Revoit le brouillon de conception
[`2026-09-10-dragon-memory-design.md`](./2026-09-10-dragon-memory-design.md).
C'est la lecture **hors famille** que ce brouillon demandait et que la revue
[`2026-09-10-dragon-memory-design-review-claude.md`](./2026-09-10-dragon-memory-design-review-claude.md)
déclarait encore due. Les trois rapports d'étude
([Fable](./2026-09-10-memoire-agent-fable.md),
[Perplexity](./2026-09-10-memoire-agent-perplexity.md),
[ChatGPT](./2026-09-10-memoire-agent-chatgpt.md)) sont d'une autre nature :
sollicités *avant* le brouillon, ils l'ont alimenté.

---

# Revue du design de mémoire du Dragon

**Date :** 10 septembre 2026  
**Préparé par ChatGPT prompté par Ha-Duong Minh**  
**Document examiné :** `dragon-memory-design.md`, « The Dragon's memory: measured assessment and design proposal », version du 10 septembre 2026.  
**Verdict :** révisions substantielles avant validation du programme ; réparations structurelles à poursuivre sous des critères de sortie corrigés.

## Synthèse exécutive

Le document fournit une base de diagnostic utile : séparation index/corps, inventaire des canaux résidents, recherche des mécanismes effectivement connectés, couverture de provenance et reconnaissance des limites des traces. Je conserverais cette architecture. Je ne validerais cependant pas encore les vagues 2–3 comme un programme cohérent de rétention.

Deux problèmes de conception sont bloquants. Premièrement, « les corps sont gratuits » désigne seulement leur absence du contexte résident, mais sert à justifier une conservation sans limite, alors que T7 annonce un plafond de corpus. Deuxièmement, la solution centrale — index résident borné et catalogue complet consultable — n'a aucun ticket ni critère d'acceptation. Tous les tickets pourraient être livrés sans que cette solution existe.

Deux conclusions empiriques sont également trop fortes : les sondes ne démontrent pas l'absence universelle de rappel automatique, et les ouvertures de corps ne mesurent pas l'utilité de la résidence. Le correctif n'est pas de renoncer à mesurer, mais de définir l'observabilité et d'ajouter des tests contrefactuels hors production.

**Décision recommandée :** poursuivre provenance, résolution des références et détection de doublons ; implémenter le catalogue complet et le budget résident ; différer le score composite et redéfinir le plafond de corpus. Tester les effets avant de rendre la consolidation plus autonome.

## Sommaire

1. Périmètre et points à conserver
2. Blocages de conception
3. Solidité des mesures
4. Identité, promotion et validité
5. Réponses aux six questions de revue
6. Programme et critères d'acceptation corrigés

## 1. Périmètre et points à conserver

Cette revue porte sur le document fourni, pas sur une inspection du dépôt. Les instruments, les traces, les versions exactes des PR et la note bibliographique citée en §3 n'ont pas été examinés. Les observations rapportées sont donc évaluées quant à leur cohérence et à la portée de leurs conclusions ; elles n'ont pas été reproduites.

Je conserverais quatre décisions : les corps hors du contexte résident ; un stockage explicite et inspectable ; la provenance couvrant tous les objets ; des contrôles vérifiant la population réellement parcourue par chaque mécanisme. La séparation entre index et corps est particulièrement utile. Le défaut n'est pas une absence de sophistication : c'est l'insuffisance des contrats entre ces pièces. [D, §1, §2.5, P6]

## 2. Blocages de conception

### B1 — P1 et T7 ne définissent pas la même politique de rétention

P1 affirme que rien n'est supprimé pour une raison de taille. P2 prévoit un index complet qui continue à tout lister. T7 plafonne le corpus et exige une consolidation avant une écriture dépassant le plafond. Il manque une définition de ce qui est borné : entrées actives, fichiers, caractères, octets, versions ou stockage total. [D, P1–P2, §6, T7]

Ces engagements peuvent coexister si le plafond ne porte que sur la mémoire active, ou si l'admission peut être refusée. Ils ne peuvent garantir à la fois un stockage total borné, une conservation sans perte et l'acceptation indéfinie d'expériences nouvelles. Une consolidation peut elle-même supprimer de l'information ; son caractère narratif ne supprime pas cet arbitrage.

**Modification proposée à P1 :** « Démoter avant de supprimer. L'absence de résidence ne signifie pas absence de coût. La mémoire active, les opérations de maintenance et le stockage conservé ont des politiques distinctes ; toute perte d'information significative est explicite. »

Je distinguerais trois contrats :

- un budget en caractères pour le contexte résident, qui est le problème immédiatement documenté ;
- un budget de travail par passe de maintenance, afin de ne pas retraiter indéfiniment tout le corpus ;
- une politique de conservation du stockage froid, avec un plafond global, le périmètre des historiques et une issue explicite lorsque l'admission ne peut plus être satisfaite.

Un plafond par projet ne borne pas le total lorsque le nombre de projets augmente. Une suppression du fichier courant ne supprime pas nécessairement ses versions conservées. Les traces doivent également avoir leur propre politique si elles appartiennent au périmètre de stockage géré.

Le document ne justifie pas encore un nombre maximal précis de corps. Un quota arbitraire pourrait être moins pertinent qu'un budget résident strict et une maintenance incrémentale. Les seuils proposés dans la synthèse précédente ne sont pas des valeurs empiriquement validées pour ce corpus.

### B2 — La solution centrale n'a pas de ticket

P2 propose un index résident court, une porte d'entrée et un catalogue complet. Aucun ticket de l'annexe A ne construit cette séparation. Le plafond existant est en lignes ; aucun nouveau critère de sortie ne borne explicitement les caractères de l'index résident. [D, §2.5, P2, annexe A]

Ajouter un ticket préalable aux démotions et à T7 : **« Catalogue complet, index résident borné et recherche ciblée »**. Ses invariants devraient être :

1. tout corps vivant possède une entrée résoluble dans le catalogue complet ;
2. toute entrée résidente renvoie à une mémoire valide ou à une référence explicitement marquée ;
3. une entrée démotée reste trouvable par une opération testée ;
4. la somme des index effectivement injectés respecte le budget résident ;
5. index, catalogue et références sont modifiés de façon cohérente, ou peuvent être restaurés après interruption.

La présence d'un lien vers le catalogue n'est qu'une condition d'accès. Elle ne garantit pas que l'agent pense à l'utiliser. Le chemin de consultation doit être testé sur des tâches nécessitant un souvenir froid et permettre une recherche ciblée, sans imposer l'ouverture intégrale d'un catalogue toujours plus grand.

## 3. Solidité des mesures

### M1 — §2.4 établit une non-détection, pas l'absence universelle d'un canal

Le contrôle « 32 descriptions sur 40 apparaissent quelque part » démontre que la recherche textuelle retrouve des chaînes dans les traces, notamment dans les lectures et écritures. Il ne démontre pas que ces traces exposent le contenu réellement injecté dans les messages système ou dans d'autres parties de l'entrée du modèle. [D, §2.4]

Les sondes pourraient manquer une injection non journalisée, une sélection située hors des 40 descriptions testées, une troncature, une reformulation, ou un mécanisme dont les conditions de déclenchement n'ont pas été rencontrées.

**Reformulation recommandée :** « Aucune injection verbatim des sondes n'a été détectée dans les canaux observables des traces étudiées. Aucun canal de rappel automatique n'est démontré par cette instrumentation. »

L'architecture peut, par prudence, ne dépendre d'aucun rappel automatique non vérifié. C'est une décision robuste sans nécessiter de prouver son inexistence.

**Test de réfutation proposé.** Placer plusieurs valeurs aléatoires artificielles uniquement dans des corps de mémoire. Les titres et questions ne doivent pas révéler les réponses. Tester des sessions neuves avec des déclencheurs pertinents ; instrumenter les accès explicites par lecture, recherche, shell et descendants de sous-agents. Ajouter un cas sans mémoire, un cas de lecture explicite et un cas d'injection contrôlée dans le canal dont on veut vérifier la visibilité. Ne pas neutraliser par inadvertance le mécanisme natif recherché. Capturer l'entrée effective du modèle lorsque c'est possible.

La restitution d'une valeur sans accès expliqué révèle une voie non couverte par l'observation ; elle ne prouve pas à elle seule quel mécanisme précis l'a transportée. L'absence de restitution ne suffit pas à prouver l'absence de toute voie possible.

### M2 — « Non indexé » ne signifie pas « inaccessible »

Même sans rappel automatique, un fichier peut être découvert par recherche de contenu, parcours de répertoire ou référence ailleurs. Il devient moins découvrable par la voie d'orientation prévue, pas nécessairement introuvable. L'annexe B reconnaît justement une invisibilité partielle des recherches `Grep`. [D, §2.4, annexe B]

L'argument « aucune occurrence nommant le slug, donc le résidu est petit » ne borne pas ce résidu : une recherche par contenu n'a précisément pas besoin de nommer le slug. Corriger cette conclusion et distinguer perte de visibilité, absence de référence canonique et perte physique.

### M3 — Les taux d'ouverture ne mesurent pas l'utilité

Les 11 % mesurent des sessions de travail avec une ouverture détectée. Les 94 % mesurent l'absence d'ouverture détectée pour une grande partie des entrées. Le texte reconnaît que certains titres peuvent suffire : ni l'une ni l'autre de ces statistiques n'est une mesure de bénéfice causal. [D, §2.3, P4, question 3]

Il faut également rattacher les lectures des sous-agents à leur tâche racine : une session de travail peut bénéficier d'une lecture faite par un descendant sans ouvrir elle-même le corps. Ajouter des opportunités d'exposition par entrée, car une mémoire créée récemment et une mémoire présente pendant toute la fenêtre ne sont pas comparables.

Les 55 638 caractères par ouverture sont un ratio d'exposition de l'index à une action détectée, pas un coût par résultat utile. Préciser si les tailles d'index sont reconstruites à la date des sessions ou si le calcul applique rétrospectivement les tailles actuelles. Les 5 022 tokens sont un maximum par projet, tandis que les 11 % agrègent des sessions : ces deux chiffres ne décrivent pas nécessairement la même population.

### M4 — #875 démontre une économie de caractères, pas une non-régression

Une phrase dans un corps non résident ne duplique pas fonctionnellement la même phrase dans un index résident. Supprimer le « hook » peut économiser des caractères tout en supprimant une consigne immédiatement disponible. Le gain de 44 % rapporté est utile ; le bénéfice net reste à tester. [D, §1, §7]

Construire des replays hors production avec corpus figé, tâches vérifiables et information disponible avant chaque tâche. Comparer index complet, titres seuls et index court avec consultation ciblée. Mesurer erreurs répétées, succès, recours correct aux souvenirs froids et coût total. Les déclarations de l'agent sur les mémoires qu'il aurait utilisées peuvent aider au diagnostic, mais ne remplacent pas l'ablation.

### M5 — Nettoyage arithmétique et de population

- « Writes exceed reads » inverse les chiffres : 726 écritures sont inférieures à 974 lectures. Le diagnostic « maintenance élevée » reste possible, mais il faut un coût et un dénominateur cohérents. [D, §2.5]
- 949 − 651 = 298, tandis que §7 rapporte 308 corps sans provenance. 651 + 308 = 959, pas 960. Des populations ou instantanés différents peuvent expliquer ces écarts ; ils doivent être identifiés. [D, §2.5, §7]
- Donner un tableau de passage entre corps vivants, tombstones, entrées de provenance et liens d'index, avec date et instantané. Épingler aussi les versions appliquées des PR pour permettre une reproduction exacte.

La note bibliographique citée en §3 n'est pas jointe. Je n'ai pas validé ses études ni ses scores. Ajouter leurs identifiants, versions et métriques dans ce document ; conserver explicitement le statut d'analogie, déjà reconnu, du seuil de 10 KB.

## 4. Identité, promotion et validité

### I1 — La similarité lexicale est un détecteur de candidats

Le rapprochement lexical est une première méthode raisonnable, mais 35 paires ne donnent pas nécessairement 35 leçons distinctes : plusieurs paires peuvent relier un même groupe. Une similarité de nom ne prouve pas non plus l'équivalence des conditions d'application. [D, §2.5]

Retirer de T3 le critère « candidats de 3 à ~38 ». Préférer un jeu de cas comprenant équivalences attendues et ressemblances trompeuses. L'outil propose des rapprochements, une validation explicite autorise les fusions. La précision sur ce jeu et l'absence de fusion automatique erronée sont plus utiles qu'un quota de candidats.

### I2 — Une promotion doit préserver l'adressage et le périmètre

« Le corps local n'est plus vivant » n'est pas un critère suffisant pour T1. Les anciens liens doivent résoudre vers le corps canonique, les preuves locales doivent rester accessibles et les exceptions de projet doivent survivre. Une redirection résoluble peut satisfaire cet objectif, à condition que les cycles et destinations absentes soient rejetés. [D, §1, T1]

La présence dans deux projets est un signal de candidature, pas nécessairement deux validations indépendantes : une même erreur peut avoir été copiée. Séparer identité, équivalence, transfert de périmètre et confiance. Une promotion interprojets ne doit pas, à elle seule, élever le niveau de confiance ni transformer une observation en instruction autoritaire.

### I3 — Le type et la durée de validité doivent rester distincts

Les types `user`, `feedback`, `project`, `reference` classent le contenu, pas sa durée. La durabilité déclarée à l'écriture est une estimation, pas une vérité connue. Un seuil d'âge peut déclencher une revue ; il ne suffit pas à conclure qu'une mémoire est devenue fausse. [D, P3, P5, question 5]

Distinguer au minimum date de création, dernière modification, dernier usage observé et dernière confirmation. Une lecture, un changement de ponctuation ou une consolidation ne valent pas confirmation. Une date récupérée dans Git doit conserver son sens de date historique, pas devenir implicitement une validation factuelle.

Avant T5, vérifier que les 28 préfixes correspondent réellement à 28 valeurs du champ `metadata.type`. Des noms de fichiers hétérogènes ne démontrent pas à eux seuls un schéma canonique invalide. Si T4 continue d'utiliser des seuils par type, la normalisation de ces types devient un préalable effectif, pas une tâche parallèle sans dépendance.

### I4 — Différer le score composite

Le score peut être reproductible tout en étant mal calibré. Ici, l'usage observé est incomplet et biaisé, la durabilité est déclarative et le sens de la taille n'est pas fixé. Pour un budget d'index, le dénominateur pertinent est le coût résident de la ligne, pas automatiquement la taille du corps. [D, P4, T6]

Commencer par un ordre déterministe simple : éléments protégés explicitement, état du projet actif, sélection de leçons validées pertinentes ; reste dans le catalogue complet. Introduire un score seulement s'il améliore des replays par rapport à cette référence.

Enfin, « extraire cinq insights » doit autoriser zéro résultat. Un nombre fixe de découvertes attendues contredit l'admission sélective ; ce risque est cohérent avec la croissance rapportée, sans que le document établisse un lien causal. [D, §1, §2.5]

## 5. Réponses aux six questions de revue

| Question | Réponse |
|---|---|
| 1. §2.4 est-il juste ? | Trop catégorique. Le constat de non-détection est recevable ; l'absence de tout canal ne l'est pas encore. Ajouter des canaris et une vérification de la visibilité des injections. |
| 2. L'index mérite-t-il 5 022 tokens à 11 % ? | Indécidable avec le taux d'ouverture. Comparer coûts et résultats sur les mêmes projets. Je privilégierais une petite orientation résidente avec consultation ciblée, à évaluer contre les alternatives. |
| 3. Les 94 % constituent-ils une liste de démotion ? | Un vivier de candidats, pas une preuve d'inutilité. Le bénéfice silencieux des titres n'est pas identifiable dans ces seuls logs ; le tester hors production par ablation. |
| 4. Un plafond de corpus est-il justifié ? | Les coûts de maintenance et de stockage peuvent le justifier, pas les tokens résidents. Borner d'abord résidence et travail de maintenance ; définir ensuite le sens du plafond froid et l'issue en cas de saturation. |
| 5. La durabilité est-elle le bon axe ? | Plus pertinente que le type pour estimer une durée, mais distincte du statut de validité et de la date de réexamen. Elle doit rester révisable. |
| 6. Le score composite vaut-il sa complexité ? | Pas encore. Une politique simple et testable doit servir de référence ; la formule n'est utile que si elle la dépasse. |

## 6. Programme et critères d'acceptation corrigés

| Lot | Révision recommandée | Critère de sortie |
|---|---|---|
| Provenance et instrumentation | Conserver le travail de couverture ; clarifier les populations et les dates. | Chaque corps vivant est couvert ; aucun champ temporel ne prétend confirmer ce qui n'a pas été vérifié ; jeux de tests de visibilité positifs et négatifs. |
| T1 | Promotion avec conservation des références et des exceptions. | Tous les anciens chemins supportés résolvent ; aucune redirection cyclique ; corps canonique unique pour une même leçon effectivement fusionnée. |
| T2 | Réconciliateur de références, pas seulement collecteur de fichiers. | Aucun corps vivant sans catalogue, aucun lien cassé non signalé ; les 12 références sans corps sont traitées ; mode rapport avant mutation. |
| T3 | Candidats lexicaux, sans quota « ~38 ». | Cas équivalents retrouvés, cas trompeurs rejetés, fusion toujours validée. |
| Nouveau lot A | Catalogue complet, index résident borné, consultation ciblée. | Budget en caractères effectif ; les tests retrouvent les souvenirs démotés ; interruption récupérable. |
| T5 puis T4 | Schéma réel, sens des dates, durabilité et déclencheurs de revue. | Toutes les entrées sont classifiables ; aucune ouverture ne rajeunit implicitement la vérité ; éligibilité recalculée sur un instantané et des seuils fixés. |
| Nouveau lot B | Non-régression de #875 et du nouvel index. | Comparaison avec mémoire figée, tâches vérifiables, coût de lecture et de maintenance inclus. |
| T6 | Différer, puis comparer à un ordre simple. | Gain mesuré sur les mêmes tâches et budgets ; pas seulement score calculable. |
| T7 | Séparer plafond actif, travail de maintenance et stockage froid. | Dépassement traité en nombre borné d'opérations ; admission différée ou refusée explicitement si nécessaire ; aucune boucle imposant une consolidation impossible. |

Les invariants doivent être vérifiés par le programme, pas seulement décrits dans `/dream`. Le modèle peut proposer une sélection ou une fusion ; les contrôles doivent rejeter une écriture incohérente. Le document doit préciser le traitement des écritures directes qui contourneraient la voie normale.

**Ordre de livraison recommandé :** cohérence et provenance → références et catalogue complet → budget résident → validité et revue → tests de bénéfice → optimisation et politique froide.

Le but n'est pas d'ajouter une formule sophistiquée à une mémoire toujours croissante. C'est de rendre chaque transition vérifiable : admission, rappel, promotion, révision, démotion et suppression éventuelle.

## Source

[D] `dragon-memory-design.md`, « The Dragon's memory: measured assessment and design proposal », draft du 10 septembre 2026, fourni avec la demande. Les renvois désignent ses sections, principes P1–P6 et tickets T0–T7. Aucun chiffre externe n'a été ajouté comme résultat établi.
