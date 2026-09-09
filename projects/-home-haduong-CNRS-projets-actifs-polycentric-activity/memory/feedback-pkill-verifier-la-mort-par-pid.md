---
name: pkill-verifier-la-mort-par-pid
description: "Un pkill peut ne rien tuer sans le dire ; vérifier la mort par PID avant tout test aval, sinon le diagnostic accuse un innocent"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e500d939-2872-4bb3-8c3e-dccff667c823
  modified: 2026-08-20T18:34:50.323Z
---

Sur padme (2026-08-20), `pkill -x llama-server` dans un one-liner ssh a laissé
vivant le llama-server qu'il visait (PID 16130, 25,7 Gio de VRAM). Les deux
lancements suivants ont échoué en OOM CUDA et le premier diagnostic a accusé
le flag `--tensor-split` — verdict caduc dès que le fantôme a été trouvé par
`nvidia-smi --query-compute-apps`. Cause du non-match `pkill -x` non isolée
(le nom de processus aurait dû matcher) ; l'observation suffit pour la règle.
Piège frère, lui isolé, même session : `pkill -f`/`pgrep -f` matche sa propre
ligne de commande — ici le *nom du fichier log* `~/llama-server.log` passé
dans la même commande ssh — et tue le shell porteur (exit 255 muet).

**Why:** `pkill` n'a pas de mode « confirme la mort » : exit 0 = signal
envoyé, pas cible morte ; et un test lancé sur un état supposé propre produit
des échecs qu'on impute au mauvais paramètre. C'est la famille « la sortie
muette n'est pas une preuve » ([[checkout-ref-ecrase-l-index]]).

**How to apply:** Après tout kill/pkill, vérifier la mort par PID (`kill -0`,
`pgrep -x`, ou pour un serveur GPU `nvidia-smi --query-compute-apps`) avant
d'enchaîner ; en cas d'échec aval inattendu, chercher d'abord le détenteur de
la ressource (port, VRAM) avant d'accuser un flag. Ne jamais mettre dans la
ligne de commande porteuse d'un `pkill -f` une chaîne qui matche le motif
(nom de log compris) ; préférer tuer par PID relevé.
