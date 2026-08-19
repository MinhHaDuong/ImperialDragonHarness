---
name: feedback-bibcnrs-ezticket-pas-de-cookies-txt
description: "BibCNRS passe par une passerelle ezticket en JS : un cookies.txt rejoué par requests ne peut pas marcher, et les vrais cookies de session ne sont pas dans cookies.sqlite"
metadata:
  type: feedback
---

Pour acquérir un fulltext sous abonnement CNRS, `fetch_ezproxy.py` de
[[reference-doifetch]] attend `EZPROXY_BASE` + un `cookies.txt` Netscape. Sur
BibCNRS, cette voie **ne peut pas aboutir telle quelle**, pour deux raisons
indépendantes trouvées le 2026-08-19.

**1. Les cookies d'authentification ne sont pas dans `cookies.sqlite`.**
Un export depuis la base du profil Firefox ne rend que du traçage — `_ga`,
`datadome`, `OptanonConsent`, `_pk_id`, `_pxvid`. Aucun cookie de session.
Firefox les garde en mémoire ; ils sont recopiés dans
`<profil>/sessionstore-backups/recovery.jsonlz4` (format mozlz4 : magie
`mozLz40\0` puis bloc lz4, `lz4.block.decompress` le lit). C'est là que sont
`_shibsession_…` et `bibapi_token` sur `bib.cnrs.fr`, `__Host-shib_idp_session`
sur `janus.cnrs.fr`, et les cookies EZproxy sur `.<institut>.bib.cnrs.fr`.
Corollaire : l'institut de la session vivante se lit là, pas dans la base — la
session observée était sur **INEE**, pas INSHS comme le laissaient croire les
cookies persistants.

**2. Même avec les bons cookies, `requests` ne passe pas.** La passerelle
`bib.cnrs.fr/api/ezticket/login` est une SPA Tailwind : **zéro lien et zéro
formulaire rendus côté serveur**, le bouton « Connect with janus » est
construit par JavaScript. BibCNRS ne fait donc pas de l'EZproxy host-based
classique — il émet un ticket par session. Un client HTTP ne peut pas
traverser ce flux, quel que soit le cookie.

**Why:** le diagnostic naturel après un mur de login est « les cookies sont
mauvais / la session a expiré ». Ici c'était faux : la session était fraîche
(checkpoint à 11:41 le jour même) et les cookies étaient les bons. Le vrai
défaut est que le client ne sait pas exécuter le JS. Deux causes très
différentes, un seul symptôme — et la mauvaise conclusion envoie chercher des
identifiants au lieu d'un moteur de rendu.

**How to apply:** ne pas repartir sur `cookies.txt` + `requests` pour BibCNRS.
La route à essayer d'abord est un navigateur piloté (Playwright) alimenté par
les cookies récupérés dans `recovery.jsonlz4` : le JS s'exécute, le ticket se
crée, et `storage_state` se persiste ensuite. Piloter la connexion Janus
complète avec `JANUS_USERNAME`/`JANUS_PASSWORD` (présents dans
`~/.config/keys/janus.env`, qu'aucun code n'utilise — ils semblent là pour le
jeton ISTEX) est un second recours : le MFA n'a pas pu être établi, et l'échec
répété d'une authentification automatisée risque le blocage du compte
institutionnel. Une extension navigateur est la pire option malgré son
apparente simplicité : Firefox release impose la signature, donc un
side-load temporaire par `about:debugging` qui saute à chaque redémarrage.
