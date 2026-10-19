# Review identity evidence — PRs 1462–1464

1. Audience: public; repository changes, review reports and runtime identity limitations only.
2. Writer context: root Codex session; live session_meta exposes provider `openai`, turn_context exposes model `gpt-6.1-sol` and effort `low` throughout this task. No verbatim provider-qualified model-id string or model-version is exposed. These separate fields are not concatenated into a guessed provider-qualified pin.
3. Reviewer context `/root/gaze_removal`: native Codex child explicitly launched as `gpt-6.1-sol`, effort `medium`; runtime exposed no verbatim provider-qualified model-id string or model-version. It performed portable explicit-diff review and coordinated PR1462.
4. Reviewer context `/root/gaze_removal/adherence`: a single reused native Codex context performed adherence, correctness, portable simplify and the final gate on PR1462, in sequence. Its reports do not expose a verbatim provider-qualified model-id or model-version. It is not four independent reviewers.
5. Reviewer context `/root/review_docs`: native Codex child explicitly launched as `gpt-6.1-sol`, effort `medium`; runtime exposed no verbatim provider-qualified model-id or model-version. The same context reviewed/gated PR1463 and PR1464 and checked both rebases. Five perspectives were passes within this context, not five agents.
6. Native `/review` was unavailable. PR1462 used a portable orchestrator review and a reused child; PR1463/1464 used portable explicit-diff review and simplify. No cross-family independence is claimed.
7. PR1463 advisory: README.md:48, the author's shortened Brood wording, omits explicit-request/nomination detail; adopted: no, author wording preserved. No blocking findings were reported.
8. PR1462 reviewed head e822025b65a3feaf323bc128925cd738c07c0317. PR1463 attempts covered 115756f4999af665fee2f8939e1c3c029b3470d4 then a3952880acb552ef4bbca86ec45c1ebede17fa3c; PR1464 attempts covered 595b5dbb3eba356c7c0c402c222875d10e49aaae then c7ecd23324587535654cc9d38cfd12f6b47cafb7. Both range-diffs reported identical patches; the reviewing context explicitly rechecked base interactions.

## Durable forge reports (verbatim bodies)

### PR 1462: https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1462#issuecomment-6269790637

## /gaze actions

round: 1
tier: small
risk_band: normal
circuit_breaker: none
multi_ticket: none
adherence: PASS — 0 blocking; `make lint`: 186 passed, 1575 deselected.
review: 0 findings — portable explicit current-diff review substituted for unavailable native `/review`.
review-pr: 0 findings
review-pr scope: one correctness seat (28 changed lines / 2 files; no pipeline path)
panel integrity: COMPLETE for selected correctness perspective; same-family replication, no cross-family independence claimed. No external panel selected.
battery: ran with portable `/review` substitution; adherence, correctness, portable simplify, and gate used sequential stages of one Sol 6.1 low worker (OpenAI), plus orchestrator review. Slot pressure prevented extra simultaneous workers.
simplify: CLEAN, 0 fixes; portable route examined manifest reuse, repeated fixture paths, and regression overlap.
gate: ran

## /verify-gate verdict

/verify-gate round=1 verdict=APPROVED
verdict: APPROVED
gate_session_id: 92743d15-d21c-40fc-a893-4ea819a4afac
review_worktree_path: /home/haduong/.agents/.claude/worktrees/review-1462
ruled_tip_sha: e822025b65a3feaf323bc128925cd738c07c0317

Exit criteria (PR body; Ticket: none):
- Remove global instruction registration: ADDRESSED — this SHA removes the sole `~/.claude/CLAUDE.md` manifest entry; `tests/test_projection_validator.py:140` forbids its registration.
- Retain repository AGENTS.md: ADDRESSED — complete changed-file roster is only `adapters/projections.json` and `tests/test_projection_validator.py`; AGENTS.md is unchanged and present.
- Startup no longer requires global instructions: ADDRESSED — `scripts/validate-projections.py:357` loads declared entries only; regression `tests/test_projection_validator.py:709` accepts absent global instructions.
- Claude hook plugin remains required: ADDRESSED — `adapters/projections.json:5` retains required claude-code adapter; updated assertion at `tests/test_projection_validator.py:139` and positive launch control at `:369` still reject its broken projection.
- Foreign global instructions ignored and preserved: ADDRESSED — new regression `tests/test_projection_validator.py:713` accepts a foreign dangling link; validator checks only manifest entries (`scripts/validate-projections.py:368`), installer iterates only manifest entries (`adapters/lifecycle.py:60`), so neither examines nor replaces the retired path.

Unresolved review comments: none (top-level, reviews, inline comments fetched).
Unresolved simplify: none.
Adherence: PASS.
Scope overflow: none.
Nits: no ticket; no explicit test plan in PR body (nonblocking).

Rationale: the manifest is the common ownership boundary for installation and launch validation. Deleting this single entry retires the global instruction requirement without weakening the separately retained hook projection. Regression changes move broken-guard controls to the actual hook source. Full `make check` on exact committed content passed 1758 tests / 3 skipped (caller log `/tmp/retire-global-claude-20261019-check.log`, inspected); all ten GitHub checks succeeded. This gate does not independently attest the live symlink deletion, which the author authorized and caller performed. No source, ticket, branch, commit, or push mutation by review.

telemetry: tier=small risk_band=normal wall=na agents=1 tokens=na cost~=na

Containment: review scratch archived under `/tmp/pr1462-gaze-evidence`, clean isolated review worktree removed; author worktree remains on `retire-global-claude-20261019`, author and main checkouts clean.


### PR 1463: https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1463#issuecomment-6269785062

## /gaze actions
round: 1
review route: portable explicit-diff review, five perspectives
reviewer: gpt-6.1-sol @medium, OpenAI; same-family, not independent
adherence: PASS — full make check: 1757 passed, 3 skipped
review-pr: no blocking findings
simplify: portable — no must-fix findings

## /verify-gate verdict
verdict: APPROVED
gate_session_id: review-docs-1463-115756f4
review_worktree_path: /home/haduong/.agents/.claude/worktrees/readme-split-20261019
ruled_tip_sha: 115756f4999af665fee2f8939e1c3c029b3470d4

Exit criteria:
- Guides separated and author README edits preserved: ADDRESSED — INSTALL.md and CONTRIBUTING.md contain setup/runtime and development/ticket guidance; README links to both.
- git-erg, Arena and local links remain discoverable: ADDRESSED — README links retained; all nine local links across the guides resolve.
- Root catalog generated, exact drift checked and staged by hook: ADDRESSED — catalog_document(), check-skills-drift.py and hooks/pre-commit target skills-catalog.md; hook tests cover skill and unrelated commits.
- Private skill symlinks excluded: ADDRESSED — existing exclusion and behavioral test retained.
- New documents tracked: ADDRESSED — git ls-files confirms all three root documents as regular tracked files.
- Alphabetical catalog relocated; category frontmatter and AGENTS excluded: ADDRESSED — all 42 rows byte-match the previous README, no skill or AGENTS edits in this PR.

Unresolved blocking findings: none.
consider: the author's short Brood sentence omits details of its explicit-request and nomination boundaries. Those remain in the skill; preserved author wording, advisory only.

Native /review unavailable; portable current-diff review used. Full suite logs were inspected by the reviewing seat. No cross-family independence claimed.


### PR 1463: https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1463#issuecomment-6269926438

## /gaze actions
round: 1
review route: portable explicit-diff review, five perspectives
reviewer: gpt-6.1-sol @medium, OpenAI; same-family, not independent
adherence: PASS — full make check: 1758 passed, 3 skipped
review-pr: no blocking findings
simplify: portable — no must-fix findings

## /verify-gate verdict
verdict: APPROVED
gate_session_id: review-docs-1463-a3952880
review_worktree_path: /home/haduong/.agents/.claude/worktrees/readme-split-20261019
ruled_tip_sha: a3952880acb552ef4bbca86ec45c1ebede17fa3c

Exit criteria:
- Guides separated and author README edits preserved: ADDRESSED — INSTALL.md and CONTRIBUTING.md contain setup/runtime and development/ticket guidance; README links to both.
- git-erg, Arena and local links remain discoverable: ADDRESSED — README links retained; all nine local links across the guides resolve.
- Root catalog generated, exact drift checked and staged by hook: ADDRESSED — catalog_document(), check-skills-drift.py and hooks/pre-commit target skills-catalog.md; hook tests cover skill and unrelated commits.
- Private skill symlinks excluded: ADDRESSED — existing exclusion and behavioral test retained.
- New documents tracked: ADDRESSED — git ls-files confirms all three root documents as regular tracked files.
- Alphabetical catalog relocated; category frontmatter and AGENTS excluded: ADDRESSED — all 42 rows byte-match the previous README, no skill or AGENTS edits in this PR.

Unresolved blocking findings: none.
consider: the author's short Brood sentence omits details of its explicit-request and nomination boundaries. Those remain in the skill; preserved author wording, advisory only.

Native /review unavailable; portable current-diff review used. Full suite logs were inspected by the reviewing seat. No cross-family independence claimed.

Base refresh: rebased onto9577eccb (mergedPR1462). range-diff is identical (=); all11 reviewed file contents unchanged. The same-family reviewer rechecked the base delta and found no interaction. Combined full make check is recorded in /tmp/readme-split-rebased-check.log. Original criteria and advisory disposition remain unchanged. Local selected skill-lint passed; this is not a full local container run.


### PR 1464: https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1464#issuecomment-6269785472

## /gaze actions
round: 1
tier: small
review route: portable explicit-diff review, five perspectives
reviewer: gpt-6.1-sol @medium, OpenAI; same-family, not independent
adherence: PASS — full make check: 1757 passed, 3 skipped
review-pr: no blocking findings
simplify: portable — no must-fix findings

## /verify-gate verdict
verdict: APPROVED
gate_session_id: review-docs-1464-595b5dbb
review_worktree_path: /home/haduong/.agents/.claude/worktrees/state-roadmap-20261019
ruled_tip_sha: 595b5dbb3eba356c7c0c402c222875d10e49aaae

Exit criteria:
- Separate strategic direction from immediate handoff: ADDRESSED — ROADMAP.md states its scope; STATE.md retains the dated handoff.
- Three open tickets and dependency accurate: ADDRESSED — erg ls/ready and ticket1099 confirm 1045 and1100 ready, 1099 blocked by1100.
- Local CI/review first, testing next: ADDRESSED — ROADMAP priorities and next-workstream section include AST dependency analysis, measurements against full suite, conservative fallback and integrated revision/review evidence.
- Testing remains design work: ADDRESSED — ROADMAP explicitly states it is not an implementation ticket.
- STATE excludes repeated guidance, Zotero history and personal chores, within20 lines: ADDRESSED — 17 lines; retained lifecycle and attribution handoff verified against closed1095/1119/1120 and snapshot0136a24c.

Unresolved review comments, simplify findings and adherence violations: none. Cached current-head forge histories contain no comments, reviews or inline findings. All four local document links resolve.
Native /review unavailable; portable current-diff review used. Full suite logs were inspected by the reviewing seat. No cross-family independence claimed.


### PR 1464: https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1464#issuecomment-6269958542

## /gaze actions
round: 1
tier: small
review route: portable explicit-diff review, five perspectives
reviewer: gpt-6.1-sol @medium, OpenAI; same-family, not independent
adherence: PASS — full make check: 1758 passed, 3 skipped
review-pr: no blocking findings
simplify: portable — no must-fix findings

## /verify-gate verdict
verdict: APPROVED
gate_session_id: review-docs-1464-c7ecd233
review_worktree_path: /home/haduong/.agents/.claude/worktrees/state-roadmap-20261019
ruled_tip_sha: c7ecd23324587535654cc9d38cfd12f6b47cafb7

Exit criteria:
- Separate strategic direction from immediate handoff: ADDRESSED — ROADMAP.md states its scope; STATE.md retains the dated handoff.
- Three open tickets and dependency accurate: ADDRESSED — erg ls/ready and ticket1099 confirm 1045 and1100 ready, 1099 blocked by1100.
- Local CI/review first, testing next: ADDRESSED — ROADMAP priorities and next-workstream section include AST dependency analysis, measurements against full suite, conservative fallback and integrated revision/review evidence.
- Testing remains design work: ADDRESSED — ROADMAP explicitly states it is not an implementation ticket.
- STATE excludes repeated guidance, Zotero history and personal chores, within20 lines: ADDRESSED — 17 lines; retained lifecycle and attribution handoff verified against closed1095/1119/1120 and snapshot0136a24c.

Unresolved review comments, simplify findings and adherence violations: none. Cached current-head forge histories contain no comments, reviews or inline findings. All four local document links resolve.
Native /review unavailable; portable current-diff review used. Full suite logs were inspected by the reviewing seat. No cross-family independence claimed.

Base refresh: rebased onto4b2258c7 afterPR1462/1463. range-diff is identical (=); STATE and ROADMAP contents unchanged. Same-family reviewer revalidated links, ticket census, dependency and17-line limit with no new findings. Full combined suite recorded in /tmp/state-roadmap-rebased-check.log. Local selected validate-tickets passed; this is not a full local container run.


## PR1462 raw phase artifacts

### adherence.md

# Adherence — PR 1462

```yaml
adherence: PASS
escalation: null
head: e822025b65a3feaf323bc128925cd738c07c0317
base: 0136a24c05db95678b57bb03ecd0a22819513b43
branch: retire-global-claude-20261019
semantic_review:
  applicable: false
  status: skipped
  reason: No discovered instruction or rule file changed. The manifest-only ownership removal and regression-test adjustments leave no architectural concern uncovered by projection tests; no semantic fallback trigger remains.
  rule_sources: [AGENTS.md, rules/guards.md, rules/workflow.md, rules/git.md, rules/README.md, rules/coding-python.md, rules/prose-adherence-tests.md]
  worker_id: null
  model: unavailable
  family: unavailable
  effort: unavailable
  route: null
  launch_evidence: null
  completion_evidence: null
mechanical_failures: []
semantic_findings: []
untested_rules: []
```

Declared runner: Makefile:28–32 documents `make lint` as the adherence gate, corroborated by rules/coding-python.md Testing. `make -n lint` exited 0 and resolved to `uv run --frozen python3 -m pytest tests/ -m adherence`. Initial sandbox execution failed acquiring a uv cache lock on read-only /data/cache/uv; approved escalation reran the identical declared command successfully: **186 passed, 1575 deselected in 9.19s**, exit 0 (execution session 9394, completed via write_stdin). This limitation was resolved, not treated as a clean initial run.

Static reference-resolution phase inapplicable: only adapters/projections.json and tests/test_projection_validator.py changed; no .tex/.qmd/.bib. `git diff --check origin/main...HEAD` exited 0. No trace input supplied. CI contract inspected at .github/workflows/CI.yml; no conflicting adherence declaration. No manuscript exists in the changed scope, so prose-adherence-tests.md does not bind. Skill catalog untouched. Test updates use disposable fixture paths, standard assertions, and no new dependencies/imports or subprocesses. Existing projection guards remain registered in the manifest; the removed instruction path is explicitly forbidden by test_projection_validator.py:140 and covered absent/dangling at lines 709–715.

Full-suite result supplied by caller: exact committed content 1758 passed, 3 skipped in /tmp/retire-global-claude-20261019-check.log; not independently rerun by this seat. Semantic fallback was explicitly assessed and skipped, not claimed as an independent semantic worker. Authoring process/TDD chronology is outside this diff-only seat's evidence; no violation inferred. No source, ticket, branch, commit, or forge mutation performed.

### portable-review.md

reviewed_sha: e822025b65a3feaf323bc128925cd738c07c0317
route: portable explicit-diff review; native /review unavailable
reviewer: gaze orchestrator, OpenAI family (not independent)
verdict: CLEAN
paths: adapters/projections.json; tests/test_projection_validator.py; adapters/lifecycle.py; scripts/validate-projections.py
Evidence: manifest removes only global CLAUDE.md entry; required claude-code adapter link remains first (lines 5-12). Validator main (lines 357-368) checks load_entries results; install_links (adapters/lifecycle.py:60) likewise iterates only entries(), so neither inspects nor writes the removed path. Test fixture derives projections from current manifest. New absence/foreign dangling symlink test lines 709-714 covers both accepted states. Existing foreign directory and broken guard launch tests now point at actual required hook adapter. Repository AGENTS.md unchanged in diff.
Blockers: none
Minors: none

### correctness.md

# Correctness seat C — PR 1462

Verdict: PASS. Confidence: high within this two-file diff. Findings: none.

Reviewed head e822025b65a3feaf323bc128925cd738c07c0317 against base 0136a24c05db95678b57bb03ecd0a22819513b43. This is the distinct correctness stage by the adherence worker, not an independent additional identity.

The removed adapters/projections.json entry previously claimed ~/.claude/CLAUDE.md. scripts/validate-projections.py:290–337 expands only declared paths and filters by runtime; no wildcard can reconstruct that removed root-level path. adapters/lifecycle.py:40–41 and :59–60 use that same manifest for installation. Therefore future installs no longer create this link, and absent, dangling, or foreign global instructions cease to block validation. Existing global instruction files are preserved; removing already-installed global files is outside this diff and not implicitly performed by installation.

The substitutions at tests/test_projection_validator.py:139, :244–249, and :364 retain the actual Claude guard projection as the tested failure surface. The plugin is an explicit manifest entry, with explicit-entry precedence preserved by loader de-duplication; the generic skill registration does not displace it. Directory refusal still validates a foreign real directory without replacing it, and the launch positive control still plants a required dangling guard and checks launch refusal. The new :709–715 regression exercises absent and dangling global instructions, while :140 ensures the path cannot be reintroduced as any manifest entry. All new fixture writes remain inside disposable HOME.

Evidence: declared adherence gate completed 186 passed; caller supplied exact-content full check 1758 passed/3 skipped (not independently rerun here). No new executable path or dependencies. No claim of forge CI or live-machine migration verification. No commits, pushes, branches, source edits, or ticket edits performed.

### simplify.md

# Portable simplify pass — PR 1462

Verdict: CLEAN. No change candidates recommended. Head: e822025b65a3feaf323bc128925cd738c07c0317.

This pass ran after the separate correctness assessment. It is a portable review pass by the same worker, not a claimed external simplify tool invocation.

Candidates examined:

- Manifest deletion versus adding an exemption in the validator: deletion is already the smaller design and reuses the shared manifest contract for check/install/launch.
- Repeated replacement path in tests: ~/.claude/skills/claude-code is only repeated in the existing focused guard checks; a new constant/helper would add indirection without removing meaningful complexity.
- New regression versus existing unlisted-link tests: the named regression pins the specific retired requirement, while generic ownership tests retain broader semantics. Its two validation calls cover absent and dangling states without parametrization overhead.
- Assertion overlap at :140 and :709–715: these guard different properties (manifest ownership versus runtime behavior). Both are short and serve the requirement; removing either weakens the stated contract.
- Remaining RTK/tickets projection entries: these are unchanged, outside the requested single-path retirement. Their possible future cleanup is not a simplification finding in this diff.

No source writes or additional tests performed in this stage. Existing adherence result and caller-supplied full-check evidence remain applicable because source content did not change.

### gate.md

verdict: APPROVED
round: 1
pr: 1462
ticket: null
gate_session_id: 92743d15-d21c-40fc-a893-4ea819a4afac
review_worktree: /home/haduong/.agents/.claude/worktrees/review-1462
ruled_tip_sha: e822025b65a3feaf323bc128925cd738c07c0317
per_exit_criterion:
  - criterion: "Remove the global ~/.claude/CLAUDE.md registration while retaining the repository AGENTS.md."
    status: ADDRESSED
    evidence: "e822025b65a3feaf323bc128925cd738c07c0317 deletes the sole global-instruction entry between adapters/projections.json:40 and :43; tests/test_projection_validator.py:140 forbids any entry with that path. AGENTS.md exists and its origin/main...HEAD diff is empty."
  - criterion: "startup no longer requires global instructions"
    status: ADDRESSED
    evidence: "e822025b65a3feaf323bc128925cd738c07c0317 tests/test_projection_validator.py:709-714 (test_claude_does_not_require_or_register_global_instructions) validates successfully without the file and with a dangling foreign link; scripts/validate-projections.py:290-337 expands only manifest entries, and :358-368 checks only those entries."
  - criterion: "the Claude hook plugin remains required"
    status: ADDRESSED
    evidence: "e822025b65a3feaf323bc128925cd738c07c0317 adapters/projections.json:5-10 retains required=true for ~/.claude/skills/claude-code; tests/test_projection_validator.py:139 asserts required membership. test_a_missing_plugin_link_blocks_the_launch at :664 and test_positive_control_planted_broken_link_blocks_the_launch at :369 enforce missing/dangling guard refusal."
  - criterion: "foreign global instructions are ignored and preserved"
    status: ADDRESSED
    evidence: "e822025b65a3feaf323bc128925cd738c07c0317 tests/test_projection_validator.py:713-714 accepts a foreign dangling instruction link. adapters/lifecycle.py:40-41 and :59-60 install only manifest entries; removed global path is absent and cannot be overwritten by that loop. Validator scripts/validate-projections.py:368 only checks listed entries and performs no instruction-file writes."
unresolved_review_comments: []
malformed_minors: []
unresolved_simplify_findings: []
unresolved_adherence_violations: []
scope_overflow: []
nits:
  - no_ticket
  - PR body lacks an explicit test-plan section; exact-content full-gate evidence is available separately.
review_limitations:
  - "Same-family reused worker across adherence, correctness, simplify, and this gate; no claim of independent lineage."
  - "Native /review unavailable: orchestrator's explicit-diff portable-review.md substitution was inspected; it is not independent review."
  - "Inline review comments and ten successful CI checks supplied by orchestrator's fresh forge reads; this seat independently read PR body, empty comments/reviews, and matching forge head after sandbox escalation."
  - "Already-removed live symlink is an external action stated by the PR, not a repository exit criterion or a fresh filesystem fact established by this gate."
rationale: |
  All four PR-body requirements are addressed by the manifest deletion, retained required plugin entry, focused regression tests, and the actual shared manifest consumers. No ticket exists and no close claim is dangling. Round 1 follows the empty PR comment history. The exact-head full-check log ends with 1758 passed, 3 skipped in 70.09s, and this worker separately ran the declared adherence gate: 186 passed. These results support, but do not replace, the criterion-specific source evidence above. The two-dot branch log contains one commit changing only adapters/projections.json and tests/test_projection_validator.py; both are attributable to the retirement and its regressions. All four inspected phase reports are clean, with no contradictory signals or must-fix simplify requests.
  Strongest remaining attack: removing a managed path might disable guards or erase foreign content. The guard plugin remains required and its planted-dangling launch test is retained; installation iterates current manifest entries and thus does not touch the retired instruction path. Existing unrelated instruction files are intentionally preserved. This reversible removal changes one registration, not guard code, credentials, or migration logic; ordinary same-family review is proportionate. No required cross-family perspective is represented as having run.
  Immediately before this ruling, git -C on the named review tree returned full HEAD e822025b65a3feaf323bc128925cd738c07c0317, matching the anchor and independently read forge head. Commit timestamps were readable. No tests rerun for the gate, no source/git/forge mutations, and no PR comment posted; orchestrator owns combined posting.
