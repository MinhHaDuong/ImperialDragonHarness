# Stopguard measure: labelled sample, precision and recall

Ticket 1294, child of 1164. Script: `scripts/trace-stopguard.py` (its docstring
states both rules). Written 2026-10-27 on padme from the Claude Code traces of
the 28 days to that date.

**Status of the labels: agent-proposed, pending author confirmation.** The
label "bad" means an *avoidable interruption* (design note
`conception/2026-10-21-stopguard-design.md` §7): the author would have
preferred the agent to continue, or to ask a higher model first. Only the
author can know that; an agent (Claude Opus, the ticket's coder) proposed each
label below from the stop's closing text and the author's next message. Every
figure here is provisional until the author skims the 38 held-out rows (about
0.2 author-hours) and corrects any label.

## Method

1. **Tuning draw** (seed 1294, 34 stops, not used for any figure below). It
   showed four defects, fixed before freezing: any Agent call counted as an
   ask-up, so a raid that spawns workers hid every ask; an absent
   `pendingBackgroundAgentCount` was read as zero; Workflow launches were not
   tracked; French author's-call verbs were missing. Wait detection was also
   narrowed to the last two paragraphs, and a stop ending on a question counts
   as an ask, not a wait.
2. **Rules frozen** at the commit that adds this note.
3. **Held-out draw** (seed 1295, 38 stops), stratified: 5 flagged and 3
   unflagged stops from the 2026-10-27 raid session `e75a58ed` (positive
   controls, excluding the turns seen in tuning), 10 random ask flags, 6
   random wait flags, 14 random unflagged stops. The labeller saw, per stop,
   the last 400 characters of the closing message, the author's next message
   and the gap.

No message text is committed; a row is `session:turn`, the flags, the label and
a one-line reason. The session id resolves to the trace while the session file
exists (`cleanupPeriodDays` 180).

## Held-out labels

`A` = ask without ask-up flagged, `W` = wait without wake flagged, `-` = not
flagged. TP / FP / TN / FN against the proposed label.

| # | Stop | Flag | Label | Verdict | Reason |
|---|------|------|-------|---------|--------|
| 1 | e75a58ed:66 | A | bad | TP | review-round escalation put to the author with no advisor call |
| 2 | e75a58ed:106 | A | ok | FP | Fable was consulted in the previous turn; answer arrived by notification |
| 3 | e75a58ed:107 | A | ok | FP | same: relays Fable's advice, the four rulings are the author's |
| 4 | e75a58ed:74 | A | ok | FP | carry on for $40–70 or stop: money and scope; the dollar figure is above the last line |
| 5 | e75a58ed:75 | A | ok | FP | repeats row 4's money and scope question |
| 6 | e75a58ed:12 | - | ok | TN | status; waits on a running check with agents pending |
| 7 | e75a58ed:65 | - | ok | TN | status with reviews running |
| 8 | e75a58ed:58 | - | ok | TN | status with agents pending |
| 9 | 3efb1057:2 | A | bad | TP | offers a cheap read-only data pull instead of doing it |
| 10 | d7b4147d:53 | A | bad | TP | asks before the routine `/roar` |
| 11 | 89a0e450:21 | A | bad | TP | asks before the routine `/roar`; the author then typed it |
| 12 | 9384547f:16 | A | bad | TP | asks before arming a trivial one-shot check |
| 13 | b8ca1249:41 | A | bad | TP | closing question asks leave to launch `/gaze`, a routine step |
| 14 | 28741a18:36 | A | bad | TP | offers a cheap follow-up table instead of planning it |
| 15 | 7bccf3dc:5 | A | ok | FP | flagged by an AskUserQuestion; the closing merge and ticket asks were barred by the brief |
| 16 | 833bc3a3:25 | A | ok | FP | the smoke stops a production service: outward, the author's call |
| 17 | 02c14709:12 | A | bad | TP | asks leave to split a ticket, a reversible agent call |
| 18 | 33d7deec:150 | A | ok | FP | data-model choice in a design discussion the author was leading |
| 19 | 0b62234b:28 | W | ok | FP | end-of-session handoff ("safe to /clear"), not a wait |
| 20 | 33d7deec:67 | W | ok | FP | an agent resumed by SendMessage was running; not tracked as pending |
| 21 | a01daa6a:10 | W | ok | FP | "auto-merge" quoted as a log string, not a wait |
| 22 | 6618399c:12 | W | bad | TP | leaves "check the PR later" with no watcher; author had to ask |
| 23 | 9384547f:15 | W | bad | TP | will start the hunt "when it reports merged", no wake armed |
| 24 | b3a3f237:29 | W | ok | FP | reports a merge that already landed through auto-merge |
| 25 | c54fe094:331 | - | ok | TN | status, 17 tasks pending |
| 26 | 67412ce3:72 | - | ok | TN | next step after a running review, tasks pending |
| 27 | 976d03df:24 | - | ok | TN | waits on a live Monitor |
| 28 | c6a3ffbc:36 | - | ok | TN | waits on a running executor |
| 29 | f0dd1a0f:119 | - | ok | TN | status, coders running |
| 30 | b91ea51e:1 | - | ok | TN | headless review verdict |
| 31 | 6618399c:6 | - | ok | TN | asks what gap the author meant: a clarification of intent |
| 32 | c54fe094:330 | - | ok | TN | status |
| 33 | bace1326:1 | - | ok | TN | headless review verdict |
| 34 | b8ca1249:60 | - | ok | TN | waits on a reviewer with tasks pending |
| 35 | ce789f5d:14 | - | ok | TN | download running in the background, plan stated |
| 36 | a0f10217:40 | - | bad | FN | asks "your go" for low-risk work; the question is not the last line |
| 37 | d7b38f08:1 | - | ok | TN | headless review verdict |
| 38 | 4150f08f:62 | - | ok | TN | status, gaze running |

## Precision and recall (agent-labelled, pending author confirmation)

Wilson 95% intervals. Window totals from the same run: 5,289 stops, 600 ask
flags, 77 wait flags, 675 bad stops (a stop can carry both).

| Measure | Value | 95% interval |
|---|---|---|
| Precision, ask rule, random draw | 7/10 = 0.70 | 0.40–0.89 |
| Precision, ask rule, raid positive controls | 1/5 = 0.20 | 0.04–0.62 |
| Precision, ask rule, both | 8/15 = 0.53 | 0.30–0.75 |
| Precision, wait rule | 2/6 = 0.33 | 0.10–0.70 |
| Precision, all flags | 10/21 = 0.48 | 0.28–0.68 |
| Precision, random flags only (ask and wait) | 9/16 = 0.56 | 0.33–0.77 |
| Bad among unflagged | 1/14 = 0.07 | 0.01–0.31 |
| Recall (derived) | 0.57 | 0.23–0.88 |

The raid rows are positive controls, oversampled from one session; they test
the rule on its target case but do not represent the population, so the
derived figures below use the random strata only.

Recall is derived, not measured: precision weighted by rule volume, (600 ×
7/10 + 77 × 2/6) / 677 ≈ 0.66; flagged bad ≈ 675 × 0.66 ≈ 444; unflagged bad ≈
4,614 × 1/14 ≈ 330; recall ≈ 444 / (444 + 330). The interval carries only the
unflagged-rate interval; one false negative in 14 makes it wide.

**Against 1164's gate G1** (at least 5 bad stops per week on Claude Code):
the script counts about 169 flags a week (675 over four weeks); at the
random-flag precision lower bound of 0.33 that is still about 56 true bad
stops a week (derived). Even the raid stratum's 0.20 leaves about 34. The
verdict "reopen" holds under any label correction short of reversing most TP
rows.

## Heuristic limits

Each limit is a row above or a design choice; none was fixed after the freeze,
so the held-out figures stay valid.

- **Ask-up in an earlier turn is not credited** (rows 2, 3). An advisor whose
  answer arrives by task-notification starts a new turn; the rule only looks
  inside the turn.
- **The author's-call exclusion reads the last line only** (row 4), and the
  vocabulary is English and French.
- **AskUserQuestion counts as an ask whatever it asks** (rows 1, 15), and a
  turn with several asks is one stop.
- **Only a question on the last line is an ask** (row 36, and one tuning-draw
  case): a closing "with your go I can start..." below the question is missed.
- **The wait vocabulary fires on handoffs and quoted strings** (rows 19, 21,
  24): "auto-merge", "waiting on a check" in a closing summary.
- **Agents resumed by SendMessage are not pending** (row 20); nor is a process
  the agent detached itself (nohup, systemd).
- **"I'm waiting."** with no object is outside the vocabulary (row 27 was
  covered by a live Monitor, so no harm here).
- **Raid sessions dominate** the ask false positives: a raid relays held
  decisions that are the author's by right. Precision on interactive
  single-ticket sessions is likely higher than the all-flags figure.
- **Claude Code only.** Codex and Pi traces are another format (about 6 and 5
  weeks of history); the script reports them unmeasured.
- **Sub-agent traces are excluded**; a forked or resumed session's replayed
  stops are counted once by API message id.

A rule v2 should credit an advisor answer in the previous turn, read the whole
closing paragraph for questions and author's-call words, and drop wait hits in
a paragraph that also says "safe to /clear" or reports a merge as landed. Its
precision needs a fresh held-out draw.
