---
name: project-critere-du-compte-non-tranche
description: "Le critère qui décide si une source compte comme découverte HET n'est pas tranché ; quatre critères en vigueur se divisent 3-1 sur Cournot"
metadata: 
  node_type: memory
  type: project
  originSessionId: 1e742b5d-6433-44f8-b6a3-8dbb03a621ba
  modified: 2026-08-17T13:12:09.154Z
---

Le manuscrit HET applique **quatre critères de compte qui ne coïncident pas**, et
la décision de savoir lequel gouverne n'est pas prise. C'est le verrou réel de la
lane, au-dessus du sort de chaque candidat pris isolément.

| Critère | Où | Verdict sur Cournot 1838 |
|---|---|---|
| Le théorème est l'équivalence, et il n'en énonce qu'un sens | §1, test formel | pas une découverte |
| Signature de reconnaissance : borne partout, égalité sur le support | l. 151-153 | découverte |
| Reconnaissance de l'instance, pas le lemme général | §2.1 l. 296-299, via MR #131 | découverte |
| Existence d'un optimum, ou certification d'un objet donné | MR #135 | découverte |

**Why:** au 2026-08-17 trois questions de compte sont en vol simultanément —
Cournot 1838 (ticket 0200), la strate EDF 1946-1965 (MR #130), le trio spatial
rétrogradé par le 0110. Les trancher séparément produit une suite de décisions
locales qu'un rapporteur pourra opposer les unes aux autres. Le décompte 3-1
ci-dessus est la démonstration : un seul cas, quatre critères en vigueur, trois
verdicts contre le quatrième — qui est celui que la recommandation gardait.

**How to apply:** fixer le critère d'abord, l'appliquer aux trois cas ensuite.
Pour tout nouveau candidat, appliquer le premier critère sous sa forme
explicative : le théorème est un **critère qui sépare des cas**, donc chercher si
les hypothèses écrites par la source suppriment les cas à séparer. Chez Cournot
elles le font sur trois sites — mécanisme de rappel (f. 31, l'existence ne peut
pas échouer), détermination des flux exigée (f. 40, « ce qui répugne »),
généricité des bornes (f. 39 et 41, la dégénérescence bannie). Cette forme passe
le §2.3 l. 451-453, qui récuse le raisonnement d'intention, là où un argument
tiré de ce que l'auteur « n'a en vue » y échoue.

**Contrôle à repasser avant d'adopter le discriminant de #135** : sa note le
passe sur huit lignes et n'en tue qu'une ; Cournot est une neuvième ligne et n'a
pas été testé — or il l'épargne, le chapitre III n'ayant aucun problème
d'optimisation. Voir [[project-test-de-vacuite-du-cycle]] pour la question du
graphe, qui est distincte et déjà tranchée.
