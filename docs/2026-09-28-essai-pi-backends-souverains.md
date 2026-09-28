# Essai 0977 : Pi avec backends souverains (padme, Albert, ILaaS, HumaNum)

2026-09-28, doudou, Pi 0.87.1, `pi --print`. L'essai mesure, il ne câble rien
dans le harnais : seuls le ticket, ce rapport et `~/.pi/agent/models.json`
(changé, hors dépôt) portent des traces.

## Méthode

Témoin positif d'abord : padme (déjà configuré) passe le smoke test avant
toute conclusion ailleurs. Témoins négatifs : une clé volontairement fausse
doit produire une erreur visible, pas une réponse vide. Aucune clé réelle
n'existe encore pour Albert, ILaaS ni HumaNum dans `~/.config/keys/` ;
les raisons observées sont donc enregistrées telles quelles.

## Tableau par backend

| Backend | Endpoint | API | Modèles | Contexte | Tool-calling | Latence indicative | Conditions d'accès |
|---|---|---|---|---|---|---|---|
| padme | `http://100.93.160.120:8080/v1` (VPN NetBird ; repli LAN `192.168.0.131:8080` injoignable ce jour) | `openai-completions` | `qwen3.8-27b` servi, vérifié via `GET /v1/models` (completion + multimodal) | 131072 (config Pi) | **oui** — prouvé : lecture de `probe.txt` via l'outil `read`, contenu exact restitué | 14 s (invite simple), 4 s (appel d'outil) | serveur local, clé factice ; aucun accès à obtenir |
| Albert | `https://albert.api.etalab.gouv.fr/v1` | compatible OpenAI (`/v1/chat/completions`, `/v1/models`) | catalogue via `GET /v1/models` (utiliser le champ `id`, pas les alias — les identifiants changent sans préavis) ; `albert-large` déclaré en attendante | à vérifier avec la clé | non testé (pas de clé) ; la doc officielle indique que **Pi nécessite un proxy** (llm-proxy, J. Bousquié / O. Booklage, Licence Ouverte 2.0) pour que les tool calls fonctionnent | n/a | jeton via ProConnect (agents de la fonction publique d'État), `albert.api.etalab.gouv.fr` → `~/.config/keys/albert.env` — **étape auteur** |
| ILaaS | `https://llm.ilaas.fr/v1` | compatible OpenAI (`/models`, `/chat/completions`) | modèles des partenaires de la fédération, énumérables via `GET /v1/models` avec la clé | à vérifier avec la clé | non testé (pas de clé) | n/a | clé d'API demandée au consortium (« consommateur d'inférence ») → `~/.config/keys/ilaas.env` — **étape auteur** ; l'établissement porte la demande |
| HumaNum | aucun endpoint d'inférence LLM documenté | — | « services prêts à l'emploi » (transcription via compte ShareDocs) sur l'infrastructure GPU réservée (CC IN2P3) ; pas d'API consommable par Pi | — | non (pas d'API) | n/a | personnels des EPSC/EPST publics et doctorants, adresse académique requise ; accès par service, pas par API |

Le ticket nommait « LIaaS » ; le nom réel du service est **ILaaS**
(Inference LLM as a Service, ilaas.fr, fédération ESR soutenue par le MESRE).

## Témoins

- **Négatif, HTTP direct** : clé fausse → `401` visible sur Albert et ILaaS
  (`curl /v1/models`). Réponse d'erreur, pas de réponse vide.
- **Négatif, via Pi** : avec un identifiant de modèle résolvable,
  Albert renvoie `403 status code (no body)` et ILaaS `401 "Unauthorized"` —
  erreurs visibles en sortie de `pi --print`. Critère respecté.
- **Positif** : padme — invite simple `17*23` → `391` (14 s) ; tâche avec
  appel d'outil (lire `probe.txt`) → contenu exact `SMOKE-0977-pi-backends` (4 s).

## Observation Pi : reroutage silencieux vers openrouter

En tentant `pi --print --provider ilaas` alors que l'identifiant de modèle
fourni ne se résolvait pas, Pi a servi la requête via `openrouter/auto`
(vérifié en `--mode json` : `"provider":"openrouter"`) — **sans aucun
avertissement**, alors que la même requête avec un modèle résolvable
échoue proprement sur llm.ilaas.fr. Une défaillance d'authentification est
visible ; une défaillance de résolution ne l'est pas. Pour des sièges
souverains, c'est la panne dangereuse : l'invite part vers un backend
commercial non souverain pendant que l'écran affiche une réponse normale.
Recommandation : toujours vérifier `"provider"` en `--mode json` lors des
essais, et corriger coté configuration (identifiants de modèles toujours
résolvables). Suit ticket 0979.

## Changements hors dépôt

- `~/.pi/agent/models.json` : fournisseurs `albert` et `ilaas` déclarés
  (clés factices, commentaires pointant vers `~/.config/keys/*.env` et vers
  `GET /v1/models` pour les identifiants). Sauvegarde :
  `models.json.bak-20260928`.
- Rien dans le harnais. Aucune clé en clair dans le dépôt ni ce rapport.

## Recommandation (critère 5)

0540 (panel de relecture) est clos Stale ; la recommandation s'adresse au
ticket successeur éventuel :

1. **padme** : seul siège souverain immédiatement viable — prouvé avec
   appel d'outil, local, sans dépendance externe.
2. **Albert** : viable siège une fois le jeton ProConnect obtenu, à
   condition du proxy pour les tool calls (sinon siège en lecture simple) ;
   tester le tool-calling réel avant de le déclarer.
3. **ILaaS** : viable une fois la clé consortium obtenue ; tool-calling à
   tester (l'API l'implémente coté schéma, non observé).
4. **HumaNum** : pas un backend aujourd'hui ; ne pas déclarer.

Les étapes auteur restantes : jeton Albert via ProConnect, clé ILaaS via
l'établissement, puis remplacer les clés factices dans `models.json` et
énumérer les modèles via `GET /v1/models`.

## Addendum 2026-09-28 : activation d'Albert

Le jeton Albert est arrivé (ProConnect, `~/.config/keys/albert.env`). Mesures
d'activation, mêmes protocoles que l'essai :

- **Catalogue** : `GET /v1/models` avec la clé révèle 7 modèles de génération
  de texte + 1 OCR, tous open-weights servis par la DINUM. Ids vérifiés (champ
  `id`, pas les alias) : `gpt-oss-120b` (ctx 131072),
  `qwen3-coder-30b-a3b-instruct` (ctx 262144),
  `mistral-small-3-2-24b-instruct-2506` (ctx 128000, texte+image),
  `deepseek-v4-flash-0731` (ctx 131072), `gemma-4-31b-it` (ctx 262144,
  texte+image), `ministral-3-8b-instruct-2512` (ctx 262144),
  `lightonocr-2-1b` (OCR). Pas de « albert-large » : l'attendante d'origine
  était fausse, d'où la règle « vérifier via /v1/models ».
- **Déclaration** : 4 modèles déclarés dans `~/.pi/agent/models.json`
  (gpt-oss-120b, qwen3-coder, mistral-small-3.2, deepseek-v4-flash), clé
  collée depuis `~/.config/keys/albert.env`, sauvegarde
  `models.json.bak-20260928-albert`.
- **Smoke simple** (gpt-oss-120b) : `17*23` → `391`, **1 s**, fournisseur
  `albert` vérifié en `--mode json`.
- **Tool-calling, par modèle** :
  - `gpt-oss-120b` : **PASS** — appel `read` propre, toolResult exact
    (`ALBERT-ACTIVATION-0977`), réponse finale exacte, 2 s.
  - `qwen3-coder-30b-a3b-instruct` : **FAIL** — le modèle émet l'appel
    d'outil comme texte littéral (`<function=read>...`), aucun outil ne
    s'exécute. C'est exactement la panne que la doc officielle adresse avec
    le proxy llm-proxy ; le caveat est donc **par modèle**, pas global.
- **Conséquence sièges** : Albert est un siège souverain pleinement viable
  dès maintenant via `gpt-oss-120b` (le plus grand modèle général du
  catalogue). Pour les modèles qui émettent leurs appels en texte
  (qwen3-coder), passer par llm-proxy ou ne pas les déclarer sièges.
- **Incident à consigner** : le fichier de clé utilise un nom à traits
  d'union (`ALBERT-API-KEY`), non sourçable en shell ; une tentative de
  `source` a échoué et **a affiché la clé dans le journal d'une session
  d'agent**. Rotation recommandée après usage, et renommer la variable en
  `ALBERT_API_KEY`.
