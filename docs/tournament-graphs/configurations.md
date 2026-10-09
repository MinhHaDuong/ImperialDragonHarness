# Identités des configurations testées

Identifiants déclarés et observés dans les manifests conservés des runs du tournoi (3–8 octobre 2026). Les alias API ne garantissent pas une version immuable du modèle hébergé.

| Série | Provider Pi | Identifiant de modèle |
|---|---|---|
| a | padme | `qwen3.8-27b` |
| b | padme-strata | `coder-iq1_m` |
| b2 | padme-strata | `qwen3.8-flash-next-iq3_s` |
| b3 | padme-strata | `qwen3.8-flash-next-q2_0` |
| c | padme-35b | `qwen3.6-35b-a3b` |
| c2 | padme-35b | `qwen3-coder-30b-a3b` |
| d | anthropic | `claude-opus-5-5` |
| d2 | anthropic | `claude-opus-5-5` |
| e | openai | `gpt-6-sol` |
| e2 | openai | `gpt-6.1-sol` |
| e3 | openai | `gpt-6.1-sol` |
| f | mistral | `zai-glm-5-3` |
| g | anthropic | `claude-sonnet-5-5` |
| i | deepseek | `deepseek-flash` |
| j | openrouter | `z-ai/glm-5.3-flash` |
| k | openrouter | `xiaomi/mimo-v2.6-flash` |
| l | openai | `gpt-6-luna` |
| mi | mistral ; openrouter | `mistral-large-4` ; `mistralai/mistral-large-4-0` |
| n | anthropic | `claude-haiku-5-5` |
| mr | mistral ; openrouter | `mistral-large-4` ; `mistralai/mistral-large-4-0` |

Les six séries locales sont Qwen 3.8 27B Q4_K_M (a), Flash-Next Coder IQ1_M pruned (b), Flash-Next IQ3_S (b2) et Q2_0 (b3), Qwen 3.6 35B-A3B UD-Q4_K_XL (c), Qwen 3 Coder 30B-A3B UD-Q4_K_XL (c2). Ces noms décrivent les configurations ; aucune empreinte des poids au moment du test n’a été conservée dans les manifests consultés.

Pi 1.0.4 était rapporté dans le relevé de session Mistral du 6 octobre ; sa version n’est pas enregistrée systématiquement par tentative. Certains runs récents enregistrent le build Strata : version 0.1.38, source `d844541998f4d168` (exemple : 0333-b2). Ces informations ne prouvent pas que tous les runs utilisaient ce build. Le commit llama.cpp n’est pas enregistré dans les manifests consultés.

Les efforts figurent dans le PDF. Pour Mistral, « off » désigne le réglage Pi : cela ne prouve pas l’absence de raisonnement interne côté API. Les séries « dernier succès » et « toutes tentatives » utilisent le même modèle et des périmètres comptables différents ; toutes deux incluent le succès OpenRouter du ticket 0874.

## Arm N — Haiku 5.5 (8 octobre 2026)

Provider Anthropic natif, effort `medium` explicite, Pi **1.1.0** (installation gérée). Dix tickets lancés en parallèle après autorisation explicite de dépasser le seuil d’admission de 5 USD ; aucun plafond monétaire de remplacement n’a été fixé. Plafond de 7 200 secondes par tentative.

Périmètre **toutes tentatives** : coûts et durées de toutes les tentatives candidates cumulés par ticket, y compris échecs et reprises. Les notes suivent le panel existant Gemini, Grok et MiniMax (somme sur 30). Aucun retry automatique des tickets ; au plus une reprise manuelle pour incident d’infrastructure, avec conservation des preuves. Les échecs du modèle restent notés 0/30.

Bilan observé : 10 tentatives, 0 reprises, 0 tickets échoués, 0 dépassements de délai. Coût candidat total : **1.2571 USD**. Le smoke (0.00028389 USD) et les juges (1.483838 USD) sont comptés séparément. Les tarifs Haiku sont appliqués par requête, cache inclus, avec multiplication par cinq au-delà de 100 000 tokens de prompt.

Table par ticket : [haiku55-results.csv](haiku55-results.csv). Audit des tentatives, tarifs, coûts et scores : [haiku55-accounting.json](haiku55-accounting.json). Les données des séries existantes sont inchangées ; les figures, PDF et comparaisons statistiques ont été régénérés avec N. Les comparaisons multiples passent de 120 à 136 par axe ; aucune ne passe Holm.
