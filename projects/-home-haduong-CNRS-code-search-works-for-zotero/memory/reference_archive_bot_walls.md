---
name: archive-bot-walls
description: "Which public archives serve bytes to scripts and which answer with a challenge page (HAL Anubis, Gallica ALTCHA, UK Gov Web Archive WAF), measured 2026-09-02 while sourcing the fixture corpus"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 6d767542-7121-4b6a-b5bb-36be109cd846
  modified: 2026-09-02T09:26:06.005Z
---

Measured 2026-09-02 with curl and a browser user agent, sourcing the golden
fixture corpus (ticket 0029, PR #177):

- **Serve bytes to scripts**: Internet Archive (`archive.org/download/…`, plus
  `/metadata/<id>` for md5/sha1), Wikimedia Commons (`upload.wikimedia.org`),
  Wikisource (`action=raw&oldid=`), FAOLEX's PDF host `faolex.fao.org/docs/pdf/`
  (its portal `fao.org/faolex` is 403 to scripts), Zotero public library API.
- **Challenge page instead of bytes**: HAL (`hal.science/…/file/…`, Anubis
  proof-of-work, HTTP 200 with a challenge; the API `api.archives-ouvertes.fr`
  still answers metadata), Gallica (`ark:/…pdf` → 302 to ALTCHA; OAI/IIIF
  metadata endpoints still answer), UK Government Web Archive (`/ukgwa/…` → 405
  with a WAF captcha). Solving these is anti-bot circumvention and the permission
  classifier refuses it.

**How to apply:** for HAL/Gallica/UKGWA entries, record the identifier and a
`sha256_reason`, fetch once in a browser, hash, pin. Also: an rtk-rewritten
`sha256sum` echo dropped one hex character on 5 of 10 files in a subagent's run;
read hashes from a file, and length-check them. See [[verify-the-load-bearing-claim]].
