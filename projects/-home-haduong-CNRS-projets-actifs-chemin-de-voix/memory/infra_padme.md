---
name: Infra PADME
description: Chemins et accès SSH de la machine GPU PADME
type: reference
originSessionId: 06412290-2998-434a-8efa-7054c7857af7
---
- **Hostname** : `padme` (NetBird VPN — doit être actif)
- **Repo git** : `~/chemin-de-voix/` (cloné depuis GitHub MinhHaDuong/Tracing-Kieu)
- **Corpus/données** : `/data/projets/chemin-de-voix/corpus/` (partition /data séparée, volumineuse)
- **GPU** : A4000 16GB → QLoRA NF4 4-bit, bf16 LoRA préféré sur Qwen3.x
- **Accès** : `ssh padme <commande>` depuis doudou quand VPN up

Distinction importante : `/data/` = données volumineuses, `~/` = projets/code.
Ne jamais cloner un repo dans `/data/`.
