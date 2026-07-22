---
name: hal-sword-update-recipe
description: HAL SWORD new-version deposit — exact headers, dotted JEL form, per-document password leak trap
metadata:
  type: reference
---

Working recipe for depositing a new version of an existing HAL record via SWORD
(validated 2026-07-21 on hal-05558422 v2, online next morning):

- `PUT https://api.archives-ouvertes.fr/sword/<halId>` with the AOfr zip
  (meta.xml + PDF); credentials via chmod-600 `curl -K` config file.
- Headers: `Content-Type: application/zip`, `Packaging:
  http://purl.org/net/sword-types/AOfr`, and **`Content-Disposition:
  attachment; filename=meta.xml`** — the filename must be the XML inside the
  zip, not the zip name (400 "content-disposition mismatched" otherwise).
- **JEL codes use HAL's dotted form** (`B.B2.B20`, `Q.Q5.Q54`), not bare
  `B20` (400 "notInArray"). Recover the exact forms from the existing record:
  `search/hal/?q=halId_s:<id>&fl=jel_s`.
- The 201 response embeds a **per-document password in CDATA** —
  `<hal:password><![CDATA[...]]></hal:password>`. A mask matching
  `[^<]*` misses CDATA; strip `<hal:password>.*</hal:password>` non-greedy
  across the CDATA form BEFORE displaying any response.
- 201 = "stored in HAL workspace"; online status is CCSD moderation, checked
  via `search/hal/?q=halId_s:<id>` (returned = online) or email.
Related: [[reference_zotero]]; skill update-publist §2 has the base recipe.
