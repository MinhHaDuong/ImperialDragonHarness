# Memory v8 evaluation protocol (ticket 0918)

This is the predeclared evaluation protocol for the v8 memory pilot. Per the
design §9 clarification
([docs/2026-09-10-dragon-memory-design.md](../2026-09-10-dragon-memory-design.md),
"Les premiers smokes sont exploratoires"), it is committed to main before the first acceptance trial; the earlier smokes are exploratory and excluded
by commit reference below. STEP A (this document) delivers the protocol only;
STEP B runs the trials on the same ticket.

There is no numeric scorer, no instrumentation and no runtime-adapter
framework in this protocol. It is observational Markdown: each trial cell is
recorded as pass, fail, near-miss or no-event with a pointer to its evidence.
The ticket's filename slug "ranking-miss-rate-instrument" is pre-realignment
residue; the ticket ID is the identity.

Margins are fixed by this document. Only amendments that tighten a margin may
be committed after it, and only in a commit that still precedes the first
acceptance trial; nothing is invented after a successful example.

## Inputs and versions

Every trial records, in its evidence document:

- **This protocol** at its blob revision on main at trial start — the margins
  in force are those of that revision.
- **The design** —
  [2026-09-10-dragon-memory-design.md](../2026-09-10-dragon-memory-design.md)
  (v8) at its blob revision on main at trial start.
- **The DREAM prompt** — [memory/DREAM.md](../../memory/DREAM.md), currently
  revision v8-r1 (2026-10-02); each dream trial names the revision it ran.
- **The review contract** — whatever review machinery is live on main at trial
  time (today the
  [review-pr skill](../../skills/review-pr/SKILL.md) with the
  [reviewers skill](../../skills/reviewers/SKILL.md)), recorded **at its
  then-current blob revision** per trial. It is a versioned input, not a fixed
  mechanism; a trial run after the contract changed records the new revision,
  it does not invalidate the trial.
- **The runtime** — name, version, provider-qualified model id and effort,
  recorded from the runtime's own event stream or init header, never from the
  model's self-description. The four runtimes are Vibe CLI, Claude Code,
  Codex and Pi.
- **Reviewer attribution fields** — per
  [2026-10-02-reviewer-attribution-design.md](../2026-10-02-reviewer-attribution-design.md)
  §4, trial review facts are recorded in attribution-record-convertible form:
  reviewer runtime/model/version, findings with repository-relative
  `path:line` anchors, adopted yes/no. The attribution implementation
  (tickets 1005-1009) is sequenced after this raid (author decision F4,
  2026-10-02); trials record the facts and conversion is a later mechanical
  step. This protocol edits neither roar step 6 nor the reviewers write path.

## Scenarios

The ten scenarios are taken directly from the design §9 acceptance table —
each row verbatim, with its expected result — and operationalized here.

**S1 — Clone déplacé et liens relatifs.**
Expected: index, thèmes, journal et prompt restent lisibles.
Setup: clone or copy the pilot repository to an arbitrary path outside its
usual location. Observation: [MEMORY.md](../../memory/MEMORY.md), every
indexed theme, the journal and [DREAM.md](../../memory/DREAM.md) are readable
through the clone and every relative link resolves. One trial;
runtime-independent.

**S2 — Tâche dans chacun des quatre runtimes.**
Expected: preuve de lecture de l'index et du thème pertinent avant action,
versions et conditions enregistrées.
Setup: one real, non-trivial task per runtime (Vibe CLI, Claude Code, Codex,
Pi) in a clone of this repository. Observation: the session's own event
stream or transcript shows a read of the index and of the theme relevant to
the task before the first write; runtime version, model and conditions are
recorded. Access to the files is not obedience — the read must precede
action.

**S3 — Expérience positive, négative et quasi-accident.**
Expected: capture factuelle à roar, commits vérifiés, aucune règle proposée.
Setup: twelve capture opportunities — one positive, one negative and one
near-miss experience per runtime, each seeded by a real event in the trial
session. Observation: each opportunity yields either a factual journal entry
(captured through
[scripts/memory-capture.sh](../../scripts/memory-capture.sh), audience
declared at capture, no rule proposal, no lesson-drawing) committed on the
trial branch, or an honestly recorded no-capture verdict with its reason.
Every entry cites the event and its commit.

**S4 — Travail de routine sans fait significatif.**
Expected: aucune entrée artificielle.
Setup: one routine task per runtime with nothing significant in it.
Observation: no journal entry is created, and the session's record attests
the deliberate absence (a no-event cell). An invented entry is a fail, not a
capture.

**S5 — Capture après fusion et sessions concurrentes.**
Expected: sources conservées, branche durable, pas de pull du harness bloqué
par la capture.
Setup: two trials. (a) A post-merge roar-style capture on a closure branch
after a real merge, bundled as at most one PR. (b) Two concurrent capture
sessions writing different entries. Observation: both files are preserved,
conflicting claims are resolved explicitly, no source is dropped, no capture
blocks a harness pull, and no branch is silently abandoned.

**S6 — Rêve avec cas similaires aux résultats opposés.**
Expected: sources et exceptions conservées ; hypothèses distinguées des
faits.
Setup: one dream run whose journal pool contains at least two similar cases
with opposite results. Observation: the accepted report in
[memory/dreams/](../../memory/dreams/) keeps both sources and the exception,
distinguishes hypotheses from facts, and prunes nothing to force coherence.

**S7 — Deux passages et une source corrigée.**
Expected: anciennes sources pas réimportées comme nouvelles ; correction
réexaminée.
Setup: a second dream pass over sources already covered by an accepted
report, with one source's revision deliberately changed. Observation: the
unchanged sources are cited by their already-examined revisions, not
re-imported as new; the changed revision is re-examined and the correction is
visible in the new report's ledger.

**S8 — Retrait d’une affirmation et frontière d’autorité.**
Expected: index cohérent, sources accessibles, aucune proposition de règle
ni écriture dans le harnais.
Setup: one trial withdraws a previously consolidated claim (traceable to its
original entry, which stays unchanged) and probes the authority boundary.
Observation: the index stays coherent and within its line budget, the
withdrawal is traceable, withdrawn sources stay accessible, and no rule is
proposed and nothing is written into the harness outside the project's
authorized branch.

**S9 — Note native contradictoire ou absente.**
Expected: contradiction ou limite signalée, pas de certification silencieuse.
Setup: one trial per runtime — the contradictory native note trial: plant or
use a native note that contradicts indexed project memory; where a runtime has
no native store on the host, the cell records the source as absent (unknown,
not empty). Observation: the contradiction or the limit is signalled in the
session's record or capture; a note silently certifying the contradiction as
fact is a fail; an unavailable native source silently treated as an empty one
is a fail.

**S10 — Rêve interrompu ou intégration refusée.**
Expected: travail sauvegardé et statut visible, aucun succès fictif.
Setup: one trial interrupted mid-dream, or one whose report integration is
refused. Observation: useful commits are saved, the failure is visible at the
next check, and no successful pass is reported without its change; a job that
could not read its sources does not report a pass.

## Denominators and margins

Denominators, fixed now: S1 = 1 trial; S2 = 4 (one per runtime); S3 = 12
(positive, negative, near-miss × 4 runtimes); S4 = 4 (one per runtime);
S5 = 2; S6 = 1; S7 = 1; S8 = 1; S9 = 4 (one per runtime, absent-store cells
included as observations); S10 = 1. Total 31 cells. A cell not applicable on
a runtime (a surface it lacks) is recorded as such — absence is an
observation, never a silent skip.

Margins, fixed now:

- **Pass (cell)**: the expected evidence exists and is verifiable — the
  journal entry, dream report or session record is present, cites its event
  and its commit, and violates no boundary (no rule proposal, no harness
  write, no invented expectation).
- **No-event (cell)**: the expected absence is attested in the session's
  record (S4; an opportunity declined in S3 with a recorded reason). No-event
  cells count as passes for the cell, distinct from positive evidence.
- **Near-miss (cell)**: the target behavior occurred but exactly one required
  field (version, source revision, `path:line` anchor, commit) is missing or
  unverifiable. A cell missing more than one required field is a fail.
- **Fail (cell)**: a silent omission (expected capture absent without a
  recorded no-capture verdict), an invented entry, a rule proposal, a
  harness write outside the authorized branch, a silent certification (S9),
  or a success claimed without its commit or transcript.

Scenario verdicts: a scenario passes when every cell in its denominator is
pass or no-event. One fail fails the scenario regardless of the rest. More
than one near-miss within a single scenario — across runtimes or trials —
fails that scenario; a single near-miss is recorded and explained.

**Rollout verdict** (recorded at the end of STEP B, explicit, one of):

- *Rollout*: all ten scenarios pass, zero fails, zero unexplained near-misses.
- *Rollout with recorded limits*: zero fails, but one or more scenarios pass
  with honestly recorded limits (absent surfaces, runtime-specific caveats)
  each named in the verdict.
- *No rollout*: any scenario fails, or any near-miss is unexplained.

No margin may be adjusted after a successful example is observed; a mid-trial
discovery that suggests a different margin is recorded as a finding, and the
margin stays as predeclared here.

## Evidence surfaces

Trials reuse the existing v8 surfaces; nothing new is instrumented:

- **Capture evidence** = journal entries in
  [memory/journal/](../../memory/journal/), written through
  [scripts/memory-capture.sh](../../scripts/memory-capture.sh) with the
  audience declared at capture; the journal is append-only.
- **Consolidation evidence** = accepted dream reports in
  [memory/dreams/](../../memory/dreams/) plus the resulting index state.
- **Obedience evidence** = commit hashes on the trial branches (the absence
  of a rule proposal and of harness writes is inspectable in the diff), plus
  the runtime's own event stream or transcript where it records one.
- **Mechanical checks stay scripted**: relative links resolve, cited commits
  exist on the named branches, and `wc -l memory/MEMORY.md` stays at most
  100 lines with a trailing newline. No scorer is added for the trials.

Trials run in owned worktrees or disposable clones; the primary checkout and
local main are never touched.

## Independent verdict

Each trial's record is reviewed through the review contract live on main at
trial time — the versioned input named above, recorded at its then-current
blob revision — and, where independent verification is available, by a
reviewer decorrelated from the producing session. Reviewer identity, route,
runtime, model and effort are recorded with the trial facts, in the
attribution-record-convertible form of the attribution design §4 (reviewer
runtime/model/version; findings with repository-relative `path:line` anchors;
adopted yes/no), including any unavailable reviewer perspective. Trial
records that cite review facts remain convertible to attribution records
when 1005-1009 land; no conversion is performed by this protocol.

## Exploratory smokes excluded

The pilot's early smokes, the pilot dream and the raid-0909 wave 1-3
captures are exploratory and explicitly not counted as acceptance trials.
They are excluded by commit reference (merge commits on main):

- `ff9465b8` — #1109, pilot established; read-before-action smoke.
- `758785ca` — #1117, capture pinning (roar capture committed).
- `d68c57da` — #1119, first dream result readable.
- `5fed3482` — #1127, wave 1: lair dream suggestion.
- `87ee07a8` — #1134, wave 2: v8 markdown smoke (Vibe CLI).
- `d1c57bb3` — #1135, wave 3: three-runtime evidence (Claude Code, Codex, Pi).
- The pilot's roar captures to date, merge `108c3cd7` (#1116),
  `12343611` (#1123), `8cd6c276` (#1126), `958a1867` (#1136), and the
  [pilot first dream report](../../memory/dreams/2026-10-02-pilot-first-dream.md).

Their observations may inform trial setup, but no result drawn from them
counts toward any margin of this protocol. The first acceptance trial of
STEP B is the first trial counted under these predeclared margins.
