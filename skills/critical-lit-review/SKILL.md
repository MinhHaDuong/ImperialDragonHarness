---
name: critical-lit-review
description: "Critical literature review for history of economics and STS: scoping, consultation table, corpus analysis, report."
---

For helper commands, set `IDH_ROOT="$(cd -P "$(dirname "<loaded-SKILL.md>")/../.." && pwd -P)"` in the same shell call. Replace `<loaded-SKILL.md>` with the absolute path the runtime supplied for this skill.

# Critical Literature Review

Conduct rigorous critical literature reviews that map scholarly debates, institutional conflicts, and methodological controversies. Produce publication-ready technical reports, not descriptive surveys.

## Core Principle

A literature review constructs a **scientific object**, not just summarizes a theme. The review is analytical (identifies theoretical tensions, lacunae, naturalized assumptions) rather than descriptive (lists what has been written).

## Input Flexibility

Initialize with whatever you have:
- A research prompt or question
- A conference abstract or paper draft  
- Initial notes or brainstorming
- A paragraph describing the research idea
- Preliminary bibliography

## Output Portfolio

1. **Scoping document** - Delimited scientific object, corpus justification, analytical axes
2. **Consultation table** - Screening decisions for all sources encountered (300-1000+)
3. **PDF download script** - Parallelized script to download kept documents
4. **Reading notes** - Individual analyses for seminal/key articles (delegated to reading-notes skill)
5. **Corpus analysis table** - Annotations for computational analysis (100-200 kept sources)
6. **Corpus analysis report** - Computational methods confirming/illustrating key findings
7. **Annotated bibliography** - Thematic bibliography with all cited sources
8. **Technical review report** - Publication-ready structured analysis (8000-15000 words)

## Workflow Overview

1. **Object construction** - Define scientific object, period, exclusions
2. **Corpus building** - Web crawl with search engine scripts, consultation table
3. **Reading notes** - Delegate to reading-notes skill for deep analysis
4. **Actor mapping** - Identify scholars, institutions, positions
5. **Controversy analysis** - Map explicit debates and silent assumptions
6. **Corpus analysis** - Computational methods (clustering, topic modeling, network analysis)
7. **Technical report drafting** - Write analytical review with citations
8. **Bibliography compilation** - Extract all cited references, annotate
9. **Quality control** - Checklist verification

## Step 1: Object Construction

### 1.1 Initial Dialogue

Ask user to provide initial materials (prompt, abstract, notes, draft, bibliography).

### 1.2 Construct Scientific Object

**Guide user to define object as scientifically constructed, not just a theme:**

Questions to ask (max 3 per message):
- What is your research question? (seek "How was X constituted as Y by Z?" form)
- What period should be covered?
- Which institutional actors are central?
- What are the adjacent disciplines to include/exclude?

**Distinguish theme from object:**
- ✗ Theme: "climate finance" (too broad, vague)
- ✓ Object: "climate finance as an economic object constructed through OECD quantification practices, 1990-2025"

### 1.3 Formulate Single Guiding Question

Help user formulate ONE directorial question in form:
- "How was [concept] constituted as [object type] by [actors/practices]?"
- "What theoretical tensions structure debates over [measurement practice]?"
- "How do [institutional actors] naturalize [category] through [methods]?"

### 1.4 Explicit Delimitation

Create scoping document specifying:

**Included:**
- Time period with justification
- Main disciplinary field
- Adjacent relevant disciplines
- Central institutional actors

**Excluded (with justification):**
- Out of period (why this cut-off?)
- Out of field (which adjacent work is excluded and why?)
- Out of intellectual tradition (which approaches are excluded?)

**Analytical axes (3-5 maximum):**
- Economic categories mobilized
- Quantification and measurement tools
- Institutional roles of economists
- Methodological controversies
- Performative effects of numbers

Each axis must enable:
- Classification of corpus
- Comparison between authors
- Identification of tensions or ruptures

### 1.5 Deliver Scoping Document

Create document titled "Scoping Document: [Object Name]" containing:
- Scientific object definition
- Single guiding question
- Period and field delimitation
- Explicit inclusions and exclusions with justifications
- 3-5 analytical axes with rationale

## Step 2: Corpus Building with Search Engine Scripts

### 2.1 Search Engine Access Strategy

**IMPORTANT - Search engines require specialized access scripts:**

When Claude cannot directly access search engines, use prepared scripts in `scripts/` directory to:
- Query search engines programmatically
- Extract and structure results
- Ingest into consultation table

**Prepared search scripts:**
- `"$IDH_ROOT/skills/critical-lit-review/scripts/search_istex.py"` - French academic database (search.istex.fr)
- Not shipped yet (write ad hoc, or ask the user): HAL (hal.science), CNRS bibliography, Semantic Scholar API, Google Scholar (use carefully)

**When scripts not available for a specific search engine:**
- Kindly ask user to perform search manually
- Provide complete specifications: exact query, database, filters, what to extract
- Request results in structured format (CSV or JSON) for ingestion

**For user and colleagues' publications:**
- Use scripts to search user's name + institutional affiliations
- Identify frequent co-authors
- Search their publications
- Establish intellectual genealogy

### 2.2 Search Prioritization

**Run searches in this order:**

1. **French academic sources** (priority for French research contexts)
   - search.istex.fr via `search_istex.py`
   - hal.science via `search_hal.py`
   - bib.cnrs.fr via `search_cnrs_bib.py`

2. **International academic databases**
   - Semantic Scholar via `search_semantic_scholar.py`
   - Google Scholar via `search_google_scholar.py` (with rate limiting)

3. **AI deep research** (for broad exploration)
   - ChatGPT Deep Research mode
   - Perplexity with Academic source
   - SciSpace for academic papers

4. **User-specific**
   - Publications by user
   - Frequent collaborators
   - Institutional repositories

### 2.3 Query Formulation

For each search engine, prepare queries in format:

```
Primary query: [topic] [key concepts] [period if relevant]
Filters: 
  - Date range: [start year]-[end year]
  - Document types: articles, reports, books
  - Language: English, French [others as relevant]
  - Fields: title, abstract, keywords
```

**Example query:**
```
Primary: climate finance quantification OECD 1990-2025
Filters:
  - Date: 1990-2025
  - Types: @article, @report, @inproceedings
  - Languages: en, fr
  - Fields: title, abstract
```

### 2.4 Results Ingestion and Consultation Table

**For each search result, extract:**
- BibLaTeX category (@article, @book, @report, etc.)
- Authors (full list)
- Year
- Title
- DOI (if available)
- URL (prefer direct PDF link)
- Abstract
- Source (which search engine/database)

**Create Consultation Table as CSV:**

**Columns:**
- `source_id` - Unique identifier (auto-increment)
- `search_source` - Which database/engine found it
- `category` - BibLaTeX type
- `authors` - Full author list
- `year` - Publication year
- `title` - Full title
- `doi` - DOI if available
- `url` - Accessible URL
- `abstract` - Full abstract text
- `keep_in_corpus` - Decision (TRUE/FALSE/PENDING)
- `do_reading_note` - Decision (TRUE/FALSE)
- `justification` - Short rationale for decisions

**Note on scale:**
- **You can screen 300-1000+ sources** in consultation table
- Most will be EXCLUDE or FALSE for keep_in_corpus
- Typical funnel: 1000 screened → 200 kept → 20 reading notes

### 2.5 Web Crawl Iteration

For articles marked keep_in_corpus=TRUE:

1. **Expand via citations**
   - Extract cited-by and citing works (no script shipped; OpenAlex or Semantic Scholar APIs)
   - Add new candidates to consultation table
   
2. **Follow actors**
   - Identify key authors
   - Search their other publications
   - Track institutional affiliations

3. **Iterative screening**
   - Each new source added to consultation table
   - Make keep/exclude decision with justification
   - Update table continuously

### 2.6 Paywall Management

**When encountering paywalled content:**

- Mark in consultation table with note in `justification` field
- If article identified as critical for reading note:
  - Ask user to access via institutional login
  - Provide: authors, year, title, DOI, journal
  - Explain why critical (seminal work, key controversy, etc.)
- If only needed for corpus (not reading note):
  - Note paywall in table
  - Continue without requesting access
  - User can decide later if worth pursuing

### 2.7 AI Tool Quality Control

After AI-assisted search, verify:
- ✓ Check claims in original sources (AI can misinterpret)
- ✓ Look for missing seminal works (AI biased to recent/popular)
- ✓ Verify citations exist (AI can hallucinate)
- ✓ Cross-check user/colleagues' publications

### 2.8 Stopping Rule

**Corpus building complete when:**
- Seminal papers identified (those everyone cites)
- Recent contributions covered (last 2-3 years)
- Key methodological documents included
- All major institutional positions represented
- Main theoretical traditions covered
- User/colleagues' relevant work identified

**Typical scale:**
- Consultation table: 300-1000+ sources screened
- Keep in corpus: 100-200 sources
- Reading notes needed: 15-25 sources

### 2.9 Deliver Outputs from Step 2

**Output 1: Consultation Table**
- Filename: `consultation_table_[topic]_[date].csv`
- All screened sources with decisions
- Sort by: keep_in_corpus (TRUE first), then year (desc), then authors

**Output 2: PDF Download Script**
- `download_pdfs.py` reads consultation table
- Downloads all where keep_in_corpus=TRUE
- Parallelized with retry logic
- See `"$IDH_ROOT/skills/critical-lit-review/scripts/download_pdfs.py"` template

**Output 3: Search Logs**
- `search_logs_[date].txt` documenting:
  - Which engines queried
  - Query strings used
  - Number of results per source
  - Any errors or limitations encountered


## Step 3: Reading Notes (Delegated)

### 3.1 Identify Articles for Deep Analysis

From consultation table, select where `do_reading_note=TRUE`:
- Seminal papers (foundational, widely cited)
- Direct precedents (closest to research question)
- Methodological exemplars
- Representatives of major controversy positions
- User's key publications if relevant

**Typical selection:** 15-25 articles maximum

### 3.2 Delegate to Reading Notes Skill

**IMPORTANT:** Do not write reading notes directly. Instead:

1. **Trigger reading-notes skill** for each selected article
2. **Provide to skill:**
   - Full citation
   - PDF file or accessible link
   - Context: which analytical axis, which controversy, why this matters
   
3. **Reading notes skill produces:**
   - Structured note (summary + critical analysis + relevance)
   - Standard format (1-2 pages)
   - See reading-notes skill documentation

### 3.3 Collect and Organize Reading Notes

Store all reading notes from skill in organized directory:
- `reading_notes/[AuthorYear]_[ShortTitle].md`

These feed into:
- Step 4 (Actor Mapping) - identifying key scholars and positions
- Step 5 (Controversy Analysis) - mapping debates and tensions
- Step 7 (Technical Report) - citations and specific arguments

## Step 4: Actor Mapping

### 4.1 Identify Recurrent Actors from Corpus

**From consultation table and reading notes, extract:**

**Scholars:**
- Names appearing frequently (≥3 publications in corpus)
- Institutional affiliations and changes over time
- Career trajectories (student → professor → policy advisor)
- Funding sources where visible

**Institutions:**
- Organizations producing knowledge (OECD, World Bank, universities)
- Academic journals (which publish what perspectives?)
- Research centers and laboratories
- Professional associations and networks

### 4.2 Classify Actor Roles

For each major actor, assign role(s):

**Category producers:**
- Who invented key concepts? (e.g., "climate finance," "additionality")
- In what institutional context?
- What legitimated their authority to define?

**Normalizers:**
- Who standardized measurement practices?
- What guidelines/frameworks did they create?
- How did informal practices become official methodologies?

**Critics:**
- Who challenges mainstream frameworks?
- From what theoretical/institutional positions?
- What alternative categories do they propose?

### 4.3 Identify Coalitions and Networks

**Map implicit alliances through:**
- Citation patterns (who cites whom positively/critically?)
- Co-authorship networks
- Institutional collaborations (which organizations work together?)
- Shared theoretical commitments (efficiency vs justice framings)
- Conference participation (who appears on same panels?)

**Create network visualization if useful:**
- Nodes = scholars/institutions
- Edges = citations, co-authorship, institutional ties
- Clustering reveals coalitions

### 4.4 Actor Positioning Framework

For 10-15 key actors, create detailed profiles:

**Institutional trajectory:**
- Current position and institution
- Previous affiliations
- Movement between academia/policy/advocacy

**Theoretical orientation:**
- Disciplinary home (economics, political science, STS)
- Frameworks employed (welfare economics, political economy, etc.)
- Methodological preferences (quantitative, qualitative, mixed)
- Normative commitments (explicit or implicit)

**Position in debates:**
- Defender of existing practices or critic?
- Methodology developer or external evaluator?
- How have positions evolved over time?

### 4.5 Deliver Actor Mapping Report

Create document: "Actor Mapping: [Object Name]"

**Contents:**
- Table of major actors with roles (category producers, normalizers, critics)
- Institutional genealogy (which organizations shaped the field when)
- Network visualization if created
- 10-15 detailed actor profiles
- Coalition analysis (which groups align around what positions)

## Step 5: Controversy Analysis

### 5.1 Explicit Controversies

From corpus and reading notes, identify open debates:

**Methodological controversies:**
- Which measurement approaches are contested?
- What alternative methods are proposed?
- What evidence is marshaled by each side?
- Who are the protagonists in each debate?

**Empirical disputes:**
- Which numbers/data are questioned?
- What alternative counts or measurements exist?
- How are discrepancies explained by different actors?

**Theoretical tensions:**
- Efficiency vs justice framings
- Technical vs political characterizations
- Market failure vs structural critique
- Optimal policy vs power redistribution

### 5.2 Silent Controversies (CRITICAL)

Identify what is NOT openly debated:

**Unquestioned choices:**
- What assumptions go undiscussed?
- Which alternatives are never considered?
- What is framed as "technical" rather than political?

**Naturalized categories:**
- What is presented as self-evident?
- Which concepts are used without definition?
- What historical contingency is obscured?

**Absences and silences:**
- Which perspectives are missing from the literature?
- Which actors are systematically not cited?
- What questions are not being asked?

**Consensus that might be problematic:**
- What do all sides agree on that shouldn't be taken for granted?
- Which "settled" questions might need reopening?

### 5.3 Underlying Political-Institutional Dynamics

For each controversy (explicit or silent), analyze:

**Interests served:**
- Whose interests are advanced by different positions?
- What institutional mandates shape arguments?
- Who benefits from particular framings or definitions?

**Power asymmetries:**
- Which actors have more authority to define categories?
- How do power relations structure what counts as legitimate knowledge?
- What gives some definitions more force than others?

**Stakes beyond the technical:**
- What political, economic, or institutional stakes underlie technical disputes?
- How do definitional choices affect resource flows?
- What would change if alternative framings prevailed?

### 5.4 Historiographical Positioning

Situate the literature in broader intellectual traditions:

**History of quantification** (Desrosières, Porter, Espeland):
- How do measurement practices constitute the objects they claim to measure?
- What social processes underlie "technical" choices?

**STS and performativity** (MacKenzie, Callon, Latour):
- How do economic representations shape economic realities?
- What is the agency of calculation devices and accounting frameworks?

**Disciplinary histories:**
- Which lineages from environmental economics inform current debates?
- How do climate/development economics frameworks differ from predecessors?
- What theoretical innovations or path dependencies are visible?

### 5.5 Identify Lacunae (Your Contribution)

Determine what is genuinely missing from the literature:

**Types of potential lacunae:**
- Institutional blind spot (actor or process not analyzed)
- Absence of historical perspective (treating recent as natural/inevitable)
- Missing comparative dimension (assuming universality of local patterns)
- Category/instrument confusion (conflating representation with object)
- Methodological gap (certain methods not applied to this domain)

**Verify lacuna is:**
- Real (actually absent, not just dispersed across literature)
- Documentable (you can fill it with available evidence/methods)
- Publishable (journals/audiences would find it significant)
- Tractable (achievable within scope of this project)

### 5.6 Deliver Controversy Analysis Report

Create document: "Controversy Analysis: [Object Name]"

**Contents:**
- Mapping of 3-5 explicit controversies with protagonists
- Analysis of 2-3 silent controversies (naturalized assumptions, absences)
- Political-institutional dynamics underlying key debates
- Historiographical positioning (which intellectual traditions relevant)
- Statement of identified lacuna with justification


## Step 6: Corpus Analysis with Computational Methods

### 6.1 Purpose and Scope

**Goal:** Use computational methods to confirm, illustrate, or discover patterns that support findings from actor mapping and controversy analysis.

**Not a replacement for qualitative analysis** - computational methods complement and validate interpretive work, they don't substitute for it.

### 6.2 Dialogue with User Before Analysis

**CRITICAL:** Do not launch heavy computational analysis without user consultation.

**Present options to user:**

"Based on your corpus of [N] documents, I can apply computational methods to confirm or illustrate key findings. Here are possible approaches:

**What I can do (within Claude's environment):**
- Text vectorization and clustering (identify thematic groups)
- Topic modeling (discover latent topics across corpus)
- Keyword extraction and frequency analysis (track concept evolution)
- Citation network analysis (map intellectual influence patterns)
- Temporal analysis (how do themes/actors evolve over time)
- Controversy detection (identify documents with opposing positions)

**What you can do (with specialized tools):**
- Large-scale network analysis (Gephi, NetworkX for 500+ nodes)
- Advanced NLP (fine-tuned transformers, domain-specific models)
- Bibliometric analysis (VOSviewer, Bibliometrix)
- Qualitative coding (MAXQDA, NVivo with AI assistance)

**Questions before proceeding:**
- Which findings from actor/controversy analysis should we validate computationally?
- Do you have preferences for methods?
- Do you want lightweight exploration or comprehensive analysis?
- Should we focus on specific analytical axes or scan broadly?"

### 6.3 Formal Corpus Aggregation

Before analysis, ensure corpus is properly prepared:

**Step 6.3.1: Verify File Availability**
- Check all PDFs where `keep_in_corpus=TRUE` are downloaded
- Note any missing files (paywall, broken links)
- Decide if missing files are critical or can be excluded

**Step 6.3.2: Extract Contents to Machine-Readable Format**
- Extract full text from all PDFs (no script shipped; pdftotext)
- Handle errors (password-protected, image-only PDFs)
- Store extracted text in structured format

**Step 6.3.3: Create Corpus Analysis Table**

**Decision: Use SEPARATE table from Consultation Table**

Rationale:
- Consultation table = screening phase (300-1000+ sources, lightweight)
- Corpus analysis table = kept corpus only (100-200 sources, rich annotations)

**Corpus Analysis Table columns:**
- `source_id` - Links to consultation table
- `category` - BibLaTeX type
- `authors` - Author list
- `year` - Publication year
- `title` - Full title
- `doi` - DOI
- `url` - URL
- `file_path` - Path to downloaded PDF
- `extracted_text_path` - Path to extracted text file
- `word_count` - Number of words in document
- `abstract` - Abstract text
- `actor_codes` - Coded actor roles (producer/normalizer/critic)
- `controversy_codes` - Which controversies this addresses
- `analytical_axis` - Which axes (1-5) this informs
- `vector_embedding` - Serialized embedding vector (if computed)
- `cluster_assignment` - Cluster ID from clustering (if run)
- `topic_distribution` - Topic probabilities (if topic modeling run)
- `notes` - Any qualitative annotations

### 6.4 Computational Methods Library

Based on user preference, apply selected methods:

#### 6.4.1 Vectorization and Clustering

**Purpose:** Identify thematic groups; validate that "coalitions" cluster together

**Method:**
```python
# Vectorize using sentence transformers
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')

# Create embeddings from abstracts or full text
embeddings = model.encode(texts)

# Cluster using K-means or hierarchical clustering
from sklearn.cluster import KMeans
clusters = KMeans(n_clusters=5).fit(embeddings)

# Validate: Do OECD publications cluster separately from civil society?
```

**Output:**
- Cluster assignments added to corpus analysis table
- Visualization (2D projection via UMAP/t-SNE)
- Interpretation: What does each cluster represent thematically?

#### 6.4.2 Topic Modeling

**Purpose:** Discover latent topics; track topic evolution over time

**Method:**
```python
# Use BERTopic for coherent topics
from bertopic import BERTopic
topic_model = BERTopic()
topics, probs = topic_model.fit_transform(texts)

# Examine top words per topic
# Analyze topic distribution by year, by institution
```

**Output:**
- Topic labels and representative words
- Topic prevalence over time
- Topic distribution by institutional affiliation
- Added to corpus analysis table

#### 6.4.3 Keyword and Concept Evolution

**Purpose:** Track when concepts emerge, stabilize, or fade

**Method:**
```python
# Extract keywords by year
# Track frequency of terms like "additionality," "mobilization," "climate finance"
# Identify when concepts first appear and how usage evolves

# Can use bag-of-words or more sophisticated (TF-IDF, KeyBERT)
```

**Output:**
- Timeline plots showing concept frequency
- Co-occurrence networks (which concepts appear together)
- First mentions and stabilization periods

#### 6.4.4 Citation Network Analysis

**Purpose:** Map intellectual influence; identify central works and periphery

**Method:**
```python
# Build citation graph from corpus
# Nodes = documents, edges = citations
# Calculate centrality metrics (degree, betweenness, PageRank)
# Identify communities (groups of mutually-citing works)
```

**Output:**
- Network visualization with communities highlighted
- Central works (most cited within corpus)
- Bridge documents (connecting different communities)
- Validation: Do identified "coalitions" form distinct communities?

#### 6.4.5 Temporal Analysis

**Purpose:** Show how debates evolve; when controversies emerge

**Method:**
```python
# Analyze corpus by time periods (e.g., 5-year bins)
# Track:
#   - Which authors publish when
#   - Topic prevalence shifts
#   - Keyword usage changes
#   - Citation pattern evolution
```

**Output:**
- Timeline showing field evolution
- Period characterizations (e.g., "1990-2000: category formation," "2010-2020: measurement controversies")
- Validation of historical periodization from qualitative analysis

#### 6.4.6 Controversy Detection

**Purpose:** Identify documents with opposing positions on same topic

**Method:**
```python
# For documents discussing same topic, analyze:
#   - Sentiment towards key concepts
#   - Which other documents they cite positively/negatively
#   - Vocabulary differences (efficiency vs justice language)
```

**Output:**
- Pairs or groups of documents representing opposing positions
- Validation: Confirm controversy structure from Step 5
- Potential: Discover controversies not identified qualitatively

### 6.5 Annotation Workflow

**Decide with user how to annotate corpus:**

**Option A: Lightweight annotation**
- Use consultation table justifications
- Code documents into 3-5 analytical axes
- Mark actor roles and controversy positions manually (10-20 key docs)

**Option B: Comprehensive annotation**
- Create detailed coding scheme
- Code all kept documents (100-200)
- Include: actor roles, controversy positions, theoretical frameworks, methods used
- Store in corpus analysis table

**Option C: Hybrid (recommended)**
- Comprehensive coding for reading note documents (15-25)
- Lightweight coding for rest of kept corpus (100-200)
- Use computational methods to propagate patterns from coded subset

### 6.6 Integration with Qualitative Findings

**For each computational analysis, ask:**

1. **Does this confirm qualitative findings?**
   - Example: Do OECD documents cluster together as expected?
   - Example: Does topic model reveal the theoretical tensions we identified?

2. **Does this illustrate patterns more clearly?**
   - Example: Citation network shows visually how coalitions form
   - Example: Timeline makes concept evolution concrete

3. **Does this reveal unexpected patterns?**
   - Example: Clustering shows a group we didn't identify qualitatively
   - Example: Topic model finds latent theme we missed

**Any surprises or contradictions warrant deeper investigation**

### 6.7 Deliver Corpus Analysis Report

Create document: "Corpus Analysis: [Object Name]"

**Contents:**

**1. Corpus Statistics**
- N documents in corpus analysis table
- Distribution by year, category, institutional affiliation
- Coverage assessment (are all major actors/positions represented?)

**2. Methods Applied**
- Which computational methods used and why
- Parameters and decisions made
- Validation steps taken

**3. Findings for Each Method**
- Results (clusters, topics, network structure, etc.)
- Interpretation relative to qualitative findings
- Confirmation, illustration, or surprise

**4. Key Figures and Tables**
- Cluster visualization with interpretation
- Topic evolution over time
- Citation network with communities
- Keyword frequency timelines
- Any other relevant visualizations

**5. Integration with Qualitative Analysis**
- How computational findings support actor mapping
- How they validate controversy analysis
- Any discrepancies or unexpected patterns
- What was learned that wouldn't be visible qualitatively

**6. Recommendations for Technical Report**
- Which figures/tables should be included in final report (Step 7)
- How to present computational findings alongside qualitative
- What statistical claims can be made confidently

### 6.8 Data Outputs

Provide user with:

**1. Corpus Analysis Table**
- Filename: `corpus_analysis_[topic]_[date].csv`
- All kept documents with annotations and computed features

**2. Extracted Texts**
- Directory: `extracted_texts/` with one .txt file per document
- Filename convention: `[source_id]_[AuthorYear].txt`

**3. Computational Results**
- Embeddings matrix (if computed): `embeddings_[date].npy`
- Cluster assignments: in corpus analysis table
- Topic model output: `topic_model_[date].pkl` (serialized model)
- Network graph: `citation_network.gexf` (for Gephi) or `.graphml`

**4. Analysis Scripts**
- All Python scripts used for analysis
- Documented and reproducible
- User can modify and re-run if needed


## Step 7: Technical Review Report

### 7.1 Purpose and Scope

**Output:** Publication-ready technical report (8000-15000 words)

**NOT venue-specific:** Write comprehensive technical report. User will adapt/project to specific venues later (journal articles, conference papers, book chapters).

**Includes:**
- Full citations in-text
- Complete bibliography (all cited sources)
- Figures and tables from corpus analysis (Step 6)
- Comprehensive analytical narrative

### 7.2 Structure Template

**Recommended structure for technical report:**

**1. Introduction (10-15%)**
- Scientific object and guiding question
- Why this matters: theoretical and empirical stakes
- Contribution: what lacuna this fills
- Scope: period, field, exclusions
- Structure overview

**2. Institutional Genealogy (15-20%)**
- Which actors constitute this domain and when?
- How did key categories emerge historically?
- What organizational frameworks structure the field?
- Who has authority to define and why?
- **Cite specific documents, name specific actors**

**3. Measurement Practices and Methodologies (15-20%)**
- What quantification/measurement practices are employed?
- How are concepts operationalized into metrics?
- What controversies exist over methods?
- How do different actors measure differently?
- **Cite methodological documents, provide examples**

**4. Theoretical Tensions and Explicit Controversies (20-25%)**
- Map 3-5 major explicit debates
- For each: protagonists, positions, evidence marshaled
- Theoretical divides (efficiency vs justice, technical vs political)
- Empirical disputes (which numbers, what counts)
- **Name scholars, cite their arguments, show positions**

**5. Silent Controversies and Naturalized Assumptions (15-20%)**
- What is presented as self-evident but is actually contingent?
- What questions are not being asked?
- Which perspectives are systematically absent?
- What consensus might be problematic?
- **Use corpus analysis to show patterns of absence**

**6. Computational Validation and Illustration (10-15%)**
- Present key findings from corpus analysis (Step 6)
- **Include figures/tables recommended in Step 6 report**
- Show how computational methods confirm qualitative findings
- Highlight any unexpected patterns discovered
- Interpret quantitative patterns in theoretical context

**7. Historiographical Positioning and Contribution (10%)**
- How does this literature relate to broader intellectual traditions?
- What theoretical frameworks are most relevant?
- What performative effects do current framings have?
- What is the identified lacuna and why does it matter?

**8. Conclusion (5%)**
- Synthesis of key findings
- Research agenda implications
- Methodological contributions
- Theoretical implications

### 7.3 Writing Principles

**Analytical throughout:**
- ✗ "Author X argues Y" (mere description)
- ✓ "Author X's argument naturalizes Z by framing it as W" (analysis)

**Citations mandatory:**
- Every specific claim must be cited
- Format: (Author Year) or (Author Year: page) for specific points
- Track all citations for bibliography extraction (Step 8)

**Evidence-based:**
- Specific examples, not generalizations
- Quote sparingly (prefer paraphrase with citation)
- When quantitative claims, provide numbers
- When pattern claims, reference corpus analysis findings

**Theoretically sophisticated:**
- Use concepts precisely
- Situate in intellectual traditions
- Show theoretical implications of empirical findings

**Figures and tables from Step 6:**
- Include key visualizations that support narrative
- Caption fully (title, explanation, source/method)
- Reference in text at relevant points
- Typical: 3-6 figures, 2-4 tables

### 7.4 Citation Tracking

**CRITICAL:** Track every citation as you write

Maintain working bibliography file `working_bibliography.bib` (BibTeX format):
- Add entry for every source cited in report
- Include complete metadata (authors, year, title, venue, DOI/URL)
- Use standard BibTeX keys: AuthorYear or Author1Author2Year

**All cited sources MUST appear in Step 8 bibliography**

### 7.5 Figures and Tables to Include

**From Step 6 corpus analysis report, select for inclusion:**

**Typical figure set (3-6 figures):**
- F1: Corpus timeline (publications by year, by actor type)
- F2: Citation network with communities highlighted
- F3: Cluster visualization (thematic groups)
- F4: Keyword/concept evolution over time
- F5: Topic distribution by institutional affiliation
- F6: [Other relevant from Step 6]

**Typical table set (2-4 tables):**
- T1: Corpus statistics (N documents by category, year, institution)
- T2: Key actors and roles (producteurs/normalizers/critics)
- T3: Major controversies with protagonists
- T4: Topic model top words per topic (if relevant)

**Note in Step 6 report which figures/tables to make for Step 7**

### 7.6 Iterative Writing Process

**Draft in sections:**
- Write Introduction and Conclusion last
- Start with sections 2-5 (substantive analysis)
- Add section 6 (computational findings) once Step 6 complete
- Revise for coherence and flow

**Internal consistency:**
- Analytical axes from Step 1 should structure analysis
- Controversies from Step 5 should be clearly presented
- Actor mapping from Step 4 should be integrated
- Computational findings from Step 6 should validate claims

### 7.7 Deliver Technical Report

Create document: "Technical Review Report: [Object Name]"

**Format options:**
- Markdown with BibTeX references
- LaTeX source (for academic formatting)
- DOCX with citations (Zotero/Mendeley compatible)

**Length:** 8000-15000 words (excluding bibliography)

**Includes:**
- All sections per structure template
- In-text citations throughout
- Figures and tables integrated at relevant points
- Working bibliography file for Step 8 extraction

## Step 8: Annotated Bibliography Compilation

### 8.1 Extract All Cited References

**Source: All citations from Step 7 technical report**

**Process:**
1. Extract complete list of cited sources from working_bibliography.bib
2. Verify each entry has complete metadata
3. Ensure every entry has DOI or accessible URL (2026 standard)
4. Cross-check: are there citations in report not in working bibliography?

**Do NOT include:**
- Sources in consultation table but not cited in report
- Sources in corpus analysis table but not cited in report
- Only sources actually cited in technical report

**Typical size:** 80-150 sources (subset of 100-200 kept in corpus)

### 8.2 Thematic Organization

**Organize bibliography to reveal intellectual structure:**

**Recommended sections (adapt to specific domain):**

1. **Foundational Policy Documents**
   - Agreements, pledges, official commitments
   - UN, OECD, World Bank landmark documents

2. **Official Methodologies and Guidelines**
   - OECD-DAC guidelines
   - Measurement frameworks
   - Reporting standards

3. **Institutional Reports and Analysis**
   - IO-produced research and data
   - Official assessments and reviews

4. **Civil Society Counter-Accounting**
   - Advocacy organization reports
   - Alternative measurements and critiques
   - Monitoring and watchdog publications

5. **Academic Political Economy Literature**
   - Critical scholarly analysis
   - Political economy frameworks
   - Justice and equity perspectives

6. **Academic Economics Literature**
   - Mainstream economic analysis
   - Welfare economics approaches
   - Cost-benefit and efficiency studies

7. **Specific Controversy Analyses**
   - Studies of additionality, mobilization, accounting disputes
   - Empirical validation or critique of methods

8. **Theoretical and Methodological**
   - STS and performativity literature
   - History of quantification
   - Relevant theory from other domains

9. **Historical and Comparative**
   - Historical development of field
   - Comparative analyses across countries/regions

10. **Data Sources and Datasets**
    - Primary data sources
    - Databases and repositories

### 8.3 Entry Format

For each cited source:

**Full citation (BibTeX format exported to readable style):**
```
Author(s) (Year). Title. Venue. Volume(Issue): Pages. DOI/URL
```

**Annotation (2-4 sentences):**
- What does this contribute to the literature/debates?
- What position does it take in controversies (if relevant)?
- Why is it cited in this review?
- Key concepts, methods, or findings

**Example:**
```
Weikmans, R., Roberts, J. T., Baum, J., Bustos, M. C., & Durand, A. (2017). 
Assessing the credibility of how climate adaptation aid projects are categorised. 
Development in Practice, 27(4), 458-471. 
https://doi.org/10.1080/09614524.2017.1307325

Empirical analysis questioning reliability of OECD-DAC Rio markers for 
adaptation finance. Finds significant inter-coder disagreement and potential 
for inflated reporting. Represents academic critique from political economy 
perspective, challenging technical-neutrality framing of official accounting.
```

### 8.4 Quality Standards

**Completeness:**
- Every source cited in Step 7 report included
- No cited sources missing from bibliography
- All metadata complete (authors, year, title, venue, pages)

**Accessibility (2026 standard):**
- Every entry MUST have DOI or accessible URL
- Prefer DOI when available
- For reports: link to official organization website
- For working papers: link to institutional repository
- For books: link to publisher or WorldCat
- Test all links to verify they work

**Annotations:**
- 2-4 sentences per entry
- Explains contribution and position
- Connects to debates mapped in report
- Substantive, not generic

### 8.5 Deliver Annotated Bibliography

Create document: "Annotated Bibliography: [Object Name]"

**Format:**
- Markdown or LaTeX with clear section headers
- Alphabetical by first author within each thematic section
- Numbered entries for easy reference

**Metadata:**
- Total number of sources
- Distribution by category (articles, books, reports, etc.)
- Distribution by section
- Note any missing DOIs/URLs with explanation

## Step 9: Quality Control Checklist

Before finalizing, systematically verify:

### 9.1 Object Construction
- ☐ Scientific object clearly constructed (not vague theme)
- ☐ Single guiding question formulated and maintained throughout
- ☐ Period explicitly delimited with justification
- ☐ Exclusions explicitly justified

### 9.2 Corpus Quality
- ☐ Consultation table complete (300-1000+ sources screened)
- ☐ Corpus analysis table complete (100-200 kept sources)
- ☐ Seminal papers identified and included
- ☐ Most recent contributions (last 2-3 years) covered
- ☐ User/colleagues' relevant publications identified
- ☐ All major institutional positions represented
- ☐ French sources explored (istex, hal, CNRS) if relevant

### 9.3 Reading Notes (Delegated)
- ☐ 15-25 articles selected for deep analysis
- ☐ Reading notes skill successfully used
- ☐ Notes cover seminal works and key positions
- ☐ Notes inform actor mapping and controversy analysis

### 9.4 Analytical Rigor
- ☐ Review is analytical throughout (not descriptive)
- ☐ Theoretical tensions made explicit
- ☐ Silent controversies identified (naturalized assumptions, absences)
- ☐ Historiographical positioning clear
- ☐ Lacuna identified and justified

### 9.5 Actor Mapping
- ☐ 10-15 key actors profiled with institutional affiliations
- ☐ Roles distinguished (producers/normalizers/critics)
- ☐ Coalitions and networks identified
- ☐ Citation patterns analyzed
- ☐ Positions in debates clearly mapped

### 9.6 Corpus Analysis
- ☐ Dialogue with user completed before heavy analysis
- ☐ Corpus formally aggregated (files verified, text extracted)
- ☐ Corpus analysis table created with annotations
- ☐ Computational methods selected and applied
- ☐ Findings integrated with qualitative analysis
- ☐ Figures and tables produced for technical report
- ☐ Corpus analysis report delivered

### 9.7 Technical Report
- ☐ Follows structure template (8 sections)
- ☐ 8000-15000 words (excluding bibliography)
- ☐ All claims cited with specific sources
- ☐ Figures from Step 6 integrated (3-6 figures)
- ☐ Tables from Step 6 integrated (2-4 tables)
- ☐ Analytical throughout (not descriptive)
- ☐ Working bibliography tracked during writing

### 9.8 Bibliography
- ☐ All sources cited in Step 7 included
- ☐ No cited sources missing
- ☐ Every entry has DOI or accessible URL
- ☐ Annotations explain contributions (2-4 sentences each)
- ☐ Thematic organization (10 sections)
- ☐ Typically 80-150 sources
- ☐ All links tested and working

### 9.9 Outputs Complete
- ☐ Scoping document
- ☐ Consultation table (300-1000+ screened)
- ☐ PDF download script
- ☐ Search logs
- ☐ Reading notes (15-25, delegated to skill)
- ☐ Actor mapping report
- ☐ Controversy analysis report
- ☐ Corpus analysis table (100-200 kept)
- ☐ Corpus analysis report with figures/tables
- ☐ Technical review report (8000-15000 words)
- ☐ Annotated bibliography (80-150 sources)

## Critical Success Factors

**What distinguishes excellent critical review:**

✓ Constructs scientific object (not just theme summary)  
✓ Screens 300-1000+ sources systematically  
✓ Keeps 100-200 in corpus with justified decisions  
✓ Deep analysis of 15-25 via reading notes skill  
✓ Identifies explicit AND silent controversies  
✓ Names actors with roles and positions  
✓ Uses computational methods to validate qualitative findings  
✓ Produces publication-ready technical report (8000-15000 words)  
✓ Integrates figures/tables from corpus analysis  
✓ All cited sources in annotated bibliography  
✓ Every reference has DOI or URL  

**What to avoid:**

✗ Chronological organization (obscures theoretical tensions)  
✗ Descriptive summaries without analysis  
✗ Missing silent controversies (only reporting explicit debates)  
✗ Computational analysis without interpretive integration  
✗ Citations in report missing from bibliography  
✗ Bibliography including uncited sources from corpus  
✗ Generic annotations ("This article discusses X")  

## References

See `references/` for:
- `controversy_patterns.md` - Theoretical tension archetypes and mapping
- `reading_note_template.md` - Template (though delegated to skill)
- `scoping_template.md` - Template for scoping documents
- `corpus_analysis_methods.md` - Detailed guide to computational methods

See `scripts/` for:
- `search_*.py` - Search engine access scripts (istex, hal, CNRS, etc.)
- `download_pdfs.py` - Parallel PDF downloader
- `extract_pdf_text.py` - PDF text extraction
- `expand_citations.py` - Citation network expansion
- `analyze_corpus.py` - Template for corpus analysis methods

## What This Skill Does NOT Do

- Generate original research contributions
- Judge scientific validity of claims
- Replace domain expertise or close reading
- Guarantee publication acceptance
- Substitute for deep theoretical engagement
- Write reading notes (delegated to reading-notes skill)
- Adapt technical report to specific venues (user does this)

The skill structures a systematic research process; intellectual substance and theoretical insight come from the researcher.

## References

- `references/scoping_template.md`: scoping document template
- `references/reading_note_template.md`: reading note template
- `references/corpus_analysis_methods.md`: computational corpus analysis methods
- `references/analytical_frameworks_guide.md`: analytical frameworks for the critical synthesis
