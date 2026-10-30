# How the harness is governed: norms, powers and roles

Status: doctrine, proposed 2026-10-30 for the author's review. It describes; it
binds nothing until the author says so.
Asked 2026-10-30 in the session that settled ticket 1366: rules carry no
forge names, detail belongs to memory ("Loi vs. Décret d'application vs.
Règlement"), memory is "more like Jurisprudence than Décrets", how this
articulates with MOA/MOE, and whether the memory discussion is a question
of government ("legislative, judiciary, executive").

Three frames, each answering its own question:
- **Hierarchy of norms**: which text binds, and how strongly.
- **Separation of powers**: who writes, who applies, who judges.
- **MOA / MOE**: the contract between an owner and a builder, one project at a time.

## 1. Hierarchy of norms

| Norm | In the harness | Binds |
|---|---|---|
| Constitution | `rules/guards.md` (never display credentials, never edit another project) | every agent, every runtime; nothing overrides it |
| Loi | `rules/` | every project; a principle readable without memory, naming no forge or vendor |
| Décret d'application | skills, their references, scripts | how a rule is carried out |
| Règlement | configuration: CI files, `.merge-gate.json`, settings | one mechanism's settings |
| Arrêté local | a project's own `AGENTS.md`, `CLAUDE.md`, local skills | that project; a derogation states its reason in place (yawn check 14: `ok (reasoned)`) |
| Contrat | the ticket and its exit criteria | one piece of work |
| Jurisprudence | project memory: journal, topics, rulings | nobody; it informs interpretation |
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
- what happened, and how it was ruled → memory;
- why the system is shaped this way → `conception/`.

Worked example (ticket 1366): "a push by commit id needs no read-back" is
not a rule (too specific, would need a forge-aware exemption), not a décret
(the script already does it), but a case and its ruling: memory
(`memory/journal/2026/2026-10-30-push-by-commit-id-exit-code-1366.md`).

## 2. Separation of powers

| Power | Holder | Acts |
|---|---|---|
| Constituent | the author | `rules/guards.md` |
| Legislative | the author | rules; crystallisation of case law into law (AGENTS.md: an explicit request with its destination) |
| Executive | the MOE: the interface session, team leads, executors | skills, scripts, configuration, the work itself |
| Judiciary | review seats and gates; the author as last instance | gaze, verify-gate, the merge gate; ESCALATE and NEEDS-AUTHOR go up to the author |

The executive may draft a bill (propose a rule wording) but never enacts it.

The harness already enforces judicial independence where it matters most:
- a writer never judges its own work: a `seats: self-only` gaze record counts
  as no review;
- a high-risk change needs a seat from another model family: the judge is
  decorrelated from the executive that produced the change;
- the gate rules on evidence against the contract (exit criteria), never on
  the executive's account of it;
- the gate allows two rounds; a third goes up, like an appeal.

### Who makes the jurisprudence?

Here the separation is weakest. Today the executive records its own cases:
roar writes the journal entry about the task that the same session just
executed. Smelt, which consolidates cases into leading decisions, is also an
executive run. The author is the only independent instance, at the end
(accepting or rejecting a smelt PR: the fifth consolidation, PR #1975, was
rejected as "redo").

So the memory discussion is a question of government. It asks who may
write case law, who may consolidate it, and who decides that a precedent is
retired. Options for the memory design (ticket 1350), to price there:
1. keep it as now, the author as sole reviewer of consolidations;
2. a recorder that is not the executor (another seat writes the journal entry from the evidence);
3. a judicial review of each smelt by a decorrelated seat before the author sees it.

## 3. MOA / MOE

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

## 4. How the frames meet

The author holds several powers at once:
- **Legislator** for every project: writes the harness's rules.
- **Constituent**: writes `rules/guards.md`.
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
- record cases.

It never enacts law, never judges its own work, and never accepts its own
work on the owner's behalf.

## Open questions for the author

1. Is `rules/guards.md` the constitution, or should AGENTS.md's guard
   pointer and the project memory boundary also count as constitutional?
2. Who should write and consolidate jurisprudence (section 2, options 1-3)?
3. Should this frame name the user memory (the author's conventions and agenda
   map) and the host memory? Proposed reading: both are case law about a party
   (the author, a machine), not law.
