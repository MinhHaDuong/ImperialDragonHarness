# Cooldown review of the harness-government memo

Ticket 1369, run 2026-11-09 on padme. Subject: `design/2026-10-30-harness-government.md`
(PR #2040). This record holds three reviews as returned, a draft triage table and an
advisor's row-by-row answer on it. The triage table is a draft by this session's workers,
made under the author's license of 2026-11-09 to reconsider needs-human; Astra agrees with
it on five rows and disagrees on F4. It is not the author's triage: exit criterion 2 stays
open, the triage is the author's, and nothing here marks a follow-up need, want or drop on the author's behalf, and nothing in
the memo has been implemented, ticketed or written into a rule, skill, guard or memory file.

The author's caution framed every seat: "It is easy to be overenthusiastic about a metaphor."

## Seats and conditions

| Seat | Reviewer, as observed | Family | Door | Observed how |
|---|---|---|---|---|
| Step 1, Fable | `claude-fable-5-2` | Anthropic | Claude Code subagent, launch pinned `model: fable` | the seat's own report line, copied from its system prompt |
| Step 2, cross-family | `gpt-6-astra`, reasoning effort high | OpenAI | `codex exec -s read-only -m gpt-6-astra -c model_reasoning_effort=high`, codex-cli 0.167.0, session `01a1c249-77b7-7540-8be6-acb80c67a3ad` | the session header printed by codex |
| Step 3, KISS | `claude-opus-5-5` | Anthropic | Claude Code subagent, launch pinned `model: opus` | the seat's own report line |
| Triage draft | `claude-opus-5-5` (the coder of this ticket) | Anthropic | — | own system prompt |

**Family.** Fable, the KISS seat and the coder who drafted the triage are all Anthropic
models: Fable and the KISS seat are the same family as each other and as the drafter.
They add angle and replication, not independence. Astra is the only independent seat.
The KISS seat went to the ASSURANCE cluster (`skills/route/SKILL.md`: judgment work)
with a "prefer deleting to adding" lens.

**Conditions.** All three seats got the same brief: the memo path, permission to open
files the memo cites in order to check its claims, and an explicit ban on `tickets/1369-*`,
`memory/`, any other `design/` file and any session transcript. None saw the conversation
that produced the memo, nor each other's output. The three ran concurrently. The brief
asked each for the same things: an overall verdict, metaphor as real work or decoration
per frame, and NEED / WANT / DROP for six follow-ups:

- F1: AGENTS.md states that it is the constitution (memo follow-up 1).
- F2: `rules/guards.md` names itself ordre public (follow-up 1).
- F3: `rules/guards.md` gains the enforcement column (follow-up 1, §3).
- F4: the memory court, three gaze chambers on every smelt merge request (follow-up 2, §4).
- F5: registries, facts with a date and a probe that the materiality chamber re-runs (follow-up 2, §5).
- F6: ticket 1350 takes §4 and §5 as its frame (follow-up 2).

The KISS seat's brief added a KISS lens and a "drop, merge, or vocabulary only" section.

**Limitations observed.**
- Astra reported that a runtime hook injected gaze case notes from memory into its
  context when it read `skills/gaze/SKILL.md`. It says it did not use them as evidence. Its
  isolation from memory was therefore not complete.
- Fable opened `tickets/closed/1350-*`. The brief allowed this (only 1369 was banned), and
  the memo cites 1350.
- The coder wrote its draft column before reading any seat's output
  (`F4 WANT, reduced` was its own view, recorded before the three DROPs came in).

## Draft triage table

Verdicts are NEED, WANT or DROP. "Converge" means all four columns agree.

| # | Follow-up | Fable | Astra | KISS | Coder draft | Converge? |
|---|---|---|---|---|---|---|
| F1 | AGENTS.md is the constitution | DROP: AGENTS.md now calls itself harness-only bylaws (1412); the label would be false | DROP: misstates a project-scoped file's authority | DROP: label only; AGENTS.md does not hold the "powers" | DROP: relabel, changes no decision | converge: DROP |
| F2 | guards.md named ordre public | DROP: vocabulary only, it already says nothing overrides it | DROP: existing non-override language does the work | DROP: pure relabel | DROP: vocabulary only | converge: DROP |
| F3 | guards.md enforcement column | WANT: real gap, but keep the table outside the resident file | NEED: prevents false assurance; record partial coverage and bypasses | WANT: honest gap map; all rows "declared only"; one line or none | WANT: honest map, but upkeep (the memo's own table is already stale) | diverge: Astra NEED, three WANT |
| F4 | Memory court on every smelt MR | DROP: no recurring defect; n=1; memory rarely read | DROP: duplicates existing checks; pick review by risk | DROP: one failure caught without a court; use one gaze brief | WANT, reduced to one other-family materiality seat | diverge: coder WANT, three DROP |
| F5 | Registry facts: date + probe; chamber re-runs | WANT: dating is cheap; probes fit host facts; chamber falls with F4 | WANT: for volatile facts; allow authoritative sources; no standing chamber | WANT: cheap habit for host facts; drop the chamber half | WANT, host facts only | converge: WANT, narrowed to dating plus a probe for host facts (Astra: volatile facts, authoritative sources allowed), without the chamber |
| F6 | 1350 takes §4–5 as frame | DROP: 1350 closed 2026-11-01 (PR #2170) | DROP: would prejudge the storage design | DROP: ties a stores design to an unproven court | DROP: premise expired, 1350 closed under option b (coder's own check of the ticket) | converge: DROP |

Overall verdicts: Fable KEEP, TRIMMED; Astra KEEP, TRIMMED; KISS VOCABULARY ONLY.

Where the seats agree beyond the table. All three call MOA/MOE mostly decoration; Fable
and KISS call separation of powers decoration, while Astra calls it real work. All three keep, as real work, the "where does new
knowledge go" list (§1), the declared-versus-enforced distinction (§3) and the
fact-versus-ruling split (§5). They also agree on stale facts in the memo:
- `conception/` is now `design/`;
- ~256K versus 230K in guards.md;
- the self-only gaze claim was reversed by an author ruling on 2026-11-01 (Fable and KISS);
- the AGENTS.md scope (Fable and Astra);
- `guard-destructive-bash.sh` lives in `scripts/`, not `hooks/` (Fable and KISS).

Coder's reading. Six rows: four converge (F1, F2, F6 DROP; F5 WANT, narrowed) and two
diverge. On F3 the question is how strongly: NEED or WANT, and inside or outside the
resident guards file. On F4 the coder's draft is the only one not to drop the court. In
light of the seats, the coder's reduced variant (one other-family materiality seat) is
close to the KISS seat's fallback ("if a smelt review is wanted, add one gaze brief"),
which does not require another family; Astra's check disputes it. That variant is a new
proposal, not the memo's follow-up.

## Advisor check of the draft: GPT-6 Astra, row by row

A separate call, made after the three reviews and the table above existed:
`gpt-6-astra` at reasoning effort high (OpenAI). The codex session header reported it;
the session was `01a1c24c-5093-7692-b578-3dc3ee6c5726`. It was given this record and the
memo, and asked AGREE or DISAGREE with the coder draft column, row by row. It is the same
model as the step 2 seat, so it is not independent of review 2. Answer as returned:

| # | AGREE/DISAGREE | Your verdict | Why |
|---|---|---|---|
| F1 | AGREE | DROP | The label misstates AGENTS.md’s project scope. Documenting actual scope and precedence helps; calling this file the constitution does not. |
| F2 | AGREE | DROP | Existing non-override language already states the operative constraint. The French label adds neither enforcement nor a decision rule. |
| F3 | AGREE | WANT | An enforcement inventory helps, but a maintained column in resident guards is optional. Correct false enforcement claims now; any inventory should distinguish operating modes, partial coverage, and bypasses, with dated evidence. |
| F4 | DISAGREE | DROP | Reducing three mandatory seats to one retains an unproven recurring requirement. The KISS fallback allows a review when warranted; it does not justify another-family materiality review on every consolidation. Use existing review, with briefs matched to demonstrated risks. |
| F5 | AGREE | WANT | Dated evidence and a recheck method help volatile host facts. Keep this lightweight, permit authoritative sources where commands cannot establish the fact, and remove the standing chamber. Rechecking remains useful without institutional machinery. |
| F6 | AGREE | DROP | The cited ticket is closed, and adopting both sections would bundle useful freshness practices with an unsupported review structure. Any remaining requirement should stand on its own justification. |

Missing follow-up: NEED—correct or explicitly supersede the memo’s stale claims and contradictions, especially authority scope, the memory-based read-back exemption, review independence, and merge versus author acceptance.

Summary: AGREE on F1, F2, F3, F5 and F6; DISAGREE on F4, where it would put DROP, as all
three seats did. It names one candidate follow-up the table lacks: correct or supersede
the memo's stale claims. Editing the memo is the author's call under the cooldown; this
run did not edit it.


## Review 1: Fable (`claude-fable-5-2`, Anthropic), as returned

reviewer: model=claude-fable-5-2

### Overall verdict
KEEP, TRIMMED. Three pieces earn their place: the "where does new knowledge go" list (§1), the enforced-versus-declared table (§3), and the fact-versus-ruling split with dated facts (§5). The rest relabels what `rules/workflow.md`, `rules/guards.md` and the skills already say, and the metaphor has started generating institutions (a three-chamber court) with no named recurring defect behind them. Ten days after writing, the memo already carries about ten stale claims, two of them on its headline labels (constitution, judicial independence). A text that ages this fast should stay an explanatory note in `design/`, not be written into resident files. Keep §1's routing list, §3's table and §5; cut the constitution label, the powers table and the court.

### Metaphor: real work versus decoration
- **Hierarchy of norms**: real work in part. The routing list tells an agent where a piece of knowledge goes, and the "rule readable without memory" test catches an error. The nine-row French ladder is decoration; `rules/README.md` already states the working sentence in one line.
- **Separation of powers**: decoration. The executive writes the skills that define the courts, writes the hooks, and launches the judges; the one concrete independence claim (self-only counts as no review) has been reversed. The useful residue is one sentence: a rule change does not ride in a project merge request.
- **Ordre public and force publique**: the labels are decoration, since `guards.md` already says nothing overrides it. The distinction underneath (a prompt declares, only a mechanism refuses) does real work: it shows that three of the listed guards have no enforcement.
- **Memory court**: metaphor overreach. "Case law needs a court" is an inference from the analogy; the evidence is one PR, which the existing process caught. It also conflicts with `workflow.md`: "a new round, seat or guard answers a named risk, not a reflex".
- **Facts versus case law / registries**: real work. The two age differently, and "date plus probe" is an actionable check. The word "registry" is optional.
- **MOA/MOE**: decoration here. It already lives in `workflow.md` § Posture; §6 restates it and adds only "merge is the réception".

### Follow-ups: need, want or drop

| # | Follow-up | Verdict | Reason |
|---|---|---|---|
| F1 | AGENTS.md states that it is the constitution | DROP | AGENTS.md now declares itself harness-only bylaws (ticket 1412); the statement would be false. |
| F2 | `rules/guards.md` names itself ordre public | DROP | Vocabulary only; the file already says no rule or skill overrides it. |
| F3 | `rules/guards.md` gains the enforcement column | WANT | Real gap, but keep the table outside the resident file; "declared only" there advertises non-enforcement. |
| F4 | The memory court: three gaze chambers on every smelt merge request | DROP | No recurring defect named; three seats per run; ticket 1350's census shows working sessions rarely read repository memory. |
| F5 | Registry facts carry date and probe; materiality chamber re-runs probes | WANT | Dating facts is cheap and useful; probes fit host facts only; the chamber re-run falls with F4. |
| F6 | Ticket 1350 takes sections 4 and 5 as its frame | DROP | Ticket 1350 closed 2026-11-01 (PR #2170) on a different question; nothing left to frame. |

### Errors or stale claims
- §1, §2, §7: AGENTS.md as constitution binding "every agent, every runtime". Its header now reads "the harness repository's own bylaws, read only when a session works on the harness itself"; law for every project lives in `rules/`.
- §1: the constitution row lists the project and memory boundaries; both live in `rules/guards.md`. §2 attributes the crystallisation clause to AGENTS.md; it is in `guards.md`.
- §1 (twice) and one more place: `conception/` no longer exists; the directory is `design/` (ticket 1477), where the memo itself sits.
- §2: "a `seats: self-only` gaze record counts as no review". `skills/merge/SKILL.md` now says it "is a review like any other" (author ruling 2026-11-01), so "a writer never judges its own work" (§2, §7) no longer describes the system.
- §3: "~256K tokens"; `guards.md` says 230K.
- §3: lists three prohibitions; `guards.md` has four. "Skill load is not write authorization" is a clause of the project-files guard, and the memory-stays-in-its-repository guard is missing from the enforcement table.
- §3: `guard-destructive-bash.sh` is listed under hooks but lives in `scripts/` (a PreToolUse hook); `hooks/` holds only git hooks.
- §1: "Loi ... naming no forge or vendor". `rules/claude-code.md` and `workflow.md` § Cross-project name Claude Code, Codex and Pi; I found no forge name, so only the vendor half is overstated.
- §3: "enforce on padme and doudou" is an undated host fact with no probe, against §5's own discipline; the hook's default mode is `warn`.
- §4: "the court is a gaze configuration". Gaze posts one result (REVIEWED / FINDINGS / ESCALATE); per-claim confirm/amend/strike with kept dissent is a new output format, not a configuration.
- §4 and follow-up 2: "price to confirm in ticket 1350" and "ticket 1350 takes sections 4 and 5" point at a closed ticket.
- Status line: "proposed ... binds nothing until the author says so" is stale against the acceptance.
- Internal: §1 says each layer yields to those above and places `guards.md` inside Loi; §3 makes it non-derogable above other rules, a rank the table does not have.
- Not verifiable from the cited files: the PR #1975 "redo" account.
- Verified as stated: yawn check 14 `ok (reasoned)`, verify-gate's two rounds, the `hooks/reference-transaction` header, the pgrep clause in `rules/coding-bash.md`, and the existence of the 1366 journal path (not opened).

## Review 2: GPT-6 Astra (`gpt-6-astra` @high, OpenAI), as returned

### Overall verdict

KEEP, TRIMMED. The memo earns its place through practical distinctions: binding instructions versus advisory memory, declared prohibitions versus enforcement, and historical episodes versus current facts. Its constitutional hierarchy misstates AGENTS.md’s scope, while its memory court turns useful review questions into an insufficiently justified standing institution. Existing smelt requirements already cover provenance, coherence, and the prohibition on promoting memory into rules; the memo does not establish why every consolidation needs three reviewers. Keep the placement guidance and enforcement inventory, correct the authority model, and treat additional review as a proportionate experiment. Acceptance as doctrine should not automatically authorize its proposed machinery.

### Metaphor: real work versus decoration

- **Hierarchy of norms — real work, with corrections:** tells agents where knowledge belongs and prevents advisory memory overriding rules; the proposed ordering mishandles scope and local exceptions.
- **Separation of powers — real work:** distinguishes proposing rules, authorizing them, implementing changes, and reviewing evidence; these distinctions do not require separate institutional machinery.
- **Ordre public and force publique — mixed:** *ordre public* renames existing non-overridable guards; distinguishing declarations from actual enforcement exposes consequential gaps.
- **The memory court — mostly decoration:** its three questions are useful review dimensions, but naming chambers supplies no evidence that three standing seats improve decisions.
- **Facts versus case law / registries — real work:** different aging mechanisms justify different checks; command probes cannot establish every preference, convention, or historical fact.
- **MOA/MOE — mostly decoration here:** repeats the existing workflow posture without adding a decision rule; equating merge with owner acceptance creates ambiguity.

### Follow-ups: need, want or drop

| # | Follow-up | Verdict | Reason |
|---|---|---|---|
| F1 | AGENTS.md states that it is the constitution | DROP | Misstates a project-scoped file’s authority; document scope and precedence directly. |
| F2 | `rules/guards.md` names itself ordre public | DROP | Existing non-override language already does the work; the French label adds no operational distinction. |
| F3 | `rules/guards.md` gains the enforcement column (each prohibition names its mechanism or says "declared only") | NEED | Prevents false assurance; record partial coverage, operating mode, and bypass limits alongside each mechanism. |
| F4 | The memory court: three gaze chambers (constitutionality, materiality, coherence) on every smelt merge request | DROP | Mandatory seats duplicate existing checks without demonstrated benefit; select independent review according to specific risks. |
| F5 | Registries: registry facts in memory carry the date established and a probe command; the materiality chamber re-runs probes | WANT | Useful for volatile operational facts; allow authoritative sources instead of commands and avoid dependence on a standing chamber. |
| F6 | Ticket 1350 (memory stores design) takes sections 4 and 5 as its frame | DROP | Borrow justified requirements individually; adopting both sections would prejudge storage design and mandate an unvalidated review structure. |

### Errors or stale claims

- Section 1 makes harness AGENTS.md bind every project and runtime; AGENTS.md explicitly scopes itself to the harness and assigns shared policy to `rules/` or skills.
- Sections 1 and 7 point doctrine and design rationale to `conception/`; AGENTS.md names `design/`, where this memo resides.
- “Each layer yields” conflicts with the table’s reasoned local derogations; `skills/yawn/SKILL.md` check 14 explicitly accepts justified local overrides.
- Section 1’s worked example says memory establishes “a push by commit id needs no read-back,” contradicting its non-overriding-memory principle and `rules/git.md`’s unqualified forge read-back requirement.
- Section 2 says high-risk changes *need* another model family; current `rules/workflow.md` says they *prefer* such a panel.
- Section 3 gives the context threshold as approximately 256K tokens; `rules/guards.md` specifies 230K.
- Section 3 overstates the main-update guard’s coverage: `hooks/reference-transaction` documents a hooks-path bypass and an unrefusable deletion path.
- “A court can only rule after” conflicts with the memo’s own classification of before-merge gates as judiciary.
- Section 4’s “There is no test to run” is too categorical: smelt requires mechanically checkable links, provenance, and index limits, alongside substantive source judgments.
- Sections 6–7 conflate merge with owner acceptance while forbidding executive acceptance on the owner’s behalf; delegated landing and reserved author judgment need separate definitions.

Review limitation: a runtime hook automatically injected unrelated gaze memory notes after a permitted skill read. I opened no memory file and excluded those notes from the assessment.

## Review 3: KISS (`claude-opus-5-5`, Anthropic), as returned

reviewer: model=claude-opus-5-5

### Overall verdict
VOCABULARY ONLY.

Almost every frame gives a French legal name to something the harness already does. Rules already exclude forge names. `rules/guards.md` already says "no other rule or skill overrides them". Brood and guards.md already set the crystallisation boundary ("explicit user request naming the destination"). Gaze already runs panels, and verify-gate already caps review at two rounds. The memo has one test that tells an agent where new knowledge goes (section 1), and one gap it names honestly (the "declared only" rows). Both fit in a few lines of an existing file. The only new mechanism it proposes is the three-chamber memory court, which adds three seats to every smelt run on the strength of one failed consolidation (PR #1975). That failure was caught ad hoc, and the author closed the PR: the existing review already worked. The memo also carries several stale claims, one of which contradicts a 2026-11-01 author ruling. That is the metaphor's risk in practice: the story reads coherent while the facts drift.

### Metaphor: real work versus decoration
- **Hierarchy of norms**: partly real work. The "where does new knowledge go?" list and the rule "a rule must stay applicable without memory" change where an agent writes. The nine-row table naming each layer is decoration.
- **Separation of powers**: decoration. "Writer never judges own work", decorrelation and two rounds then appeal already live in route/decorrelation, gaze and verify-gate. The bullet about self-only is now false (see Errors).
- **Ordre public and force publique**: the label is decoration, since guards.md already declares itself the floor. The idea of a prohibition being "enforced by X / declared only" does real work: it shows which floor rules nothing enforces.
- **Memory court**: real work only as a proposal, and not justified yet. It would change the smelt process, but the evidence is n=1, and smelt already says (line 176) that review of its merge request is the review.
- **Facts versus case law / registries**: partly real work. "A fact carries its date and a way to re-check it" is a useful memory-writing habit. The cadastre and état civil framing is decoration.
- **MOA/MOE**: decoration here. `rules/workflow.md` § Posture already holds it, and section 6 restates it.

### Follow-ups: need, want or drop
| # | Follow-up | Verdict | Reason |
|---|---|---|---|
| F1 | AGENTS.md states that it is the constitution | DROP | Label only. Nothing an agent does changes, and AGENTS.md does not list the "powers" the memo assigns it. |
| F2 | `rules/guards.md` names itself ordre public | DROP | Its header and opening line already say nothing overrides it. Pure relabel. |
| F3 | `rules/guards.md` gains the enforcement column | WANT | Honest gap map, but all four guards rows say "declared only", which signals that no mechanism is wanted. One line or none. |
| F4 | The memory court: three gaze chambers on every smelt merge request | DROP | One failed smelt, caught without a court. Three seats per run cost more than the risk. Use an ordinary gaze with a brief. |
| F5 | Registry facts carry a date and a probe; the materiality chamber re-runs probes | WANT | Adding a date and a probe is a cheap habit for host facts. Re-running probes needs the court, so drop that half. |
| F6 | Ticket 1350 takes sections 4 and 5 as its frame | DROP | It would tie a stores design to an unproven court and a metaphor. Let 1350 pick its own frame. |

### Errors or stale claims
- The Doctrine row and the routing list say memos go in `conception/`. That directory does not exist: AGENTS.md:26 puts design history in `design/`, where this memo itself sits.
- Section 3 says "split work beyond ~256K tokens", but `rules/guards.md` says 230K.
- Section 2 says "a `seats: self-only` gaze record counts as no review". `skills/gaze/SKILL.md`:140-143 says a self-only result "is a valid review" (author ruling 2026-11-01).
- `guard-destructive-bash.sh` is presented under hooks. It lives in `scripts/`, not `hooks/`.
- The status line ("proposed… binds nothing until the author says so") is stale, given the author has since accepted the memo.
- The merge gate is listed both as judiciary (section 2, Judiciary row) and as force publique (section 2 table and section 3). The memo's own separation does not hold.
- The constitution row claims AGENTS.md holds "the powers". It does not: AGENTS.md covers routing, tickets, memory, the catalog and profiles.
- Section 3 lists three guards prohibitions. guards.md has four bullets: the memory boundary is left out.

### Drop, merge, or vocabulary only
- Hierarchy table (section 1): vocabulary only. Merge the "where does new knowledge go?" list and the "rule readable without memory" principle into `rules/README.md`, or AGENTS.md § Project memory, as about six lines.
- Worked example 1366: drop it from doctrine. It already lives in memory.
- Separation of powers (section 2): vocabulary only. Its content already sits in route/decorrelation, gaze and verify-gate.
- Ordre public naming (section 3, F2): vocabulary only.
- Enforcement column (section 3, F3): merge as a short "Enforced by" note per bullet in guards.md, or drop.
- Memory court (section 4, F4): drop. If a smelt review is wanted, add one gaze brief to smelt, with per-claim confirm/amend/strike, and no new process.
- Registries (section 5, F5): merge "date plus re-check command for host and machine facts" as one line into smelt's or roar's capture guidance. Drop the chamber.
- MOA/MOE (section 6): drop. `rules/workflow.md` § Posture covers it.
- "How the frames meet" (section 7): merge one sentence into workflow.md or guards.md: "a rule change does not ride inside a project ticket's merge request without the author's explicit word". It is the only new rule in that section. Drop the rest.
- F1 and F6: drop.
- The memo itself: keep it in `design/` as history, fix the stale claims or mark it superseded, and do not cite it as binding doctrine.
