---
name: feedback-zotero-import-force-le-role-auteur
description: zotero-import écrit creatorType=author en dur ; un ouvrage dirigé demande un PATCH pour rétablir « editor »
metadata:
  type: feedback
---

`~/.claude/scripts/zotero-import.py` n'a pas de clé `editors` : `entry_to_zotero_item()`
passe chaque nom par `author_to_creator()`, qui fixe `creatorType: "author"` en dur.
Un ouvrage dirigé injecté tel quel arrive donc avec ses directeurs en auteurs,
sans que rien ne le signale — `--dry-run` le montre, l'API l'accepte.

Rétablir après l'injection, sur la clé rendue :

```bash
VER=$(curl -s -H "Zotero-API-Key: $KEY" ".../items/$ITEM" | jq -r .version)
curl -X PATCH -H "Zotero-API-Key: $KEY" -H "If-Unmodified-Since-Version: $VER" \
  -d '{"creators":[{"creatorType":"editor","firstName":"…","lastName":"…"}]}' ".../items/$ITEM"
```

**Pourquoi :** dans un Handbook, la distinction porte la citation — un chapitre se
cite à son auteur, le volume à ses directeurs. Confondre les deux fausse toute
référence au volume.

**Comment l'appliquer :** pour tout ouvrage dirigé, prévoir le PATCH dans la foulée
de l'`inject` et relire les `creators` par l'API avant de conclure. Vaut pour les
volumes II et IV du Handbook Faccarello-Kurz, encore à verser. Voir
[[project-zotero-injection-auto.md]] et [[reference-zotero-collection-polycentric]].
