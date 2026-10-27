# Review, merge and propagation flows: fewer, not more

Status: proposed, for the author. Asked 2026-10-27 (tickets 1276, 1277 logs): "recalibrate the mental
models … design note first, review for practices and values; more choice is not always better."
Legend: **[M]** measured (cited source, or this session on padme); **[I]** inferred (code read or reasoning, not run).
Inputs: `local-merge-gate-policy.md` ("policy"), `2026-10-21-main-update-guard.md` ("guard"),
`2026-10-27-notes-review-spec.md` ("spec"), `2026-10-27-notes-transport-trial.md` ("trial"), tracker 1252,
`scripts/raid_land.py` + `scripts/forge.py` NoneForge as merged in PR #1806.

## 1. Three choices, four flows

- **A, where review evidence lives**: forge comments (today) or `refs/notes/review` (spec; 1273/1274, unbuilt).
- **B, who moves main**: the forge's PR merge, or a local gated merge (`raid_land.py branch:<name>`, PR #1806).
- **C, how main propagates**: GitHub as hub; a bare repo under `/srv` on padme as hub; peer to peer.

Facts every flow inherits:
- Guard in `enforce` on padme [M, `git config idh.mainGuard` this session] and doudou [caller's statement].
  Main moves only (i) to `origin/main` or by fast-forward along it, (ii) to the tip just fetched from the remote
  named `origin`, or (iii) onto one two-parent merge whose first parent is the current main and whose candidate
  carries a passing note in `refs/notes/gate` (guard "Gated update"; `classify()` in the hook).
- Path (i)/(ii) needs no gate note at all; path (iii) needs the note *before* main moves, and admits **one merge
  hop**: catching up two merges from anything but `origin` is refused [I, code read of `classify()`, not run].
- Neither clone nor fetch brings notes [M, trial case 1]. Ruleset `main-traceability` covers `main` only;
  `refs/notes/*` can be force-updated and deleted with the session credential [M, trial case 6]. GitHub
  Actions is off: no forge CI on any flow [M, policy "Forge settings"].
- Web sessions (ChatGPT Work, Claude Code Web) reach GitHub; whether they fetch or push notes is untested
  [spec §2, legs pending]. They cannot reach padme's `/srv` or doudou [I: no route from a vendor sandbox].

| Flow | A | B | C | Canonical main |
|---|---|---|---|---|
| F1 review local, forge merge | comments (notes later) | forge | GitHub | GitHub |
| F2 local merge, push upstream | notes | local | GitHub | GitHub (`origin/main`); the local repo when no remote exists |
| F3 local merge, `/srv` hub | notes | local | padme `/srv` | ambiguous: `/srv` or GitHub |
| F4 peer to peer | notes | local | none | none |

**F1.** Buys: today's practice; forge merge is atomic and serialised by GitHub; every environment, web
included, can take part; ruleset applies; nothing new to build. Costs: GitHub API and PR plumbing on the
landing path; evidence in comments is forge-bound (the reason for 1252). Failure modes: forge outage blocks
landing (not work); comment evidence lost with the forge. Needs from 1273-1276: nothing (it is the forge path
they must leave unchanged); notes as its evidence store would need extra work outside 1252.

**F2.** Buys: landing without the GitHub API (git over ssh only), the same gate record, pinned head and
read-back; on a repo with no remote, the full chain runs locally (1252's exit criteria). Costs: two landing
paths into one main. Failure modes: (a) a concurrent forge merge or second local landing makes the push
non-fast-forward: local main ahead of `origin/main`, the open item in 1276's log ("exit 6 … who reconciles is
unwritten"); (b) offline: the push fails the same way; (c) notes ordering is benign: the gate note is pushed
when recorded, and other clones follow main by path (i), which needs no note [I]; (d) ruleset holds (the push is
a fast-forward); there is no forge CI to bypass. Needs: 1273, 1274 (evidence), 1275 (done), 1276.

**F3.** Buys: a hub the author owns, independent of GitHub. Costs: padme is not always reachable, so the hub is
offline exactly when a laptop is; web sessions are excluded; the guard trusts only the remote named `origin`, so
either `/srv` becomes `origin` (GitHub becomes a second remote and the forge route must be re-plumbed) or every
catch-up from `/srv` must pass path (iii), one hop at a time with notes fetched first; no ruleset on `/srv`
(only `receive.denyNonFastForwards`/`denyDeletes`, and a pre-receive gate check would be a guard on the guard).
Failure modes: two hubs, two mains (GitHub and `/srv` diverge whenever a forge merge and a `/srv` landing
overlap); which one is canonical is decided per incident. Needs: 1273-1276 plus a remote-generalised guard,
helper refspecs per hub, a hub sync rule, an audit across hubs.

**F4.** Buys: no single point of failure. Costs: no canonical main by construction; every pull is path (iii)
with notes first, one merge at a time, or a refusal; each peer must be reachable from each other; web sessions
excluded; the audit (`main_sweep.py`) has no reference to sweep. Failure modes: divergent mains are the normal
state, reconciled by merge commits that carry no gate record. Needs: all of F3 and a reconciliation protocol.

## 2. Judged against the harness's values

- "**Trust** the delegate and the existing checks; a new round, seat or guard answers a named risk, not a
  reflex" (workflow.md, Trust, Verify, Monitor). F1 and F2 reuse the guard, the gate record and the ruleset
  as they are. F3 and F4 need new guard paths and hub checks for risks nobody has observed.
- "**No guards on guards**" and "when a guard misfires, prefer deleting the guard … over growing it" (workflow.md,
  Severity floor). F3/F4 grow the guard (remote-generalised on-origin path, pre-receive on `/srv`): rejected.
- "**The forge stays the central origin: one place to pull from**" (policy, Direction) and "forge-independent,
  not forge-free — the forge stays the default route" (1252 ruling). F1 default and F2 fallback both keep one
  place to pull from. F3 and F4 remove it.
- "**Local main syncs by ref, never by assumption**" and "**Never read a SHA … from output a proxy may
  rewrite**" (git.md). F2's CAS + read-back meets both; F4 has no ref to sync to.
- "**Run to the end** … mid-run returns are for new scope or irreversible actions" (workflow.md, Autonomous
  action). A per-incident "which main is right?" (F3, F4) is exactly such a return, recurring.
- "**More choice is not always better**" (author). Each kept flow is a path the skills must describe, the
  guard must admit and 1276 must exercise; each costs reading time in every session forever.

## 3. Recommendation

**One default, one fallback, one hub.**
- **Default: F1.** Review locally (seats run where the work is), land by forge PR merge, GitHub is the hub.
  Evidence stays in forge comments on this route for now (spec §5: "the forge route is unchanged in 1252").
- **Fallback: F2, pushing to `origin` = GitHub.** Trigger, deliberate and only this: `IDH_FORGE=none` set by
  the author or by a session the author told to (already ruled, 1277 log point 5), used when the GitHub API is
  unavailable or for a repository that has no forge. Never chosen automatically, never because `gh` is absent.
- **Offline is not a landing flow.** Work, review and gate locally; the branch waits. Landing needs `origin`
  reachable. This is the single choice that keeps F3/F4 unnecessary.
- **Rejected: F3** (second hub, unreachable for web sessions and often for laptops, guard growth, two mains).
  **Rejected: F4** (no canonical main, contradicts "one place to pull from"). If the worry behind F3 is losing
  GitHub, a **push mirror** to `padme:/srv` (`git push --mirror` from `/lair`, never landed on, never pulled from
  by sessions) gives a backup with no canonical claim; optional, outside 1252.
- **Canonical main**: F1 and F2: `origin/main` on GitHub. F2 with no remote: that repository's own `main`.
- **Reconciliation rule for F2's push failure** (the 1276 open item): `origin/main` is canonical, local main is a
  cache. If the remote tip is unchanged since the landing read it, retry the push (transient error). If
  `origin/main` moved, return local main to `origin/main` (the guard admits it: path (i) [I, code read]), keep
  the branch, rebase, re-gate, re-land. "Never reset main" then means never off `origin/main`, not never to it.

## 4. What changes in the tickets and the rule

- **1273 (C3)**: no change in substance. Simplification: `review_notes.py setup/sync/publish` talk to `origin`
  only; no hub selection, no per-remote refspecs.
- **1274 (C4)**: no change.
- **1275 (merged)**: no code change now; its exit-6 state gets the reconciliation rule above, implemented with
  1276 (raid_land: on push failure, compare `origin/main` with the read base tip and report which branch of the
  rule applies; ~1 agent-hour).
- **1276 (C6)**: unhold. Exercise F2 only, in two shapes: no remote (temp repo, `gh` absent, existing criterion)
  and a local bare repo standing in as `origin` (push, a concurrent second landing, reconciliation per §3), plus
  the spec §8 rebase and concurrent-append cases. Do not exercise F3 or F4. F1 is covered by "forge path unchanged".
- **rules/git.md, line 9** (written at C5's merge per 1277 point 5; text proposed, the author's call):
  "Everything … lands via branch + PR on the forge. With `IDH_FORGE=none` set deliberately, it lands via branch +
  local gated merge (merge skill) pushed to `origin`, which stays the one canonical main; offline, the branch waits."

## 5. The author's decisions, priced

| # | Decision | Recommended | Author | Agent |
|---|---|---|---|---|
| 1 | Two flows only (F1 default, F2 fallback by `IDH_FORGE=none`); F3, F4 rejected | yes | 5 min | 0 |
| 2 | Offline never lands (vs land locally, push later) | yes | 2 min | 0; the alternative is F2 failure (b) made normal |
| 3 | F2 push-failure rule: retry if unchanged, else back to `origin/main` and re-land | yes | 3 min | ~1 h in 1276 |
| 4 | rules/git.md line 9 text above | yes | 3 min | 0.25 h |
| 5 | Optional push mirror to `padme:/srv` for backup | only if GitHub loss worries you | 10 min (`/srv` setup) | ~0.5 h |
| 6 | Later: notes as evidence store on the forge route too (one store for A) | wait for web legs | 15 min, after 1276 | ~4-6 h [I] |

1276 as rescoped: ~3-4 agent-hours [I]. Rejected cost avoided: F3 ~8-12 agent-hours + 30 author-minutes, F4
~15+ agent-hours, both open-ended in maintenance [I, rough].

**Probability the recommendation holds for six months: ~0.75** [I]. It breaks if (a) the author needs to land
for days with GitHub unreachable from both hosts (then F3, with `/srv` renamed `origin`, is the next step, not
F4), or (b) the web legs show a web session cannot push to GitHub at all, which weakens the F1/F2 hub argument
less than it seems: such a session could not reach `/srv` either.
