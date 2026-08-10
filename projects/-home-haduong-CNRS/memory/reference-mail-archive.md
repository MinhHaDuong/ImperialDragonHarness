---
name: reference-mail-archive
description: "Archive email locale dans ~/.mail/ (mbox Thunderbird, ~22 Go) — lecture autorisée, READ ONLY strict"
metadata: 
  node_type: memory
  type: reference
  originSessionId: ceb24c88-cdf1-479e-986b-08d286b1acfc
  modified: 2026-07-28T14:53:25.104Z
---

L'archive email locale de l'auteur est `~/.mail/` : **Maildir** (un fichier
par message sous `Archives/cur/`, plus index Thunderbird `.msf`, `Junk`,
`Trash`), ~22 Go au 2026-07-28.

**Autorisation accordée (2026-07-28) : lecture seule.** Jamais d'écriture, de
déplacement ou de suppression dans ce répertoire — pas de `mv`, pas d'édition
d'index `.msf`. Fouiller au ripgrep : `/usr/bin/rg -a` (chemin explicite ou
`rtk proxy rg` — le hook rtk réécrit `rg` nu en GNU grep) ; extraire dates et
pièces jointes avec `python3` + `email.message_from_binary_file` sur le
fichier du message (vérifié 2026-07-28 : pièce jointe AEDIST retrouvée et
confirmée par SHA-256).

Usage type : retrouver la date exacte d'un envoi ou une pièce jointe
authentique pour les registres de releases sous `papiers/` (cf. l'épisode
AEDIST : la reconstruction « conf + 10 jours » était fausse de 9 jours, le
mail faisait foi).

Note : `~/.thunderbird` et des profils Evolution existent aussi, mais `~/.mail`
est l'archive de référence désignée par l'auteur.
