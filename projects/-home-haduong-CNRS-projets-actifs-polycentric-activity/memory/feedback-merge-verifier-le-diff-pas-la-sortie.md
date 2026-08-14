---
name: feedback-merge-verifier-le-diff-pas-la-sortie
description: "Après un merge d'intégration, vérifier `git diff origin/main --stat` et exiger que seuls vos propres fichiers restent — la sortie du merge dit « clean » dans les deux cas"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d656551a-8f4e-4a1d-b7f0-2ea8536cf852
  modified: 2026-08-14T08:26:07.591Z
---

Après chaque `git merge origin/main` dans une branche, la vérification qui
attrape une base périmée est `git diff origin/main --stat` **en exigeant qu'il
ne reste que vos propres fichiers**. La sortie du merge ne sert à rien ici :
elle annonce « clean » aussi bien quand l'intégration est bonne que quand
`origin/main` a bougé entre votre `fetch` et votre `merge`.

**Why :** j'avais donné la règle « un auto-merge propre n'est pas une preuve,
grep-vérifiez les marqueurs des deux côtés » (vague multi-PR, 2026-08-14). Une
session parallèle l'a appliquée puis améliorée : elle a dû intégrer `main`
trois fois de suite parce qu'il rebougeait à chaque tour, et le tell n'a pas
été un conflit mais un **diff résiduel** — sa branche *retirait* `a4paper`
d'un manuscrit, ce qu'elle a d'abord pris pour une mauvaise résolution avant
de voir qu'un commit tiers était arrivé entre son fetch et son merge. Le grep
de marqueurs vérifie ce qu'on pense avoir touché ; le diff-stat révèle ce
qu'on n'a pas prévu de toucher, qui est justement le symptôme.

**How to apply :** après l'intégration, lancer `git diff origin/main --stat`.
Tout fichier qui n'est pas le vôtre est un signal, pas du bruit — soit
`origin/main` a bougé (re-fetch, re-merge), soit la résolution a dérapé. Ne
commiter qu'une fois la liste réduite à vos fichiers. Le grep de marqueurs
reste utile, il est complémentaire et non substituable. Voir
[[feedback-grep-context-audit]].
