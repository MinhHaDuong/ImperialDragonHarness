# Caractérisation 0979 : reroutage silencieux de Pi quand la résolution provider/modèle échoue

2026-10-02, Pi 0.87.1 (installée) et 1.0.0 (installation temporaire hors
dépôt), `pi --print --mode json`. Suite de l'essai 0977
([2026-09-28-essai-pi-backends-souverains.md](2026-09-28-essai-pi-backends-souverains.md)) :
l'essai a observé un reroutage silencieux vers openrouter avec un
identifiant de modèle non vide et non résolvable sous `--provider ilaas` ; ce
document caractérise un déclencheur reproduit sur padme (voie `--model`
vide/absent) et retient la mitigation harnais. Le déclencheur de 0977 reste
non réconcilié (voir § Portée). Ticket
[tickets/0979-pi-reroute-sans-avertissement-vers-openr.erg](../tickets/0979-pi-reroute-sans-avertissement-vers-openr.erg).

## Méthode

Témoin positif d'abord (discipline `rules/workflow.md`) : padme devait servir
une requête avec `"provider":"padme"` visible en `--mode json` avant toute
conclusion négative. Constat de configuration : la déclaration padme créée par
l'essai 0977 dans `~/.pi/agent/models.json` avait disparu — la config vivante
ne contient plus que `~/.pi/agent/models-store.json` (simple cache catalogue,
clé racine `huggingface`) et un `settings.json` vide de fournisseurs ; aucun
backend souverain n'était résolvable. La déclaration padme a été reconstruite
hors dépôt dans `~/.pi/agent/models.json` (endpoint VPN de l'essai, clé
factice locale, `api: openai-completions`) avec l'identifiant réellement servi
`qwen3.8-27b`, vérifié résolvable via `GET /v1/models` avant tout test. Sans
cette reconstruction, le témoin positif ne pouvait pas partir.

Chaque variante a été lancée en `pi --print --mode json --no-session
--no-context-files` avec une invite courte ; le fournisseur lu est celui de
l'événement `turn_end` du flux JSONL (`turn_end.message.provider`), pas le
fournisseur demandé. Sont enregistrés : provider servi, message visible
(stderr ou flux json), code de sortie. Aucun identifiant d'authentification
n'apparaît ici ; la clé padme est factice et le repli observé s'est servi
d'un jeton déjà présent dans l'environnement de la machine.

## Témoin positif

`pi --print --mode json --provider padme --model qwen3.8-27b` (invite
arithmétique simple) → `turn_end.message.provider` = `"padme"`, model
`qwen3.8-27b`, réponse exacte servie, exit 0. **Le témoin part du feu** : le
contrôle `"provider"` en `--mode json` distingue bien le fournisseur réel du
fournisseur demandé.

## Tableau des déclencheurs (Pi 0.87.1)

| Variante | provider servi (`turn_end`, `--mode json`) | Visible ? | Exit |
|---|---|---|---|
| `--provider no-such-provider --model qwen3.8-27b` | aucun tour servi | oui — erreur explicite `Unknown provider "no-such-provider"` sur stderr | 1 |
| `--provider padme --model padme/no-such-model` | `"padme"`, id `no-such-model` passé tel quel | oui — avertissement stderr `Model "no-such-model" not found for provider "padme". Using custom model id.` | 0 |
| `--provider padme --model no-such-model` | `"padme"`, idem | oui — même avertissement stderr | 0 |
| `--provider padme --model ""` | **`"huggingface"`, model `moonshotai/Kimi-K2.6`** — reroutage silencieux, le `--provider` explicite est ignoré | **non — rien ni sur stderr ni dans le flux json** | 0 |
| `--provider padme` (sans `--model`) | **`"huggingface"`, model `moonshotai/Kimi-K2.6`** — même reroutage silencieux | **non** | 0 |

Mécanisme (source 0.87.1, `model-resolver.js`, `findInitialModel`) : la
priorité 1 teste `cliProvider && cliModel` — si l'identifiant de modèle est
vide ou absent, **la paire CLI entière est sautée, `--provider` compris**, et
Pi retombe sur la priorité « premier modèle disponible avec une clé valide ».
Aujourd'hui ce repli tombe sur huggingface (jeton présent dans
l'environnement). La destination du repli dépend donc des fournisseurs
authentifiés sur la machine — le danger n'est pas openrouter en particulier
mais n'importe quel fournisseur non souverain authentifié.

Le `--provider` explicite n'est ni une garde ni un simple indice dans le cas
vide : il n'est tout simplement pas lu. En revanche, un nom de fournisseur
inconnu **est** une garde (erreur visible, exit 1), et un identifiant de
modèle inconnu avec fournisseur explicite **reste** sur le fournisseur
demandé, avec un avertissement stderr — dans les variantes testées (padme,
une configuration machine), le reroutage inter-fournisseurs de 0.87.1 ne se
produit que par la voie vide/absente.

## Versions

- **0.87.1** (installée) : caractérisée ci-dessus. Le déclencheur
  reroutage-silencieux est la résolution vide/absente du modèle.
- **1.0.0** (testée en installation temporaire hors dépôt, préfixe npm sous
  `$TMPDIR` ; l'installation 0.87.1 n'a pas été touchée) : témoin positif
  padme passe ; la variante `--model ""` devient une erreur visible
  `Error: --provider requires --model`, exit 1 — ce déclencheur précis est
  corrigé en amont ; la variante modèle inconnu garde l'avertissement
  `Using custom model id` avec fournisseur préservé. La chaîne de repli
  « premier modèle avec clé valide » existe toujours dans la source amont
  (`model-resolver.ts`, priorité 4) au 2026-10-02 : la garde ne tient qu'à
  l'exigence du `--model`. Le comportement est signalé en amont :
  `earendil-works/pi#10236` (« `--provider <name>` does not restrict model
  resolution, silently running a different provider », ouvert le 2026-09-30,
  fermé), et les notes de version 1.0.0 indiquent : « Fixed `--provider`
  without `--model` being silently ignored and running the default model from
  another provider; it now fails with an error (#10236) ».

## Portée

Constat limité à ce qui a été testé : voie `--model` vide/absent, backend
padme, une configuration machine. L'essai 0977 (2026-09-28) a observé
`"provider":"openrouter"` avec un identifiant **non vide** non résolvable sous
`--provider ilaas` ; ce déclencheur reste **non réconcilié** avec le tableau
ci-dessus, où un identifiant non vide inconnu reste sur le fournisseur
demandé. ILaaS n'a pas été testé (clés en attente), et rien ne montre que le
`--model` de 0977 était vide : le déclencheur de 0977 n'est pas reproduit.
La règle d'assertion de fournisseur couvre les deux cas.

## Sévérité

Sur 0.87.1, une invocation destinée à un backend souverain peut voir son
contenu partir en silence vers un fournisseur non souverain : exit 0, réponse
normale à l'écran, aucun avertissement. C'est une égression (egress) de
contenu d'invite — potentiellement non défriché (uncleared) — hors du
périmètre souverain demandé, invisible sans la vérification `"provider"` en
`--mode json`. Le seul témoin fiable est le provider servi, jamais le
fournisseur demandé ni le code de sortie.

## Mitigation retenue

Règle documentée dans
[adapters/pi/README.md](../adapters/pi/README.md) : toute exécution Pi
ciblant un backend souverain doit vérifier que `"provider"` dans la sortie
`--mode json` égale le fournisseur demandé avant de faire confiance à la
réponse, et les identifiants déclarés dans la config Pi vivante doivent
rester résolvables. Aucun site d'appel `pi --print` n'existe aujourd'hui dans
le code du harnais (vérifié par grep lors du raid 2026-10-02) : la règle est
une garde documentée, pas un enrobé (wrapper).

La règle de résolvabilité est de l'hygiène ; c'est la règle d'assertion de
fournisseur qui garde contre le reroutage, quel qu'en soit le déclencheur.

Le contrôle de cohérence de `models.json` au healthcheck a été rejeté comme
mauvaise couche : `~/.pi/agent/models.json` est machine-local, hors du dépôt,
et le healthcheck vérifie des conventions de dépôt — il ne peut pas garantir
la résolvabilité d'une configuration qui ne vit pas dans ce qu'il audite.
La règle d'assertion de fournisseur, elle, s'applique à chaque exécution
réelle, quelle que soit l'état de la config.

## Changements hors dépôt

- `~/.pi/agent/models.json` : déclaration padme reconstruite pour la
  caractérisation (endpoint VPN de l'essai 0977, clé factice locale, id
  `qwen3.8-27b` vérifié résolvable). Aucune clé réelle n'y figure.
- Installation temporaire de Pi 1.0.0 sous `$TMPDIR`, supprimée après les
  tests ; l'installation 0.87.1 est inchangée.
