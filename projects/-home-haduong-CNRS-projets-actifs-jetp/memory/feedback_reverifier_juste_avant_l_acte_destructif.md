---
name: feedback_reverifier_juste_avant_l_acte_destructif
description: Une vérification d'identité faite plus tôt dans la session ne vaut plus au moment de renommer ou supprimer — refaire la comparaison dans le même souffle que l'acte.
metadata:
  type: feedback
---

Le 2026-09-11, en passant en `.bak` lecture seule 46 fichiers de `jetp/` jugés
redondants, j'en ai inclus un — `cr-reunion-2026-09-08-christophe.md` — sur la
foi d'une comparaison faite **au début de la session**. Entre-temps le fichier
avait grossi de 31,0 K à 35,3 K et portait du contenu absent de la copie
versionnée (la cible du papier court précisée en « Policy Analysis de moins de
5 000 mots »). Restauré en écriture, rien n'a été perdu.

Les 45 autres étaient sûrs : eux avaient été revérifiés octet pour octet
juste avant. Le seul fichier non couvert par la vérification fraîche est
exactement celui qui avait bougé.

**Pourquoi.** L'auteur fait tourner des sessions sœurs en parallèle sur les
mêmes fichiers. Un répertoire sans git n'a ni historique ni verrou : une
comparaison y est un instantané, pas un état. Et un fichier mis en lecture
seule sur un mauvais diagnostic ne proteste pas — la perte est silencieuse.

**Comment l'appliquer.** La vérification et l'acte destructif sont une seule
opération, pas deux étapes séparées par du travail. Si la liste est construite
à partir d'un ensemble vérifié, tout élément ajouté à la main hors de cet
ensemble doit être revérifié nommément. Et regarder la mtime : un horodatage
du jour sur un fichier censé être une copie dormante est le signal.

Voir [[project_jetp_strate_de_climate_finance_het]].
