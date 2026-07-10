---
name: reference_paywalled_acquisition
description: "How to acquire paywalled fulltext for cited works — ISTEX, BibCNRS/EZproxy, Click&Read+Anna's Archive, DOIfetch; the cited-works gate"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 796836f2-caf1-4c02-8aa0-ad83e8baacbd
---

Closing the `docs/articles/` fulltext gap for paywalled cited works (2026-07-08).
The enforced gate is `tests/test_cited_works_available.py` +
`config/no-fulltext-allowlist.txt` (ticket 0197, PR #904): every `@cited` key
must have a `file=` or sit on the allowlist. See [[reference_bib_fulltext_index]].

**Acquisition ladder, cheapest first:**
1. **Unpaywall→curl** (OA) — [[reference_bib_fulltext_index]].
2. **ISTEX** (CNRS national licence, back-catalogue) — token in
   `~/.config/keys/istex.env` as `ISTEX_ACCESSTOKEN` (no export; `set -a; . file`).
   Ran via `~/CNRS/code/DOIfetch` `--source istex`; got 5 paywalled articles.
   ISTEX lacks recent (2023+) articles and JSTOR/figshare.
3. **Click&Read + Anna's Archive** (the practical route for the hard ones).

**BibCNRS/EZproxy findings** (the author uses INSHS institute):
- `EZPROXY_BASE = inshs.bib.cnrs.fr` (found in Firefox history:
  `www-<pub-with-dots-as-hyphens>-com.inshs.bib.cnrs.fr`). It IS EZproxy.
- Auth is federated SSO (Janus/RENATER) via `bib.cnrs.fr/api/ezticket/login`
  (plain username/password POST, no CSRF, no MFA field). Janus creds in
  `~/.config/keys/janus.env`.
- **Headless fetching largely fails**: the EZproxy session cookie is an
  in-memory session cookie Firefox doesn't persist to `cookies.sqlite`; and
  publishers bot-wall (JSTOR PerimeterX "Access Check", Elsevier Cloudflare
  "Security verification", Sage/Atypon "Please Return Soon"). Playwright with a
  real Chromium + exported cookies reaches the authenticated *article pages*
  (JSTOR included) but PDF extraction still hits per-publisher secondary gates.
- **What actually works**: human-in-the-loop. Open the DOIs in an HTML page in
  the author's Firefox; they click the Click&Read (CR) button (falls back to
  Anna's Archive); a `~/Downloads` watcher identifies each PDF by first-page
  title and files it. Got care_weber2023, dimaggio1983, shang_jin2023 this way.
  Beware: CR may serve the *Correction/erratum* (distinct DOI) — keep BOTH the
  article and its correction as separate records; verify DOI on first page.

- **UNFCCC decision PDFs are Incapsula-walled** (`unfccc.int/resource/docs/...`
  returns a ~212-byte challenge to curl). The **Wayback Machine** serves the real
  file: prefix the original URL with `https://web.archive.org/web/2id_/` (the
  `2id_` suffix returns the raw capture, no toolbar). Got decision 1/CP.21
  (`.../2015/cop21/eng/10a01.pdf`, the full FCCC/CP/2015/10/Add.1 with the
  §51 no-liability clause) this way, 2026-07-09. Verify doc symbol + a known
  paragraph on the pdftotext output before trusting it. Prior wins the same way:
  Cancún 1/CP.16 (`10a01.pdf` route), Biennial Assessment via reliefweb.
  Watch the round-number truncation trap (Wayback once cut a PDF at exactly 5 MiB).

**DOIfetch** (`~/CNRS/code/DOIfetch`, author's fork `MinhHaDuong/DOIfetch`,
upstream `hanhan6688/DoiHarvest` — push to the `fork` remote): fetcher convention
`fetch_pdf(doi,title,output_dir)->{status,file_name,...}`, sources in `SOURCES`/
`SOURCE_ORDER`. Added `fetch_ezproxy.py` (PR #5, headless — works only for
cooperative publishers). A parallel session added Zotero-dedup, SciDB/Anna's
Archive, and `--isbn`. Harness rule for the gate: ImperialDragonHarness PR #443.
