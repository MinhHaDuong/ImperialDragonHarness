# Project Memory

## Key insights

- Methodological honesty is a hard norm: computation *corroborates* history, and a cited number must trace to an archived pipeline output. A count that moves between passes is an alarm.
- Corpus: full = scholarship around climate finance, core subset `cited_by_count >= 50`, multilingual; three acts, 1990-2006 / 2007-2014 / 2015-2025, history first.
- A guard earns trust from its shape: assert the data-carrying property, not a text pattern, and red-test it by replaying the defect that motivated it.
- Two machines, one direction: data flows padme to doudou only, and `uv` is absent from the non-interactive PATH.
- The author publishes diamond OA without APC, in a History of Economic Thought register, runs parallel sessions, and takes weekends off.
- Gate in proportion to risk: a full /gaze loop cost ~75 min / ~1M tokens where a checklist took 11 min.

## Entries

### Author

- [Author's ORCID is 0000-0001-9988-2100: use it verbatim, never guess](user_orcid.md)
- [CNRS evaluation: peer-reviewed lines count, diamond OA, CNU05 list a signal not a gate](user_cnrs_section41.md)
- [Keep chat reports terse: pointer plus delta, never a recap of the PR or ticket](feedback_terse_reports.md)
- [No project work on weekends: a health boundary, not a preference](feedback_weekend_boundary.md)
- [REALF how-tos 41–51: the author's rules for submitting, revising and releasing outputs](reference_realf_release_rules.md)
- [Render every ad-hoc PDF (letters, notes) in A4, never US letter](feedback_a4_paper.md)

### Working with the author

- [A child ticket quotes the author's acceptance sentence verbatim, not just the mechanism](feedback_exit_criteria_carry_author_intent.md)
- [A follow-up ticket exists so the parent closes now; never keep it open as a pseudo-tracker](feedback_followup_lets_parent_close.md)
- [A mock shown for approval carries real values from the served data, never invented ones](feedback_mocks_use_real_values.md)
- [Decide what documents or the author's own pages settle; never relay an obvious question](feedback_dont_relay_obvious_questions.md)
- [For a one-time operation the command is the deliverable: no script, tests or ticket](feedback_no_tool_for_single_use.md)
- [For structured extraction, try a purpose-built tool (GROBID, spaCy) before an LLM](feedback_purpose_built_over_llm.md)
- [Name vocabulary values by the axis that separates them, two words max](feedback_name_values_by_their_distinguishing_axis.md)
- [Notes that route work to tickets get written into those tickets in the same PR](feedback_propagate_notes_to_tickets.md)
- [Over a size cap, delete the lowest-value content; never compress to game the count](feedback_caps_force_pruning_not_compression.md)
- [Plan multi-step revisions as shippable version increments, never a phase waterfall](feedback_version_increment_planning.md)
- [Record an author decision with its evidence, quoted, so a diff-only reviewer can check it](feedback_hitl_decision_cite_evidence.md)
- [Split a god module along real seams with domain names, under 500 lines, not just under 800](feedback_arch_not_linecount.md)
- [When the author settles a debate, write it into the editorial brief in the same commit](feedback_settled_debates_to_brief.md)

### Writing and sources

- [Cite only what you have read and can argue serves the paper's core; decline padding](feedback_read_before_cite.md)
- [Draft all prose in the author's voice (docs/style-anchor-v205.md) from the first draft](feedback_het_register.md)
- [Fulltext acquisition ladder: Unpaywall, ISTEX, Click&Read via the author, Wayback, cookies](reference_paywalled_acquisition.md)
- [HAL SWORD update: filename=meta.xml, dotted JEL codes, mask the CDATA password](reference_hal_sword_update_recipe.md)
- [Name a claim's falsifier ex ante and land it once; a conclusion introduces no new facts](project_0171_conclusion_rebuild.md)
- [Start any new paper deliverable in plain LaTeX, not Quarto](feedback_prefer_latex_over_qmd.md)
- [Œconomia rejected the history article for good (2026-09-16): never route work there](project_oeconomia_rejected.md)

### Paper ideas

- [Next-paper seed: build the joint-production (von Neumann–Sraffa) IAM the paper historicizes](project_paper_ceiling_growth_imaginary.md)
- [Next-paper seed: which way instrument concepts circulate (grey literature vs theory)](project_paper_instrument_circulation.md)

### Agents, gates and merging

- [Autonomous: a circuit-breaker-only ESCALATE may merge on evidence; a design call stops](feedback_escalate_procedural_vs_substantive.md)
- [Executor briefs forbid make check, unscoped pytest, uv sync, and venvs in shared /tmp](feedback_agent_briefs_scoped_gates.md)
- [Give git-touching helpers isolation: worktree; merge their PRs from your tree, then detach](feedback_helper_agent_needs_own_worktree.md)
- [Reviewers: DeepSeek (OpenRouter) + Terra, never Luna; set REVIEWERS_REPO, read seat status](feedback_external_panel_inert.md)
- [Size the gate to the PR's risk; never resume a fat executor for a small fix](feedback_gate_proportionate_to_risk.md)

### Machines and data flow

- [Data flows padme→doudou only: make corpus + dvc push on padme, corpus-sync on doudou](feedback_data_direction.md)
- [Machine padme: ssh via NetBird, uv PATH, llama-server, Linger=no, remote git via script](reference_machine_padme.md)
- [Run make/dvc corpus stages in the foreground so the author sees progress; never background](feedback_longrunning_jobs.md)

### Corpus and analysis

- [A corpus rerun is never additive: back up, force offline, byte-compare every stage](feedback_corpus_rerun_byte_compare.md)
- [Human annotations live in an append-only file, never a column the pipeline regenerates](feedback_human_labels_never_in_regenerable_files.md)
- [Null DOIs: dropna before merge/set_index on doi; blank NaN via pd.isna, never `or ""`](feedback_dropna_before_merge.md)
- [The efficiency–accountability axis is a unimodal continuum; never cite ΔBIC as bimodality](project_axis_is_unimodal.md)
