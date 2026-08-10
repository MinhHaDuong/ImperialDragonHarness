---
name: reference-nextcloud-tasks
description: "Accès CalDAV à la liste de tâches Nextcloud de l'auteur (serveur, compte, où est le secret, quelle liste)"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 4f38ce30-21e6-43a5-9b5b-36131219140c
  modified: 2026-08-10T18:53:40.649Z
---

Liste de tâches Nextcloud de l'auteur, accessible en CalDAV depuis doudou :

- Serveur : `https://nx11797.your-storageshare.de` (Hetzner Storage Share)
- Compte : `Admin` ; app-password dans le trousseau GNOME (schema
  `org.qt.keychain`, attribut
  `user=Admin_app-password:https://nx11797.your-storageshare.de/:0`,
  valeur encodée base64) — lisible via `secretstorage`, ne jamais l'afficher.
  **Deux items du trousseau matchent ce préfixe ; seul le premier est valide**
  (le second donne 401) — itérer et s'arrêter au premier qui s'authentifie,
  avec fallback `raw.decode()` si le base64 ne décode pas en UTF-8.
- Liste acceptant les VTODO : « Personnel » →
  `/remote.php/dav/calendars/Admin/personal/`
  (l'autre calendrier, anniversaires, n'accepte que VEVENT).
- Créer une tâche : PUT d'un VTODO sur
  `.../personal/<uuid>.ics` (HTTP 201). Vérifié 2026-08-10 (rappel
  « Envoyer les dossiers du livre », DUE 2026-09-01).
- Nextcloud n'émet pas de notification fiable sur les VALARM de VTODO ;
  pour un vrai rappel, doubler d'un email (msmtp configuré sur doudou,
  compte ouvaton, from minh@haduong.com) ou d'un cron.

CardDAV (mêmes identifiants) — carnets d'adresses :
- Actif : « Contacts » → `/remote.php/dav/addressbooks/users/Admin/contacts-propre/`
  (~1 850 fiches). Archive figée 2026-02 : `.../contacts/` (~2 100 fiches) — ne pas modifier.
- Recherche : REPORT `addressbook-query` avec `prop-filter name="FN"` ;
  création/fusion : PUT/DELETE de `.vcf` individuels. Vérifié 2026-08-10.
- Avant toute mutation de masse : backup intégral
  (`~/.local/state/carnet/*.vcf`, passe de dédoublonnage 2026-08-10).
