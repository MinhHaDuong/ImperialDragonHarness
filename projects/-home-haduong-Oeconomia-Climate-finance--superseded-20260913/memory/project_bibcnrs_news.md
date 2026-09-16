---
name: bibCNRS provides news, not WoS/EconLit
description: bibCNRS exports come from Gale/Wanfang/NewsBank (news databases), not academic databases as documented
type: project
---

The bibCNRS exports (data/exports/bibcnrs_*.ris) come from Gale In Context, Wanfang (Chinese), Japanese Periodical Index, NewsBank, HAL, Cairn — NOT from WoS/EconLit/FRANCIS as previously stated. Zero abstracts in exports (portal doesn't include them in RIS/BibTeX).

**Why:** bibCNRS is an EBSCO EDS frontend. The databases it searches depend on CNRS subscription. Our title queries ("finance climat") match news articles more than journal papers in these databases.

**How to apply:** bibCNRS's value is non-English public discourse on climate finance, not academic literature. The data paper describes it as a "legacy portal" for "news & grey sources." No API access available — would need EBSCO EDS API key from INIST. OpenAlex covers the academic side.
