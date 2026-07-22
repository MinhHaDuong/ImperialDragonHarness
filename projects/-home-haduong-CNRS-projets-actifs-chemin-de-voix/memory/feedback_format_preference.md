---
name: Format preference — demander avant d'optimiser
description: Ne pas sur-ingénier le format des données sans demander la préférence utilisateur
type: feedback
originSessionId: 06412290-2998-434a-8efa-7054c7857af7
---
Demander la préférence de format avant de proposer une "optimisation".

Dans cette session : corpus harvest proposé en JSONL (une ligne par doc, HF-ready),
puis revertí en txt individuels ("un texte par fichier") sur demande utilisateur.
Deux commits inutiles.

**Why:** L'utilisateur a une intuition claire sur la structure des données — un fichier par texte
est plus lisible, browsable, et tout aussi HF-compatible avec Dataset.from_list().

**How to apply:** Pour toute question de format de sortie (JSONL vs txt, un fichier vs plusieurs,
structure de répertoire), poser la question d'abord plutôt que de choisir et d'implémenter.
