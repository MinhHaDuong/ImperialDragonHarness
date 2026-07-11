# Activity Report Writer - Memory

## Project status

- **Rapport à vague CID 52**: 22 pages, 131 KB. All 9 sections drafted.
- **Avis différé** from CID 52 (July 2025). Complément addresses: production scientifique, encadrement, responsabilités collectives, mise en oeuvre AEDIST.
- **Build**: `cd rapport-vague-cid52 && make all` → PDF at `output/rapport-vague-cid52.pdf`

## File organization

- `CLAUDE.md` → contains only `@AGENTS.md`
- `AGENTS.md` → general writing/formatting rules (reader-targeted writing, SF-DORA, enumerated lists, unnumbered subsections, realized-before-planned)
- `rapport-vague-cid52/AGENTS.md` → project-specific rules (CNRS formatting, CID 52 criteria, multi-agent review procedure, publication counts, HAL notes, sensitive topics)

## User preferences

- CLAUDE.md should only contain `@AGENTS.md` — all instructions go in AGENTS.md
- Prefers parallel agent orchestration for large tasks
- Writes in French for the rapport, instructions may be in French or English
- Values scientific substance over administrative detail
- SF-DORA strict: no h-index, no IF, no citation counts anywhere

## Key directories for fact-checking

- BibTeX: `~/CNRS/html/files/Ha-Duong.bib`
- RIBACs: `~/CNRS/secretariat/rapports-d-activite/RIBAC/`
- Avancement DR1: `~/CNRS/secretariat/rapports-d-activite/avancement/2025/`
- Projects: `~/CNRS/projets/actifs/`, `~/CNRS/projets/sent/`, `~/CNRS/projets/placard/`
