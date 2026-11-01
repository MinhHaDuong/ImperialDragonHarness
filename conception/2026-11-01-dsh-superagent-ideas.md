# What to take from DeepSeek's dsh-superagent prototype

Source: <https://github.com/deepseek-ai/dsh-superagent-prototype> (main,
shallow clone 2026-11-01, MIT). Read: README, `docs/000`–`004`, all of
`prompts/`; `docs/005`–`008` skimmed by heading only. Code not read. The
README calls it research code, partly agent-written, and not the internal
version.

## What it is

A proactive coding agent bound to one GitHub repository, with Feishu chat
as an optional second input. It runs as a bundle on DeepSeek Harness. One
**main Session** (the router) reads events from GitHub and Feishu, decides
whether each one asks for work, and opens a **Ticket** for it. Each Ticket
gets its own **Executor Session** and its own directory, usually a git
worktree, and the Executor delivers a PR. A web panel lists only what
waits for a person. Its founding rule: *take as little human attention as
possible, give as much value as possible* — every message, setting, panel
element and doc paragraph must be worth the attention it costs.

The flow is Source → Trigger → Thread → Eval (a deterministic gate, then a
model assessment) → Ticket with a Mandate → Assignment → Executor; replies
go back out through a Channel.

## Where we already agree

These need no action. They confirm choices the harness already made.

| dsh-superagent | Harness equivalent |
|---|---|
| Attention is the scarce resource | workflow.md § Autonomous action |
| One concrete question at a time | "Questions to the author: one at a time" |
| Router forwards the original source, never rewrites the request | "Delegate intent, not procedure" |
| One worktree per ticket, named from its short name | hunt § Worktree |
| The main Session never sleeps or polls; long commands run in the background | memory `feedback_no_blocking_waits` |
| A PR that exists is not "ready"; a draft is reported as blocked | verify-gate, honest reporting |
| Yield to duplicate work and close your own PR | "Someone beat you → delete the branch" |
| At most three automated-review rounds | gaze panel.md: a blocker still arriving at round 3 means redesign |
| "Tune for less noise: shorter prompts, not more messages" | "prefer deleting the guard" |

## Ideas worth taking

Ranked by expected value over cost. All costs are agent work, reviewed by
gaze; author time is noted only where the author must decide.

### 1. Observe mode before auto mode for any new autonomous behaviour — **take**

Every proactive rule starts in `observe`: the model judges, and a positive
judgement is stored as an "ignore" marked "would accept". Nothing is
executed. The operator reads those records and only then switches the rule
to `auto`.

*Here:* sweeps that file tickets (molt, yawn → molt), raid's choice of
targets, and every new guard. Today a new guard is either on or off. A
shadow run, where the guard logs "would have refused X" for a week before
it blocks anything, is exactly the measurement that Trust-Verify-Monitor
asks for, and it lets the severity floor be checked against real hits
before the guard can misfire.
*Cost:* a convention plus one log path. Roughly 1–2 h of agent work, then
one author decision per guard when it goes live.
*Probability it pays off:* high (~70%). Guard misfires are a recurring
reason the harness deletes guards.

### 2. Make "waiting on the author" a structured field — **take, small**

The prototype explicitly rejects "inferring 'waiting on a person' from a
report's free text". An Executor that needs a decision fills one
`human_action` field with one question. The host routes that question,
the panel's "Awaiting answer" stage comes from that field, and the
question is not considered resolved until it is cleared explicitly.

*Here:* author questions are spread across ticket logs, PR comments and
chat. A single ticket header, for example `Needs-author: <one question>`,
that `/dashboard` lists first ("what waits for a person, first; a healthy
state takes no space") would make the "one at a time, queue the rest"
rule easy to check.
*Cost:* ~2 h (tickets/AGENTS.md, an erg check, dashboard ordering).
Checking the ticket format first may show a header that already does this.

### 3. Derive ticket stage from facts, first matching row wins — **consider**

`003-execution.md` derives a Ticket's stage from stored facts, checked in
order: undelivered → awaiting answer → awaiting review → blocked/failed →
queued → idle → working. No agent declares the stage. This could replace
any hand-written status in the dashboard and `STATE.md` with a pure
function over ticket headers, PR state and gate records.
*Cost:* ~3–4 h. Worth it only if the dashboard's status logic is in fact
drifting. Check before ticketing.

### 4. Mandate strength: explicit vs inferred — **consider**

Each accepted piece of work records *why it may be done*: the policy
version, its scope, a strength (`explicit`, meaning a listed person asked;
or `inferred`, meaning a rule matched), and which rules matched. Inferred
work gets narrower authority: "only the accepted local change", and it
stops with `dropped` rather than widening its scope.

*Here:* the open question is whether a ticket the author filed and a
ticket a sweep minted are treated differently by raid. If they are not,
an `Origin: author|sweep` header plus "raid merges sweep-minted tickets
only at the lower gating tier" is a cheap safety margin.
*Cost:* ~1–2 h, plus one author decision (whether it changes the gating
tier).

### 5. Recovery note on resume — **take, trivial**

After a restart, every interrupted Assignment restarts with a fixed note:
*check your directory, git history and the forge before repeating any
outside action.* This guards against double posts and double pushes after
a crash.
*Here:* raid already resumes from its sitrep. Adding that one sentence to
the resume path of hunt/raid (and to the coder profile) costs minutes. It
complements "verify a forge mutation by reading it back".

### 6. Overrides record their base — **consider if overrides exist**

A team's override of a built-in prompt stores which default it was based
on. When an upgrade changes that default, the panel marks the override
**Default updated** and shows the diff, and the team decides. An override
identical to the default is removed, so the part follows future defaults
again.
*Here:* this applies to `harness-extension-point` blocks and to
per-project rule overrides, if projects override harness text locally.
A base hash and a drift check in molt, ~2 h. Skip if no project
overrides anything.

### 7. "Rejected concepts" table in design docs — **take, zero cost**

`001-domain.md` closes with a table: *Rejected | Reason*. It is short,
easy to scan, and stops the same rejected idea from being argued again. The design
note template already has "§ 4 Alternative solutions". A one-line hint,
"close with a Rejected/Reason table", would capture it.

## Not worth taking

- **Sources, Triggers, Threads, Subscriptions, fan-out, follow-up
  handback.** This machinery exists for a team where many people message a
  bot on several platforms. The harness has one author and a ticket store
  as the only channel between projects. Most of the prototype's complexity
  (002 Authorization, ~13 KB) solves a problem we do not have.
- **Stored-work outbox with ordered retries and deduplicated
  acknowledgements.** Sound for a long-running daemon. Our sessions are
  short-lived and git is the store.
- **100-word hard limit on chat messages enforced by the transport.**
  Fine for team IM. Author reports here are already shaped by the
  executive format.
- **The "three facts before accept" assessment prompt** (target is this
  project, intent to change, direction settled). Well written, but it
  judges chat for implied requests. Our work enters as explicit tickets.
- **Auto-merge under 200 lines as a second account.** The point that
  GitHub attributes a merge to whoever enabled it is worth knowing, but
  the merge skill and its gating tiers already decide this.

## Suggested next step

Ideas 1, 2 and 5 are cheap and independent: one ticket each, or a single
small ticket for 5. Ideas 3, 4 and 6 first need a read of the dashboard,
raid's target selection and the override inventory, to find out whether
the problem they solve exists here.
