# Guichet: triaged intake between repositories

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

The author's first direction **[author]**: talk first; the *receiving*
repository records, triages and answers with a new ticket, an amended
ticket, or pushback. After a red-team round, the author chose the simpler
form (§ 5): the asker files an intake over git, a fresh read-only triager
on the receiver's side decides, and nobody holds a dialogue session open.

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
how the superseded guichet session would have run.

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
`feedback_ticketwork_automerge`). Under C1 (§ 5) intake branches are an
exception: the asker never merges them.

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
The guichet drafts' vocabulary mapped onto it (ACK and T are retired under
C1): ACK = `agree` made mandatory with T as reply-by; NEW/AMENDED = `inform-done` with the ticket as result; PUSHBACK =
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

**What this changed in the guichet drafts** (kept for the record; C1 in
§ 5 needs only (1) and (4)). (1) Messages are notification, the ticket
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
direction). Dialogue first; the receiver writes the ticket. Amended seven
times on 2026-11-12, then rejected after the red-team round (§ 5, How the
choice was reached).

**C. Asynchronous intake by ticket, triaged on a timer** (different family:
no dialogue at all). Askers drop tickets as today, tagged `incoming`; a
scheduled triage run in the receiving repo (part of `molt`, or its own timer)
reads them, merges duplicates, rewrites them in the house voice, or closes
them with a pushback note, and logs the outcome where the asker's roar or
lair will see it. Works on every runtime today, needs no live peer; loses the
clarifying questions and answers hours later instead of minutes. **C1**,
the recommendation (§ 5), is C with an event trigger instead of a timer, an
intake branch and notes thread instead of a merged ticket, and questions
kept as notes.

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
a carrier for live dialogue, which C1 (§ 5) no longer needs; it was
considered as a carrier for B, now rejected. None of the tools examined
provides the triage role or the durable record in the receiving store, and
none documents Vibe support; their discovery features were not compared.

## 5. Synthesis and recommendation

**Pick C1 in its first variant, over git alone [author, 2026-11-12]: the
asker files an intake branch with a notes thread in the receiving
repository, launches a fresh read-only triager, and leaves. A script, not
the model, writes the verdict.** C1 is alternative C with an event trigger:
the dropped ticket stays the channel, and it now gets an owner within
minutes.

### How the choice was reached

B, a guichet session receiving dialogue, went through seven amendments on
2026-11-12 (persistent Claude `--bg` session, card file and file inboxes,
Pi-hosted single path, kernel lock, self-closing). A red-team round
(gpt-6-astra and Claude Fable, independent briefs; Review section) returned
NEEDS-REDESIGN from both seats: the inbox was an unauthenticated user turn
into a session that can run bash; the ticket-only limit was unenforced
(`idh-guard.ts` on Pi inspects only `--hard` commands and fails open);
`replyTo` was an arbitrary write; clearance looked only at the receiver; a
wedged session held its lock with no recovery; tickets laundered authority
into raid. Both seats also found the value weak: none of the six observed
cases needed a question round, and four closed within 35 minutes. What each
case needed was an owner looking promptly. The author then saw that the
redesign amounted to "drop a ticket, then wake someone to look at it", and
chose C1.

Five variants of C1 were weighed **[author]**:

| Variant | Verdict |
|---|---|
| 1. file the intake, launch a triager, leave | **chosen** |
| 2. as 1, then wait for questions, answer, repeat | folded into 1: a question is a note; the asker answers when it next looks (roar, lair), never blocking |
| 3. file and merge the ticket at once, then as 1 | rejected: the outsider's framing lands on main before triage, raid can pick it up, and a report costs two merges |
| 4. as 3, then as 2 | rejected, for both reasons |
| 5. any of these, but talk to an idle session first | rejected: it brings back an unconfined session receiving peer text, mixes unrelated context, needs discovery across runtimes, and may interrupt the author's own session; the triager's read-only live-work survey gives the same knowledge |

A forge pull request was the first carrier considered for variant 1; the
author ruled **no forge**: the intake rides on git branches and git notes,
as reviews already do (`refs/notes/review`, `scripts/review_notes.py`).

### Roles

- **Asker** states facts and evidence from its side: what it saw, where,
  with paths and commits. No orders, no patch to the receiver's files, no
  diagnosis passed off as fact.
- **Triager** (the guichet, as a role, not a session): one fresh run per
  intake, read-only, in the receiving repository. It reads the intake, the
  store, the history and the live work, and outputs one verdict.
- **Verdict script**: the only writer. It acts on the verdict and refuses
  anything outside the intake's own scope.

### The intake unit

- **Intake id** `<asker-repo>-<date>-<rand>`, minted by the asker; it is
  the deduplication key (A2A's `contextId`, § 3).
- **Receivers** are listed in one harness file with their remote URL and
  home host (harness, git-erg, padme), so an asker on any host knows where
  to push without a local checkout of the receiver.
- **Intake branch** `intake/<id>`, pushed by the asker to the receiving
  repository's remote (from that list, not the asker's own `origin`) with a
  plain `git push`, no forge API,
  together with its head ref `refs/intake-heads/<id>` and the thread. It adds
  exactly one **intake file**, `tickets/intake/<id>.md`: plain markdown, not
  an erg ticket, so erg ignores it (probed: `erg check` passes with such a
  file present) and the asker needs neither the receiver's erg nor an ID
  claim in its store. The file opens with `Origin: <asker-repo>` and
  `Intake: <id>` lines, then the facts and the evidence. erg's ticket header
  set is closed **[author]**, so these lines never go into an erg ticket.
  The branch sits on a base the request note records (the receiver's `main`
  at filing). The asker never merges it.
- **Intake thread** on `refs/notes/intake`: one note per intake on a fixed
  anchor (`git hash-object` of `idh-intake <id>`), one JSON object per line,
  `ts` first: `request`, `answer` (asker); `verdict` (triager, through the
  script); `promoted`, `declined`, `resume` (owner); `held` (script or
  sweep); each with its author and the branch head. Transport and concurrent-write merging are
  those of `refs/notes/review` (glob fetch refspecs, `cat_sort_uniq`, sync
  without force); the code is a sibling of `review_notes.py` sharing its
  transport layer, with its own entry schema and lock (review entries and
  locks are review-specific). The asker's head is kept at
  `refs/intake-heads/<id>`; branch and head ref are deleted together, after
  a PUSHBACK or once a promoted intake has landed.
- Verdict states keep A2A's names: `completed` (NEW or AMENDED), `rejected`
  (PUSHBACK), `input-required` (QUESTION), `failed` (the triager could not
  decide).

### The flow

1. The asker pushes the intake branch and appends the `request` note.
2. It tries `runtime.py triage <receiver> <id>` on the receiver's host
   (over `ssh` from another host). The launcher, a script, first writes
   the run's inputs as files into a run directory: the intake branch's
   diff, the intake thread, the recent history of the paths the intake
   cites, and a live-work snapshot (worktree locks with their tickets and
   liveness, each live branch's changed files). It then
   starts one headless run with read-only tools only (Pi: `--tools
   read,grep,find,ls`, no extensions), **inside a sandbox that makes only
   the receiving repository and the run directory readable** (a
   `systemd-run --user` unit with read-only bind mounts, or `bwrap`;
   phase 1 proves it, including that the model's credentials reach the
   runtime without being readable by its `read` tool), capped in wall time,
   model by route at the advisor tier **[author]**. Runs are serialized per
   receiver by `flock -o`; the launcher holding the lock drains every
   `runnable` intake of that receiver (§ Intake lifecycle), one fresh run each, and after releasing
   the lock scans once more, relocking if anything arrived meanwhile, so a
   second launch that finds the lock held can just leave. A failed launch is harmless: the intake stays
   durable and the sweep (step 6) finds it. The asker leaves.
3. The triager reads the run directory, the receiving store and its
   history (§ Knowing the repository's live work below), and prints one
   verdict as JSON.
4. The verdict script acts, after checking that the asker's commits
   (from the recorded base to `refs/intake-heads/<id>`, the asker's
   submission) add exactly one `tickets/intake/<id>.md` and nothing else,
   and
   that the branch tip satisfies the invariant of the intake's state
   (§ Intake lifecycle below).
   **It never lands anything on main [author].** It pushes its commit and
   notes to the receiver's remote and records the prepared head in the
   verdict note; from then on the prepared head, not the asker's, is the
   reference. A crash repair compares the tip with the recorded prepared
   head: equal means the action is done.
   **The asker pushes only when filing.** Corrections come as `answer`
   notes, or as a new intake with a new id.
   - **NEW**: in one commit on the intake branch, creates the ticket with
     `erg new` (an ID claimed by the receiver), written in the receiver's
     voice and labelled `needs-human`, adds the erg log line `intake <id>
     from <asker-repo>`, and deletes the intake file; the owner's promotion
     lands it;
   - **AMENDED**: in one commit, adds to the existing ticket the erg log
     line `intake <id> from <asker-repo>` with the report quoted as data,
     never touching the ticket's scope or exit criteria, and deletes the
     intake file; the owner's promotion lands it.

   Either way the prepared head's net change against `main` touches only
   `tickets/*.erg` (and claims), so the intake file never reaches `main` and
   the promotion is bookkeeping tier with no gate change.
   - **PUSHBACK**: writes the reason in the thread and deletes the intake
     branch;
   - **QUESTION**: writes the question in the thread and stops.

   Every outcome is a `verdict` note first, so a crash between note and
   action is repaired by rerunning the action.
   **Promotion.** The receiver's `/dashboard` lists intakes awaiting
   promotion (NEW or AMENDED, prepared, not landed). An owner (the author,
   or a session of the receiver acting with the author's leave) promotes
   one by opening the receiver's ordinary merge request for the intake
   branch at exactly the prepared head and writing a `promoted` note, or
   declines it with a `declined` note and a reason. Once `promoted`, the
   receiver's merge process owns the branch (a rebase before the gate is
   normal); an owner who closes the promotion without merging writes a
   `declined` note. Promotion is the owner's
   decision, so the automerge habit for ticket-only requests applies from
   that point on. A NEW ticket keeps `needs-human` after landing unless the
   owner removes it in the promotion.
5. The asker reads the outcome when it next looks (its roar or lair):
   `git fetch` of the receiver and the intake thread. It answers a question
   with an `answer` note and relaunches the triager (a failed relaunch is
   caught by the sweep), at most three rounds;
   unanswered after seven days, the triager decides on what it has (a
   failure to decide is a `failed` verdict like any other).
6. **Sweep.** The receiver's `/molt` applies the lifecycle table below:
   it runs the triager on runnable intakes older than an hour, decides
   questions unanswered for seven days, retries failures, and deletes the
   branch and head ref of finished intakes. `/dashboard` lists intakes
   runnable, waiting on a question, failed, prepared, promoted and held. The launch in step 2
   is therefore never a single point of failure.

### Intake lifecycle

The state of an intake is read from the last entry of its thread and, for
`landed`, from the receiver's `main`. Each state fixes what the branch tip
must be; a tip that breaks its state's invariant moves the intake to
`held` (from any state with an invariant), with no retriage.

| State | Entered by | Tip invariant | Next |
|---|---|---|---|
| `runnable` | a `request` note, or an `answer` note while `waiting` (an answer moves no other state) | the asker's head | the launcher runs it at once (no delay); the sweep after an hour |
| `waiting` | a QUESTION verdict | the asker's head | `runnable` on an answer; after seven days, or after the third round, the triager decides on what it has |
| `prepared` | a NEW or AMENDED verdict, with its prepared head | the asker's head while the script's commit is pending (the sweep pushes the very commit whose sha the verdict recorded, kept under `refs/intake-heads/<id>-prepared`), then the prepared head | `promoted` or `declined` by an owner |
| `promoted` | the owner's `promoted` note, written before the merge request is opened at the prepared head | owned by the receiver's merge process | `landed`, or `declined` by the owner's note if closed unmerged |
| `landed` | a ticket on the receiver's `main` carries the log line `intake <id> from …` (NEW and AMENDED alike) | none | finished; the sweep deletes branch and head ref |
| `rejected` | a PUSHBACK verdict | none | finished; branch and head ref deleted, by the script or the next sweep |
| `declined` | an owner's `declined` note (also written when a promotion is closed unmerged) | none | finished; deleted as above |
| `failed` | a `failed` verdict | the asker's head | `runnable` again, twice (failures counted since the last `resume`); then `held` |
| `held` | a broken tip invariant, or a third failure, recorded as a `held` note with the reason and the state it left | none enforced | an owner's `resume` note returns it to the state it left (to `runnable` when it left `failed`), after the owner has reset the branch to that state's recorded head if the tip moved; or a `declined` note; the sweep skips it |

"Landed" is detected on `main`, not from the branch, so a merge that
rebases or deletes the branch is still recognized.

### Knowing the repository's live work

Unchanged in substance, now read-only and pre-computed: the launcher's
snapshot gives worktree locks (ticket and owner pid), pid liveness, claims,
open branches and each live branch's changed files, and the triager
matches the intake's evidence paths against them. A shared path is the overlap signal. On
overlap the verdict is AMENDED on the running ticket, naming the branch
and session, or PUSHBACK "in progress on `<branch>`". It never messages a
session, never steers one, and never reads a transcript: the informant and
the redirect of earlier drafts are dropped, since they reached into other
sessions.

### What the red team's findings become

| Finding | Under C1 |
|---|---|
| peer text as a user turn into a shell | the triager has no shell; git and `/proc` are read by the launcher script, and the intake is a file the triager reads as data |
| ticket-only unenforced | the model writes nothing; the asker may add only its intake file; the script writes only `tickets/*.erg` (through erg) and deletes the intake file, refuses any other path, and records the exact head the owner may promote |
| `replyTo` arbitrary write | gone: replies are notes in the thread |
| clearance on the receiver only | clearance is the stricter of asker and receiver, defaulting to uncleared; the sandbox makes only the receiving repository and the run directory readable. Until phase 1 proves the sandbox, C1 does not run where the host holds uncleared material outside the receiver: a local model would stop leaks to a provider, not quotes into a ticket |
| wedged session, lost request | no session to wedge; a run has a wall-time cap; branch and notes are durable before any run starts |
| authority laundering | origin kept in the erg log line and the intake thread; nothing lands without an owner's promotion; `needs-human` on every NEW |
| cost runaway | one run per intake, serialized per receiver, a daily cap per receiver in the launcher |
| cross-host replies | git remotes reach every host |

### Authorization and the rule

`rules/guards.md` allows, in another project, tickets only. C1 widens that
exception from "a ticket" to "an intake branch adding one file under `tickets/intake/`, its head
ref under `refs/intake-heads/`, and its intake note". Rules are the author's law, so phase 3 proposes the wording
and the author decides. The asker's launch of a triager in the receiving
repository is the standing authorization the author ruled for: triage
only, under that repository's rules, read-only.

### Model and family

Route picks the model for the triage role at each launch; the tier is
advisor by the author's ruling, recorded on route's side; uncleared content
forces a local model. Any runtime whose headless door supports read-only
tools can run it (Pi's does; another runtime only once its door is shown
to confine reads, phase 1). The asker and the
triager may be the same family; the mitigation is the protocol's: facts
from the asker, checks against the receiver's own store, no argument
toward consensus.

### Failure modes handled

| Failure | Handling |
|---|---|
| launch fails, model unavailable, Pi down | intake stays; the sweep relaunches |
| triager crashes mid-run | no verdict note; the sweep relaunches |
| crash after the verdict note | the action is rerun from the note |
| two askers file the same bug | the draining launcher triages them in turn; the second finds the first: AMENDED |
| asker gone before the verdict | the thread and the store keep the outcome |
| question never answered | decided after seven days |
| notes written concurrently | `cat_sort_uniq` merge, as for reviews |

### Costs

Estimates by the drafter; author-hours are review time; USD unmeasured.

| | Author-hours | Agent time | USD (rough) | Undo |
|---|---|---|---|---|
| A wording | 0.3 | one small MR | < 1 | revert one paragraph |
| C1 (variant 1) | 1.5 | notes and launcher, verdict script, profile, rule: ~4 MRs | 5–15 build; one advisor run per intake | revert the rule; intakes revert to plain dropped tickets |
| B guichet, as amended through PR #2470 | 3+ | ~6 MRs plus Pi extension work | 10–30 build | superseded by the red-team round |
| D A2A server | 6+ | daemon, auth, adapters | 50+ build, plus upkeep | stop the service |

## 6. Implementation plan

One tracker, children in order, each one merge request. The rule changes
last.

1. **Intake plumbing.** The receivers list; `refs/notes/intake` (a sibling
   of `review_notes.py` sharing its transport); the intake branch, base and
   head conventions; `runtime.py triage` (run directory, sandbox with
   credentials kept unreadable, read-only tools, `flock -o` with the drain
   and rescan, wall-time and daily caps, model by route); and the verdict
   script with its range and tip checks. *Proves*, by a dry run between two
   of the author's repositories, each verdict: NEW and AMENDED leave a
   prepared head for the owner to promote, PUSHBACK deletes branch and head
   ref, QUESTION waits and resumes on an answer; each move into `held` and
   out by `resume`; `declined` from `prepared` and from `promoted`; `landed`
   detected after a rebase merge; and that the sandbox denies a read outside
   the receiver.
2. **Triage profile.** `profiles/guichet/PROFILE.md` and its shell: facts
   against framing, duplicate search, the live-work read, clearance as the
   stricter of the two repositories, the verdict format. *Proves*, on the
   six observed cases of § 2 replayed as intakes, that the verdicts match
   what the owners eventually did.
3. **Rule rewrite.** `rules/workflow.md` § Cross-project work: file an
   intake and launch the triager, instead of dropping a ticket; the
   `rules/guards.md` exception widened to intake branches and notes, for
   the author to decide. Callers (`roar` step 8, `raid`) cite the new
   wording. *Proves* nothing new: it records what phases 1 and 2 showed.
4. **Sweep and promotion view.** `/molt` applies the lifecycle table
   (§ 5, Intake lifecycle); `/dashboard` lists every state but the
   finished ones. *Proves* that an intake whose launch failed, or
   whose answer's relaunch failed, gets a verdict within a day.
5. **Report, conditional.** After the review below, if the data show
   something: a HAL technical report on the design case and its outcomes,
   citing § 3.

**Observe, then assess.** Each verdict note records the model, the run's
duration and cost when known, the rounds, and the time from request to
verdict. **Review after 20 intakes or six weeks after phase 3, whichever
comes first**, in a doctor-journal revisit (memory
`feedback_no_wait_tickets`), deciding:

- **value**: how many verdicts changed what a plain dropped ticket would
  have become (duplicate merged, premise corrected, refused with reason),
  against the § 2 cases as baseline;
- **speed**: time to verdict against the pre-C1 waits;
- **tier**: keep advisor, or step down if owners never reverse verdicts;
- **questions**: how often a round was needed; near zero confirms dropping
  the dialogue;
- **upgrade to C2** (a raw note in an inbox before any ticket) only if
  outsider text in intake branches proves harmful or askers need answers
  sooner than their next roar.

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
(a section of the superseded guichet design, in git history);
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
sections of the superseded guichet design, in git history;
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
reused (vocabulary section of the superseded design, in git history). The guichet does not middleman: when a live session
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

**Red-team round (2026-11-12), on the design as merged through PR #2470.**
Same brief to two seats, attack surfaces named, conclusions not given.
- *Seat A: OpenAI gpt-6-astra @medium* (other family, `codex exec`,
  read-only). NEEDS-REDESIGN. Critical: prompt injection into an
  unconfined executor; no trust boundary on inboxes, cards or locks;
  `replyTo` and informants open to exfiltration. High: delete-before-record
  loss; no cost bound; tickets laundering authority. Medium: benefit
  unproven, alternative C credible.
- *Seat B: Anthropic Claude Fable* (advisor model, subagent, read-only).
  NEEDS-REDESIGN. Critical: inbox as an unauthenticated user turn into a
  shell; ticket-only unenforced (`idh-guard.ts` on Pi checks only `--hard`;
  the bookkeeping fast track also covers `memory/` and `STATE.md`). High:
  `replyTo` arbitrary write; clearance on the receiver only; lock held while
  wedged; laundering into raid. Medium: cross-host replies, cost. Value:
  weak against the observed cases; C with a trigger, a fresh read-only run
  and a scripted writer wins.
- The drafter verified each code claim (`idh-guard.ts:162-167`,
  `idh-wake.ts` delete right after delivery, `merge-gate.py` bookkeeping
  list, `~/.local` mode 0700 with every agent under one account).

**Author rulings (2026-11-12, intake file):** intake files live under
`tickets/intake/` and are not erg tickets; erg's header set is strictly
closed, so `Origin:` and `Intake:` appear only in the intake file, and the
erg ticket records the origin as a log line, which landing detection reads.

**Author ruling (2026-11-12, landing):** option (b): the triager never
lands; accepted intakes land through the receiver's normal merge process
at the owner's promotion. Gaze rv-20261112-pr-2473-165b had found that the
local gated merge refuses `branch:` units in a repository with an `origin`.

**Author rulings (2026-11-12, C1):** "looks like it starts by dropping a
ticket, then try waking up someone"; "Just C1"; variants 1 to 5 discussed,
variant 1 chosen with questions folded in; "NO FORGE, git notes". § 5 and
§ 6 rewritten accordingly; the guichet machinery of PRs #2460 to #2470
(sessions, inboxes, cards, locks, A2A message protocol, Pi extension,
informant, redirect) is superseded and kept in git history. T = 5 min and
the reused session, earlier author rulings, are retired with it.

KISS pass by the drafter: one branch, one notes thread, one read-only run,
one writer script, one sweep. The A2A state names stay as labels only.
