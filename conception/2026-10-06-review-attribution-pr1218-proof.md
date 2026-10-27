# PR1218 review attribution proof

Merged PR1218: `1aaf71ecd0603a1ea909b9044d4e2d2c78c053a9`.
Writer: runtime=claude-code; model=`anthropic/claude-sonnet-5-5`; effort=`medium`. Runtime message model and top-level effort/perTurnEffort fields establish these facts throughout the production session, including its publication and merge acknowledgements.
Reviewer: runtime=codex; model=`openai/gpt-6.1-sol`; effort=`medium`; seat=local-ci-read-only; status=ran. One completed read-only attempt, 2026-10-06T03:04:07Z–03:05:01Z. Runtime turn_context supplies model/effort; final response supplies completion and findings. Scope: draft local CI runner/workflow/image, before publication. Syntax checked; runner not executed by reviewer. Exact final merged head was not reviewed in this attempt.



The reviewer reported seven numbered categories, some containing several independently dispositioned findings. Preserve the following distinct claims when encoding fixed-line findings; anchors below map to merged code at1aaf71ec, rather than inventing an exact reviewed SHA.

- Machine/token exposure remains accepted for author-owned code: scripts/local-ci.sh:18, adopted:no for restricting persistent credentials.
- Empty/discovery-failed job-list false green fixed: scripts/local-ci.sh:100 and:102, adopted:yes.
- Inherited .actrc dryrun false green fixed: scripts/local-ci.sh:39, adopted:yes.
- Stale cloned revision fixed by fresh clone: scripts/local-ci.sh:60, adopted:yes.
- Shared mutable clone contamination fixed between jobs: scripts/local-ci.sh:129, adopted:yes.
- Forge merge-result and checkout semantics remain explicitly different: scripts/local-ci.sh:10 and:131, adopted:no for reproducing forge merge/checkout behavior.
- Hardcoded/stale base and self-as-sibling lookup improved via fresh fetch and actual PR metadata: scripts/local-ci.sh:68 and:82, adopted:yes. Reviewer warning about swallowed sibling API failures is not evidence that that existing guard was fixed here.
- Existing image/environment approximation remains: ci-local/Containerfile:1, adopted:no for full forge environment parity.
- Hang/signal handling improved: scripts/local-ci.sh:34 and:131, adopted:yes. No claim that every container-residue/token-failure subfinding was fixed.
- Ignored delivery files fixed by tracked ci-local files and gitignore exceptions; uncommitted-change warning fixed: scripts/local-ci.sh:46, adopted:yes.

Producer contemporaneous acknowledgement at03:05:51Z lists reliability fixes to implement; public PR body states empty-job/.actrc/stale-base/shared-clone findings were fixed and lists persistent token, head-only revision and image limits. Final merged code supports the anchors above. Categorize factual bug findings as verifiable; retained design/environment tradeoffs may be consider. No second completed reviewer attempt is established by the located reviewer session.


## Actual reviewer coordinates (use these for record encoding)
The completed reviewer report itself supplied `local-ci.sh:49–63` for credential/socket exposure; `:55–71` for zero-check discovery/.actrc; `:43–45,61` for revision/checkout/shared clone; `:41–48` for collision/base/PR lookup; `:34–37` plus Containerfile (no line) for environment drift; `:19–21,29,49` for hangs/residue; and no path:line for delivery/documentation. Normalize the explicitly named runner basename to `scripts/local-ci.sh`, the repository path of that reviewed file. A single supplied starting coordinate can represent a finding's actual report range (49,55,43,41,34,19 respectively). The earlier merged coordinates are analyst disposition mappings, never reviewer-reported coordinates. Delivery/documentation category has no supplied coordinate and must not receive invented coordinates. Split composite findings only with explicit prose explaining which subclaim was adopted. No coordinate was supplied for Containerfile; omit that invented coordinate from fixed-line finding encoding.

PR1232 independently added the [fixed-line record](../memory/journal/2026/2026-10-06-review-attribution-pr1218.md). After direct metadata/coordinate verification and independent candidate review, the author explicitly approved ticket1055’s exact four-fact correction as an exception to design section3’s append-only policy. The corrected record changes only writer effort, the unsupported delivery coordinate, the supplied retained-checkout coordinate, and the retained environment adopted flag; all earlier context prose remains byte-for-byte with a dated superseding correction appended. No schema or standing rule changes. Unanchored delivery/documentation advice remains qualitative context and is excluded from mechanical per-anchor estimates; no location is invented. [The public PR body](https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1218) corroborates the completed review, implemented false-green fixes and retained limits.
