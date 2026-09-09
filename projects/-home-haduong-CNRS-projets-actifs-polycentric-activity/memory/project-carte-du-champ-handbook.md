---
name: project-carte-du-champ-handbook
description: "carte du Handbook HET (196 notices, 1613 renvois) — le bench v2 a rendu son verdict, note technique dans conception/"
metadata: 
  node_type: memory
  type: project
  originSessionId: 51594d4e-b4b5-4060-a112-a50aed5d0ece
  modified: 2026-08-20T17:42:23.567Z
---

La carte du *Handbook on the History of Economic Analysis* (196 notices,
1613 renvois, `conception/handbook-map.md`, pointeur `.knowledge.toml`) a été
mesurée deux fois en août 2026. Verdict v2 (60 questions stratifiées, deux
campagnes Sonnet/Opus, copie salée, six juges) — tout est dans
`conception/note-technique-bench-carte-het.md`, artefacts de rejeu dans
`docs/bench-carte-het/` (hors git, à préserver des purges EDM) :

- **Le corpus élève la note** (+4,3/60 chez Sonnet) ; **la carte n'ajoute
  rien à la note** par rapport aux PDF nus, et n'économise ni temps ni
  tokens de façon fiable.
- Ses acquis démontrés : la **provenance** (folios exacts) et la **détection
  d'absence** (dire qu'une notice n'existe pas — un grep ne le peut pas).
- **Décision pré-enregistrée appliquée : le New Palgrave ne sera pas
  cartographié.** Ne pas re-proposer.

Les chiffres v1 (20/20 avec la carte, 11,5/20 web…) sont invalides — le
questionnaire portait sur l'appareil du manuel et la carte servait de
corrigé. Ne plus les citer. Rejeu prévu avec Qwen 3.8 27B sur padme, mode
d'emploi dans la note. Voir [[feedback-benchmark-concurrent-maladroit]] et
[[feedback-copie-salee-etalonne-le-jury]].
