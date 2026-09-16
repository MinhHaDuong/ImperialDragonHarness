# Teaching scraper regression lessons

## DOI format from LLM extraction
- gemma-2-27b-it extracts DOIs as full URLs (`https://doi.org/10.xxx`) from PDF text
- The normalize stage stored them as-is, breaking deduplication
- Fix: `clean_doi()` in utils.py strips URL prefixes using regex `(10\.\d{4,}[^\s]*)`
- Apply cleaning both in normalize stage AND on CSV load in build_teaching_yaml.py

## Convergence filter and manual catalog
- Old system: manual catalog readings bypassed the convergence filter (n_courses >= 2/3)
- Removing manual catalog (#258) silently regressed output from 87 to 27 readings
- Fix: two-tier filter — "detailed syllabi" (>= 20 DOI readings) get their DOI readings at n_courses >= 1
- Harvard FECS (124 readings, 143 universities) is the archetype of a detailed syllabus

## LLM extraction quality limits
- gemma-2-27b-it misses ~30% of DOI-only readings from the old manual catalog
- It extracts the same papers but with wrong DOIs (confused between papers by same author)
- CrossRef title lookup doesn't fully compensate — common author names cause false matches
- Follow-up: #279 tracks extraction quality improvement

## Testing approach
- REFERENCE_DOIS test set should reflect achievable ground truth, not aspirational targets
- Adding minimum output size assertions catches regressions more robustly than exact DOI matching
