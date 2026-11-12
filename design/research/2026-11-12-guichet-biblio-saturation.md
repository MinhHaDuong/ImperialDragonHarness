# Bibliographic saturation: guichet transport and cross-repository bug reports

Run 2026-11-12 for `design/2026-11-12-guichet-inter-repo-dialogue.md` § 3,
by the `biblio-saturation` skill. Coverage status: **partial** for all three
claims (completeness critic below); no claim meets the saturation conditions.

| Phase | Worker | Independence |
|---|---|---|
| search, three blind angles | Claude, pinned `sonnet` | blind to each other |
| adversarial judgment | Claude Fable | same family as searchers; re-fetched primary texts |
| completeness critic | OpenAI gpt-6-astra @medium, `codex exec` read-only | other family; logs only, no web access |

## Claims and verdicts

- **C1**, first to specify an A2A custom binding over the local filesystem
  (card file, inbox directories, atomic rename, pid liveness): **partly
  anticipated**. No such binding among the a2aproject proposals we examined
  as of 2026-11-12; each ingredient exists elsewhere.
- **C2**, coding-agent CLIs of several vendors talking live as peers through
  one standard protocol: **anticipated** (synapse-a2a, a2abridge, a2a-serve;
  evidence partly self-declared by those projects).
- **C3**, a measured report of coding agents in one repository reporting bugs
  to a repository or service they depend on: **not found** in the searches
  described; coverage partial (no Semantic Scholar, OpenAlex or HAL search;
  several exclusions from abstracts only).

Safe wording for C3: "We did not identify a matching study in the searches
described."

## Pending angles (critic)

Non-English and HAL searches; surveys and citation trails (from Lin et al.
2022, Saeidi et al. 2025, Maaz et al. 2025, tap); tuple-space and blackboard
systems; theses (TU Delft); AWCP full text; full texts behind the nine
abstract-only exclusions; feature history and tests of the C2 bridges;
bug tossing, misrouted reports, duplicate detection, service incident
reporting.

## Adversarial judge ledger

## biblio judge, phase 3 (2026-11-12)

Judge re-fetched every primary text cited below (GitHub REST/GraphQL via `gh api`,
raw files, arXiv API + arXiv HTML full text, PyPI/npm JSON, one publisher PDF).
Same-family judge as the searchers: no independent reviewer. Tool fields come from
READMEs and docs; nothing was installed or run.

### Summary (final answer)

#### Verdicts per claim

**C1: partly anticipated. Do not write "first".**
No A2A binding over the local filesystem appears among the a2aproject
proposals as of 2026-11-12 (STDIO #2048, WebSocket #1864, SLIMRPC, email #2191,
fmsg #2185, Agent Messaging #2438). Each ingredient exists elsewhere:
- a local, socket-free A2A binding with the pid in the session binding and a
  card obtained out of band: #2048;
- store-and-forward A2A bindings for offline agents: #2191, #2185, #2438;
- one registry file per agent at a fixed path, written by atomic replace,
  holding the pid, liveness by `os.kill(pid, 0)`: synapse-a2a;
- inbox directories with claim by atomic rename for coding agents, without
  A2A: a2a-relay, abq, agent-message-queue, pi-messenger, tap.

The label is also wrong. The design note adopts A2A's vocabulary, not A2A,
and A2A requires of a custom binding that "All core operations must be
supported".

Safe wording: "a filesystem transport that borrows A2A's vocabulary. We found
no A2A binding over the local filesystem among the proposals published by
2026-11-12; the closest are the STDIO and store-and-forward proposals, and
file-mailbox tools that do not use A2A."

**C2: anticipated. Drop the claim.**
synapse-a2a (first release 2025-12-31), a2abridge (2026-05-09) and the
official a2aproject/a2a-serve (v0.1.0, 2026-11-11) each put coding-agent CLIs
of several vendors on A2A as peers. agmsg, hcom, repowire,
agent-message-queue and tap do it over their own protocols. Cite them as the
state of practice.

**C3: novel within the examined scope; coverage partial.**
We found no study measuring coding agents in one repository reporting defects
to a repository they depend on, with outcomes. Nearest: agentic PBT (the
authors selected and reported 5 bugs), tap (one repository, review
artifacts), the repowire draft (routing agreement, "no result here concerns
downstream task outcome"), and the human upstream-bug literature.
Safe wording: "To our knowledge, no published study measures bug reports sent
by coding agents working in one repository to a repository they depend on,
with their outcomes. Our observations come from one author's fleet of N
repositories, not from open-source upstreams."

#### must_cite

A2A issues #2048 and #2191; synapse-a2a; a2abridge; a2a-serve;
agent-message-queue; abq; a2a-relay; repowire; agmsg; hcom; Kim, tap, arXiv
2606.14445; Maaz et al., arXiv 2510.09907; Saeidi et al., arXiv 2511.04986;
Lin et al., EMSE 27:134 (2022), doi 10.1007/s10664-022-10173-y.

#### Unresolved

- AWCP arXiv 2602.20493: abstract only (C1, low risk).
- bamboo-subagent, agent-team-mail-core, mabl blog, curl reports, TU Delft
  thesis: not re-fetched (background).
- A2A conformance of synapse-a2a and a2abridge: self-declared, untested.
- C3 gaps: no forward-citation trail from Lin 2022 or arXiv 2511.04986, no
  Semantic Scholar or OpenAlex, HAL blocked. The judge's six arXiv probes and
  three web searches found nothing new.

#### Reuse comparison (README-level, nothing installed; "unv." = unverified)

Runtimes column: Claude Code / Codex / Pi / Mistral Vibe.

| Tool | Runtimes | Daemon | Two-way | Durable store | Licence | Maturity | Starts a turn in an idle session |
|---|---|---|---|---|---|---|---|
| agent-message-queue | yes/yes/yes/no | no broker; a wake process per agent | yes | files, fsync + rename | MIT | 92 stars, v0.142.1, 2026-11-12 | yes: tty doorbell, `codex queue`, `claude --print` |
| hcom | yes/yes/yes/no | none stated; launch through `hcom` | yes | SQLite | MIT | 656 stars, v0.7.31, 2026-10-21 | yes |
| repowire | yes/yes/yes/no | yes | yes | daemon store | MIT on PyPI; no LICENSE file | 272 stars, v0.21.1, 2026-10-27 | yes |
| agmsg | yes/yes/no/no | none; optional agmsgd beta | yes | SQLite WAL | MIT | 1581 stars, v1.7.2, 2026-11-12 | Claude Code yes; Codex only with agmsgd |
| a2abridge | yes/yes/no/no | yes, directory service | yes | `./.a2a/inbox.json`; restart unv. | MIT | 16 stars, v4.0.3, 2026-10-29 | off by default; opt-in `A2A_NUDGE`, unv. |
| synapse-a2a | yes/yes/no/no | an A2A server per agent, wrapping a PTY | yes | registry only; message store unv. | MIT on PyPI; no LICENSE file | 19 stars, v0.35.0, 2026-05-03 | yes, writes into the PTY |
| a2a-serve | yes; others via ACP, unv. | yes; Docker by default | yes | SQLite; running tasks fail on restart | Apache-2.0 | 5 stars, v0.1.0, 2026-11-11 | only in sessions it manages |
| tap | yes/yes/no/no | none central; Codex bridge | yes | markdown files in `inbox/` | MIT on npm; no LICENSE file | 39 stars, v0.6.1, last push 2026-06-20 | unv. |
| a2a-relay | generic CLI, no adapters | no | yes | JSON files + JSONL log | MIT | 0 stars, no release, 2026-05-11 | no |
| abq | generic CLI, no adapters | no | yes | JSON files | MIT | 0 stars, no release, 2026-01-29 | no |

No tool supports Mistral Vibe. Three cover Claude Code, Codex and Pi:
agent-message-queue, hcom and repowire. agent-message-queue is nearest to the
transport as designed (files, rename, no broker, wake of idle sessions);
repowire is nearest to the use case ("Ask another repo"). Price a trial of
agent-message-queue before building. None provides the triage role, which
sits above the transport.

### Evidence ledger (one verdict per candidate)

Format: candidate — verdict (claim) — passage — locator — what was read.

#### C1 candidates

1. **a2aproject/A2A issue #2048**, "[Porposal] : STDIO Custom Protocol Binding
   for A2A", hackeramitkumar, 2026-07-12, open, 2 comments — **must_cite** (C1).
   "the client spawns the agent as a subprocess and exchanges messages over its
   `STDIN`/`STDOUT` pipes ... There is no listening socket, no port, and no
   network endpoint" (issue body, Abstract). Draft spec
   `hackeramitkumar/A2A@stdio_spec:docs/bindings/stdio.md`: handshake carries
   `"pid": 42137` (§2.2); "Liveness is primarily detected by the operating
   system: if either process exits, the peer observes end-of-file (EOF)"
   (§2.3); "the Agent Card is typically obtained out-of-band (for example,
   shipped alongside the executable or provided by the host's agent
   configuration)" (§10). Difference: pipes between parent and child, no
   files, no inbox, no peer that outlives the caller. Read: issue, comments,
   spec sections 2, 9.6, 10.
2. **a2aproject/a2a-rs issue #15**, "task: add stdio transport binding",
   2026-04-04, open — **does_not_preempt** (C1). "Add a stdio transport binding
   for subprocess-hosted agents using stdin/stdout ... The existing bindings
   are network-oriented." (body, Summary/Why). Difference: an SDK task for
   stdio; no file transport. Read: issue body.
3. **a2aproject/A2A issue #2191**, "MailA2A custom protocol binding for
   store-and-forward email", 2026-08-30, open — **must_cite** (C1). "maps A2A
   v1.0 operations and data onto RFC 5322 email threads and MIME parts. The use
   case is asynchronous, store-and-forward agents" (Abstract). Spec
   `kotoba-lang/mail-a2a:spec/v1.md`: "`url` MUST be a `mailto:` URI" (line
   54); no occurrence of Maildir, mbox or filesystem delivery (grep). Difference:
   email transport; local delivery format unspecified. Found by the judge.
   Read: issue body, spec grep.
4. **a2aproject/A2A issues #2185 (fmsg), #2438 (Agent Messaging), discussion
   #792 (broker "Agent Inbox Pattern")** — **does_not_preempt** (C1). #2438:
   "keep messages while the agent is away and deliver them in order when it
   returns" over "NATS JetStream and RabbitMQ" (Motivation, Reference
   implementation). Difference: brokers and federated mail, not a filesystem.
   Found by the judge. Read: issue bodies; #792 first post and file-related
   comments.
5. **Hosuke/a2a-relay** (MIT, 0 stars, created 2026-05-08, last push
   2026-05-11) — **must_cite** (C1). "The first transport is a filesystem
   mailbox that can live on a jump host" (README, intro); "`poll` first
   atomically claims a file into `processing/<agent>/`" and "`heartbeat` —
   liveness ping" (README, "v0.2 reliability semantics" and message types).
   Difference: own message schema, no reference to the A2A specification, no
   agent card, no pid (README grep for "agent card", "well-known", "pid",
   "a2a-protocol": no hit). Read: README in full.
6. **aygp-dr/abq** (MIT, 0 stars, 2026-01-28/29) — **must_cite** (C1, and the
   inter-repository use case). "A minimal file-based message bus for
   coordinating AI agents across repositories, worktrees, and processes";
   "Test agent in repo A needs to signal app agent in repo B"; "recv() claims
   via atomic rename"; message `from` carries `"pid": 12345`; `abq check
   --channel "$worker" --alive` (README, Problem Statement, Maildir Format,
   Architecture). Difference: no A2A vocabulary or card; A2A appears only in a
   cited survey (README line 547). Read: README.
7. **avivsinai/agent-message-queue** (MIT, 92 stars, v0.142.1 2026-11-12) —
   **must_cite** (C1, C2, reuse). "Each agent has an inbox and an outbox under
   a local queue root ... AMQ writes and syncs a temporary file, then publishes
   it with a rename" (README, "How it works"); "This walkthrough connects
   Claude Code and Codex CLI on one machine" (Getting started); pi bridge:
   "Every fact crosses the filesystem as a complete, atomically published file"
   (`docs/pi-bridge-protocol.md`). Difference: no A2A (grep over README,
   INSTALL, COOP, adapter, routing, wake docs: no hit). Read: README, INSTALL,
   COOP, four docs.
8. **s-hiraoku/synapse-a2a `synapse/registry.py`** — see C2 item 11; for C1
   it shows the registry-file pattern: `~/.a2a/registry/<agent>.json`, "Write
   JSON file atomically via temporary file + replace", `"pid": os.getpid()`,
   `os.kill(pid, 0)` (registry.py lines 61-64, 143-155, 236). Message delivery
   is UDS/HTTP, not files.
9. **nicobailon/pi-messenger** (743 stars, last push 2026-10-30) —
   **does_not_preempt** (C1, C2). "All coordination is file-based, no daemon
   required. Shared state (registry, inboxes, swarm claims/completions) lives
   in `~/.pi/agent/messenger/`" (README line 415); "An extension for Pi coding
   agent" (line 7). Difference: Pi only, no A2A. Read: README grep.
10. **AWCP, arXiv 2602.20493** — **unresolved** (C1). Abstract only: "decouples
    a lightweight control plane from pluggable transport mechanisms, allowing a
    Delegator to project its workspace to a remote Executor". The abstract
    describes files as the delegated payload, not as the message channel; the
    full text was not read. Attempt: arXiv API abstract.

#### C2 candidates

11. **s-hiraoku/synapse-a2a** (PyPI 0.1.0 on 2025-12-31, 0.35.0 on 2026-05-03,
    189 releases; repo 19 stars) — **preempts** (C2). "A framework that enables
    inter-agent collaboration via the Google A2A Protocol while keeping CLI
    agents (Claude Code, Codex, Gemini, OpenCode, GitHub Copilot CLI) exactly
    as they are"; "Codex receives an A2A message from Claude"; "Each agent
    publishes an Agent Card at `/.well-known/agent.json`" (PyPI description,
    lines 12, 42, 1398). Read: PyPI long description, registry.py.
12. **vbcherepanov/a2abridge** (MIT, 16 stars, v1.0.0 2026-05-09, v4.0.3
    2026-10-29) — **preempts** (C2). "wrap each agent into a standard A2A 1.0
    peer"; "Each running agent is an A2A peer. Agent Card on
    `/.well-known/agent-card.json`, JSON-RPC (`POST /`) and HTTP+JSON bindings
    served by the official a2a-go SDK"; installer targets Claude Code, Codex
    CLI, Cline, Continue, Cursor, Gemini CLI, Antigravity CLI (README, "The
    pain it solves", "What you get", "What the installer does"). For C1:
    transport is HTTP loopback with a directory daemon on 127.0.0.1:7777;
    the inbox file `./.a2a/inbox.json` is written by the receiving bridge.
    "the bridge doesn't wake idle agents" (README, inbox flow) against
    `A2A_NUDGE` "wake an idle agent on inbound" (env table). Read: README.
13. **a2aproject/a2a-serve** (Apache-2.0, created 2026-10-26, v0.1.0
    2026-11-11, 5 stars) — **preempts** (C2). "Turn opencode, Claude Code, or
    any ACP coding agent into a sandboxed A2A agent that people, messengers,
    and other agents can call" (README, first line); "The agent calls your
    contacts and webhook nodes with the `a2a` CLI" (`docs/guide/agent2agent.md`).
    Found by the judge. Read: README, supported-agents, agent2agent,
    architecture.
14. **Kim, "tap: A File-Based Protocol for Heterogeneous LLM Agent
    Collaboration", arXiv 2606.14445v1 (2026-06-12)** — **must_cite** (C2, C3).
    File-based: "a markdown message containing YAML metadata is first written
    to inbox/" (§3). Not A2A: "Google A2A [7] ... assumes HTTP/SSE-based
    network connectivity and therefore addresses a different problem" (§1).
    Measured: "209 tap-related pull requests and 717 operational artifacts ...
    375 review artifacts ... 69.8% for heterogeneous model pairs and 53.1% for
    homogeneous model pairs" (abstract, Table 3). Difference for C3: "conducted
    in one operational repository" (§5 Limitations (3)); no report to another
    repository. Read: full HTML.
15. **fujibee/agmsg** (MIT, 1581 stars, v1.7.2) — **must_cite** (C2).
    "Claude Code, Codex, Gemini CLI, GitHub Copilot CLI, and any other CLI
    agent message each other directly through a shared local SQLite database";
    "Not MCP ... just `bash` + `sqlite3`" (README lines 22, 31). Difference: own
    protocol, not a standard. Read: README.
16. **aannoo/hcom** (MIT, 656 stars, v0.7.31) — **must_cite** (C2). "Works with
    `claude` `codex` `opencode` `grok` `hermes` `pi` ..."; "Hooks record
    activity to a local SQLite database and deliver messages from it"; "wake
    idle agents immediately" (README lines 9, 92, 102). Difference: own
    protocol. Read: README.
17. **prassanna-ravishankar/repowire** (272 stars, v0.21.1) — **must_cite**
    (C2, C3 use case). "Claude Code in one repo, Codex in another ... Repowire
    gives them names and lets them pass messages"; "Project A needs the real
    API shape from Project B. Ask `project-b`; the peer answers from its live
    checkout" (README line 17, "Ask another repo"). Its unpublished draft
    `paper/latex/main.tex` ("When Routing Benchmarks Reward Repetition", draft
    of 14 October 2026, TODO markers) measures "908 routing decisions
    reconstructed from the event journal of a production agent mesh" and
    states "no result here concerns downstream task outcome" (abstract, §1).
    Difference: own protocol; the draft measures recipient agreement, not
    report outcomes. Read: README, draft abstract and §§1-2.
18. **Gemini CLI remote subagents**
    (`google-gemini/gemini-cli:docs/core/remote-agents.md`) —
    **does_not_preempt** (C2). "Gemini CLI supports connecting to remote
    subagents using the Agent-to-Agent (A2A) protocol ... delegating tasks to
    remote services" (line 3). Difference: one vendor's CLI as an A2A client of
    remote services, not CLIs of several vendors as peers. Note for C1: the
    card can be a local file entry, `agent_card_json` in `.gemini/agents/*.md`.
    Read: doc file.

#### C3 candidates

19. **Maaz, DeVoe, Hatfield-Dodds, Carlini, "Agentic Property-Based Testing",
    arXiv 2510.09907v1** — **must_cite** (C3). "we selected the following
    particularly interesting bugs to report to the original developer" (§4,
    "Reported bugs"); "We reported 5 bugs, 4 with patches ... with 3 patches
    merged" (abstract). Difference: the authors select and report; the agent
    scans packages and is not a consumer working in a dependent repository;
    n = 5; no duplicates, latency or fan-out. Read: full HTML.
20. **Saeidi et al., "What About Our Bug?", arXiv 2511.04986v1** —
    **must_cite** (C3, human baseline). "30,340 bug reports across 500 of the
    most depended-upon npm packages ... median project-level responsiveness of
    70%" (abstract); RQ1 concerns "bug reports submitted by downstream
    developers" (§III-A); LLMs classify issues (§III-C). Difference: human
    reporters. Read: full HTML.
21. **Lin, Zhang, Adams, Hassan, "Upstream bug management in Linux
    distributions", EMSE 27:134 (2022)** — **must_cite** (C3, human baseline).
    "13.9% of the upstream package bugs are explicitly reported being fixed by
    upstream, and 13.3% being fixed by the distribution" (abstract, p. 1).
    Difference: human maintainers, Debian and Fedora. Read: PDF p. 1.
22. **Li, Zhang, Hassan, "AIDev", arXiv 2602.09185v1** — **does_not_preempt**
    (C3). "a large-scale dataset focused on agent-authored pull requests";
    issues appear as "GitHub issues related to PRs" (abstract; Table 1).
    Difference: pull requests inside the target repository; no agent-filed
    report to a dependency. Read: full HTML.
23. **arXiv 2603.20847, 2607.04697, 2603.03194, 2604.04059, 2606.13468,
    2505.20749, 2601.00205, 2509.14745, 2602.00164** — **does_not_preempt**
    (C3), abstracts only. Each abstract states its object: bugs in the agent
    tools' own trackers, agent pull requests (conflicts, references, rejection,
    merge latency), cross-repository benchmarks, dependency decisions. None
    states agents reporting to a dependency with outcomes. Read: arXiv API
    abstracts.

### Search probes by the judge (dated 2026-11-12)

- GitHub issue and PR search in org a2aproject: "filesystem binding",
  "file-based transport", "unix domain socket", "mailbox", "inbox directory",
  "maildir", "custom protocol binding"; title search "binding"; discussions
  search (4 queries). New: #2191, #2185, #2438, #792, a2a-serve.
- GitHub repository search: 6 queries on A2A + filesystem/maildir. Only
  a2a-relay.
- arXiv API: 6 queries on agents filing upstream bug reports. Nothing new.
- WebSearch (standard): 3 queries (C3 twice, C1 once). Nothing new.
- README grep for "mistral|vibe" over all ten tools: no support found.

## Completeness critic (verbatim)

**Verify — completeness assessment.** Independent assessment of the supplied logs; no sources reconsulted or probes executed because web access is unavailable.

1. **C1 — `partial`.** Covered: A2A proposals and repositories; adjacent IPC, STDIO, email, brokers, Maildir and file-mailbox vocabularies; limited JADE/FIPA history; recent software gray literature through 2026-11-12. Missing: non-English searches, substantive surveys and citation trails, older tuple-space/blackboard systems, theses, and AWCP full text. Proposed probes: inspect AWCP’s transport specifications and references; follow the A2A survey cited by abq; search “A2A filesystem binding” alongside “shared directory,” “spool,” “Maildir,” and translated equivalents; inspect implementations behind email/fmsg proposals. Older systems contextualize transport novelty but only an actual A2A binding can directly preempt C1.

2. **C2 — `partial`, with strong documented counterexamples.** Covered: heterogeneous CLI interoperability, peer messaging, A2A/ACP bridges, GitHub/PyPI documentation and recent preprints. Missing: non-English sources, systematic surveys/citation trails, historical feature verification, and evidence distinguishing advertised capability from demonstrated live interoperability. Proposed probes: inspect versioned adapters, integration tests, demonstrations and release history for synapse-a2a, a2abridge and a2a-serve; follow tap’s references and citations; search “cross-vendor coding agents” and “peer CLI interoperability.” Earliest package release dates do not establish when the relevant feature appeared. Preemption need not await exhaustive searching, but coverage is not saturated.

3. **C3 — `partial`.** Covered: empirical software engineering, downstream/upstream bugs, agent PR datasets, cross-repository benchmarks, agentic testing, operational blogs and a draft paper. Missing: citation trails from Lin, Saeidi and Agentic PBT; bug tossing, misrouted reports, duplicate detection, autonomous issue submission, dependency/service incident reporting; substantial surveys, theses and non-English repositories. Proposed probes: those vocabularies in scholarly indexes; direct HAL and national-repository searches; retrieve the Delft thesis and mabl series; follow citations and search recent industrial reports measuring submission, acknowledgment, fixes or closure. Preserve **services** in the search scope: the judge repeatedly narrows the claim to repositories.

**Evidence fragility.** C2 preemption rests substantially on self-described documentation; source/tests could change individual verdicts. C3’s nine abstract-only `does_not_preempt` verdicts are too strong: an abstract’s silence cannot exclude a relevant experiment. Retrieve those papers before excluding them. AWCP remains unresolved. README keyword absence likewise cannot establish nonconformance or unsupported adapters. The failed French search does not establish that HAL is unindexed.

**Wording.** C1 should say “among the a2aproject proposals we examined,” rather than implying exhaustive coverage of published proposals. Its design-conformance assertion is not independently assessable from these logs. C3’s “no published study” and “novel” overreach partial coverage; use “We did not identify a matching study in the searches described.” No claim meets the documented saturation conditions: material gaps remain, and no adequate dry round covering them is demonstrated.
## Search log, angle 1

### biblio angle 1 log (2026-11-12). Interface: WebSearch/WebFetch (standard mode)
Queries (8 searches, ~10 fetches):
1 "A2A custom transport binding stdio/unix socket/filesystem" - 3 leads
2 "a2aproject issue stdio transport" - 2 leads (a2a-rs#15)
3 "file-based agent mailbox inbox atomic rename Maildir" - 5 leads
4 "arXiv agent comm protocol local IPC filesystem A2A ACP ANP" - 1 weak (AWCP 2602.20493)
5 "experimental-cpb binding repo" - 2 leads (experimental-cpb-slimrpc)
6 "A2A unix domain socket agent card" - 0 (IETF draft DNS-SD TCP only)
7 "JADE intra-platform / FIPA MTP file/named pipe" - 0 (JADE IMTP=RMI; MTPs IIOP/HTTP/WAP)
8 "A2A same machine filesystem agent card inbox pid" - 2 leads (a2a-relay, a2abridge)
#### Candidates
- https://github.com/a2aproject/A2A/issues/2048 (read in full) ADJACENT/near-preempt for "stdio": STDIO custom protocol binding proposal, 2026-07-12. "There is no listening socket, no port, and no network endpoint." Session binding includes pid (sec 9.6). Not filesystem.
- https://github.com/a2aproject/a2a-rs/issues/15 (read) ADJACENT: "task: add stdio transport binding", 2026-04-04. "The existing bindings are network-oriented." Parent #12 lists SLIMRPC, WebSocket, stdio.
- https://github.com/Hosuke/a2a-relay (README read) ADJACENT-strong: "The first transport is a filesystem mailbox"; inbox/<agent>/, processing/, "poll first atomically claims a file"; heartbeat message as "liveness ping". Own schema "a2a.v1", no A2A spec reference, no agent card, no pid. ~2026-05.
- https://github.com/aygp-dr/abq (README read) ADJACENT: "uses the same atomic-rename trick that makes Maildir reliable"; records sender pid; --alive check. Cites A2A survey only.
- https://github.com/avivsinai/agent-message-queue (README read) ADJACENT: "Each agent has an inbox and an outbox"; tmp+rename. No A2A, card, pid.
- https://docs.rs/crate/bamboo-subagent/latest/source/src/mailbox.rs (snippet only) ADJACENT: Maildir new/cur, temp-then-rename.
- https://docs.rs/crate/agent-team-mail-core/0.9.0/source/src/io/inbox.rs (read) ADJACENT: <agent>.json inboxes, lock + tmp swap; no A2A.
- https://github.com/vbcherepanov/a2abridge (pkg page read) ADJACENT: A2A 1.0 peers, card at /.well-known/a2a, ./.a2a/inbox-<ppid>.json, but transport HTTP loopback.
- https://github.com/shoedog/a2acp BACKGROUND: A2A HTTP front, ACP over stdio.
- https://github.com/a2aproject/experimental-cpb-slimrpc BACKGROUND: only existing experimental binding (snippet).
- https://arxiv.org/abs/2602.20493 AWCP BACKGROUND (abstract via search): transport adapters SSHFS/archive/git; discovery via A2A.
- IETF draft-zhao-a2a-dns-sd-00 BACKGROUND: TCP only.
- JADE/FIPA BACKGROUND: IMTP via RMI; FIPA MTPs IIOP/HTTP/WAP.
#### angle_blocked
- Semantic Scholar/OpenAlex APIs, HN/Reddit search: not run (general WebSearch only; no direct API use).
- ACP (IBM/BeeAI) local-IPC claim from gocodeo blog: unverified.
- JADE source MTP packages, Tuple-space/blackboard (Linda files): not run.
- No full text of dev.to 1995 mailbox post (404) or mail-async skill.

## Search log, angle 2

### biblio angle 2 (2026-11-12) - claim REFUTED
Queries (WebSearch standard, 2026-11-12): (1) Claude Code Codex CLI peer-to-peer A2A bridge; (2) pi-messenger; (3) Gemini CLI A2A remote agents; (4) arXiv heterogeneous coding agents interop peer messaging. Fetched: synapse-a2a PyPI, a2abridge pkg.go.dev, arXiv 2606.14445 abs.
Candidates
- https://pkg.go.dev/github.com/vbcherepanov/a2abridge (read) PREEMPTS: "The open A2A protocol bridge for AI coding agents." Claude Code, Codex, Gemini CLI, Cline, Cursor; Aider best-effort; A2A 1.0 JSON-RPC peers.
- https://pypi.org/project/synapse-a2a/ (read first 100k chars) PREEMPTS: "each agent operates as an A2A server"; Claude Code, Codex, Gemini, OpenCode, Copilot CLI.
- https://arxiv.org/abs/2606.14445 (abstract) ADJACENT/preempts non-A2A: tap, file-based protocol, Claude+Codex "collaborate on one codebase"; not A2A.
- https://github.com/nicobailon/pi-messenger (search snippets only) ADJACENT: Pi-only peer messaging, no vendor mix.
- https://geminicli.com/docs/core/remote-agents/ (snippets) ADJACENT: Gemini CLI consumes A2A remote agents (experimental).
- repowire (dev.to), agmsg, hcom, nexscope, firstintent a2a-bridge (snippets only) ADJACENT: cross-CLI messaging, non-A2A or MCP-based.
- codex.danielvaughan.com 2026/04/09 protocol-gap posts: BACKGROUND, claim neither CLI natively speaks A2A.
angle_blocked: none; second-level reads of GitHub repos, Semantic Scholar/OpenAlex not done.

## Search log, angle 3

### biblio angle 3, 2026-11-12. Interface: WebSearch (standard) only; no full-text reads (snippets/summaries only).
#### Queries (all WebSearch, 2026-11-12) and leads
1. AIDev dataset agentic PRs ... -> arXiv 2602.09185 (AIDev, MSR26), 2509.14745, 2602.00164, 2606.13468
2. AI coding agents file issues upstream dependency bug reports -> 2601.00205 (agent dependency changes), 2603.20847 (bugs in agents' own trackers), 2505.20749
3. cross-project bugs upstream bug reports fix latency -> arXiv 2511.04986 (npm maintainer responsiveness), Ding APSEC17, Ma 2017, MSR18 Rails, Lin EMSE22 (Debian/Fedora upstream)
4. LLM agent-authored issues maintainers response -> TU Delft thesis (90 PRs, 45 repos), no agent-issues study
5. fleet agents upstream issue filed blog -> 2510.09907 agentic PBT (bug reports to maintainers)
6. AI slop bug reports curl -> news (Register, LWN, Stenberg); human-driven LLM reports, no agents measured
7. cross-repository coordination AI agents -> BeyondSWE 2603.03194, 2607.04697 (agent PR conflicts), 2604.04059
8. French/HAL query -> nothing relevant (angle_blocked: HAL not indexed by WebSearch)
9. mabl 75 repos -> mabl blog parts 1-2
10. agentic PBT maintainers -> paper + red.anthropic.com
11. Claude Code issue on third party repo -> aiweekly (unverified), "4worlds" anecdote
#### Candidates
- https://arxiv.org/html/2510.09907v1 Agentic PBT (Maaz et al.). Read: search summary only. ADJACENT (closest): agent reports bugs to upstream maintainers with outcomes. "reported 5 bugs, 4 with patches ... 3 patches merged". Not agents reporting from a working repo to a dependency, no dup/latency/fan-out.
- https://arxiv.org/pdf/2511.04986 npm maintainer responsiveness to downstream bugs. Summary only. ADJACENT (human): "clear references and high textual similarity ... increase the likelihood of an upstream fix".
- https://arxiv.org/html/2602.09185v1 AIDev. Summary only. BACKGROUND: PR-centric, 932,791 agentic PRs; issues only linked for curated subset; no cross-repo reporting.
- https://www.mabl.com/blog/how-we-built-a-system-for-ai-agents-to-ship-real-code-across-75-repos-part-2 mabl. Summary only. BACKGROUND: cross-repo coordination failures, "an agent updated three repos but missed a fourth"; internal repos, no issue filing.
- https://sail.cs.queensu.ca/data/pdfs/2022_Upstream_bug_management_in_Linux_distributions.pdf Lin et al. Snippet only. ADJACENT (human): "less than 14% are clearly fixed upstream".
- Also background: Ding/Ma cross-project bugs (human); MSR18 Rails issue linking; curl slop reports (theregister 2025/05/07, human-submitted LLM reports, no measured agent pipeline); arXiv 2607.04697 agent PR conflicts; BeyondSWE 2603.03194.
#### Verdict: no preemption found in this angle.
#### angle_blocked
- HAL / French: WebSearch does not index HAL; no hit.
- No full-text reading; classifications from snippets.
- ttal not found (no query hit); bug tossing / misrouted reports and LLM duplicate detection not searched separately (budget).
- US-only search tool, 2026 arXiv ids unverified beyond snippets.

