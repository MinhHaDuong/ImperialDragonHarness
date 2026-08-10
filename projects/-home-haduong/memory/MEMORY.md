## Key insights

- Zotero est le système de référence ; tout le reste (`.bib` locaux, `docs/`) est du staging transitoire — la discipline vaut pour la bibliographie comme pour les sources.
- Instructions minimales : skills et règles ne portent que les contraintes non évidentes, découpées par cause racine ; pour le reste, faire confiance au modèle.
- L'auteur est allergique aux tics de prose LLM (métaphores répétées, padding) — nommer les choses par leur nom réel, une fois.
- Avant une action de réorganisation ou de suppression, chercher la décision antérieure (tickets du projet voisin, règles serveur) — elle existe souvent.
- Fan-out : épingler le modèle à chaque lancement (le frontmatter ne se propage pas) ; l'effort ne se règle par appel que via agent() de Workflow.

## Entries

- [Bibliography toolchain](user_bibliography_toolchain.md) — biblatex+biber, Zotero canonical, local .bib is staging, import at submission
- [Trust the LLM](feedback_trust_the_llm.md) — skills contain only non-obvious constraints; don't re-teach domain knowledge or invent fake thresholds
- [Skill topic boundaries](feedback_skill_topic_boundaries.md) — split rules across git/coding/state/workflow by root cause, not by consequence; one short bullet per file
- [Avoid costume metaphor (HET)](feedback_avoid_costume_metaphor_het.md) — don't repeat/explain the "costume" framing on the HET paper; reads as LLM padding
- [HET submission branches protected](project_het_submission_branches_protected.md) — climate-finance-het rejects deletion of submission/* branches (server-side rule)
- [Check sibling tickets before reorg](feedback_check_sibling_tickets_before_reorg.md) — before a cross-repo move, check the other repo's tickets for a prior decision on the same question
- [Subagent model/effort levers](feedback_subagent_model_effort_levers.md) — model needs per-call pin everywhere; effort is settable per-call only via Workflow's agent(), not the Agent tool
- [Feuille de route → workpackages](project_roadmap_to_workpackage_map.md) — les noms de lignes CNRS diffèrent des répertoires ; les 3 drafts polycentric_activity sont solo
- [Nextcloud tasks](reference_nextcloud_tasks.md) — CalDAV nx11797.your-storageshare.de, compte Admin, secret dans le trousseau, liste « Personnel » (personal/)
- [Relance JETP 2026](project_jetp_relance_2026.md) — roadmap Cassen envoyée 10 août, saturation OK, pilote ledger run 1 fait ; run 2 verrouillé sur ratification vérité terrain + RMP
