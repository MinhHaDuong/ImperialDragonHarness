# Reading Note Template

This template provides a structured format for creating reading notes that are both machine-processable and human-readable.

## Structure

### Document Header (Required)
```markdown
# Reading note of: [Article Title]

**Processing datetime:** YYYY-MM-DD HH:MM:SS UTC  
**Agent:** Claude [model version]  
**Skill:** reading-note v1.0
```

### Metadata Block (Required)
```yaml
---
title: "Full article title"
authors: "Author names"
year: YYYY
journal: "Journal name"
volume: "Volume number"
issue: "Issue number"
pages: "Page range"
doi: "DOI identifier"
url: "Canonical URL"
date_read: YYYY-MM-DD
reader: "Your name"
---
```

### Summary Section (Required)
**Purpose:** Provide factual overview of the work
**Length:** ~300-500 words
**Machine purpose:** Training data for summarization, topic modeling

Content to include:
1. **Research Question:** What problem or question does this address?
2. **Main Argument/Findings:** Core claims in 3-5 bullet points
3. **Methods and Data:** What evidence? What analytical approach?
4. **Theoretical Framework:** What concepts, theories, or frameworks are employed?

### Critical Analysis Section (Required)
**Purpose:** Engage critically with the work's contributions and limitations
**Length:** ~400-600 words
**Machine purpose:** Controversy mapping, gap analysis, literature positioning

Content to include:
1. **Strengths and Contributions:** What does this work do well?
2. **Limitations and Gaps:** What is missing, weak, or unexamined?
3. **Position in Debates:** How does this relate to other scholarship?
4. **Assumptions (Explicit & Implicit):** What is taken for granted?
5. **Naturalized Elements:** What appears technical but may be political/contingent?

### Research Relevance Section (Required)
**Purpose:** Connect to your own research agenda
**Length:** ~200-300 words
**Machine purpose:** Research question mapping, citation planning

Content to include:
1. **Connection to Your Question:** How does this inform your work?
2. **Analytical Axes:** Which of your research themes does this illuminate?
3. **Controversies Mapped:** What debates does this help you navigate?
4. **Literature Gaps:** What absences in existing work does this reveal?

### Key Quotations (Optional but Recommended)
**Purpose:** Preserve important formulations for potential citation
**Format:** 
```markdown
> "Exact quotation with page number" (p. XX)

**Context:** Brief explanation of why this quote matters
```

**Guidelines:**
- Select 2-4 quotations maximum
- Choose quotes that capture essential arguments or revealing formulations
- Include page numbers for citation purposes
- Brief context note for each quote

### Notes for Future Writing (Optional)
**Purpose:** Capture ideas for how to use this work in your writing
**Machine purpose:** Citation planning, argument structuring

Quick notes on:
- Where/how you might cite this work
- What arguments it could support
- Which sections of your work it informs

## Writing Guidelines
1. **Consistent structure:** Use exact section headers as shown
2. **YAML metadata:** Complete all fields in metadata block
3. **Clear attribution:** Distinguish author's claims from your analysis
4. **Explicit/implicit markers:** Tag assumptions clearly as explicit or implicit

### For Human Readability
1. **Write for an informed reader:** Not just yourself
2. **Be precise:** Avoid vague references
3. **Use active voice:** Make analysis clear and direct
4. **Connect to research question:** Maintain focus throughout

## Quality Checks

Before finalizing, verify:
- [ ] Document header with processing datetime and versions
- [ ] All metadata fields completed
- [ ] Summary captures main argument in your own words
- [ ] Critical analysis distinguishes explicit from implicit
- [ ] Research relevance connects to your specific project
- [ ] Quotations include page numbers
- [ ] Author's claims clearly separated from your commentary
- [ ] Total length: 1000-1500 words (excluding quotes)
