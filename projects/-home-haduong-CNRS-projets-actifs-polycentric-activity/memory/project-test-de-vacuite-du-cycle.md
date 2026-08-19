---
name: project-test-de-vacuite-du-cycle
description: "Sur quel graphe les cycles d'une source tournent réellement — tranche la réduction de l'appendice, mais plus le compte"
metadata: 
  node_type: memory
  type: project
  originSessionId: 1e742b5d-6433-44f8-b6a3-8dbb03a621ba
  modified: 2026-08-17T13:11:51.578Z
---

Pour toute source du dossier HET, établir **sur quel graphe ses arbitrages
tournent réellement**, avant de dire quoi que ce soit de sa condition de cycle.
Trois questions dans cet ordre : quels sont les arcs, et lesquels sont
réversibles ? les coûts sont-ils tous d'un signe sur le graphe des données ?
si oui, existe-t-il un graphe résiduel ou mixte sur lequel l'auteur fait
effectivement tourner ses arbitrages ?

**Why:** Enke 1951 tombe parce que dans du transport à un bien tous les coûts
d'arc sont positifs, donc aucun cycle n'est améliorant. Opposée à Cournot 1838
(2026-08-17), la même objection mord sur son graphe des bornes `γ` — des prix de
transport, positifs en logarithmes — et ne mord pas sur le graphe **mixte** du
§17, pp. 37-38, où l'arc de remise est réversible à taux réciproque
(`c_{i,k} = 1/c_{k,i}`) et fournit des coûts des deux signes, tandis que l'arc
d'expédition ne l'est pas. Cournot y compose une jambe de transport au
coût-limite avec une jambe de virement au taux intérieur.

**Ce que ce test tranche, et ce qu'il ne tranche plus.** Il tranche la décision
d'architecture de l'appendice (`app:dictionary`) : la réduction se fait sur le
graphe mixte, sinon elle avoue une trivialité qu'elle a elle-même fabriquée.
Il **ne porte pas le verdict de compte** — 0150 avait déjà déclassé la vacuité
en confirmation pour Enke, au motif qu'elle « se corrige dans la réduction », et
la reprendre comme raison rouvrirait ce qui a été tranché. Une première version
du dossier Cournot l'avait fait ; corrigé le 2026-08-17. La vacuité est
aujourd'hui un cas particulier de la première des trois hypothèses de
[[project-critere-du-compte-non-tranche]], pas un appui séparé.

**Corollaire de méthode, appris deux fois le même jour.** Un raccourci de
structure se vérifie sur un contre-exemple avant d'être écrit : « $r-1$ paires
actives, donc arbre couvrant » est faux en général — un triangle plus une arête
disjointe fait quatre arêtes sur cinq places, déconnecté. Ce qui rétablit
l'arbre est la généricité posée par l'auteur, au prix d'une analyse de cas sur
les orientations qu'il ne pose jamais. Voir
[[feedback-ocr-perd-les-equations-affichees]] pour l'instrument de lecture.
