# How the harness is governed: norms, powers and roles

Status: doctrine, proposed 2026-10-30 for the author's review. It describes; it
binds nothing until the author says so.
Asked 2026-10-30 in the session that settled ticket 1366: rules carry no
forge names, detail belongs to memory ("Loi vs. Décret d'application vs.
Règlement"), memory is "more like Jurisprudence than Décrets", how this
articulates with MOA/MOE, and whether the memory discussion is a question
of government ("legislative, judiciary, executive"). Revised the same day on
the author's answers: AGENTS.md is the constitution, `rules/guards.md` is
ordre public, case law needs a court of its own, and agents need facts as well as
case law.

Three frames, each answering its own question:
- **Hierarchy of norms**: which text binds, and how strongly.
- **Separation of powers**: who writes, who applies, who judges, who enforces.
- **MOA / MOE**: the contract between an owner and a builder, one project at a time.

## 1. Hierarchy of norms

| Norm | In the harness | Binds |
|---|---|---|
| Constitution | `AGENTS.md`: the powers, the project boundary, the memory boundary, the profiles | every agent, every runtime |
| Loi | `rules/` | every project; a principle readable without memory, naming no forge or vendor |
| Décret d'application | skills, their references, scripts | how a rule is carried out |
| Règlement | configuration: CI files, `.merge-gate.json`, settings | one mechanism's settings |
| Arrêté local | a project's own `AGENTS.md`, `CLAUDE.md`, local skills | that project; a derogation states its reason in place (yawn check 14: `ok (reasoned)`) |
| Contrat | the ticket and its exit criteria | one piece of work |
| Jurisprudence | project memory, case-law part | nobody; it informs interpretation |
| Registres | project, user and host memory, factual part (section 5) | nobody; it informs action |
| Doctrine | `conception/` memos | nobody; it explains |

Each layer yields to the ones above it. A ticket cannot set aside a rule, a
skill cannot contradict one, and memory interprets the law without
overriding it. A rule must stay applicable when memory is unavailable: no
term whose meaning lives only in memory (2026-10-30: "exotic", defined against
a forge's runner image, was replaced by a self-sufficient principle).

Where does new knowledge go? Ask what it is:
- a principle that should hold everywhere → a rule (the legislator's act);
- how to apply a principle → a skill, reference or script;
- a setting → configuration;
- what one piece of work must deliver → the ticket;
- what happened, and how it was ruled → memory, case law;
- what is true now, and how to check it → memory, registry;
- why the system is shaped this way → `conception/`.

Worked example (ticket 1366): "a push by commit id needs no read-back" is
not a rule (too specific, would need a forge-aware exemption), not a décret
(the script already does it), but a case and its ruling: memory
(`memory/journal/2026/2026-10-30-push-by-commit-id-exit-code-1366.md`).

## 2. Separation of powers

| Power | Holder | Acts |
|---|---|---|
| Constituent | the author | `AGENTS.md` |
| Legislative | the author | rules; crystallisation of case law into law (AGENTS.md: an explicit request with its destination) |
| Executive | the MOE: the interface session, team leads, executors | skills, scripts, configuration, the work itself |
| Judiciary | review seats and gates; the author as last instance | gaze, verify-gate, the merge gate, the memory court (section 4); ESCALATE and NEEDS-AUTHOR go up to the author |
| Force publique | hooks, permission rules, the before-merge checks (section 3) | refuses a forbidden act before it happens |

The executive may draft a bill (propose a rule wording) but never enacts it.

The harness already protects judicial independence where it matters most:
- a writer never judges its own work: a `seats: self-only` gaze record counts
  as no review;
- a high-risk change needs a seat from another model family: the judge is
  decorrelated from the executive that produced the change;
- the gate rules on evidence against the contract (exit criteria), never on
  the executive's account of it;
- the gate allows two rounds; a third goes up, like an appeal.

## 3. Ordre public and the force that enforces it

`rules/guards.md` is ordre public: the few prohibitions that no contract,
project or local derogation can set aside (never display credentials, a
skill load is not write authorization, split work beyond the context
limit). Enforcing them falls to the force publique, which is mechanical:
- hooks (for example `guard-destructive-bash.sh`, which refuses a
  self-matching `pgrep -f`; the main-update guard, which refuses a write to
  main);
- the runtime's permission rules and its auto-mode classifier;
- the before-merge checks of the merge gate.

A prompt can declare an order; it cannot enforce one. It raises the odds of
compliance and stops nothing. Only a mechanism refuses before the act, where
a court can only rule after it. So each prohibition should name the
mechanism that enforces it, or say plainly that none does:

| Prohibition | Enforced by |
|---|---|
| never display credentials | declared only (no output filter) |
| a skill load is not write authorization | declared only |
| split work beyond ~256K tokens of context | declared only |
| main is read-only | the main-update guard (enforce on padme and doudou) |
| no destructive shell patterns | `guard-destructive-bash.sh` |

The "declared only" rows are prohibitions with no enforcement: the place to
ask whether a mechanism is possible and worth its cost. The harness's own
doctrine limits that growth: a guard that misfires is deleted before it is
grown, and no guard watches another guard (test-doctor's domain).

## 4. Who makes the jurisprudence: a memory court

Roar records cases: it writes the journal entry about the task it just ran,
as a clerk writes up minutes. Smelt writes consolidated case law, the
equivalent of leading decisions (arrêts de principe). Both are executive
runs. Today the only independent instance is the author, at the very end
(the fifth consolidation, PR #1975, was rejected as "redo").

Smelt's output should be judged, but not as a code change is. There is no
test to run; the evidence is the sources; the verdict is per claim (confirm,
amend, strike), and dissent is kept. Proposed: a court of three chambers,
each a gaze seat with its own brief, run on every smelt merge request.

| Chamber | Asks | Evidence |
|---|---|---|
| Constitutionality | Does the consolidation turn into law (the crystallisation boundary)? Does it cross the project or user boundary? Does it contradict a rule? Does it expose credentials or personal data? | AGENTS.md, rules, ordre public |
| Materiality | Is each fact real and sourced? Are time and money costs right, measured and derived numbers labelled? Was a still-needed fact dropped? Does each registry fact still pass its probe? | journal, commits, measurements re-run where cheap |
| Coherence and integration | Does it contradict other topics or precedents? Is supersession explicit? Does it fit the size caps? Is it navigable from the index? | the whole memory tree |

Gaze already runs panels of seats with roles and rulebooks, so the court is
a gaze configuration with three briefs and a per-claim verdict format. The
materiality chamber sits in another model family than the writer: it is the
one most exposed to a model confirming its own account. The author still
accepts or rejects, reading three rulings instead of a full diff. Roar's
recordings can take a light check from the materiality chamber alone.

Price (to confirm in ticket 1350): about 2 to 3 agent-hours for the briefs
and the smelt wiring; then three seats per smelt run.

## 5. Facts and case law

Law separates questions of fact from questions of law, and the State keeps
registries of fact (cadastre, état civil) apart from its case law. Memory
holds both, and they age differently.

| | Case law | Registry |
|---|---|---|
| Example | "a push by commit id needs no read-back" (1366) | "padme: 32 cores; the hourly snapshot timer is stopped until the HDD arrives" |
| Lifecycle | accumulates, then is consolidated | current state; history in git |
| Ages by | being superseded | going stale |
| Checked by | the court | a probe: a command that re-establishes the fact |

A registry fact carries the date it was established and its probe. The
materiality chamber checks it by re-running the probe, not by reading. The
user store (the author's conventions, the agenda map), the host stores and
much of each project's memory are registries: facts about a party, a machine
or a codebase. Case law is the smaller part.

## 6. MOA / MOE

MOA/MOE is a contract frame, not a constitutional one: an owner (maîtrise
d'ouvrage) commissions a work, a builder (maîtrise d'œuvre) designs it and
directs the companies that build it, the owner accepts it (réception).
In the harness:
- the author is MOA of each project: writes or accepts its tickets, its contracts;
- the interface session is MOE two levels up, governing by intention through
  team leads (`rules/workflow.md` § Posture);
- the executors are the companies;
- verify-gate checks the work against the contract; merge is the réception,
  and the author's acceptance where a ticket asks for it.

## 7. How the frames meet

The author holds several powers at once:
- **Constituent**: writes AGENTS.md.
- **Legislator** for every project: writes the harness's rules.
- **Last judicial instance**: escalations and NEEDS-AUTHOR verdicts come to the author.
- **Project owner** (MOA): one per project, signing its contracts (tickets) and accepting the work.

Holding them together is sound in a system with one principal. It needs one
discipline: each act should be made in the right capacity. A rule
written as legislator reads as general law, not as one project's need. That
is why rules name no forge and carry no project specifics, and why a rule
change does not ride inside a project ticket's merge request without the
author's explicit word.

The MOE is the executive. It may:
- draft décrets (skills, scripts) and règlements (configuration), under the
  law, subject to review;
- propose bills;
- record cases and keep the registries.

It never enacts law, never judges its own work, and never accepts its own
work on the owner's behalf.

## Follow-ups, once accepted

1. AGENTS.md states that it is the constitution; `rules/guards.md` names
   itself ordre public and gains the enforcement column of
   section 3.
2. Ticket 1350 takes sections 4 and 5 as its frame: the memory court, and
   registries with dated facts and probes for the user and host stores.
