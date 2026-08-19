---
name: feedback-intervalle-liste-nest-pas-perimetre
description: "Un ticket qui liste un intervalle de fichier dans Relevant files n'en couvre pas le contenu ; le passage reste sans propriétaire et personne ne le signale"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 7d0b1352-9048-4e50-af9e-d5bf52c0ec61
  modified: 2026-08-17T13:40:02.706Z
---

Dans une épique découpée en enfants, deux questions différentes se confondent
facilement : **quel fichier un enfant touche-t-il**, et **quel passage son
périmètre couvre-t-il**. La première se lit dans `Relevant files`, la seconde
dans les `Actions` et les `Exit criteria`. Un passage peut tomber dans un
intervalle listé sans qu'aucun périmètre ne l'atteigne — il est alors sans
propriétaire, et rien ne le signale : l'épique le croit couvert parce que le
fichier est listé, et l'enfant ne l'écrit pas parce que ce n'est pas son objet.

**Why:** le 2026-08-17, l'enfant 0151 de l'épique HET listait `§3.1 l. 596-714`
et `l'introduction l. 78-113`. Deux affirmations d'unicité du §3.1 (l. 705-709 et
l. 710-713) et le crédit du `tab:pump` au §1 tombent dans ces intervalles. Mais
les cinq Actions, les six cases de vérification et les deux critères de sortie du
0151 portent tous sur le **statut** de la section — la réécrire en contexte et non
en découverte, le titre, le placement, la phrase de découpage du §2.1, la
pagination. Aucun ne touche les affirmations d'unicité ni le crédit du
dispositif. Le ticket 0220 a d'abord décrit cela comme « hors du rayon », ce qui
était faux ; la formulation juste est « sans propriétaire », et elle est à la fois
vérifiable ligne à ligne et plus utile, parce qu'elle dit quoi faire — rattacher
explicitement au périmètre de l'enfant plutôt que d'ouvrir un ticket concurrent.

**How to apply:** quand on veut établir qu'un passage n'est pris en charge par
personne, ne pas comparer au rayon d'explosion de l'épique ni à la liste des
fichiers. Lire les `Actions` et les `Exit criteria` de chaque enfant et chercher
lequel *produirait* le passage. Si un enfant liste le fichier sans que son
périmètre couvre le contenu, l'écrire ainsi — « raffine le périmètre de NNNN » —
et non « manque dans NNNN » : la première formulation survit à la lecture du
frère, la seconde non. Symétriquement, en rédigeant une épique, ne pas croire que
lister un intervalle suffit à en confier le contenu. Voir
[[feedback-affirmation-negative-sur-source]] et
[[feedback-grep-context-audit]].
