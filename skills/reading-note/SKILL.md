---
name: reading-note
description: "Academic reading note (note de lecture) from a DOI or citation, with Zotero RDF export."
---

For helper commands, set `IDH_ROOT="$(cd -P "$(dirname "<loaded-SKILL.md>")/../.." && pwd -P)"` in the same shell call. Replace `<loaded-SKILL.md>` with the absolute path the runtime supplied for this skill.

# Reading Note (Note de Lecture)

## Overview

Create comprehensive, structured reading notes from academic articles. The skill:
1. Fetches article metadata and PDF from DOI or citation
2. Extracts bibliographic information from the PDF first page
3. Generates structured critical analysis in markdown
4. Produces Zotero-compatible RDF export with embedded note

Reading notes serve dual purposes: (1) machine-processable data for computational analysis, and (2) human-readable verification and future reference.

## Workflow

### Step 1: Obtain Article Metadata

**Attempt automated fetch:**

Try multiple approaches in sequence:

1. **DOI.org resolution** (if DOI provided)
2. **Web search** for article landing page  
3. **Script-based fetch** (if network permits):
   ```bash
   python3 "$IDH_ROOT/skills/reading-note/scripts/fetch_article.py" "10.1234/example.doi"
   ```

**If all methods fail:**

Present to user what was attempted:
```
I attempted to fetch metadata for [DOI/citation] using:
1. DOI.org resolution - [result/error]
2. Web search for article page - [result/error]  
3. Crossref API query - [result/error]
4. Unpaywall OA lookup - [result/error]

I need your help to proceed. Please provide:
- Article title
- Author names
- Journal/venue, year, volume, issue, pages
- DOI and URL if available
- PDF file if you have it
```

Wait for user to provide information before proceeding.

**When metadata is obtained:**

Present extracted/provided metadata to user for verification before continuing to Step 2.

**Important:** If PDF is downloaded, read the first page to verify and extract accurate metadata. Do NOT trust PDF metadata fields—extract information by reading the actual first page content.

### Step 2: Read PDF First Page for Metadata Extraction

If PDF was fetched (or user uploaded PDF):

```bash
# Extract first page
python3 -c "
import sys
from pypdf import PdfReader
reader = PdfReader('article.pdf')
with open('first_page.txt', 'w') as f:
    f.write(reader.pages[0].extract_text())
"
```

Extract from first page text:
- Title (exact as published)
- Authors (full names, order preserved)  
- Journal/venue name
- Volume, issue, page numbers
- Publication year
- DOI (verify match)
- Abstract if present

**Critical:** Human verification of extracted metadata is required. Present extracted metadata to user for confirmation before proceeding.

### Step 3: Generate Reading Note Structure

Create markdown file following template structure. See `references/template_guide.md` for complete specification.

**Required sections:**
1. **YAML metadata block** - All bibliographic fields in machine-readable format
2. **Summary** (~300-500 words) - Research question, findings, methods, theory
3. **Critical Analysis** (~400-600 words) - Strengths, limitations, positioning, assumptions
4. **Research Relevance** (~200-300 words) - Connection to user's research agenda
5. **Key Quotations** (2-4) - Important passages with page numbers
6. **Future Writing Notes** - Citation planning ideas

**Template reference:** Load `references/template_guide.md` for detailed structure
**Example reference:** Load `references/examples.md` for good/bad examples

### Step 4: Write the Reading Note

**Document header format:**

Start every reading note with:
```markdown
# Reading note of: [Article Title]

**Processing datetime:** YYYY-MM-DD HH:MM:SS UTC  
**Agent:** Claude [model version]  
**Skill:** reading-note v1.0
```

**Writing principles:**

1. **Distinguish author claims from your analysis**
   - "The authors argue X" (their claim)
   - "This overlooks Y" (your analysis)

2. **Identify explicit AND implicit assumptions**
   - Explicit: What authors acknowledge as givens
   - Implicit: What's taken for granted without discussion
   - Naturalized: What appears technical but may be political

3. **Position in scholarly debates**
   - What conversation does this join?
   - Who does it agree/disagree with?
   - What gap does it address?

4. **Machine-processable structure**
   - Use consistent section headers (exactly as in template)
   - Complete YAML metadata block
   - Clear paragraph structure for topic modeling

5. **Quality targets**
   - Total length: 1000-1500 words
   - Should substitute for re-reading article
   - Actionable hooks for citation
   - Clear connection to user's research question

**Before finalizing, check:**
- [ ] All metadata fields complete
- [ ] Summary captures main argument in your own words  
- [ ] Critical analysis distinguishes explicit from implicit
- [ ] Research relevance connects to specific project
- [ ] Quotations include page numbers
- [ ] Author's claims separated from commentary

### Step 5: Generate Zotero Export

Create RDF file for import into Zotero:

```bash
python3 "$IDH_ROOT/skills/reading-note/scripts/generate_zotero_rdf.py" metadata.json reading_note.md output.rdf
```

The RDF file includes:
- Complete bibliographic metadata
- DOI and URL links
- Reading note embedded as Zotero note attachment
- Compatible with Zotero File → Import

**Deliver to user:**
1. Reading note markdown file
2. Zotero RDF file for import
3. PDF if fetched

## User Interaction Guidelines

### Initial Request Patterns

Recognize these trigger phrases:
- "Faire une note de lecture pour [DOI/citation]"
- "Create a reading note from [DOI]"
- "Analyze this article: [citation]"
- "I need to document [DOI] systematically"

### Metadata Verification Step

**Always present extracted metadata for user confirmation:**

```
I've extracted the following metadata from the article:

Title: [extracted title]
Authors: [extracted authors]
Journal: [extracted journal]
Year: [year], Volume: [vol], Issue: [iss], Pages: [pages]
DOI: [DOI]

Please verify this is correct before I proceed with the reading note.
```

Wait for user confirmation or corrections before continuing.

### Research Context Questions

After metadata confirmation, ask targeted questions to inform the critical analysis:

1. **Research question:** "What is your main research question that this article relates to?"
2. **Analytical axes:** "What are the key themes or analytical dimensions in your research?"
3. **Known controversies:** "Are there particular debates or controversies this article addresses?"
4. **Gaps of interest:** "What gaps in the literature are you particularly alert to?"

These answers inform Section 3 (Research Relevance) of the note.

### During Note Writing

For long articles or complex arguments:
- Show progress on major sections
- Highlight particularly important findings or quotations
- Note any sections that need user's domain expertise

### Final Delivery

Present:
1. Complete reading note (markdown)
2. Zotero RDF import file  
3. Summary of key takeaways
4. Suggestions for how this connects to user's research

## Technical Notes

### PDF Extraction
- Use `pypdf` for text extraction (already available)
- First page often contains all needed metadata
- Some PDFs may have poor OCR—flag if text extraction fails

### Crossref API
- No API key required for basic queries
- Rate limit: ~50 requests per second
- Include User-Agent header with contact email

### Unpaywall API  
- Requires email parameter
- Finds legally available open-access PDFs
- Not all articles will have OA versions

### Zotero RDF Format
- Based on RDF/XML standard
- Uses Dublin Core and Zotero namespaces
- Notes attached as `z:Attachment` with `z:note` content

## References

**Template structure:** `references/template_guide.md` - Complete specification of reading note format

**Examples:** `references/examples.md` - Good vs. poor examples with detailed annotations

## Scripts

**fetch_article.py** - Fetch metadata and PDF from DOI/citation
- Queries Crossref for metadata
- Attempts OA PDF download via Unpaywall/arXiv
- Outputs JSON with all bibliographic fields

**generate_zotero_rdf.py** - Create Zotero import file
- Combines metadata + reading note
- Generates RDF/XML format
- Ready for Zotero File → Import
