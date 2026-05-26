---
name: project-source-classification-scheme
description: "Project-wide Tier 1/2/3 source-classification scheme — four-oracle Tier-2 stack, default-exclude for Tier 3; canonical in verification_methods.tex §verif-filter"
metadata: 
  node_type: memory
  type: project
  originSessionId: 40d5468f-5250-4ab9-9f42-bc6c8d1fdb38
---

Project-wide source-classification scheme for any experiment that admits external sources to a verified bibliography. Ratified 2026-05-21 via design dialogue; canonical spec at `report/inputs/verification_methods.tex` §`sec:verif-filter`. STANAG 2511 / Admiralty antecedent cited in §`sec:verif-frontload`.

**Three tiers, ordered by epistemic role of the datum — not by publisher identity:**

- **Tier 1 — primary.** Publisher *is* the producer of the datum (gov.vn, chinhphu.vn, moit.gov.vn, EVN, PetroVietnam, operator press releases, IFI project docs: World Bank / ADB / IEA / UNDP). AUTO-OK, marked primary.
- **Tier 2 — secondary curated with editorial responsibility.** Four oracles in precedence: (1) `docs/pipeline.ods` (References + Power plants + Terminals sheets, Ha-Duong's curated VN coal+gas bibliography), (2) `data/rag_corpus/` (18 markdown extracts of PDP7/7A/8 annexes + EVN annual reports), (3) Zotero library (API, user ID 95318), (4) domain allowlist `{gem.wiki, enerdata.net}`. AUTO-OK, marked secondary-curated.
- **Tier 3 — tertiary or no editorial responsibility.** **DEFAULT-EXCLUDE**, not per-URL HITL. Operator promotes individual URLs by answering one question: "is this URL the source of record for the claim, or citing another source?" — most tertiary aggregators don't cite anything, making the answer trivial.

Same domain can publish at different tiers per URL (banktrack.org own research = Tier 1; banktrack.org policy brief aggregating GEM = Tier 3). Classification is per-URL, not per-domain.

Generic plant DBs (`worldpowerdata.com`, `database.earth`, `worldpowerplants.com`) explicitly held at Tier 3 until earned by promotion — "looks like a database" is not sufficient.

Fuzzy URL+title canonicalization across oracles: one verified-bibliography row per *document of record*, not per URL variant (normalize `en./www./m.` hosts, strip query/fragment, fuse PDF/HTML twins, fuzzy-match preprint/publication titles).

**Why:** Front-loaded source classification is the highest-leverage QC step (per `verification_methods.tex` §`sec:verif-frontload` — "le rendement épistémique de la vérification est inversement proportionnel au moment où elle intervient"). Default-exclude for Tier 3 reflects the empirical observation that most tertiary aggregators don't cite their sources, so the HITL promotion question collapses to "can you even check?" — answer is no.

**How to apply:** When designing source-admission logic for any experiment (Exp 3, Exp 4, RAG variants), use the canonical scheme; don't reinvent. The downstream 0–5 evidence rubric in `docs/quality-grounding.md` §2.2 measures per-cell credibility against the verified bibliography this filter produces — they're complementary, not duplicative. The 1D upstream filter (Tier 1/2/3) plus the 0–5 downstream rubric together cover the two axes of the Admiralty matrix (source reliability × information credibility).

Related: [[project-exp3-reconstruction-sweep]] (Exp 3 is the first experiment using this upstream filter; pipeline.ods committed to docs/ specifically as its first-precedence Tier-2 oracle).
