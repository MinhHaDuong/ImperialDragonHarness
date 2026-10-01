# Search and Analysis Scripts

This directory contains scripts for literature review corpus building and analysis.

## Search Engine Scripts

### search_istex.py (IMPLEMENTED)
French academic database search via ISTEX API.
```bash
python search_istex.py "climate finance" --year-start 1990 --year-end 2025 --output results_istex.csv
```

### search_hal.py (TEMPLATE - TO IMPLEMENT)
HAL open archive search via HAL API.
```bash
python search_hal.py "climate finance" --year-start 1990 --output results_hal.csv
```

### search_semantic_scholar.py (TEMPLATE - TO IMPLEMENT)
Semantic Scholar API client.
```bash
python search_semantic_scholar.py "climate finance measurement" --max-results 200
```

### search_cnrs_bib.py (TEMPLATE - REQUIRES USER)
CNRS bibliography - may require institutional access.
User should search manually and export results.

## Corpus Processing Scripts

### download_pdfs.py (FROM v2.1)
Parallel PDF downloader with retry logic.
```bash
python download_pdfs.py consultation_table.csv --output-dir ./pdfs --workers 5
```

### extract_pdf_text.py (TEMPLATE - TO IMPLEMENT)
Extract text from downloaded PDFs for corpus analysis.
```bash
python extract_pdf_text.py --input-dir ./pdfs --output-dir ./extracted_texts
```

Features needed:
- Handle password-protected PDFs
- Detect image-only PDFs and apply OCR if requested
- Extract metadata (title, authors from PDF properties)
- Output plain text files with same naming convention

### expand_citations.py (TEMPLATE - TO IMPLEMENT)
Extract citation networks from corpus.
```bash
python expand_citations.py corpus_analysis_table.csv --output citations_network.gexf
```

Uses tools like:
- PyPDF2 or pdfplumber for PDF parsing
- Regular expressions for citation extraction
- NetworkX for graph construction

## Corpus Analysis Scripts

### analyze_corpus.py (TEMPLATE - TO IMPLEMENT)
Main corpus analysis script implementing methods from Step 6.

```bash
python analyze_corpus.py corpus_analysis_table.csv --methods clustering,topics,network
```

Methods to implement:
- Vectorization and clustering (sentence-transformers + scikit-learn)
- Topic modeling (BERTopic)
- Citation network analysis (NetworkX)
- Temporal analysis (pandas time series)
- Keyword extraction (KeyBERT, TF-IDF)

## Implementation Notes

**Implemented:**
- search_istex.py (complete ISTEX API client)
- download_pdfs.py (from v2.1)

**To implement as needed:**
- Other search scripts (hal, semantic scholar)
- PDF text extraction
- Citation expansion
- Corpus analysis methods

**User responsibility:**
- Institutional access searches (CNRS, paywalled databases)
- Manual searches where APIs unavailable
- Verification of extracted data quality

## Dependencies

Install required packages:
```bash
pip install requests pandas networkx scikit-learn sentence-transformers bertopic PyPDF2 pdfplumber
```

For specific methods, additional packages may be needed (see analyze_corpus.py implementation).
