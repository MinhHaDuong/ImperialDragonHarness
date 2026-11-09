# Context length: strategy and first fixes

Date: 2026-11-09. Status: proposed, not accepted. Drafted alone by the
interface session (Claude Fable 5.2) at the author's request: "Design note
and ticket. No implementation. Identify up to three small specific pain
points to solve urgently." Every judgment below is the drafter's unless it
is attributed to the author or to a reviewer. Ticket: 1499.

## 1. Problem

The harness sets limits on context length, and neither a session, nor the
author, nor a committed script can tell whether a session respects its own.

- **A session cannot see its length.** The runtime documents no usage figure
  in the model's context, and the harness adds none.
- **The author sees a percentage of the window.** On a 1M window the status
  line reads 23% at 230K and 55% at 550K.
- **The audit cannot answer the question.** `scripts/trace-compact-audit.py`
  counts runs, not sessions; it thresholds on cache-read tokens; it keeps a
  whole transcript when its last record falls in the window; and it does not
  know a session's role or model ceiling.

What an ad hoc scan shows (main-session transcripts on padme, all projects,
turns since 2026-11-01, the day the guard became a resident rule; cache-read
tokens; no committed command reproduces it):

| Sessions, 2026-11-01 to 2026-11-09 | Count |
|---|---|
| with at least one turn | 281 |
| with 100 or more turns | 28 |
| with 30 or more turns at or above 230K | 24 (19 on Opus 5.5, 5 on Fable 5.1) |
| with 30 or more turns at or above 450K | 4 |
| with 30 or more turns at or above 550K | 1 |

Long sessions ride above 230K as a rule. Against the ceilings the author set
on 2026-11-09 for interface sessions, few do. The scan cannot say which of
the 24 were interface sessions and which were unattended runs still bound
by 230K.

Two older raid sessions, the heaviest in the 28-day audit, peaked at 966K
and 757K cache-read tokens in October. The file that holds raid's handoff
rule never appears in either transcript. In 1,809 and 1,075 turns above
172K, the sessions wrote a figure for their own context twice and never.
Why they went on is not established; that the rule was absent from their
context and that they did not track their length are observations.

## 2. Situation

Read from main at 17e474ab.

**Limits.** `rules/guards.md` stops a session at 230K and forbids answering
a context wall "with a bigger window, KV tricks or compaction". PR 2358
(ticket 1497, author ruling 2026-11-09) added that an interface session's
threshold is its model's ceiling in `skills/route/SKILL.md`: 450K on Sol or
Opus, 550K on Astra or Fable, 230K on any other model. Launched workers,
team leads, and unattended runs keep 230K.
`skills/raid/references/autonomous-brief.md` and `agents/team-lead.md` hand
off at 75% of 230K. Whether a raid the author attends is an interface
session is not written anywhere.

**Measurement.** `scripts/statusline.sh` prints the percentage the runtime
gives it. The audit script (ticket 0239, June 2026) reads transcripts
offline. `skills/lair/SKILL.md` tells a session to "estimate tokens from
conversation length". Nothing reads usage during a session.

**Compaction.** Three positions coexist. The guard forbids it as an answer
to a wall. `skills/roar/SKILL.md` says "advise `/clear`, never `/compact`".
`rules/workflow.md` § Compaction says what a compaction must preserve. In
practice auto-compaction is enabled on padme with no window set, and the
runtime documents a default near 967K for 1M-window models: the 966K peak
above sits at that default.

**Reset points.** Roar ends each task with "safe to `/clear`", and perch
offers a clear when the moment suits. Both leave the choice to the author.
This session received roar's verdict shortly before it measured 211K, and
went on, at the author's choice, on the same subject.

**Other runtimes.** The shared rules and skills reach Codex and Pi, so both
read the guard, the preservation list, and roar's advice, which names a
Claude Code command. The adapters add no measurement and no display.

**Earlier findings.** `design/trace-census-2026-06.md` found main sessions
to be 76% of spend from 17% of agents, and model choice for long interactive
sessions to be possibly "the single largest lever". The ceilings rest on the
author's judgment that stronger models stay coherent longer; the harness
holds no measurement of it.

**Probe, 2026-11-09.** From inside this session, the session id in the
environment located the transcript, and the last assistant record gave
211,485 tokens of prompt (input, cache read, and cache creation summed;
209,362 of them cache read, the audit's quantity). The transcript format is
internal to the runtime; the audit already depends on it.

## 3. State of the art

- **Claude Code documentation** (read 2026-11-09 by a delegated lookup; pages
  `context-window`, `statusline`, `hooks`, `model-config`, `sessions`, and
  `sub-agents` under `code.claude.com/docs/en/`). The status line command
  receives the window size, tokens, and percentage used. Hooks can inject
  text but receive no token count. A pre-compaction hook can add
  instructions to the summary or block it. Only the user or the automatic
  threshold starts a compaction; the threshold is a setting. A model can be
  held to a 200K window by an environment variable.
- **Codex.** The Sol reviewer reports, with links the drafter did not open,
  a documented `model_auto_compact_token_limit`, a usage display, and
  `/compact`.
- **Pi** (`pi.dev/docs/latest/compaction` and package pages; code not read).
  Extensions can hook `session_before_compact`; a bundled example replaces
  compaction with a handoff to a new session.
- **Chroma, "Context Rot"** (July 2025, `research.trychroma.com/context-rot`;
  summary read). Across 18 models, reliability fell as input grew at constant
  task difficulty. It predates the models the ruling names.
- **Anthropic, "Effective context engineering for AI agents"** (September
  2025; secondary summaries only): compaction, notes kept outside the
  context, sub-agents returning a condensed result.

Not searched: published comparisons of relay or twin-session designs.

## 4. Alternative solutions

**A. The author sees tokens.** The status line prints tokens, for example
`212K`, where it prints a percentage. The author set the ceilings and
decides when to clear; this gives the number that decision needs.

**B. The session asks.** A command prints the session's own context in
tokens, and answers "could not look" with its own exit code elsewhere. It
compares nothing: the caller knows its limit. Raid calls it in its wave
loop and lair in its metrics.

**C. The harness tells.** A hook injects a line when a session crosses its
ceiling. It needs the session's role, which nothing records today.

**D. The runtime caps.** Hold workers and unattended runs to a 200K window,
or set the auto-compaction window at the ceiling with a pre-compaction hook
carrying the preservation list. No one measures anything. The first form
compacts at the wall, which the guard forbids as written; the second
reverses the ban outright.

**E. Reset at task boundaries.** A handoff, then a fresh session, each time
roar says it is safe. The procedure exists and needs no measurement. It
depends on the author taking the offer.

**F. Relay.** Two interface sessions alternate; each hands off at its
ceiling, then compacts. It needs a baton in a file, one handoff format, and
the ban lifted for interface sessions.

## 5. Synthesis and recommendation

The evidence does not yet say why sessions run long, so the first step is to
make the question answerable, at the smallest cost. Three urgent pain
points, in this order:

1. **The author cannot read the ceiling he set.** Alternative A. A few lines.
2. **No committed command says which sessions overran.** Repair the audit:
   events inside the window, sessions as well as runs, the main model, and
   a threshold per model. The scan of section 1 becomes reproducible, and
   every later choice gets a baseline.
3. **A session cannot read its own length.** Alternative B, limited to
   raid's wave loop and lair's metrics.

Both reviewers hold that point 3 comes before its diagnosis: nobody has shown
that a session that knows its length hands off. The drafter keeps it,
last, because the command is small and the audit of point 2 will show
whether raids change. The author may cut it.

For the author, not urgent:
- **Is an attended raid an interface session?** It decides which limit the
  heaviest sessions fall under.
- **What may an interface session do at its ceiling?** Keep the ban and hand
  off to a fresh session; or allow compaction as a backstop at the ceiling,
  where today it fires near 967K; or adopt it as the normal mechanism, which
  relay assumes. The drafter's pick is the backstop.

A cost the ruling carries: a turn at 550K re-reads 2.4 times the context of
a turn at 230K (derived, 550/230).

| Alternative | Agent work | Author time | To undo |
|---|---|---|---|
| A | one small merge request | one glance | revert one script |
| Audit repair | one merge request | one review | revert one script |
| B | one merge request | one review | delete a script and two call sites |
| C | a probe, then one merge request | one review | remove a hook |
| D | one merge request | one decision on the ban | unset one setting |
| E | none | a habit | nothing |
| F | a trial over several days | daily use, one verdict | stop using it |

USD is not estimated: no price table was read. For scale, the review and
gate of PR 2358 took about 8 minutes of agent time.

## 6. Implementation plan

1. **Ticket 1499**: the three pain points, in the order above. Each may land
   apart. It proves that the author, a script, and a session can each read
   length against a limit.
2. **Read the result.** Two to four weeks after the audit repair lands, run
   it and record, in a doctor journal revisit: the share of sessions over
   their limit, by model and by entry skill. That reading decides between
   C, D, and nothing more.

Later, each with no ticket until the author opens it: the two decisions of
section 5; the same reading on Codex and Pi; a relay trial against
alternative E; a planted-fact check of the ceilings.

## Review

**Opus** (Anthropic, same family as the drafter; launched as a read-only
agent with the `opus` token, default effort; the full model id was not
observed). Verdict: sound with changes. Findings:
- The diagnosis is skipped; read the raid traces before choosing a
  mechanism. Adopted: two traces probed, section 1 rewritten.
- The dollar column was the audit's recoverable saving, not a cost
  (`scripts/trace-compact-audit.py:221`). Adopted: the column is gone.
- 117 runs at 230K overstates the problem under the new ceilings. Adopted:
  section 1 now counts sessions since 2026-11-01 against each threshold.
- The restated 230K lines sit in worker text, where 230K still holds
  (`skills/route/SKILL.md:67`, `:115`). Adopted: dropped as a pain point.
- The audit thresholds on cache reads; the probe summed three fields.
  Adopted: both figures stated; the ticket asks for one definition.
- Of four call sites, only raid's fires during the work. Adopted: raid and
  lair kept.
- A hard cap by construction was missing. Adopted: alternative D.
- The monitor had no denominator. Adopted: shares, not counts.

**GPT-6.1 Sol** (OpenAI, other family; `codex exec`, read-only sandbox,
effort medium). Verdict: sound with changes; "replace 'measure first' with a
bounded trial of the existing stop-and-handoff procedure". Findings:
- Visibility is not stopping, and the cause is unknown. Partly adopted: see
  Opus's first finding; the trial is alternative E, not the pick.
- The audit thresholds on cache reads (`:126`), labels a session by its
  first skill (`:142`), keeps a whole transcript by its last timestamp
  (`:246`), and counts runs. Adopted: pain point 2.
- Codex has its own limit, usage display, and `/compact`; the shared rules
  reach Codex and Pi. Adopted in sections 2 and 3.
- The pull command and a ceiling in the status line both needed the
  session's role. Adopted: A prints tokens only; B compares nothing.
- Keep the repair of the contradictory limits. Not adopted: Opus's reading
  of the same lines was checked and holds.

**KISS pass** (drafter). Removed: the ceiling beside the status line, the
push hook as a first step, four call sites reduced to two, the restatement
sweep, and four later phases folded into one sentence.
