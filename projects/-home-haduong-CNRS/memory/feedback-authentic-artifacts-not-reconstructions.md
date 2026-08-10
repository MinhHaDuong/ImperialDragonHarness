---
name: feedback-authentic-artifacts-not-reconstructions
description: "Ne jamais fabriquer un artefact ou une date plausibles — retrouver l'authentique (mail, HAL, page perso) et vérifier par hash ; mtime aveugle au travail épistolaire"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ceb24c88-cdf1-479e-986b-08d286b1acfc
  modified: 2026-07-28T15:40:01.489Z
---

Deux erreurs de même classe dans la session du 2026-07-28 :

1. Copié le build courant d'un dépôt comme « PDF envoyé en juin » — c'était
   la v2 de juillet (76 p. contre 65 envoyées). 2. Daté un envoi « conf + 10
   jours » — le mail réel (retrouvé dans [[reference-mail-archive]]) datait
   du 15 juin, pas du 6, et la pièce jointe a été confirmée par SHA-256.
   Aussi : importé un brouillon périmé de février par-dessus une version
   plus avancée déjà dans le dépôt, faute d'avoir cherché si le dépôt en
   avait une (corrigé par PR).

**Why:** un artefact reconstruit est indiscernable d'un authentique dans un
registre de provenance — il le corrompt silencieusement. Et le mtime d'un
dossier ne mesure pas l'activité d'un objectif dont le travail est
épistolaire ou administratif (VIETSE, attentes éditeur) : diagnostiquer
« dormant » sur mtime seul est faux.

**How to apply:** avant de classer un artefact « envoyé/déposé », le
retrouver à sa source (archive mail, HAL, `html/files/`) et comparer par
hash ; avant d'importer un fichier, vérifier si la destination en détient
une version plus récente ; avant de déclarer un chantier dormant, demander
à l'auteur si le travail passe par un canal invisible au disque. Avant tout
purge : vérification d'unicité par contenu (md5 contre le remote DVC — a
sauvé 292 fichiers du worktree t101, ticket 0650 de climate-finance-het).
