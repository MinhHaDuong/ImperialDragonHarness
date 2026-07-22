#!/usr/bin/env bash
# Selftest for probe-url.py — exercises the metadata parser on offline fixtures.
# No network, no install. Run: bash ./scripts/selftest.sh
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

python3 - "$HERE/probe-url.py" <<'PY'
import importlib.util
import sys

spec = importlib.util.spec_from_file_location("probe", sys.argv[1])
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

fails = 0


def check(label, cond):
    global fails
    print(f"  {'ok  ' if cond else 'FAIL'} {label}")
    fails += 0 if cond else 1


# 1. Highwire citation_* tags — multi-author, journal, DOI
html1 = """<html><head>
<meta name="citation_author" content="Doe, Jane">
<meta name="citation_author" content="Roe, Richard">
<meta name="citation_title" content="A Study of Things">
<meta name="citation_journal_title" content="Journal of Things">
<meta name="citation_publication_date" content="2025/03/01">
<meta name="citation_doi" content="10.1234/abc.2025.001">
<title>fallback</title></head><body>x</body></html>"""
d1 = m.parse_html(html1)
check("highwire: 2 authors", d1.get("authors") == ["Doe, Jane", "Roe, Richard"])
check("highwire: title preferred over <title>", d1.get("title") == "A Study of Things")
check("highwire: journal title", d1.get("publication") == "Journal of Things")
check("highwire: date", d1.get("date") == "2025/03/01")
ids1 = m.find_identifiers("", d1.get("doi_meta", ""))
check("highwire: doi", ids1.get("doi") == "10.1234/abc.2025.001")
check("type JOUR (doi + journal)", m.suggest_type("text/html", "x.org", d1, ids1) == "JOUR")

# 2. JSON-LD NewsArticle fills gaps
html2 = """<html><head>
<meta property="og:type" content="article">
<meta property="og:site_name" content="Carbon Brief">
<script type="application/ld+json">
{"@context":"https://schema.org","@graph":[
 {"@type":"NewsArticle","headline":"Big Climate News",
  "datePublished":"2024-11-24T17:12:02+00:00",
  "author":[{"@type":"Person","name":"Aruna Chandrasekhar"},{"name":"Daisy Dunne"}]}]}
</script></head><body>y</body></html>"""
d2 = m.parse_html(html2)
check("jsonld: headline title", d2.get("title") == "Big Climate News")
check("jsonld: datePublished", d2.get("date", "").startswith("2024-11-24"))
check("jsonld: 2 authors", d2.get("authors") == ["Aruna Chandrasekhar", "Daisy Dunne"])
check("type WEB (news article, no doi)", m.suggest_type("text/html", "carbonbrief.org", d2, {}) == "WEB")

# 3. bare DOI + arXiv in free text
ids3 = m.find_identifiers("see doi 10.21201/2025.000088 and arXiv: 2401.01234v2 here")
check("free-text doi", ids3.get("doi") == "10.21201/2025.000088")
check("free-text arxiv", ids3.get("arxiv") == "2401.01234v2")

# 4. PDF mime → RPRT
check("type RPRT (pdf)", m.suggest_type("application/pdf", "iea.org", {}, {}) == "RPRT")

# 5. slug is filesystem-safe
check("slugify safe", m.slugify("COP29: Key outcomes (Baku)!") == "cop29-key-outcomes-baku")

print()
if fails:
    print(f"SELFTEST FAILED ({fails})")
    sys.exit(1)
print("SELFTEST PASS")
PY
