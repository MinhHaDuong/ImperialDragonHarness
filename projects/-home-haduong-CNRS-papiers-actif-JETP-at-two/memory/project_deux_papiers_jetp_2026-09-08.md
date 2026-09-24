---
name: project_deux_papiers_jetp_2026-09-08
description: "Structure et état des deux papiers JETP issus de la réunion du 8 septembre 2026 avec Christophe Cassen — numérotation, thèse, blocage ledger"
metadata: 
  node_type: memory
  type: project
  originSessionId: d0150b9b-532b-4fc4-854e-67338ee51348
  modified: 2026-09-10T16:58:02.455Z
---

La réunion du 2026-09-08 avec Christophe Cassen a reformulé le programme
JETP en une série numérotée : **papier 1** = hal-04412457 (janvier 2024,
rejeté deux fois, sert désormais de premier relevé ex ante) ; **papier 2**
= *JETP at four: pledges without an absorption test* (Ha-Duong & Cassen,
bilan d'étape, mécanisme « la solvabilité achète l'agentivité », comparatif
question par question sur 4 pays) ; **papier 3** = le registre JETP
(« ledger »), mesure fine et automatique sur documents primaires, pilote
Vietnam en cours dans `pilote-ledger-vn/`. Le CR complet, avec stratégie de
publication (classement à 7 revues, Development Policy Review en tête),
plan détaillé et proposition de répartition CRediT, est dans
`cr-reunion-2026-09-08-christophe.md`.

**Le papier 2 se scinde en deux soumissions**, décidé en séance sur une
règle conditionnelle : un papier court n'existe que si la courbe de
référence du décaissement (CRS, 4 pays) montre un écart net avec le JETP.
`courbe-reference-decaissement-2026-09-08.md` a tranché en sa faveur (37,3 %
de référence contre ≈ 9 % au Vietnam, facteur 5,3) — d'où **papier
court** (mesure/mécanisme macro, Minh premier auteur, cible Climate Policy,
7 000 mots, 33 j de décision vérifiés) **et papier long** (économie
politique comparée, cible Development Policy Review, Christophe porteur des
sections terrain/agentivité). Le long cite le court pour son annexe
comptable au lieu de la redémontrer — ~1 500 mots récupérés sur un format qui
étranglait sept sections comparatives.

**[MàJ 2026-09-10, fin de journée] JETP a changé d'adresse.** L'auteur a
décidé d'intégrer JETP comme strate de `climate-finance-het` plutôt que de
le laisser vivre en projet autonome (les deux mesurent de la finance climat
sur CRS ; infra de tirage CRS/IATI potentiellement partagée). Tracker
`tickets/0708` dans `~/CNRS/projets/actifs/climate-finance-het`, enfants
0709 (fait — les deux notes + le CR atterris dans `conception/`, PR #1319),
0710 (réconciliation pipeline CRS, décision d'architecture à prendre),
0711 (squelettes de livrables Quarto, bloqué par 0710), 0712 (migration
complète du reste du contenu). Le papier 1 (2024) et le dossier AFD-Sénégal
restent hors périmètre, dans `~/CNRS/projets/actifs/jetp/` — ancien
emplacement `~/CNRS/papiers/actif/JETP at two/` vidé par `mv` (pas `cp`,
correction à retenir : toujours `cp` pour un déplacement de dossier de
recherche tant que l'auteur n'a pas confirmé qu'il peut supprimer
lui-même l'original) et laissé tel quel, l'auteur le supprimera lui-même.
Notes à jour : `conception/reunions/jetp-cr-reunion-2026-09-08.md`,
`conception/jetp-papier-court-mesure.md`,
`conception/jetp-papier-long-economie-politique.md` (+ PDF pour les trois ;
montants en devise écrits "M USD"/"Md USD", jamais "M$" — le signe $ brut
casse le rendu pandoc/Quarto, cf. PR #1320).

**[MàJ 2026-09-10, fin de journée] Papier 1 rangé et vérifié.** Le dépôt
2024 (hal-04412457, ex `papier-1-2024/`) est maintenant dans
`~/CNRS/papiers/published/Reports/JETP at two/` — plus actif. Vérifié :
document de travail CIRED, indexé dans la série CIRED Working Papers sur
RePEc/IDEAS (collCode HAL inclut CIRED), `docType_s` HAL = UNDEFINED, pas de
numéro CIRED WP explicite trouvé (contrairement à hal-04094268 qui porte le
N° 2023-90). Non peer-reviewé (deux rejets : Energy Policy, Energy for
Sustainable Development). Pas encore sur la liste de publications
minh.haduong.com au 2026-09-10 — évoqué comme ajout possible, pas fait.
Statut détaillé dans `statut-2026-09-10.md` sur place.

**[Point de sauvegarde, fin de journée 2026-09-10 — reprendre ici demain]**

1. **Renumérotation à confirmer.** Le papier 1 (2024) étant maintenant classé
   et fermé, l'auteur numérote désormais **papier 1 = le papier court**
   (mesure/mécanisme) et **papier 2 = le papier long** (économie politique).
   Les notes/CR actuels utilisent encore « papier court »/« papier long »
   sans chiffre — à renommer si l'auteur confirme cette numérotation demain.
2. **Question ouverte, bloquante avant tout envoi à Christophe : cible du
   papier court.** *Climate Policy* (7 000 mots, ce qui est écrit
   actuellement, cohérent avec le classement à 7 revues terminé le 8/9) vs
   *Global Environmental Change* (4 000 mots, ce qui a été dit en direct en
   réunion — mais le classement complet a montré que le seul format court de
   GEC, une Perspective à 3 000 mots, exclut les papiers à description
   méthodologique, donc disqualifie potentiellement ce papier-ci). L'auteur
   doit trancher : suivre l'analyse complète (Climate Policy) ou revenir au
   choix énoncé en direct (GEC) contre l'avis de l'analyse.
3. **Le CR a été dégonflé** (PR climate-finance-het #1322, ouverte, PAS
   mergée) : il dupliquait presque tout le contenu des deux notes par papier,
   et mentionnait de l'organisation interne (tracker 0708, « ce dépôt »,
   climate-finance-het) jamais discutée en séance et sans signification pour
   Christophe — le CR est le document externe destiné à lui être envoyé,
   les notes de conception internes ne devraient jamais fuiter dedans.
   Leçon générale : vérifier tout document destiné à un tiers externe pour
   des références à l'outillage/l'organisation interne avant envoi.
4. **PDF non régénérés** depuis le dégonflage — à refaire une fois le point 2
   tranché (pandoc/xelatex, police DejaVu Serif, montants en "M USD"/"Md USD"
   jamais "M$").
5. Les 3 PDF (version encore ancienne/redondante) sont dans
   `~/CNRS/projets/actifs/jetp/pour-christophe-2026-09-10/` — À REGÉNÉRER
   avant envoi réel, ne pas envoyer tels quels.
6. Merger le PR #1322 seulement après le point 2 tranché et les PDF
   régénérés et recopiés dans ce dossier.

**Pourquoi :** cette numérotation et cette thèse ont été décidées en direct
pendant une séance de travail synchrone (le raisonnement a été inversé une
fois puis corrigé — la macro/solvabilité est le mécanisme premier, l'asymétrie
Nord-Sud entre bailleurs n'est que son explication, jamais l'inverse). Le
document « docs pour Christophe » promis en séance n'avait pas été rédigé
depuis quatre semaines au moment de cette note.

**Comment l'utiliser :** avant de reprendre ce dossier, vérifier que
`pilote-ledger-vn/feuille-arbitrage.md` a été ratifiée par l'auteur — elle
bloque le run 2 du ledger et l'arithmétique du bloc II du papier 2, et
n'était toujours pas ratifiée au 2026-09-10. Ne pas relancer les passes de
ciblage de revue ou de saturation bibliographique sans relire
`cible-revue-complement-2026-09-08.md` §5-7 et
`saturation-angle-absorption-2026-09-08.md` : les deux se déclarent
partiellement non vérifiées (accès bloqués, saturation non atteinte) et ne
doivent pas être citées comme définitives sans relance.

Voir aussi [[project_senegal_afd_tranche_670m]] : le volet AFD-Senelec avec
R. Blachier a été évoqué dans la même réunion comme « le meilleur article
caché » du dossier, mais mis de côté comme aside, et sa figure centrale
(670 M€) s'est révélée non vérifiée le lendemain.
