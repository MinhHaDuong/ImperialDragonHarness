# Guichet triage trial: blind replay on 27 real cases

Run 2026-11-12 for `design/2026-11-12-guichet-inter-repo-dialogue.md`, at
the author's request ("find more real cases, and run by hand"), before
deciding whether to build C1.

**Question.** Would a receiver-side triage step, applied when a
cross-project report was filed, have changed what happened, compared with
the status quo (the report filed as an ordinary ticket and handled when
someone got to it)?

**Result.** Over 25 judgeable cases: 19 no change, 3 small or partial
gains, 3 harms; 2 unjudgeable. Two of the gains (G2, H3) were also found
by the first owner read, within 26 minutes to an hour; the third (K-H1)
was partial, the triager missing the ruling the author applied a day
later. The evidence does not support building C1.

## Method

| Step | Who | Independence |
|---|---|---|
| case sweep (21 new cases, read-only over the three receivers' stores and the askers' journals) | Claude, pinned `sonnet` | — |
| blind triage, four batches | Claude, pinned `opus` (advisor tier, author ruling) | each case alone; report as first filed; receiver as a detached checkout at the parent of the filing commit; outcome files withheld |
| judgment against real outcomes | Claude Fable | another model; live repositories readable for verification |
| spot verification of the three claims the conclusion rests on | the drafter (claude-opus-5-5) | — |

Blindness breaches reported by the triagers: P3 (one `git log --all`
showing later subjects, not used) and K-P1 (later history seen; also a
replay artifact). Reports bundling several tickets (H1, H3, H5, P2) were
triaged as one case.

## Cases

Report texts are recoverable with `git show <filing commit>:<ticket path>`
in the receiver's repository. K-* are the six cases already in the design
note's § 2.

| id | receiver | ticket | asker | filing commit |
|---|---|---|---|---|
| K-H1 | harness | 1522 | climate-finance-het | `3f4357f0f8b7` |
| K-H2 | harness | 1541 | climate-finance-het | `9f2fa5cd0ffa` |
| K-G1 | git-erg | 0313 | JETP-observer | `118933d91afa` |
| K-G2 | git-erg | 0311 | JETP-observer via author | `a066f1c0d221` |
| K-P1 | padme | 0086 | arena | `6f733722ee43` |
| K-P2 | padme | 0110 | git-erg session | `2a0b6bf09eda` |
| H1 | harness | 1355 (tickets/1355-consumer-projects-get-no-after-merge-run.erg), 1356 (tickets/1356-gaze-close-reads-a-real-panel-as-seats-s.erg), 1357 (tickets/1357-review-and-gate-worktrees-blocked-by-too.erg), 1358 (tickets/1358-verify-adherence-fails-in-a-project-that.erg) | DOIfetch interface session (raid f9e483), via the harness inter-project protocol | `bf71b213ac34` |
| H2 | harness | 1471 (tickets/1471-verify-gate-cannot-clear-a-host-specific.erg) | JETP-observer night raid e34cf5 (padme), session jetp-raid-e34cf5 | `cd3fb22466d9` |
| H3 | harness | 1492 (tickets/1492-ticket-only-prs-carry-a-self-closing-tic.erg) | ~/CNRS session running a 14-repo housekeeping sweep (siblings 1493-1496 in the same commit a7b3c098f) | `a7b3c098f26a` |
| H4 | harness | 1474 (tickets/1474-on-end-sh-deletes-the-scratch-dir-on-cle.erg) | sen-causal-reading session on padme (claude) | `2ddc4bb07007` |
| H5 | harness | 1101 (tickets/1101-dream-carry-verified-quotations-and-loca.erg), 1102 (tickets/1102-rename-dream-to-hoard-off-the-native-aut.erg), 1103 (tickets/1103-rename-healthcheck-to-yawn.erg) | sen-causal-reading session (nominations, 2026-10-15) | `f0a40bc01280` |
| H6 | harness | 1411 (tickets/1411-incident-report-two-gaze-answers-without.erg) | arena repository session (incident of 2026-10-31, branch fix/f1b-production-port), written at the author request as a facts-only report | `e682f39db6ef` |
| H7 | harness | 1421 (tickets/1421-raid-skill-say-the-blind-spot-pass-is-pa.erg), 1426 (tickets/1426-pi-adapter-installs-no-agents-for-the-su.erg) | arena session (arena ticket 1111, raid 4f385e and Q3 smoke leg 0338-f1b) | `9043ffd91cee` |
| H8 | harness | 1380 (tickets/1380-interactive-sessions-land-prs-with-no-wr.erg), 1381 (tickets/1381-close-and-clean-result-line-does-not-nam.erg) | padme interactive Claude Code session (six landings, padme PRs #175-#182) | `e50bb5ce70f5` |
| H9 | harness | 1305 (tickets/1305-gaze-records-a-first-review-as-delta-whe.erg) | padme session (PR #133, 2026-10-28), filed by the author | `c8137957737e` |
| H10 | harness | 1458 (tickets/1458-setup-copy-check-refuses-a-directory-lis.erg) | JETP-observer session (PR #246, ticket 2102); claude | `09e0fea22096` |
| H11 | harness | 1472 (tickets/1472-retire-the-cross-pr-ticket-collision-gat.erg) | git-erg session (git-erg ticket 0306, PR MinhHaDuong/git-erg#386, raid 797d07) | `55cae3449c4c` |
| H12 | harness | 1478 (tickets/1478-tracker-roll-out-required-erg-id-claims.erg) | git-erg session relaying an author decision (required ID claims, git-erg 0306/0307) | `e2c0b0fc2957` |
| H13 | harness | 1513 (tickets/1513-move-the-doifetch-pin-from-v0-2-0-to-v0.erg) | DOIfetch interface session (cut v0.3.0) | `3da451c3c113` |
| G1 | git-erg | 0242 (tickets/0242-hook-template-agnostic-remediation-text.erg) | harness session, from harness ticket 0231 (cross-repo) | `352f5801dba6` |
| G2 | git-erg | 0243 (tickets/0243-erg-update-prune-orphan-ticket-skills-from-old-installs.erg) | AEDIST (transcribed from AEDIST tickets/0355, filed 2026-05-27 when that agent had no git-erg access), carried by a harness/Claude session | `2807b8e16574` |
| G3 | git-erg | 0140 (tickets/0140-erg-next-id-cross-worktree.erg) | aedist-technical-report (original AEDIST ticket 0186, filed by HDMX-coding-agent after a live collision in raid-sota-adapters), re-filed to git-erg | `a1183db73cd5` |
| G4 | git-erg | 0314 (tickets/0314-erg-log-refuses-archived-tickets-with-a.erg) | climate-finance-het raid of 2026-11-11 (harness-governed session) reported through the author | `eea5e8189c7e` |
| H14 | harness | 0215 (tickets/0215-upstream-git-erg-id-allocation-races-acr.erg) | AEDIST session (collision of ticket 0421, 2026-06-04), filed in the harness as a tracker for an upstream request | `f91e663e73ec` |
| P1 | padme | 0087 (tickets/0087-emit-replacing-llm-availability-notifica.erg) | arena session (Arena watchdog, scripts/arena-watchdog.py), request by the author, filed by Codex | `bddbcad95adf` |
| P2 | padme | 0076 (tickets/0076-rename-memory-hoard-md-to-smelt-md-after.erg), 0077 (tickets/0077-move-review-attribution-records-out-of-m.erg) | harness session, on the author instruction (renames and moves of harness tickets 1352 and 1347) | `0d6c6f902042` |
| P3 | padme | 0109 (tickets/0109-migrer-le-magasin-de-tickets-vers-les-cl.erg) | git-erg session request (required ID claims), carried by the harness rollout tracker 1478 | `2a0b6bf09eda` |

## Triage brief used (draft guichet profile)

# Triage brief (draft guichet profile, blind replay)

You are the triager of a receiving repository. Another project's session has
filed an intake: a report about the receiving repository (a bug, a problem,
a request). You decide what the receiving repository should do with it. You
do not fix anything. You never take the report's framing as fact.

#### What you may read

- The report, exactly as filed (below).
- The receiving repository **as it was just before the report was filed**:
  a detached checkout at that commit, given below. Read its files, its
  `tickets/` (open tickets; closed ones in `tickets/closed/` or in history),
  `memory/`, `design/`, `rules/`, and `git log` / `git show` **from HEAD
  only**. Do not read any ref, branch or file that is later than HEAD, do
  not run `git fetch`, and do not read the current state of any other
  checkout of this or another repository. If you are unsure whether
  something is later than HEAD, do not read it.

#### What to decide

Check, in this order:
1. **Facts against framing.** Separate what the asker observed (commands,
   outputs, paths) from what it concluded (cause, fix, design). Verify each
   observation you can against the repository. Mark each conclusion as
   supported, contradicted (cite the rule, decision, memory or code that
   contradicts it) or unchecked.
2. **Duplicates and overlap.** Search open and recently closed tickets and
   the git log for the same defect or request. An existing open ticket
   covering it means AMENDED, not NEW.
3. **Ownership.** Is this the receiving repository's to fix, or another
   project's (the asker's own, or a third one)? Name the owner.
4. **Standing rulings.** Does the request run against a recorded author
   ruling, rule or design decision? Cite it.

Then output exactly one verdict:
- `NEW`: give the ticket you would file, in the receiving repository's
  voice: title, context (facts only), exit criteria. State any correction
  to the asker's premise inside it.
- `AMENDED <ticket id>`: the existing ticket and the one log line you would
  add.
- `PUSHBACK <reason>`: not ours (name the owner), already fixed (cite the
  commit), against a ruling (cite it), or not a defect.
- `QUESTION <text>`: only if one answer from the asker would change the
  verdict; say what each answer would lead to.

#### Output format (JSON, then nothing else)

{"case": "<id>", "verdict": "NEW|AMENDED|PUSHBACK|QUESTION",
 "target": "<ticket id or owner or null>",
 "observations_checked": [{"claim": "...", "status": "verified|contradicted|unchecked", "evidence": "<path or sha>"}],
 "premise_corrections": ["..."],
 "duplicates_found": ["<ticket id: title>"],
 "ticket_or_line": "<the ticket you would file, the log line, the pushback reason, or the question>",
 "confidence": "high|medium|low"}


## Judgment

Date: 2026-11-12. Judge: one read-only pass over 27 cases (report, blind verdict, outcome), with
spot checks in the live repositories. Classes: CHANGED-BETTER, SAME, CHANGED-WORSE, MIXED,
UNJUDGEABLE. "Correction correct?" judges the triager's premise corrections, not its verdict.

Rule applied: CHANGED-BETTER needs a cost seen in the real outcome that the verdict would have
avoided. A correct correction that changed nothing observable stays SAME and is noted.

### Table

| id | receiver | verdict | real outcome | class | what it would have changed | correction correct? |
|---|---|---|---|---|---|---|
| G1 | git-erg | NEW | fixed and closed 4 min after filing | SAME | nothing; the fix (917056b) already left the binary to CI | yes |
| G2 | git-erg | NEW, retargeted to `erg init` | retargeted to `erg migrate`, widened to a repo-wide sweep on author review, PR #303 | CHANGED-BETTER (small) | "update is binary-only" caught at intake: saves one retarget commit and a renamed ticket file. The retarget took 26 min (2807b8e 08:16Z, 6fd3851 08:42Z), not the 1h45 of the outcome file. Against: it proposes `init` hash matching, not `migrate`, and "blast radius may be nil", which the author's widening contradicted | partly |
| G3 | git-erg | PUSHBACK (PEP §6, feature freeze) | implemented (#151, #152); the 3-pass scan is still in `src/go/nextid.go` | CHANGED-WORSE | refuses a fix that shipped and stayed. The cited texts were real (freeze in STATE.md from 3e409a5 to 2026-05-30; PEP §6) and the author refused the same class on git-erg#282 two weeks later, then built claims in November after a survey found about 50 duplicate IDs | partly (paths and skill ownership right; "not git-erg's" overruled by events) |
| G4 | git-erg | NEW | open, untouched | SAME | pre-answers exit criterion 4 (callers: log, label, unlabel, archive, rm); nobody has acted, so no effect to measure | yes (no `show` command at d998683; caller list matches) |
| H1 | harness | NEW x3, PUSHBACK 1358, 1357 narrowed | four fixes, four PRs, 2h13 | CHANGED-WORSE (2 of 4 tickets) | 1358: pushback on "fails by design"; the harness reversed that design the same night (30122cebd) and the skip still stands. 1357: sends the `.venv` half to DOIfetch; the harness fixed it itself (3948d6cba, the gate's own venv). 1355 and 1356 same | 1358 no (fact right, disposition overruled); 1357 no; 1355 yes |
| H2 | harness | NEW (state the rule) | denied with no change; JETP fixed its base 23 min after filing | SAME | leans the right way (the baseline is JETP's) but still asks for skill text and a test that the denial did not add; it did not issue the pushback that happened | yes |
| H3 | harness | NEW, re-aimed at the landing side | raid 4afdb3 verified the premise 1h later, author decisions, criteria reworded, PR #2349 | CHANGED-BETTER (small) | at intake: no filing flow exists, a sixth PR (#2050), the next-id timeout, repairs belong to the adopters. These are the four findings of the raid's Verify pass. Saves that pass and one criteria rewrite, under 1h. Its guard was too broad (it would block file-and-close PRs; the raid's Blind-Spot caught that) | partly (four facts yes; guard shape no) |
| H4 | harness | NEW as filed | fixed, PR #2292, 1h37 | SAME | nothing | yes |
| H5 | harness | NEW x3 | shipped; hoard renamed smelt two weeks later | SAME | repeats the report's own caveat on the hoard reservation; did not foresee the reversal | yes |
| H6 | harness | NEW plus a fix criterion | read 4.6h later, same cause found, 1418 filed | SAME | same diagnosis (`seats_claims` regex) 4.6h sooner, one ticket instead of two; missed related 0870 | yes (matches the 1411 log) |
| H7 | harness | NEW 1426; AMENDED 1417 for 1421 | both fixed standalone in under 1h | CHANGED-WORSE (mild) | folding 1421 into 1417 parks a three-line wording fix for 9 days: 1417 closed 2026-11-10 with most criteria dropped | partly (overlap real; disposition costly) |
| H8 | harness | NEW x2 as written | fixed, with another remedy for 1380 | SAME | nothing | none made |
| H9 | harness | NEW as written, "spec §4 stands" | author deleted the scope label and the carried chain | SAME | same verdict; the added constraint pointed away from the author's ruling | no (the "must keep §4" part) |
| H10 | harness | NEW as written | fixed, PR #2239, 2h50 | SAME | nothing | none made |
| H11 | harness | NEW, drops the .gitignore precondition | fixed next day, PR #2297 | SAME | removes a no-op step | yes (`!tickets/**` at .gitignore:57 of 6775d51; no .gitignore commit for claims) |
| H12 | harness | NEW tracker, author-confirm gate, children as tickets | rollout started at once, done in 6.6h | SAME (friction risk) | the gate follows `rules/workflow.md` but the author was driving live; it missed the two real frictions (wrong recipe step 2, the `--no-verify` reversal) | partly |
| H13 | harness | NEW as filed | pin bumped, PR #2421 | SAME | nothing | yes |
| H14 | harness | PUSHBACK to git-erg | git-erg#282 wontfix; convention documented | UNJUDGEABLE | the cross-project report was git-erg#282, text not recovered; the replay triaged the harness-side tracker, whose own action 1 is "file upstream". If judged: SAME | yes |
| K-G1 | git-erg | NEW plus a normaliser question | quiet hook, PR #405, 35 min | SAME | the normaliser was never built | yes (`check.go:163`, `:335` at 2f10b8c) |
| K-G2 | git-erg | NEW plus a path-filter criterion | rule dropped (#399); closed 4 min after filing | SAME (latent catch) | correct and never picked up: `rebuild-binary.yml` filters on `src/go/**` then and now. No observed cost avoided; the `--no-verify` reversal untouched | yes |
| K-H1 | harness | NEW, flags the Web API as a new backend | planned on the Web API; author corrected to the local API a day later; split into 1524-1527 | CHANGED-BETTER (partial) | the flag could have brought the transport ruling forward by up to a day. But the verdict stayed NEW with the Web API in the ticket, and it missed the recorded ruling (`memory/topics/host-environment.md:17`, `skills/zotero/SKILL.md:42` at 5c3a8bb) | partly |
| K-H2 | harness | NEW as filed | built, PR #2464 | SAME | nothing | none made |
| K-P1 | padme | QUESTION | corrected in 22 min | UNJUDGEABLE | report and fix arrived in one commit (6f73372); the profile did not exist at the cutoff | not applicable |
| K-P2 | padme | NEW, narrowed to item 1 | same split, fanned out by hand, 33 min | SAME | restates the report's own ownership split | yes |
| P1 | padme | NEW | PR #190, 70 min | SAME | nothing; the replayed text already carried the implementation log (filing commit 686f598 follows the work) | yes |
| P2 | padme | NEW x2 plus a test dependency | both closed in under 40 min | SAME | correct enrichment the worker found unaided: b901a93 changed the test, AGENTS.md and MEMORY.md in the same commit | yes (`tools/test-memory-index.sh:103` at 961dfc8) |
| P3 | padme | NEW as filed | migrated in 8 min | SAME | hedged the upgrade step that was wrong for old binaries; the tracker corrected it within 2 min anyway | yes |

### Counts

27 cases, 2 unjudgeable (H14, K-P1), 25 judged.

| class | count | cases |
|---|---|---|
| SAME | 19 | G1, G4, H2, H4, H5, H6, H8, H9, H10, H11, H12, H13, K-G1, K-G2, K-H2, K-P2, P1, P2, P3 |
| CHANGED-BETTER | 3 | G2 (small), H3 (small), K-H1 (partial) |
| CHANGED-WORSE | 3 | G3, H1 (2 of 4 tickets), H7 (mild) |
| MIXED | 0 | |

Six SAME cases carry a correct correction with no observed effect (G4, H6, H11, K-G1, K-G2, P2).
One SAME case carries a correction the author's ruling overturned (H9).

### Synthesis

1. Triage adds value where a report asserts something checkable about the receiver's own code or
   flow and gets it wrong: G2 (wrong command), H3 (a filing flow that does not exist, a missed
   sixth PR). In both, the first owner read found the same thing within 26 minutes to an hour, so
   the saving is one rewrite or one raid Verify pass.
2. The largest possible saving, K-H1 (a day on the wrong Zotero transport), is the case the
   triager half-missed: it noted a new backend and passed the request as NEW, without citing the
   recorded local-API ruling.
3. Triage adds nothing on well-formed reports, author-driven decisions and rollouts: 19 of 25. The
   median real time to first owner action was already about an hour.
4. Harm comes from PUSHBACK and deduplication against recorded text. The triager invoked a
   standing design against the request three times (G3, H1/1358, H9); each time the owner then
   reversed or deleted that design. It did not predict the one real denial (H2). H7 shows the
   dedup cost: a trivial fix parked behind a slow tracker.
5. The frictions the outcomes record are mostly outside a verdict's reach: fan-out by hand (K-P2,
   H12, H3), filing delay (G2 15 days without access, H2 25h to land), workaround then reversal
   (K-G2), cost falling on adopters (K-G1).
6. The evidence does not support building C1 over the status quo plus small additions: 3 small or
   partial gains against 3 harms in 25, with the gains reproduced by the first owner read.
7. Small additions the cases do support: wake an owner at filing; make the premise check the first
   step of whoever picks the ticket up (raid's Verify already does); if a triage run is kept, limit
   it to enrichment notes and route any ruling conflict to the author as a question, never as a
   refusal.
8. Limits: one triager run per case, one judge with hindsight, a sample of reports that were filed
   and mostly resolved, and outcome files that are not error-free (G2 timing).


## Drafter's verification

- K-H1: at the cutoff, `memory/topics/host-environment.md` already read
  "local API only, never sqlite/Web API/cache (rulings 2026-10-15/16)"; the
  triager did not cite it.
- H1 / 1358: `30122cebd` (2026-10-29T23:59+01:00), "verify-adherence: skip
  with a visible reason when no runner is declared", reversed the design
  the triager's pushback relied on, the same night.
- G2: filed `2807b8e` 08:16Z, retargeted `6fd3851` 08:42Z: 26 minutes (the
  sweep's 1h45 was wrong; the judge's correction holds).

## Limits

One triage run per case; one judge, with hindsight; a sample of reports
that were filed and mostly resolved, so tickets that waited unread are
under-represented (G4 is the only open one).
