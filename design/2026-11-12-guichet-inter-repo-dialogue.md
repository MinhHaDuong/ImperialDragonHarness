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

**Design case [author, 2026-11-12].** Projects find bugs in the services
they consume and must report them: the harness (`~/.agents`), git-erg ticket
tooling, and padme host services (repository `padme`). Those three are the
receivers; every other project is an asker. Two observed cases per receiver
are in § 2, Observed cases. Communication between sessions inside one
repository is out of scope.

The author's direction **[author]**: talk first; the *receiving* repository
records, triages and answers with a new ticket, an amended ticket, or pushback.
A dropped ticket stays as the fallback.

## 2. Situation

Read from `origin/main` at `829d7a582`.

**Observed cases.** A history sweep on 2026-11-12 (research subagent,
Claude pinned `sonnet`, read-only over the three receivers' ticket stores,
git logs and the askers' journals) found these, two per receiver; every
row was then checked against its tickets by gaze review
rv-20261112-pr-2465-7bae and corrected by the drafter (P2 replaced). Each row is what happened, not
a cause.

| # | Asker → receiver | Observed | How it travelled | What the travel cost |
|---|---|---|---|---|
| H1 | climate-finance-het → harness, 2026-11-10/11 | reading-note filing contradicted the author's new Zotero-first decision | harness ticket 1522, written from the author decisions of 2026-11-10 as relayed by the asker, planned `publish-notes` on the Web API; cfh 3019 its child | the plan ran against the standing local-API-only ruling (2026-10-15/16); it survived about a day until the author ruled the local API: cfh 3019 logged the supersession ("Web-API and project-script choices superseded") while its Choices section still names the Web API, and 1522 gained a superseding paragraph |
| H2 | climate-finance-het → harness, 2026-11-12 | `publish-notes` leaves parent items out of the project's Zotero collection | harness 1541, "relayed by a climate-finance-het session": the observation plus one suggested shape, design left to the executor | none visible: a well-formed report, after the asker had worked around it with a one-off script for 55 parents |
| G1 | JETP-observer → git-erg, 2026-11-09 | managed pre-commit printed ~40 KB of warnings per ticket commit | git-erg 0313, `Author: Claude (JETP-observer session)`, filed in the receiver's store | fixed in about 35 min (PR #405), but the fix took effect only after every adopter reinstalled its hooks, a consequence the reporter could not know: the receiver's review noted it on the ticket, and the harness tracker 1478 relayed `install --hooks` to adopters with the new pin |
| G2 | JETP-observer (claims rollout) → git-erg, 2026-11-09 | a pre-installed hook block refused committing `tickets/erg` off the default branch | git-erg 0311, filed by the author relaying JETP-observer PR #285; an earlier sighting (git-erg 0219, met in chemin-de-voix) had been partly fixed by git-erg PR #268 | the harness rollout tracker told adopters to commit with `--no-verify` (harness 1478, 12:19Z) and reversed it 6 min later when git-erg #399 dropped the rule (12:25Z) |
| P1 | arena → padme, 2026-11-01 | a profile note called 256K context "beyond native 128K", which is false | padme 0086, "Reported from an arena session" | closed in 22 min: the report named the missing check (the model card) and why it mattered (a planned long-context arm) |
| P2 | git-erg → padme, 2026-11-09 | a stale `erg` on the host PATH (no claims) and dead `core.hooksPath` in two clones of other projects | padme 0110, "Relevé par la session git-erg", filed at that session's request | one report with two observations needed four owners: padme for the PATH binary (an author decision, replace rather than delete), tickets fanned out by hand to AEDIST-technical-report (0686) and chemin-de-voix (0259), and the harness told through its tracker 1478; closed in 33 min |

What the cases show, for § 5. Reports that stated an observation and its
evidence (H2, P1, G1) travelled cheaply. The one that carried a design
built on a stale premise (H1) needed a correction the receiver's own rulings
would have given at intake. A single report can hold observations for
several owners (P2), and the fan-out was done by hand. Fixes whose consequences fall
back on askers (G1's hook reinstall, G2's temporary `--no-verify`) reached
them only through a tracker log line. The sweep did not find the source of
1341's "two corrections" line.

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

**Pi as a host.** `adapters/pi/extensions/idh-wake.ts` (ticket 1316)
already turns a file dropped in a per-session inbox into a user message in
the running Pi session when it is idle. On padme on 2026-11-12, `pi
--list-models` reached the anthropic (17 models), openai (45), mistral
(39), huggingface (81), padme local and albert providers, so one Pi
session can run a model of any family the route skill picks, local ones
included. Pi also has an `--mode rpc` and named sessions (`--name`,
`--session-id`). Not yet observed: `idh-wake.ts` delivering into a Pi
session started detached (tmux or a `systemd-run --user` unit), which is
how a guichet would run.

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

**State of practice (bibliographic saturation, 2026-11-12).** Three blind
searchers (Claude, pinned `sonnet`), an adversarial judge that re-fetched
every primary text (Claude Fable) and a completeness critic (gpt-6-astra,
logs only) examined three claims; report and logs in
`design/research/2026-11-12-guichet-biblio-saturation.md`. Coverage is
partial for every claim. Findings:
- *Local A2A transports.* No A2A binding over the local filesystem is
  among the a2aproject proposals we examined as of 2026-11-12. The nearest are the open
  STDIO binding proposal (<https://github.com/a2aproject/A2A/issues/2048>:
  "no listening socket, no port", session bound to a pid) and
  store-and-forward proposals (A2A issues 2191, 2185, 2438). File mailboxes
  with atomic-rename claims exist without A2A: a2a-relay
  (<https://github.com/Hosuke/a2a-relay>), abq
  (<https://github.com/aygp-dr/abq>), agent-message-queue
  (<https://github.com/avivsinai/agent-message-queue>), pi-messenger, tap.
  synapse-a2a keeps one registry file per agent with its pid and checks
  liveness by `kill(pid, 0)`. So the transport below is *partly
  anticipated*: each ingredient exists, the combination under A2A's
  vocabulary was not found.
- *Coding-agent CLIs of several vendors as peers.* Anticipated:
  synapse-a2a, a2abridge, and a2aproject's own a2a-serve (v0.1.0,
  2026-11-11) put Claude Code, Codex and others on A2A, by their own
  account (A2A conformance self-declared, untested); agmsg, hcom, repowire,
  agent-message-queue and tap (arXiv 2606.14445, Claude and Codex on one
  codebase) do it over their own protocols. None of the ten tools examined
  documents Mistral Vibe support.
- *Agents reporting bugs to repositories or services they depend on,
  measured.* We did not identify a matching study in the searches described
  (coverage partial: no Semantic Scholar, OpenAlex or HAL; several
  exclusions rest on abstracts). Nearest: agentic property-based testing (arXiv
  2510.09907; authors selected and reported 5 bugs), human upstream-bug
  studies (Lin et al., EMSE 2022, doi 10.1007/s10664-022-10173-y; NPM
  maintainer responsiveness, arXiv 2511.04986).

**What this changes in § 5.** (1) Messages are notification, the ticket
store is the record: every verdict names a ticket or a logged pushback.
(2) The ACK is an application-level message with the correlation id, since
no runtime's transport acknowledges across all pairs. (3) Where a Claude
Code `SendMessage` shortcut is used, the receiver's inbound hold can let
REQUESTs expire unseen; a missing ACK sends the asker to the fallback
ticket. (4) Facts, not agreement:
the guichet triages against its own repository, not the asker's framing,
and the round cap bounds loops.

## 4. Alternative solutions

**A. Status quo plus wording** (most direct). Keep "ticket there, always";
add "for a request that needs the owner's judgment, prefer a live dialogue
first". No new role, no new transport. Leaves the outsider-written ticket and
the unowned intake in place.

**B. Guichet: a service-desk role per repository** (the author's
direction). Dialogue first; the receiver writes the ticket. Detailed in § 5,
where the reviews and the author reshaped it into one Pi-hosted path.

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

**E. Reuse an existing local agent bus** (different family: buy, not
build). agent-message-queue, hcom or repowire already carry messages
between Claude Code, Codex and Pi sessions and wake idle ones (reuse table
in `design/research/2026-11-12-guichet-biblio-saturation.md`). E is
not an alternative to B but a possible carrier for its asking side, kept as
an option if our adapters prove harder than expected. None of the tools examined
provides the triage role or the durable record in the receiving store, and
none documents Vibe support; their discovery features were not compared.

## 5. Synthesis and recommendation

**Pick B with one path: a persistent guichet hosted by Pi, running the
model route picks, reached by askers of any runtime; the receiving store
records every verdict; a dropped ticket is the only fallback [author].** B
fixes both pains of § 1: the owner writes its own ticket, and intake has an
owner. An earlier version had two paths, a live guichet that only Claude
Code could host (`claude --bg`) and a one-shot run for everything else. The
author asked whether the one runtime able to host would always be selected
(it would, so route's choice was a fiction) and why not a Pi extension. Pi
already has the inbox extension and reaches every model family (§ 2, Pi as
a host), so the runtime is fixed and the model is free.

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

**When metadata is not enough: an informant reads the transcript
[author].** If the files show an overlap and the guichet needs the running
session's intent (is it fixing the same cause?), it does not query that
session, which would interrupt it, and it does not read the transcript
itself. It sends a cheap read-only informant, a small-model subagent, to
the session's live transcript, located through `transcript_spool.py`
`NAMED_ROOTS` (claude, codex, pi, aider, vibe), which returns three lines of
facts: ticket, files, current hypothesis. The guichet records facts, never
quotes; transcripts may hold uncleared material. Mapping a pid to its
transcript file is known for Claude Code (`sessionId` in `claude agents
--json`); for the other runtimes it goes through cwd and mtime, a phase 1
probe.

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
  and steps out. **A busy session is not interrupted:** where its runtime
  offers an idle notice (Claude Code: `SendMessage` `notify_when_idle: true`
  with no message, free for the session), the asker subscribes and opens
  the dialogue when the notice arrives. A session whose busy or idle state
  is not observable (today: Codex, Pi and Vibe coders, until phase 1 finds a
  signal) gets no redirect: the guichet logs the case on its ticket instead
  (next bullet). The asker stays non-blocking meanwhile; a subscription
  that expires unanswered falls back to a log line on the ticket. The asker opens its own dialogue with that
  session under the same protocol; the session records the outcome on its
  own ticket, as any receiver does. The guichet relays nothing in either
  direction.
- **The case does not touch the session's current work**, or the session
  is not reachable (its runtime has no inbox or wake adapter, § Transport
  and discovery): no redirect. The guichet logs
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
- an id still open when a running guichet stops becomes an `incoming` ticket,
  so no acknowledged request is held only in a session's context.

All of these are `tickets/*.erg` writes, landed from the guichet's own
worktree (`rules/workflow.md` § Session start) by a ticket-only merge request
on the bookkeeping fast track. The guichet writes nothing else: no journal,
no memory. The asker finds any verdict later by grepping the receiving store
for its id, which also deduplicates: a repeated REQUEST, or a fallback ticket
citing an id already answered, gets the recorded verdict back.

### Transport and discovery: runtime-neutral **(amended 2026-11-12)**

The first-class runtimes are Claude Code, Codex, Vibe and Pi, with more to
come **[author]**. A Vibe MOE in another project cannot see a Claude
`guichet-idh` through `ListAgents`, so discovery and delivery must not
depend on any one runtime's native tools.

- **Stable inbox.** Each receiver's guichet inbox lives at a well-known
  path on its host, `~/.local/state/idh/inbox/guichet-<repo>/`, independent
  of any session: an asker creates it if missing and writes there whether a
  guichet runs or not, and messages survive a guichet's closing. `idh-wake.ts`
  today creates a random per-session inbox at `session_start` and deletes it
  at shutdown when empty; it gains the option to read a preset path instead,
  and never deletes a preset inbox (phase 2).
- **Lock [drafter's proposal].** At most one guichet per receiver and host,
  enforced by the kernel, not by a file's presence: the launch command is
  `flock -o -w 2 ~/.local/state/idh/guichets/<repo>.lock <start the Pi
  guichet>`, run inside the detached session. `flock` holds the lock for
  the guichet's lifetime; `-o` keeps it out of Pi's child processes, so a
  child that outlives a crashed Pi cannot hold it (reproduced without `-o`,
  util-linux 2.39.3, gaze rv-20261112-pr-2470-8fb1); `-w 2` lets two
  racing launchers settle. A second launch fails after two seconds and does
  nothing; a crash releases the lock, so no stale lock needs breaking.
  Liveness is read without taking the lock (`lslocks` by path, or
  `/proc/locks` by the lock file's inode), so a probe never makes a launch
  fail. Under `-o` only the `flock` process holds the lock, so a guichet is
  stopped as a whole (its tmux session or systemd unit), never by killing
  `flock` alone, which would free the lock while Pi runs on. The lock file
  is never deleted: removing and recreating it while held would let a
  second guichet lock the new file. A plain card file cannot
  serve as the lock: breaking a stale one after a crash is itself a race.
- **Card.** A running guichet writes a card at
  `~/.local/state/idh/guichets/<repo>.json`, with Agent Card names: `name`,
  the inbox as `url`, `protocolBinding`, plus `model`, `host`, `pid`,
  `started`, where `pid` is Pi's, not `flock`'s. It is descriptive: who listens and with which model. Whether
  anyone listens is the lock's answer. `runtime.py guichet find <repo>`
  reads the lock state and the card from bash, so every runtime can call
  it. Two passing states are normal: lock held and no card yet (starting),
  and a card with the lock free (left by a crash, overwritten by the next
  launch).
- **Host: Pi, always; model: route's choice [author].** Every guichet runs
  as a persistent Pi session named `guichet-<repo>`, started detached in the
  receiving repository's checkout (tmux, or a `systemd-run --user` unit as
  `runtime_wake.py` already does for Codex), under that repository's rules,
  reporting to no one but the protocol. A `guichet.json` in the receiving
  repository states the role and the need, never a model or a tier: the
  guichet role, clearance, host. Route maps the role to a worker at each
  launch (`AGENTS.md`: "A skill states a role and a need; it never names a
  model or a capability tier"; the advisor tier for this role is the
  author's ruling, recorded on route's side); the card and the launch line
  record the model actually used. An asker that finds the lock free
  launches one through `runtime.py launch`; from another host, over `ssh`.
- **Delivery.** Receiving side: `idh-wake.ts` reads the guichet's stable
  inbox (exists, with the preset-path option above). A small Pi extension next to it writes the card at
  `session_start` and removes it at shutdown; replies are file writes into
  the asker's `replyTo` inbox. Asking side, one adapter per runtime: Pi
  (the same extension), Claude Code (a `wake arm` waiter on its inbox),
  Codex (`codex queue`), Vibe (below). Messages are files in the Pi
  wake-inbox format with the A2A fields in their body; a task's files mirror
  A2A's core operations (send = rename into the inbox, get = read the
  status file, list = list the task directories, cancel = write a cancel
  file; no streaming). Reusing agent-message-queue for the asking side stays
  an option if our adapters prove harder than expected (§ 4 E).
- **Vibe.** None of the tools examined documents support for it, and the
  harness has no Vibe adapter. A Vibe
  asker writes REQUESTs like any other and reads its reply inbox at its own
  pauses (non-blocking, slower); a Vibe adapter comes only if that proves
  too slow (phase 4, conditional).
- **Native channels are shortcuts.** `SendMessage` between two Claude
  sessions on one host stays allowed; it is not the protocol.
- **Cross-host.** Inboxes, locks and cards are per host. A doudou asker
  writes padme's stable inbox over `ssh padme` (its path is known without
  the card), then probes padme's lock and launches there if needed, or falls
  back.
- **A2A level: binding-shaped, not declared [author].** Field names and the
  operation mapping follow A2A, so a declared custom binding or an HTTP
  bridge stays a mechanical step. Declaring one is dropped from the build
  plan (it returns only as phase 5's conditional option):
  the filesystem binding is partly anticipated and the design borrows A2A's
  vocabulary, not its full data model (§ 3). A publication, if any, would
  rest on the measured cross-repository bug reports, the part for which
  § 3 found no matching study (pending the critic's open angles).

**Is this the cheapest local inter-runtime transport? [author]** Every
transport that starts a turn in a running session needs a per-runtime wake
adapter, so the cost difference lies elsewhere. To build, a file inbox
reuses the most of what exists (the Pi extension, `wake arm`, `codex
queue`) and needs no daemon; sockets need a listener in every session and
HTTP (alternative D) a server per agent. A shared SQLite store (agmsg,
hcom) is comparable: no required daemon, but a client in every runtime.
Reusing one (E) could be cheaper still; it stays an option if our adapters
prove harder than expected.
Cheapest of all is today's ticket-only protocol, which buys no dialogue.

### Protocol and path

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

**The path:**

0. The asker writes the REQUEST into the stable inbox, then runs
   `runtime.py guichet find <repo>`. Lock free: it launches the guichet
   **[author]** under the lock, a detached Pi session with the guichet
   profile and the model route resolves from `guichet.json`, which reads the
   waiting REQUEST on start. Lock held: nothing to launch. Two askers racing
   both try; the lock lets one guichet start. The asker never waits for the
   launch.
1. REQUEST (`submitted`), with `replyTo` → ACK
   (`working`) into the asker's inbox within **T = 5 min [author]**,
   proving the channel two-way;
2. questions and answers, at most three rounds;
3. the result (`completed`, `rejected` or `failed`), after the store line
   is written.

On start and when idle, the guichet also triages the receiving store's
`incoming` tickets, so dropped tickets reach the same desk.

**Closing [drafter's proposal].** The guichet closes itself; nobody else
does, except the author.
- **Idle for one hour**, to be measured: after an idle hour the prompt cache
  is cold, so waking the old session re-reads its whole context, which
  costs at least a fresh launch that reads only the profile and the store.
- **Before the context guard** (230K for a launched worker).
- On closing it converts open ids to `incoming` tickets, deletes its card,
  reads the inbox once more and gives anything that arrived meanwhile a
  verdict, or turns it into an `incoming` ticket when it would need a
  question round, then exits, which releases the lock. The inbox stays; the next asker's
  REQUEST launches a fresh guichet that reads whatever waits there.
- **A crash** needs no cleanup: the kernel releases the lock, and the next
  launch overwrites the stale card.
- **The author** may stop a guichet at any time (its tmux session or
  systemd unit). Lair and other sessions do not close guichets.
- **Deduplication backstop.** A REQUEST read after its asker already
  dropped the fallback ticket, or delivered twice for any reason, is
  answered with the verdict already recorded for its `contextId`
  (§ Durable record).

**Fallback** (no ACK within T, the launch fails, or Pi is down): drop an
`incoming` ticket in the receiving store citing the id, as today. The next
guichet triages it first.

**Non-blocking for the asker [author].** The asker writes the REQUEST (and
launches if needed), then continues its own work. The ACK and the result
arrive through its runtime's adapter at its next tool round, or at its
next pause for a runtime without one. It never sleeps or polls (memory
`feedback_no_blocking_waits`). A headless asker (a night sweep under
`claude -p`) that cannot wait past its turn takes the fallback directly. At
its wrap-up the asker records what it has: a verdict, or "pending at
<repo>, id X". Its next roar or lair greps the receiving store for pending
ids.

### Authorization **[author]**, and what the rule must say

The author ruled that the asker launches. Current law allows a launch "only
for authorized work that must happen now" (`rules/workflow.md` § Cross-project
work, step 3), so the ruling widens step 3; it does not narrow it. Phase 3
rewrites step 3 to give guichet runs standing authorization: triage only,
under the receiving repository's rules, memory and gate, writing tickets
only. `rules/guards.md` needs no change: the asker still writes no file in
the other project (the fallback ticket is the existing exception), and the
guichet works in its own project.

The ticket-only limit is enforced where it can be: the guichet profile,
and the Pi guard extension (`adapters/pi/extensions/idh-guard.ts`) the
guichet session loads. Where the limit cannot be enforced, the profile
states it and the observation log (§ 6) checks it.

### Model and family

- **Tier: advisor (ASSURANCE) [author]**, unless the receiving repository
  holds uncleared content, which forces LOCAL/PRIVÉ (`skills/route/SKILL.md`).
  Triage is judgment work: deciding that a foreign observation is a duplicate,
  not ours, or a symptom of a known cause.
- **Family: route's choice, free.** The author first ruled "the one
  easiest to talk to, not dogmatically the asker's". With Pi as host and a
  transport every runtime reaches, ease of talk no longer depends on family:
  route picks the model for the need `guichet.json` states, and the launch
  line records the choice and its reason, as route requires.
- **Cost.** A hosted model reached through Pi bills per API key, not under
  a runtime's subscription (local padme models and albert excepted); the
  observation records the cost per dialogue.
- **Tension with decorrelation.** The guichet's model and the asker's may
  be the same family, and
  § 3 reports that homogeneous LLM groups amplify agreement errors. The
  protocol carries the mitigation: the asker sends facts and evidence, not
  conclusions; the guichet checks them against its own store and history
  before any verdict; neither side argues toward consensus. If the
  observation shows the guichet rubber-stamping askers, revisit the family.

### Failure modes handled

| Failure | Handling |
|---|---|
| guichet crashes or stops after ACK | open ids become `incoming` tickets on stop; a crash leaves the REQUEST unrecorded, so the asker's later grep finds nothing and it drops the fallback |
| two askers launch at once | the lock lets one guichet start; the other launch is a no-op |
| guichet idle, or near its context guard | it closes itself; the inbox keeps later REQUESTs for the next launch |
| asker exits before the verdict | the store line survives; its next roar or lair reads it |
| headless asker | fallback directly |
| Pi down, or the launch fails | no ACK within T, fallback ticket |
| loops | three-round cap; Claude Code askers' messages are also throttled by their runtime (§ 3) |

### Costs

Estimates by the drafter; author-hours are review time; USD unmeasured.

| | Author-hours | Agent time | USD (rough) | Undo |
|---|---|---|---|---|
| A wording | 0.3 | one small MR | < 1 | revert one paragraph |
| B Pi-hosted | 2–3 over the phases | audit, profile and Pi extension, launcher, rule: ~4 MRs | 10–30 build; per dialogue an advisor-tier conversation through Pi plus a ticket MR, ~1–3 | revert the rule, retire the profile; the fallback is today's protocol |
| C timer triage | 1 | one skill section + timer | 5–10 build; one advisor run per sweep | disable the timer |
| D A2A server | 6+ | daemon, auth, per-runtime adapters | 50+ build, plus upkeep | stop the service |
| E reuse a bus (asking side, optional) | 1 | a trial MR, only if our asker adapters prove hard | ~5 trial; then upkeep of a pinned dependency | unpin; back to our own adapters |

The persistent guichet costs nothing while idle, but every wake re-reads
its whole context, uncached after an idle hour: unmeasured, and one of the
observation's questions.

## 6. Implementation plan

One tracker, children in order; each child one merge request. The rule
changes last, once its machinery exists **(revised after review)**.

1. **Audit [author].** (a) A Pi session started detached (tmux, then
   `systemd-run --user`) keeps running and `idh-wake.ts` delivers into it;
   the guichet's model reachable through Pi for each of route's tiers and
   each clearance level; the `flock -o` lock held for the session's lifetime,
   released by a kill even with a Pi child still running, readable without
   being taken; stopping the session stops both `flock` and Pi.
   (b) Pi with a guichet brief does triage work: ticket commands through
   bash, its own worktree, a ticket-only merge request, under `idh-guard.ts`.
   (c) One asker-side probe per runtime, including whether a `wake arm`
   waiter turns a reply file into a turn in a running Claude Code session:
   Claude Code (`wake arm` waiter),
   Codex (`codex queue`), Pi, Vibe (reply read at a pause). (d) The
   live-work join (worktree lock pid ↔ session ↔ ticket) and the
   pid-to-transcript mapping per runtime. (e) An asker subscribing to a busy
   coder's idle notice where the runtime offers one. (f) doudou → padme over
   ssh. *Proves* that Pi can host the guichet and which asker adapters are
   missing; results replace § 2's transport table.
2. **Guichet profile and launcher.** `profiles/guichet/PROFILE.md`, shell
   `agents/guichet.md` with its `tools:` grant, `Requires-tools` line; the
   verdict vocabulary, store-line format, `incoming` and `intake` tickets,
   three-round cap, the A2A field and state names, the live-work read and
   redirect rules, the informant; the card and `runtime.py guichet find`;
   the Pi card extension and `idh-wake.ts`'s preset inbox path (never
   deleted); the stable inbox directories; the lock and the idle close;
   `runtime.py launch` for a detached Pi guichet under `flock`,
   with route resolving the model; the receiver's `guichet.json` (need, not
   model) for the harness, git-erg and padme. *Proves*, by a dry run between
   two of the author's repositories, that a guichet returns a verdict and
   lands its store line by a ticket-only merge request.
3. **Rule rewrite.** `rules/workflow.md` § Cross-project work: dialogue with
   the receiving guichet first; it tickets, amends or pushes back; drop an
   `incoming` ticket when it does not answer. Step 3
   gains the guichet's standing authorization; step 2's no-authority sentence
   and step 4 stay. Callers (`roar` step 8, `raid`) cite the new wording;
   roar's tracker hand-off becomes a REQUEST, with the log line as fallback.
   *Proves* nothing new: it records what phases 1 and 2 showed.
4. **Missing adapters, conditional** (only those phase 1 finds missing and
   the observation finds costly: Vibe if replies read at its pauses prove too
   slow): an asker-side inbox adapter per runtime. *Proves* that runtime completes one REQUEST round trip as
   asker and as guichet.
5. **Report, conditional.** After the review below, if the measured
   cross-repository reports show something: a technical report (HAL) on the
   design case and its outcomes, citing § 3's state of practice. A declared
   A2A binding only if something outside this setup must talk to a
   guichet. *Proves* nothing for the harness; it is a publication choice.

**Observe, then assess.** From phase 3's merge, each guichet run adds one
field to its store line: path (guichet / fallback), model, ACK latency,
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
- **idle-wake cost** of the persistent guichet, and the cost per dialogue
  through Pi;
- **redirects**: how often the guichet sent an asker to a running session,
  and whether that session used the case or found the dialogue an
  interruption;
- **phase 5**: write the report or not.

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
(§ Protocol and path, Closing);
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
live/one-shot, persistence deferred to phase 5 (phase numbering since
superseded by the transport amendment);
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
background guichet, and phase 5 shrinks to Codex and Pi (since replaced:
the transport and one-path amendments make the path runtime-neutral and Pi-hosted, and phase 5
is now the conditional report).
**Author follow-up (2026-11-12):** the guichet must know what the
repository's other live sessions are doing, since a request may overlap
running work ("we are already doing this, I will pass your case to the
running coder"). Added § Knowing the repository's live work: read-only
signals joined by pid, no steering.
**Author rulings (2026-11-12):** A2A is not adopted, its vocabulary is
reused (§ Protocol and path, Vocabulary). The guichet does not middleman: when a live session
is better placed, it redirects the asker to talk with it directly, replacing
the relay first drafted.
**Author follow-up (2026-11-12):** asked which further state of the art
improves the design; of seven threads offered, two did and were added:
redirect to a busy session only on its idle notice (after Google SRE's
interrupt handling), and overlap detection by files in flight (after
blackboard matching). The other five confirmed existing choices and stay
out of § 3.
**Author follow-ups (2026-11-12, transport amendment):** padme is the
padme services' repository; discovery must work across Claude Code, Codex,
Vibe and Pi (a Vibe MOE cannot list Claude sessions), hence the card file,
the receiver's `guichet.json` and a runtime-neutral transport; A2A
bindings were read in the specification (§ 12 allows custom bindings, URI
identifiers, all core operations required), and the author chose
binding-shaped; a bibliographic saturation pass found the transport partly
anticipated and peer messaging across vendors' CLIs anticipated, so the
transport is reuse-first (agent-message-queue trial) and publication rests
on the measured case; the guichet sees other runtimes' sessions by
metadata first, then through a transcript-reading informant; cheapest
transport answered in § 5.
**Author follow-up (2026-11-12, lock and closing):** the review leftovers
of PRs #2467 and #2468 are folded in (redirect only to sessions whose
state is observable, preset inbox never deleted, deduplication backstop,
tier and cross-host wording, the `wake arm` probe); a guichet closes itself
when idle for an hour or before its context guard; a kernel `flock` lock,
not the card, guarantees one guichet per receiver.
**Author follow-up (2026-11-12, one path):** "Two paths is one too much."
With only Claude Code able to host, it would always be selected; Pi already
has the inbox extension and reaches every model family, so the guichet is
always Pi-hosted, route picks its model from a need stated in
`guichet.json` (never a model name), and the one-shot path, `claude --bg`
as host and the per-door write probes are removed.

KISS pass by the drafter: the FIPA/A2A mapping stays in § 3 (it fixed the
vocabulary) but adds no machinery; one path, one host runtime (Pi), one
fallback (the dropped ticket); only the asker adapters that prove costly
are built, in phase 4.
