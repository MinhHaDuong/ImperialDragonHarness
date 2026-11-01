# Raid Phase 2 (Imagine): what it produced, 2026-07 to 2026-11

Ticket 1417, exit criterion 3. Written for the author, who doubts the phase
was constructive. Method, counts, examples, limits. No recommendation on the
skill design (criteria 1, 2, 4, 5 wait for the author and 1416).

## Sample and method

- Sources: every `## Imagine*` section in `tickets/` and `tickets/closed/`
  at base fc5c4667 (55 sections); raid journal entries under `memory/journal/`
  (25 files mention Imagine); the 100 non-merge commits whose message
  matches "imagine" (2026-04-01 to 2026-11-01; 48 of them in October).
- Excluded: the 10 sections of raid 1f0534 itself (1351, 1403-1405,
  1412-1414, 1416-1418). Sample: **45 sections on 45 tickets**, mean 1.9 KB.
  36 date from 2026-10-20 to 2026-10-31, 9 are older (2026-07-11 to
  2026-10-06).
- Each section read and given one primary class by one reader (a Sonnet
  worker; no second reader). Table at the end.

Classes:

- **E** premise expiry or correction: the section shows the ticket text
  wrong or stale on a fact (renamed skill, code absent, defect elsewhere,
  proposed change would regress).
- **S** scope change proposed: narrowing, dropped items, tracker-only,
  wontfix, a decision handed to the orchestrator.
- **G** grounded confirmation: premise holds, adds file:line locations, a
  simplest path, a YAGNI note or risk class; criteria untouched.
- **R** restatement: the section adds nothing the ticket lacked.

## Headline

| Class | Tickets | Share |
|---|---|---|
| E premise corrected or expired | 9 | 20% |
| S scope narrowed, dropped or split | 6 | 13% |
| G grounded confirmation only | 28 | 62% |
| R pure restatement | 2 | 4% |

- 15 of 45 (33%) changed what a coder would have done: classes E and S.
- **Zero of 44 tickets with checkbox criteria had their criteria edited**
  by the Imagine commit, and none differs between the Imagine commit and
  the ticket's final state (checkbox text compared, state stripped; 1366 has
  no checkbox list). Phase 2 acts through annotations, never through the
  contract. Scope changes happen in the orchestrator's decisions and in the
  coder's reading of the annotation.
- 26 of 45 sections state "premise holds" or equivalent in so many words;
  27 carry a YAGNI or antipattern line
  named rejected library or helper); only 6 mention a Blind-Spot pass.

## Examples

Premise expiry or correction (E):

- 0943: as filed the ticket would have caused a regression. The keystore
  holds no bare `OPENROUTER_API_KEY`; the name is manufactured by the
  mechanism the sibling ticket 0945 deletes. The section produced the
  `--credential-env` design and the dead `--repo-root` sweep.
- 0944: the skill had one file, no script; its exit criteria could not be
  asserted against Markdown, so the ticket had to create the code.
- 0945: corrected the ticket's own framing (the xtrace guard is not
  vestigial), classified the test corpus (delete, keep, mixed), and a
  Blind-Spot finding about an out-of-repo reader of `$KEYS` was checked at
  the call site and ruled no breakage.
- 1232: the model-coherence census call lives inside the file the ticket
  deletes; silent loss otherwise.
- 1283: criterion 3's premise was partly wrong. padme had no after-merge
  record, because `cmd_run_after` raised `AttributeError` before any check
  (ten dead tips masked by a later green record). A different defect.
- 1287: the report blamed nesting; transcripts showed the fork never loaded
  `plan.md`. Cause established, two of three symptoms already fixed by 1267.
- 1348, 1349: the ticket text named `HOARD.md` and the hoard skill, renamed
  to smelt the same week.
- 1366: a third candidate (a local ref race) fitted every observation
  better than the two the ticket carried; reproduced with a bare remote.

Scope change proposed (S):

- 0254: wontfix. The close-and-archive dance failed in about 1 of 150
  merges; one `git add -u tickets/` bullet in `rules/git.md` is the whole
  deliverable. The cleanest case of Phase 2 deleting work.
- 1346: nothing left to execute; children 1353 and 1354 already carry the
  criteria; keep the parent as tracker.
- 1349: PR closes criterion 1 only; the native-store drain is out; the
  criterion 2 run needs author spend and acceptance.
- 1355: only the "reported by lair/yawn" branch of criterion 1 attempted.
- 1292: drop the nits that are not a few lines with an existing test seat.
- 1008: narrowing allowed to assisted mining with no committed pipeline;
  the incumbent's replay run goes to a follow-up.
- (1362 and 1008 chose a subset the ticket itself allowed.)

Grounded confirmation (G), typical: 1291 (swap `sync` for `refresh` in
`gate_state`, one line, side effect on `_save_state` noted), 1288, 1286,
1290, 1394 (hook payload verified by headless probe). Value: file:line
anchors, an existing helper to reuse, a cost estimate, a risk class. Cost of
a wrong guess is low for these; most were small fixes a coder could scope
alone.

Restatement (R): 1036 (rewords the ticket's retirement intent), 1043
(declares that an earlier Imagine, Blind-Spot and Plan already cover it).

## Git history beyond the surviving sections

Surviving sections undercount: tickets split or returned lose or move their
annotation. Subjects of the 100 Imagine commits show at least 10 distinct
scope events: 0024 deferred "not ripe", 0086 cut to fast mode (YAGNI),
0217 narrowed, 0254 wontfix, 1007 reworded with 1006 box 2 moved, 1032
split, 1146 decomposed into 1148-1150, 1252 children 1271-1276, 1297
returned "premise not yet met", 1298 split into 1299-1301. 0336's commit
states the rule: a premise objection is a success outcome of Imagine, not
drift.

Journal evidence of the Blind-Spot pass finding real omissions: the
2026-10-20 raid found 1142 and 1153 already implemented in open PRs (Imagine
passes, before any executor); raid f7fa41's Blind-Spot found
`get_forge(ref="")` returning the none backend; raid 1298's found a
two-step split would leave gaze writing notes. A separate interactive
Imagine on 2026-10-29 (1337-1341, outside raid) found 2 of 5 premises
already cleared. Counted from journal text, not re-run.

## Reading

- Constructive in a third of cases (E+S), including three cases that
  prevented wasted or harmful work (0254, 0943, 1346). The author's doubt
  holds for the other two thirds: 62% confirm a premise and sketch a path.
  That output has value only if the coder would not have found the same
  locations; this audit cannot test it.
- The phase never alters the ticket contract. Its consequential outputs
  (E, S) land in prose a coder or orchestrator must notice.
- Annotation length (mean 1.9 KB) does not separate classes: R sections are
  the shortest, G and E overlap.

## Limits

- One reader, no second coder; class boundaries E/G and S/G are judgment.
- Survivor bias: sections removed or rewritten are invisible (see the git
  paragraph for the compensating signal, which is subject lines only).
- Counts the annotation's claim; a claimed premise gap was not re-verified
  against the tree of its day, and downstream delivery (was the narrowed
  scope what shipped) is unmeasured.
- Sample skews to late October (36 of 45), the period of heavy raiding and
  of routine Blind-Spot use.
- No positive control for the "would a coder have found it unaided"
  question; an A/B of tickets with and without Phase 2 would be needed.

## Per-ticket table

| Class | Tickets |
|---|---|
| E | 0943, 0944, 0945, 1232, 1283, 1287, 1348, 1349, 1366 |
| S | 0254, 1008, 1292, 1346, 1355, 1362 |
| R | 1036, 1043 |
| G | 0984, 0987, 1151, 1230, 1231, 1233, 1234, 1238, 1282, 1284, 1286, 1288, 1289, 1290, 1291, 1294, 1303, 1327, 1347, 1352, 1353, 1356, 1357, 1358, 1360, 1361, 1363, 1394 |
