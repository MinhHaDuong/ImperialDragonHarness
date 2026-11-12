# Guichet: dialogue first between repositories

Status: provisional (author, 2026-11-12)

The author chose "provisional" over the template's `proposed`/`accepted`:
the design guides the work below, and its rulings may still move with
phase 1's evidence. Tickets filed from it carry `needs-human`, as from a
proposed note, until the author marks it accepted.

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

**Callers.** `skills/roar` step 8 hands a cross-repo tracker update off as one
`erg log` line on the harness tracker, landed by merge request (ticket 1409
fixed roar editing the harness directly) and messages a live harness session
when timing matters. `skills/raid` answers another project through its ticket
store, and takes a pushback up in dialogue first with a live session that can
manage the asker. Commits since 2026-10-29 touching
hand-offs or cross-project records: 39 (`git log --since=2026-10-29 -i -E
--grep="hand-off|from [a-z-]+ session|filed from|cross-project" | wc -l`; a
keyword count, an upper bound on traffic, not a measure of it).

**Transport, per runtime** (`scripts/runtime_wake.py`, tickets 1311, 1316):

| Path | Mechanism | Two-way? | Status |
|---|---|---|---|
| Claude Code → Claude Code, same host | native `ListAgents` / `SendMessage`; idle notice opt-in | yes, receipt reported; held or refused by the receiver's inbound setting (§ 3) | native; prescribed by roar step 8 and raid, no launcher or protocol |
| Claude Code → Remote Control / cloud session | same tools | Remote Control can reply; cloud cannot reply across machines; nothing reports back | native |
| any → Claude Code via `runtime.py wake send` | — | — | NOOP: "no cross-process path has been probed" |
| any → Codex | `codex queue --thread` | queued, never confirmed delivered | in `runtime_wake.py` |
| any → Pi | inbox directory read by `adapters/pi/extensions/idh-wake.ts`, delivered as a user message when idle | inbound only; a reply needs a path back | in `runtime_wake.py` |

So two-way dialogue between *live* sessions exists today on exactly one path:
Claude Code sessions on the same host. Every other pair is one-way or unprobed.

**One-shot doors.** Each runtime has a proven headless door in
`skills/route/routes.json` `launch_doors`, used daily by gaze seats:
`claude -p --restricted`, `codex exec --ignore-user-config`, `pi --print`.
Each runs one turn and exits; the caller collects the output. None keeps a
session alive: `claude -p` exits after its turn, and `--restricted` ignores
the settings files, so a headless Claude session never sees the host's
inbound-messaging setting.

**Background sessions.** Outside the harness's doors, the Claude Code CLI
(2.1.322) has `claude --bg [-n <name>]`: it starts a session in the
background, returns at once, and the session persists; `claude agents --json`
lists it (id, name, cwd, state busy/idle), and `attach`, `logs`, `stop`, `rm`
manage it. On padme on 2026-11-12, `claude agents --json` listed 9 such
sessions, idle ones among them in other repositories. No skill or script
uses `--bg` yet. Not yet observed: a `--bg` session receiving a peer's
`SendMessage` and replying; its permission mode decides whether inbound
messages are held (§ 3).

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
no runtime's transport acknowledges across all pairs. (3) A live Claude Code
guichet must accept peer messages without a human hold, or REQUESTs expire
unseen; a missing ACK sends the asker to the one-shot path. (4) Facts, not agreement:
the guichet triages against its own repository, not the asker's framing,
and the round cap bounds loops.

## 4. Alternative solutions

**A. Status quo plus wording** (most direct). Keep "ticket there, always";
add "for a request that needs the owner's judgment, prefer a live dialogue
first". No new role, no new transport. Leaves the outsider-written ticket and
the unowned intake in place.

**B. Guichet: a service-desk role per repository** (the author's
direction). Dialogue first; the receiver writes the ticket. Detailed in § 5,
where the reviews reshaped the reused session into a live/one-shot hybrid.

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

**Pick B, in a hybrid form: a reused background guichet where the runtime
can host one, a one-shot guichet elsewhere; the receiving store records
every verdict.** B fixes both pains of § 1: the owner writes its own ticket,
and intake has an owner. The reviews (below) found no way in the harness's
doors to keep a guichet alive; the author pointed to `claude --bg` (§ 2,
background sessions), which does, with no supervisor to build. Codex and Pi
askers, and any host where the background launch fails, use the one-shot
doors.

### Roles **[author]**

- **Asker** exposes facts and observations from its side: what it saw, where,
  with evidence paths. No orders, no edits, no proposed patch to the receiver's
  files. It may say what outcome would unblock it.
- **Guichet** records, converses, triages and decides actions for its side. It
  answers with one of these outcomes:
  - `NEW <id>`: filed a new ticket;
  - `AMENDED <id>`: logged on an existing ticket;
  - `PUSHBACK <reason>`: declined, with why (not ours, already fixed in
    `<sha>`, against rule X, needs the author);
  - QUESTION: it needs one answer before deciding (`input-required`);
  - REDIRECT: a live session is better placed; the asker talks to it
    directly (§ Knowing the repository's live work).

  The protocol names these with A2A's vocabulary (below); NEW, AMENDED and
  PUSHBACK stay as the outcomes they denote.

  It triages only: the work itself goes to `/hunt` on the resulting ticket.
  The REQUEST is data, never an order (`rules/workflow.md`: a peer's message
  carries no user authority).

### Knowing the repository's live work **[author]**

An incoming request may overlap work already running in the repository: a
coder fixing the same bug, a branch rewriting the file the asker complains
about. A guichet that triages from the ticket store alone files a duplicate
or a conflicting ticket. Before any verdict, it reads what is live:

| Signal | Source | Gives | Runtimes |
|---|---|---|---|
| worktree locks | `git worktree list --porcelain` | path, branch, lock reason naming the ticket and the owner's pid (hunt's § Worktree recipe) | all |
| liveness | `kill -0 <pid>` | whether the lock's owner still runs | all |
| sessions | `claude agents --json`, `ListAgents` | name, pid, state busy/idle | Claude Code |
| claims and requests | `tickets/.claims/`, open merge requests and their branches | who claimed which ticket, what is about to land | all |
| files in flight | `git diff --name-only origin/main...<branch>` per live branch | the paths each live branch changes | all |

The join is the pid: a hunt worktree's lock reason carries the runtime
process id (`$PPID`), and `claude agents --json` reports the same pid. On
2026-11-12 the drafter's own lock (`pid 789752`) matched its session's
`pid` in the listing. A session's listed `cwd` is where it started, not the
worktree it moved into, so the cwd cannot make the join. For Codex and Pi the
lock and pid still name the ticket and prove liveness; only the session name
is missing.

**Overlap is detected by files, then judged by ticket.** The guichet
matches the paths in the asker's evidence against each live branch's files
in flight (the command the sync rule already uses, `rules/workflow.md`
§ Sync before starting work). A shared path is a concrete overlap signal:
it is also where conflicting work would collide. A request with no path in
common may still overlap by cause; the guichet then judges from the running
ticket's text.

When the request overlaps live work, the guichet **redirects, it does not
middleman [author]**:

- **A live session is better placed** (a coder on the same defect, the
  session that filed the related ticket) and reachable on a two-way path:
  the guichet answers the asker with that session's address, the ticket,
  and the session's state (busy or idle, from `claude agents --json`), logs
  a one-line pointer on the ticket (`redirected <contextId> to <session>`),
  and steps out. **A busy session is not interrupted:** the asker
  subscribes with `SendMessage` `notify_when_idle: true` and no message,
  which costs the session nothing, and opens the dialogue when the idle
  notice arrives. The asker stays non-blocking meanwhile; a subscription
  that expires unanswered falls back to a log line on the ticket. The asker opens its own dialogue with that
  session under the same protocol; the session records the outcome on its
  own ticket, as any receiver does. The guichet relays nothing in either
  direction.
- **The case does not touch the session's current work**, or the session
  is not reachable (a Codex or Pi coder, § 2): no redirect. The guichet logs
  the case on the running ticket and answers `completed` with the ticket as
  artifact, so a busy coder reads it at its own pace.
- **The request would change something a live branch is rewriting**:
  `rejected` with reason "in progress, PR <n>", naming the PR to wait for.

The guichet reads live work but never steers it: no reassignment, no
reprioritization, no message asking a coder to stop or switch. Those calls
stay with the author or the session that launched the coder.

### Durable record **(revised after review)**

Messages notify; the receiving ticket store records. Before it answers, the
guichet writes one store line keyed by the correlation id:

- `NEW`: the new ticket carries the id in its log;
- `AMENDED`: the log line on the existing ticket carries the id;
- `PUSHBACK`: a log line on an `intake` ticket of the receiving store (one
  standing ticket per repository, holding pushback lines), so a refusal is as
  findable as an acceptance;
- an id still open when a live guichet stops becomes an `incoming` ticket,
  so no acknowledged request is held only in a session's context.

All of these are `tickets/*.erg` writes, landed from the guichet's own
worktree (`rules/workflow.md` § Session start) by a ticket-only merge request
on the bookkeeping fast track. The guichet writes nothing else: no journal,
no memory. The asker finds any verdict later by grepping the receiving store
for its id, which also deduplicates: a repeated REQUEST, or a fallback ticket
citing an id already answered, gets the recorded verdict back.

### Two paths

**Vocabulary: A2A's, without A2A [author].** The transport is not adopted
(§ 4 D); the names are, so a later A2A adapter would be a thin mapping
(§ 3). Every message is plain text with a header line of fields:

| Field | A2A meaning | Guichet use |
|---|---|---|
| `contextId` | conversation id, client-minted | the asker's correlation id, `<asker-repo>-<date>-<rand>`; the deduplication key |
| `taskId` | one task in the conversation | the guichet's triage of this request |
| `role` | `user` / `agent` | asker / guichet |
| `state` | task state | see below |
| `artifact` | task output | `ticket <path> new` or `ticket <path> amended`, or `redirect <session> <ticket>` |

| `state` | Sent by | Outcome it carries |
|---|---|---|
| `submitted` | asker | the REQUEST |
| `working` | guichet | the ACK, within T |
| `input-required` | guichet | a QUESTION; the asker answers in a new message on the same `contextId` |
| `completed` | guichet | NEW or AMENDED (ticket artifact), or a redirect (redirect artifact) |
| `rejected` | guichet | PUSHBACK, with the reason |
| `failed` | guichet | it could not triage (store unreadable, door error); the asker drops the fallback |

A2A has no redirect state; the guichet uses `completed` with a redirect
artifact, since its task (triage) is done. That is the one extension.

**Live path** (Claude Code askers on the same host, the only two-way path
in § 2):

0. If neither `ListAgents` nor `claude agents --json` shows a session named
   `guichet-<repo>`, the asker launches one **[author]**:
   `claude --bg -n guichet-<repo> --model <advisor> ...` in the receiving
   repository's primary checkout, with the guichet profile as its agent and
   the REQUEST as its first prompt. It persists idle between requests and
   costs nothing while idle.
1. REQUEST (`submitted`) → ACK (`working`) within **T = 5 min [author]**,
   proving the channel two-way;
2. questions and answers, at most three rounds;
3. the result (`completed`, `rejected` or `failed`), after the store line
   is written.

**Retirement.** Before the context guard (230K for a launched worker), the
guichet converts open ids to `incoming` tickets and exits; `claude stop` or
`rm` cleans it, and the next asker launches a fresh one. Two askers racing
to launch produce two guichets for a while: both write store lines, the
second AMENDs, and the elder retires the younger by name.

**One-shot path** (Codex and Pi askers, a failed background launch, or no
ACK within T):

1. The asker launches a headless run in the receiving repository through the
   door of the family chosen below, with the guichet profile and the REQUEST
   as its prompt, as its own background task (the same mechanism `wake arm`
   uses on Claude Code: the exit re-invokes the asker).
2. The run first triages the receiving store's `incoming` tickets, reads
   the repository's live work (§ Knowing the repository's live work), then
   the REQUEST; it writes the store line and prints the verdict.
3. An `input-required` result ends the run; the asker relaunches with its
   answer on the same `contextId`, at most three times, then the guichet
   decides on what it has.

**Fallback** (the launch fails, the door is down, or the asker cannot launch
a background task): drop an `incoming` ticket in the receiving store citing
the id, as today. The next guichet run, live or one-shot, triages it first.

**Non-blocking for the asker [author].** The asker sends or launches, then
continues its own work. The ACK or the run's exit arrives at its next tool
round. It never sleeps or polls (memory `feedback_no_blocking_waits`). A
headless asker (a night sweep under `claude -p`) cannot hold a background
task past its turn: it takes the fallback directly. At its wrap-up the asker
records what it has: a verdict, or "pending at <repo>, id X". Its next roar
or lair greps the receiving store for pending ids.

### Authorization **[author]**, and what the rule must say

The author ruled that the asker launches. Current law allows a launch "only
for authorized work that must happen now" (`rules/workflow.md` § Cross-project
work, step 3), so the ruling widens step 3; it does not narrow it. Phase 3
rewrites step 3 to give guichet runs standing authorization: triage only,
under the receiving repository's rules, memory and gate, writing tickets
only. `rules/guards.md` needs no change: the asker still writes no file in
the other project (the fallback ticket is the existing exception), and the
guichet works in its own project.

The ticket-only limit is enforced where it can be: the guichet shell's
`tools:` grant, and a door that can write its own worktree and nothing
wider. A one-shot guichet must write its store line itself (§ Durable
record), so the read-only seat door (`codex exec -s read-only`) is not a
guichet door; a Codex guichet needs a sandbox that writes its worktree
(`-s workspace-write`), which phase 1 checks. Where the limit cannot be
enforced, the profile states it and the observation log (§ 6) checks it.

### Model and family

- **Tier: advisor (ASSURANCE) [author]**, unless the receiving repository
  holds uncleared content, which forces LOCAL/PRIVÉ (`skills/route/SKILL.md`).
  Triage is judgment work: deciding that a foreign observation is a duplicate,
  not ours, or a symptom of a known cause.
- **Family: the one easiest to talk to [author], not dogmatically the
  asker's.** On the live path, the family of the live guichet. On the one-shot
  path, any family the asker's host can launch through a live door with
  write access to the receiving tickets; the launch line records the choice
  and its reason, as route requires.
- **Tension with decorrelation.** The easiest pair is often same-family, and
  § 3 reports that homogeneous LLM groups amplify agreement errors. The
  protocol carries the mitigation: the asker sends facts and evidence, not
  conclusions; the guichet checks them against its own store and history
  before any verdict; neither side argues toward consensus. If the
  observation shows the guichet rubber-stamping askers, revisit the family.

### Failure modes handled

| Failure | Handling |
|---|---|
| guichet crashes or stops after ACK | open ids become `incoming` tickets on stop; a crash leaves the REQUEST unrecorded, so the asker's later grep finds nothing and it drops the fallback |
| two askers launch at once | live path: two `guichet-<repo>` sessions until one retires; one-shot path: two runs. Either way the second greps the store, finds the first's id or a duplicate ticket, and AMENDs |
| asker exits before the verdict | the store line survives; its next roar or lair reads it |
| headless asker | fallback directly |
| peer message held or refused (Claude inbound setting) | no ACK within T, one-shot path |
| loops | three-round cap; Claude Code also throttles repeats (§ 3) |

### Costs

Estimates by the drafter; author-hours are review time; USD unmeasured.

| | Author-hours | Agent time | USD (rough) | Undo |
|---|---|---|---|---|
| A wording | 0.3 | one small MR | < 1 | revert one paragraph |
| B hybrid | 2–3 over the phases | audit, profile, launcher, rule: ~4 MRs | 10–30 build; per one-shot dialogue one advisor run plus a ticket MR, ~1–3 | revert the rule, retire the profile; the fallback is today's protocol |
| C timer triage | 1 | one skill section + timer | 5–10 build; one advisor run per sweep | disable the timer |
| D A2A server | 6+ | daemon, auth, per-runtime adapters | 50+ build, plus upkeep | stop the service |

The background guichet needs no supervisor (`claude --bg`), but every wake
of an idle session re-reads its whole context, uncached after an idle hour:
unmeasured, and one of the observation's questions.

## 6. Implementation plan

One tracker, children in order; each child one merge request. The rule
changes last, once its machinery exists **(revised after review)**.

1. **Audit peer-to-peer capabilities [author].** For each runtime pair
   (Claude Code, Codex, Pi; same host, cross host), probe with a
   REQUEST/ACK round trip: can A start a turn in B, can B reply, is receipt
   reported, latency. First probe: a `claude --bg -n guichet-<repo>`
   session receiving a peer `SendMessage` and replying, under each
   permission mode the guichet might run in. Second probe: the live-work
   join (worktree lock pid ↔ `claude agents --json` pid ↔ ticket) on a
   repository with a running Codex or Pi coder too. Third probe: an asker
   subscribing to a busy `--bg` coder's idle notice, then messaging it, to
   confirm the notice arrives and the coder's turn ran uninterrupted. For
   each one-shot door: can it write the receiving
   store from its own worktree. Includes `wake send` → Claude Code (NOOP
   today) and Claude's inbound hold. *Proves* which pairs the live path may
   use and which doors the one-shot path may use; results replace § 2's
   transport table.
2. **Guichet profile and launcher.** `profiles/guichet/PROFILE.md`, shell
   `agents/guichet.md` with its `tools:` grant, `Requires-tools` line; the
   verdict vocabulary, store-line format, `incoming` and `intake` tickets,
   three-round cap, the A2A field and state names, the live-work read and
   redirect rules; one launch line per door. *Proves*, by a dry run between
   two of the author's repositories, that a one-shot run returns a verdict
   and lands its store line by a ticket-only merge request.
3. **Rule rewrite.** `rules/workflow.md` § Cross-project work: dialogue with
   the receiving guichet first (live, else one-shot); it tickets, amends or
   pushes back; drop an `incoming` ticket when neither path works. Step 3
   gains the guichet's standing authorization; step 2's no-authority sentence
   and step 4 stay. Callers (`roar` step 8, `raid`) cite the new wording;
   roar's tracker hand-off becomes a REQUEST, with the log line as fallback.
   *Proves* nothing new: it records what phases 1 and 2 showed.
4. **Pi path** (only if phase 1 shows `pi --print` cannot serve a one-shot
   guichet or Pi needs a live path): extend `idh-wake.ts` with a reply route.
   *Proves* a Pi asker or guichet completes one REQUEST round trip.
5. **Live guichets for Codex and Pi, conditional.** Only if the
   observation shows one-shot cold starts costly for those askers, and
   phase 1 found a two-way path: a persistent guichet on those runtimes.
   Priced then, not now. *Proves* the live path's ACK within T for a Codex
   or Pi asker.

**Observe, then assess.** From phase 3's merge, each guichet run adds one
field to its store line: path (live / one-shot / fallback), ACK latency,
rounds, verdict, cost when the door reports it, and the paths its merge
request changed outside `tickets/` (expected: none). **Review after 20 dialogues
or six weeks after phase 3, whichever comes first**, in a doctor-journal
revisit (memory `feedback_no_wait_tickets`), deciding:

- **T**: keep 5 min, or set it from the measured live ACK latency;
- **tier**: keep advisor, or step down if verdicts are never reversed;
- **value**: count the dialogues where the guichet changed the outcome a
  blind dropped ticket would have had (duplicate merged, cause corrected,
  refusal with reason) against those where it rewrote the asker's request in
  the house voice and nothing more. Both C and B can produce PUSHBACK and
  AMENDED, so frequency alone does not credit the dialogue; compare against
  a sample of fallback tickets triaged without one. Near zero means C alone
  would do;
- **idle-wake cost** of a background guichet against a one-shot run;
- **redirects**: how often the guichet sent an asker to a running session,
  and whether that session used the case or found the dialogue an
  interruption;
- **phase 5**: start it or not.

## Review

Two decorrelated advisor-level reviews of the draft at `ff3db59b6`, with the
same brief (template conformance, findings, KISS pass, verdict; author
rulings not relitigated unless contradictory or against current law).

**Seat 1: OpenAI gpt-6-astra @medium** (other family, `codex exec` door,
read-only). Verdict NEEDS-REVISION. Findings, all adopted:
(1) an ACKed request could be lost: durable store line before verdict,
open ids become `incoming` tickets;
(2) the asker-launch ruling contradicts step 3 and `guards.md` was not
reconciled: § Authorization;
(3) fallback tickets had no guaranteed reader: every guichet run triages
`incoming` first;
(4) the prescribed wake is NOOP for headless askers: headless askers take
the fallback directly;
(5) journal writes contradicted ticket-only scope, and retirement "past" the
guard broke it: journal writes removed, retirement moved before the guard
(§ Two paths, after the `--bg` follow-up);
(6) rule before machinery, and a value metric that overclaimed: phases
reordered, metric compares against fallback triage.
KISS: drop journal hand-offs, adaptive lifetime tuning and the outbox
analogy (done for the first two; the outbox paragraph stays in § 3 as the
source of the idempotency rule).

**Seat 2: Anthropic Claude Fable** (advisor model, a different model from
the drafter, same family; subagent, read-only). Verdict NEEDS-REVISION.
Findings, verified by the drafter against the files:
(1) no mechanism keeps a guichet alive: the headless door is
`claude -p --restricted`, one turn, settings ignored. Adopted: hybrid
live/one-shot, persistence deferred to phase 5;
(2) verdicts had no durable address: same fix as seat 1 (1);
(3) the launch ruling widens step 3, and "ticket-only" was unenforced:
§ Authorization, enforcement through the `tools:` grant and sandbox;
(4) the advisor tier must yield to uncleared content: adopted;
(5) phase order and missing "proves" lines: adopted;
(6) the launch race, headless askers and the guichet's own worktree:
§ Failure modes and § Durable record;
(7) per-dialogue cost ignored cold context: noted under Costs as unmeasured;
the observation window was inconsistent: fixed;
(8) factual slips: roar's hand-off is step 8 (verified), messaging is
already prescribed by roar and raid (verified), "ticket-only" now holds
because journal writes were removed.
KISS: a one-shot-only guichet, which would drop the live path, ACK and T.
**Partly adopted**: one-shot is the default path, but the live path and
T = 5 min stay, because the author ruled for a reused session and T, and
the live path costs nothing when a session already exists. **Author follow-up (2026-11-12):** "Why not launching `--bg`?" Checked:
`claude --bg` persists a named session (§ 2), so Fable's finding (1)
no longer forces one-shot for Claude Code; the live path now launches a
background guichet, and phase 5 shrinks to Codex and Pi.
**Author follow-up (2026-11-12):** the guichet must know what the
repository's other live sessions are doing, since a request may overlap
running work ("we are already doing this, I will pass your case to the
running coder"). Added § Knowing the repository's live work: read-only
signals joined by pid, no steering.
**Author rulings (2026-11-12):** A2A is not adopted, its vocabulary is
reused (§ Vocabulary). The guichet does not middleman: when a live session
is better placed, it redirects the asker to talk with it directly, replacing
the relay first drafted.
**Author follow-up (2026-11-12):** asked which further state of the art
improves the design; of seven threads offered, two did and were added:
redirect to a busy session only on its idle notice (after Google SRE's
interrupt handling), and overlap detection by files in flight (after
blackboard matching). The other five confirmed existing choices and stay
out of § 3.

KISS pass by the drafter: the FIPA/A2A mapping stays in § 3 (it fixed the
vocabulary) but adds no machinery; no supervisor is built (`claude --bg`
does the hosting), and the Pi extension and non-Claude live guichets are out
of the first build.
