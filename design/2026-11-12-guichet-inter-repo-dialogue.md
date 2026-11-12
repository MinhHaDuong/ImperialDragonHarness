# Guichet: dialogue first between repositories

Status: proposed

Drafted 2026-11-12 by Claude (claude-opus-5-5) with the author in the loop.
Author rulings are marked **[author]**; everything else is the drafter's
judgment, open to amendment.

## 1. Problem

The cross-project protocol (`rules/workflow.md` § Cross-project work, ticket
1341) makes a ticket written *by the asker* into the *receiving* store the
channel, always. Three things hurt:

- **The ticket is written from outside.** The asker does not know the
  receiving project's rules, memory, open tickets or recent history. Its ticket
  can duplicate an open one, misname the cause, or ask for something the
  receiver's rules forbid. The 1341 evidence already said so: padme engine work
  briefed from an arena session needed two corrections.
- **A dropped ticket waits for someone to read it.** Nobody owns intake: a
  foreign ticket sits in the ready queue until a raid or the author picks it up,
  and the asker never learns whether it was accepted, merged with another, or
  refused.
- **Writing into another store is still writing into another project.**
  `rules/guards.md` carves out tickets as the one exception; the exception is the
  part of the protocol most likely to be wrong.

The author's direction **[author]**: talk first; the *receiving* repository
records, triages and answers with a new ticket, an amended ticket, or pushback.
A dropped ticket stays as the fallback.

## 2. Situation

Read from `origin/main` at `829d7a582`.

**Rule.** `rules/workflow.md` § Cross-project work (from 1341, merged in PR
#1970, 2026-10-29): (1) ticket there, always; (2) tell a live session when
timing matters (agent listing and messaging on Claude Code, `runtime.py wake
send` on Codex, ticket only on Pi); (3) launch a session there only for
authorized urgent work; (4) never edit it from here. `rules/guards.md`: project
files only in the assigned project, elsewhere only tickets.

**Callers.** `skills/roar` step 9 hands a cross-repo tracker update off as one
`erg log` line on the harness tracker, landed by merge request (ticket 1409
fixed roar editing the harness directly). `skills/raid` routes another
project's requests through its ticket store. Commits since 2026-10-29 touching
hand-offs or cross-project records: 39 (`git log --since=2026-10-29 -i -E
--grep="hand-off|from [a-z-]+ session|filed from|cross-project" | wc -l`; a
keyword count, an upper bound on traffic, not a measure of it).

**Transport, per runtime** (`scripts/runtime_wake.py`, tickets 1311, 1316):

| Path | Mechanism | Two-way? | Status |
|---|---|---|---|
| Claude Code → Claude Code, same host | native `ListAgents` / `SendMessage`; idle notice opt-in | yes, receipt reported; held or refused by the receiver's inbound setting (§ 3) | native, not yet used by any skill |
| Claude Code → Remote Control / cloud session | same tools | Remote Control can reply; cloud cannot reply across machines; nothing reports back | native |
| any → Claude Code via `runtime.py wake send` | — | — | NOOP: "no cross-process path has been probed" |
| any → Codex | `codex queue --thread` | queued, never confirmed delivered | in `runtime_wake.py` |
| any → Pi | inbox directory read by `adapters/pi/extensions/idh-wake.ts`, delivered as a user message when idle | inbound only; a reply needs a path back | in `runtime_wake.py` |

So two-way dialogue exists today on exactly one path: Claude Code sessions on
the same host. Every other pair is one-way or unprobed.

**Merge path for ticket-only changes.** `merge-gate.py tier` classifies a
`tickets/*.erg`-only diff as bookkeeping tier: no gate verdict needed, and
ticket-only merge requests are merged right after opening (memory
`feedback_ticketwork_automerge`). A guichet's output is ticket-only, so it
rides the fast track with no special rights **[author]**.

**Routing.** `skills/route/SKILL.md` sends advisor calls to the ASSURANCE tier;
family choice for independence lives in `references/decorrelation.md`.

## 3. State of the art

Sweep run 2026-11-12 by a research subagent (Claude, pinned `sonnet`; web search);
the drafter checked the claims that change the design. Grades: *primary* =
official documentation or specification read; *secondary* = blogs and search
summaries, not checked against a primary source.

**Agent-to-agent protocols.** A2A (Linux Foundation, v1.0.0) is the
surviving standard; IBM's ACP merged into it in 2025 (secondary). Its task
lifecycle has `submitted`/`working`, `input-required`, and terminal
`completed`/`rejected`/`failed`/`canceled`; a send may return at once with a
task in progress, updates come by polling, streaming or webhook, and the
specification itself warns that "messages are not a reliable delivery
mechanism for critical information" (primary:
<https://a2a-protocol.org/latest/specification/>). A2A is an HTTP server
protocol; we found no evidence that Claude Code, Codex or Pi speaks it
natively. MCP is agent-to-tool access, not peer dialogue (secondary:
<https://atlan.com/know/mcp/how-to-choose-mcp-a2a-anp/>).

**Classic multi-agent theory.** The FIPA Request Interaction Protocol
(SC00026H) has the participant answer `refuse` or `agree`, then `inform`
(done) or `failure`; `agree` may be skipped under a reply-by deadline
(secondary summaries:
<https://www.cs.sjsu.edu/~pearce/modules/lectures/abs/jadeweb/fipaIPs.htm>).
The guichet vocabulary maps onto it: ACK = `agree` made mandatory with T as
reply-by; NEW/AMENDED = `inform-done` with the ticket as result; PUSHBACK =
`refuse`; QUESTION = A2A's `input-required`. Contract Net (bidding among many
contractors) does not fit a single desk; we did not retrieve its primary
sources or KQML's.

**Runtime facts.**
- *Claude Code* cross-session messaging (primary:
  <https://code.claude.com/docs/en/cross-session-messaging.md>): the receiver
  reads a message between tool calls, or an idle session starts a turn; it
  replies with `SendMessage` to the carried address, except that cloud
  sessions cannot reply across machines and a cross-machine send without
  Remote Control carries no reply address. A send is *held*, *refused* or
  *delivered* by the receiver's `crossSessionInbound` setting and permission
  mode: a bypass-permissions receiver holds peer messages for human approval
  by default, and held messages in a `-p` session expire after five minutes.
  Per-sender rate limits, dropped identical repeats and a 50-message queue
  throttle loops. A peer message cannot approve a prompt or change
  configuration. No durability across restarts is stated.
- *Codex* `codex queue --thread` appends to a thread's input queue: an idle
  thread wakes, a busy one takes it after its turn; no acknowledgement, no
  reply channel (secondary:
  <https://codex.danielvaughan.com/2026/08/21/codex-queue-inter-session-messaging-codex-cli-v0149-orchestration-automation-agent-to-agent/>;
  no OpenAI documentation found). Matches `runtime_wake.py`'s QUEUED wording.
- *Pi* has no native messaging; community extensions exist: `pi-messenger`
  (shared-folder files delivered as steering prompts), `pi-link` (WebSocket),
  `pi-collaborating-agents` (secondary: <https://pi.dev/packages/pi-messenger>,
  <https://pi.dev/packages/pi-link>). Delivery semantics unverified.

**Organizational analogues.** The ITIL service desk is a single point of
contact whose first line logs, categorizes, prioritizes and diagnoses, then
escalates what it cannot close (secondary:
<https://advisera.com/20000academy/knowledgebase/itil-incident-management-separate-roles-different-support-levels/>).
Team Topologies' *X-as-a-Service* interaction mode asks for a clear interface
and minimal interaction, and treats open-ended collaboration as short-lived
(<https://teamtopologies.com/news-blogs-newsletters/2025/2/21/team-topologies-interaction-modes-breaking-through-common-misconceptions>).
The guichet is the service desk's first line with an X-as-a-Service
interface: a fixed vocabulary and a round cap.

**Messaging reliability.** The transactional outbox gives at-least-once
delivery, so consumers must be idempotent and track processed message ids
(<https://microservices.io/patterns/data/transactional-outbox>). The dropped
ticket is our outbox; the correlation id is the deduplication key.

**Experience reports and failure modes.** A multi-agent failure taxonomy
finds 14 modes, mostly from system design (specification, inter-agent
misalignment, verification) rather than model limits
(<https://arxiv.org/html/2503.13657v3>). Studies of LLM conformity report
that homogeneous groups amplify agreement errors and that models abandon a
correct answer under unanimous peer pressure (secondary, figures from
summaries: <https://arxiv.org/html/2605.00914>,
<https://www.alphaxiv.org/abs/2608.11247.md>). A vendor report on agents
across 75 repositories says agents lose track beyond two or three
repositories (self-reported:
<https://www.mabl.com/blog/how-we-built-a-system-for-ai-agents-to-ship-real-code-across-75-repos>).
LLM issue-type classification reaches good but project-dependent accuracy;
duplicate detection is less settled (<https://arxiv.org/html/2506.00128v1>).

**Searched, nothing found.** Measured outcomes of agents filing issues in
other repositories; LLM accuracy at routing or priority triage; official
`codex queue` documentation; any native A2A support in the three runtimes;
primary sources for Contract Net, KQML and maintainer triage practice.

**What this changes in § 5.** (1) Messages are notification, the ticket
store is the record: every verdict names a ticket or a logged pushback.
(2) The ACK is an application-level message with the correlation id, since
no runtime's transport acknowledges across all pairs. (3) A Claude Code
guichet must accept peer messages without a human hold, or a headless one
silently drops every REQUEST after five minutes. (4) Facts, not agreement:
the guichet triages against its own repository, not the asker's framing,
and the round cap bounds loops.

## 4. Alternative solutions

**A. Status quo plus wording** (most direct). Keep "ticket there, always";
add "for a request that needs the owner's judgment, prefer a live dialogue
first". No new role, no new transport. Leaves the outsider-written ticket and
the unowned intake in place.

**B. Guichet: a reused service-desk session per repository** (the author's
direction). Dialogue first; the receiver writes the ticket. Detailed in § 5.

**C. Asynchronous intake by ticket, triaged on a timer** (different family:
no dialogue at all). Askers drop tickets as today, tagged `incoming`; a
scheduled triage run in the receiving repo (part of `molt`, or its own timer)
reads them, merges duplicates, rewrites them in the house voice, or closes
them with a pushback note, and logs the outcome where the asker's roar or
lair will see it. Works on every runtime today, needs no live peer; loses the
clarifying questions and answers hours later instead of minutes.

**D. Agent-to-agent protocol server** (different family: standard transport).
Each repository exposes an A2A-style endpoint (agent card, task lifecycle,
push notification) served by a small daemon in front of whatever runtime
answers. Uniform across runtimes in principle; in practice a new service to
run, secure and keep alive on padme and doudou, for a handful of messages a
day.

## 5. Synthesis and recommendation

**Pick B, with C as its fallback leg.** B fixes both pains of § 1: the owner
writes its own ticket, and intake has an owner. C is not an alternative to B
but its degraded mode: a dropped ticket is processed by the same guichet the
next time one runs, so the two paths reach one desk.

### Roles **[author]**

- **Asker** exposes facts and observations from its side: what it saw, where,
  with evidence paths. No orders, no edits, no proposed patch to the receiver's
  files. It may say what outcome would unblock it.
- **Guichet** records, converses, triages and decides actions for its side. It
  answers with exactly one verdict:
  - `NEW <id>`: filed a new ticket;
  - `AMENDED <id>`: logged on or edited an existing ticket;
  - `PUSHBACK <reason>`: declined, with why (not ours, already fixed in
    `<sha>`, against rule X, needs the author).

  It does triage only: the work itself goes to `/hunt` on the resulting ticket.
  Its writes are ticket-only, merged on the bookkeeping fast track.

### Dialogue protocol

Every message carries a correlation id the asker mints (`<asker-repo>-<date>-<rand>`)
and a one-line first line naming the kind: `REQUEST`, `ACK`, `QUESTION`,
`ANSWER`, `VERDICT`.

1. **REQUEST** (asker → guichet): id, asker repo and session name (the reply
   address), facts, evidence, what would unblock.
2. **ACK** (guichet → asker) within **T = 5 min [author]**. The ACK is the
   proof the channel is two-way; it promises a verdict, not agreement.
3. **QUESTION / ANSWER**, as many rounds as triage needs, each carrying the
   id. Cap: three rounds, then the guichet decides on what it has.
4. **VERDICT** (guichet → asker): one of the three, with ticket path and merge
   request when one was opened.
5. The asker records the verdict on its side (journal or memory line, or the
   tracker log its skill names) and is done.

**Non-blocking for the asker [author].** The asker sends the REQUEST and goes
on with its own work; the ACK and VERDICT arrive as messages at its next tool
round (Claude Code delivers inbound messages between tool rounds; on Pi the
inbox delivers when idle). It never sleeps or polls for them (memory
`feedback_no_blocking_waits`). It checks once, at its own wrap-up
(roar/lair/end of task), what arrived:

| At wrap-up | Asker does |
|---|---|
| VERDICT received | record it; done |
| ACK but no VERDICT | the guichet owns it; record "pending at <repo> guichet, id X" |
| nothing, and the channel was never two-way | **fallback**: drop a ticket in the receiving store as today, citing the id |

The 5-minute bound decides only whether the fallback is due; the asker
enforces it by timestamp at wrap-up or at its next natural pause, not by
waiting. If the wrap-up comes sooner than T after the REQUEST, the asker
arms one wake (`runtime.py wake arm`) instead of blocking.

**Idempotency.** The guichet keys its records by correlation id: a repeated
REQUEST (asker restarted, fallback ticket also dropped) is answered with the
verdict already given, and a dropped fallback ticket citing an id the guichet
already answered is closed as a duplicate.

### The guichet session

- **One per repository, reused, findable.** Named `guichet-<repo>` so
  `ListAgents` finds it by name. Messages queue while it is busy, so two
  askers at once is safe; its replies keep their correlation ids.
- **Launched by the asker [author]** when `ListAgents` shows none: a session
  in the receiving repository's primary checkout, under that repository's
  rules, memory and gate, with the guichet brief (the profile below) and the
  REQUEST as its first message. The launch itself is the step 3 already in
  the rule ("launch a session there"), narrowed to triage.
- **Accepts peer messages without a human hold.** On Claude Code the
  receiver's `crossSessionInbound` setting and permission mode decide whether
  a REQUEST is delivered, held for approval, or refused; a headless session
  lets held messages expire after five minutes (§ 3). The guichet's launch
  must make inbound delivery explicit. That is a settings change in the
  receiving repository and the author's call: the guichet's only write right
  is ticketwork, and peer messages cannot approve prompts, which bounds the
  risk. Phase 1 probes it.
- **Retires at its context wall.** Past the guards' 230K-token threshold, or
  when idle and older than a day (to be measured), it writes a hand-off note
  into its repository's journal, answers in-flight ids with ACK-and-handover,
  and exits; the next asker launches a fresh one.
- **Processes dropped tickets too.** On start, and when idle, it triages
  fallback tickets in its own store (those citing a correlation id or tagged
  `incoming`), so C's leg reaches the same desk.

### Model and family

- **Effort and tier: advisor (ASSURANCE) [author].** Triage is hard: deciding
  that a foreign observation is a duplicate, not ours, or a symptom of a known
  cause is judgment work. Pin it there, measure, revisit.
- **Family: the one easiest to talk to [author], not dogmatically the
  asker's.** In practice the family whose runtime has a proven two-way path
  with the asker's runtime. Today that means a Claude Code guichet for Claude
  Code askers on the same host (the only two-way path in § 2). A Codex or Pi
  asker reaches no guichet today: its fallback is the dropped ticket, until the
  audit (phase 1) proves a path. The choice is recorded per launch with its
  reason, as route requires.
- **Tension with decorrelation.** The easiest pair is usually same family,
  and § 3 reports that homogeneous LLM groups amplify agreement errors. The
  protocol carries the mitigation instead of the family choice: the asker
  sends facts and evidence, not conclusions; the guichet checks them against
  its own store and history before any verdict; neither side argues toward
  consensus. If the observation period shows the guichet rubber-stamping
  askers, revisit the family.

### Costs

Estimates by the drafter; author-hours are review time.

| | Author-hours | Agent time | USD (rough) | Undo |
|---|---|---|---|---|
| A wording | 0.3 | one small MR | < 1 | revert one paragraph |
| B guichet | 3–4 over the phases | audit + profile + rule + Pi ext., ~4 MRs | 10–30 build; per dialogue ~0.5–2 at advisor tier, plus an idle session's context | revert the rule, retire the profile; the ticket fallback still works throughout |
| C timer triage | 1 | one skill section + timer | 5–10 build; one advisor run per sweep | disable the timer |
| D A2A server | 6+ | daemon, auth, per-runtime adapters | 50+ build, plus upkeep | stop the service |

B's risk is bounded because the fallback is today's protocol: if a guichet
never answers, nothing is worse than now.

## 6. Implementation plan

One tracker, children in order; each child one merge request.

1. **Audit peer-to-peer dialogue capabilities [author].** For each ordered
   runtime pair (Claude Code, Codex, Pi; same host, cross host): can A start a
   turn in B, can B reply to A, is receipt reported, latency. Probes, not
   documentation: a REQUEST/ACK round trip per pair, results as a table in this
   note's § 2 and as `runtime.py can` answers. Proves which pairs the guichet
   may rely on. Includes probing `wake send` → Claude Code (currently NOOP).
2. **Rule rewrite.** `rules/workflow.md` § Cross-project work becomes:
   dialogue with the receiving guichet first; the guichet tickets, amends or
   pushes back; drop a ticket when the channel is not two-way. Step 4 and
   `guards.md` unchanged. Callers (`roar` step 9, `raid`) cite the new
   wording; roar's tracker hand-off becomes a REQUEST, with the log line as
   fallback.
3. **Guichet profile.** `profiles/guichet/PROFILE.md` and its shell
   `agents/guichet.md`: brief, verdict vocabulary, correlation-id handling,
   three-round cap, retirement, dropped-ticket triage. `Requires-tools` line
   per AGENTS.md. A launcher line for the asker side (how to start
   `guichet-<repo>` headless in the receiving checkout).
4. **Pi extension** (only if phase 1 shows Pi lacks a reply path): extend
   `idh-wake.ts` or add an `idh-dialogue.ts` so a Pi session can receive a
   REQUEST and send ACK/VERDICT back.

**Observe, then assess.** For the first two weeks after phase 3 merges, every
dialogue logs one line in the receiving journal: id, asker, ACK latency,
rounds, verdict, whether a fallback ticket was also dropped. **Review at
2026-12-01 or after 20 dialogues**, whichever comes first, in a doctor-journal
revisit (memory `feedback_no_wait_tickets`), deciding:

- **T**: keep 5 min, or set it from the measured ACK latency (p90 × 2);
- **tier**: keep advisor, or step down if verdicts never get reversed;
- **guichet lifetime**: the retirement threshold from observed context growth;
- **value**: share of dialogues ending in PUSHBACK or AMENDED (outcomes a
  blind dropped ticket would have got wrong). Near zero means the dialogue is
  ceremony and C alone would do.

## Review

*Pending: two decorrelated advisor-level reviews and a KISS pass.*
