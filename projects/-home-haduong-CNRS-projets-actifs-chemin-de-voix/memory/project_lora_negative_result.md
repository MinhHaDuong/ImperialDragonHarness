---
name: project-lora-negative-result
description: LoRA Qwen3.5-9B échoue contre SOTA + persona — résultat à intégrer dans la coda
metadata: 
  node_type: memory
  type: project
  originSessionId: 207f5efc-4fd9-4bf1-b8ef-21487b529294
---

Sur les 14 voix × **1194 candidats** jugés par 3 LLM indépendants (Claude Sonnet 4.6, Gemini 2.5 Pro, GPT-5.4-mini) sur la rubrique 6 dimensions de GENERATION.md §3.2 :

- **LoRA Qwen3.5-9B : 0 médailles d'or sur 513 candidats × 6 dimensions** (= **3078 évaluations**). Score moyen **1.60/4**.
- **SOTA + persona en system message** (bench final v3, 9 modèles) :
  - **anthropic/claude-opus-4.6 : moy 3.10, Σ 78 ors** — le seul à dépasser 3.0, leader sur D3/D5/D6, co-leader D4
  - deepseek/deepseek-v4-pro : 2.99 (29 ors, D4)
  - anthropic/claude-opus-4.7 : 2.84 (22 ors) — plus verbeux et plus littéral que 4.6, perd côté creative
  - mistralai/mistral-large : 2.79 (38 ors) — champion D5+D6 (école française)
  - tencent/hy3-preview : 2.77 (9 ors) — leader D1 mais s'effondre ailleurs
  - openai/gpt-5.5 : 2.71 (27 ors) — spécialiste D4
  - openai/gpt-5 vanilla : 2.69 (20 ors)
  - openai/gpt-5.3-chat : 2.58 (9 ors)
  - deepseek/deepseek-chat V3 : 2.22 (4 ors) — autre échec notable
- Contrôle persona LoRA : `flag_persona ∈ {True, False}` testé via matrice GENERATION.md §2. Persona on vs off ne change rien : moy 1.60 dans les deux buckets. Pire, ~100 candidats persona-on éliminés au préfiltre vs 0 persona-off — le persona system message casse plus souvent la génération LoRA qu'il ne l'aide.

**Why:** L'hypothèse de départ du BRIEF §1 ("LoRA encode la voix-style") tombe sur le test des juges. Le projet final repose presque entièrement sur Opus 4.6 + Mistral-Large + DeepSeek V4-pro + injection LoRA forcée pour la diversité, pas sur l'effort LoRA propre. À assumer dans la coda BRIEF §8 (cf. principe d'honnêteté méthodologique §10).

**How to apply:** Quand la rédaction de la coda commencera, ouvrir `generations/coda-notes.md` qui contient le tableau complet, le contrôle persona, et une phrase candidate à reformuler littérairement. Ne pas réécrire l'analyse — c'est déjà fait et structuré. Le but est de transformer ce résultat scientifique négatif en matière éditoriale honnête (et possiblement en commentaire sur la nature de la voix : transmissibilité du style superficiel ≠ transmissibilité de la signature).

Related: [[feedback-judge-lineup]] (3-juge lineup et rationale), [[feedback-soft-cap-aggregation]] (règles d'agrégation), [[user_bio]] (auteur du projet).
