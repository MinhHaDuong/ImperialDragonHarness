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
  carries a passing note in `refs/notes/gate` (guard "Gated update"; `classify()` in the hook). Path (i) also
  admits a *stale* `origin/main`: reset to it is accepted without a fetch [M, gaze on PR 1809, scratch repo].
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

**F2.** Buys: landing without the GitHub API (git over ssh only), the same gate record and pinned head; on a
repo with no remote, the full chain runs locally (1252's exit criteria). The read-back is weaker than F1's:
`NoneForge.read_back` reads the *local* base; `origin` is checked only by the later fetch in `sync_local` [I,
code read of `scripts/forge.py`, `scripts/raid_land.py`]. Costs: two landing paths into one main. **F2 is not
deliberate-only today**: `get_forge` in auto mode returns `NoneForge` whenever `gh` is not on PATH or the ref is
not a number (`scripts/forge.py:365`) [I, code read here and by the gaze; not run], so `raid_land.py
branch:<name>` lands locally with `idh.mergeRoute` unset. Failure modes: (a) a concurrent forge merge or second local
landing makes the push non-fast-forward: local main ahead of `origin/main`, the open item in 1276's log ("exit 6
… who reconciles is unwritten"); (b) offline: the push fails the same way; (c) notes ordering is benign: the
gate note is pushed when recorded, and other clones follow main by path (i), which needs no note [I]; (d)
ruleset holds (the push is a fast-forward); there is no forge CI to bypass. Needs: 1273, 1274 (evidence), 1275
(done), 1276.

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
  Severity floor). F3 as an extra hub beside GitHub, and F4, grow the guard (remote-generalised on-origin path,
  pre-receive on `/srv`). F3 with `/srv` renamed `origin` would not (§3); its rejection then rests on the
  central-origin ruling below, not on guard growth.
- "**The forge stays the central origin: one place to pull from**" (policy, Direction) and "forge-independent,
  not forge-free — the forge stays the default route" (1252 ruling). F1 default and F2 fallback both keep one
  place to pull from. F3 and F4 remove it.
- "**Local main syncs by ref, never by assumption**" (git.md): F2's CAS and `sync_local` fetch meet it; F4 cannot.
- "**Run to the end**" (workflow.md): a per-incident "which main is right?" (F3, F4) is a recurring mid-run return.
- "**More choice is not always better**" (author). Each kept flow is a path the skills must describe, the
  guard must admit and 1276 must exercise; each costs reading time in every session forever.

## 3. Recommendation

**One default, one fallback, one hub.**
- **Default: F1.** Review locally (seats run where the work is), land by forge PR merge, GitHub is the hub.
  Evidence stays in forge comments on this route for now (spec §5: "the forge route is unchanged in 1252").
- **Fallback: F2, pushing to `origin` = GitHub.** Trigger, deliberate and only this: `git config idh.mergeRoute local` set by
  the author or by a session the author told to (already ruled, 1277 log point 5), used when the GitHub API is
  unavailable or for a repository that has no forge. This is **not true of the code today** (§1, F2): the
  principle requires that auto never selects the local merge. Fix: `get_forge` auto returns `GhForge` when `gh`
  is present and the ref is numeric, and otherwise refuses with "set `git config idh.mergeRoute local` to land without a forge".
  Review on notes may stay automatic; only landing needs the deliberate switch.
- **Offline is not a landing flow.** Work, review and gate locally; the branch waits. Landing needs `origin`
  reachable. This is the single choice that keeps F3/F4 unnecessary.
- **Boundary: offline vs no remote.** A repository *has a remote* when `git remote get-url origin` succeeds;
  reachability does not enter. `origin` configured: `origin/main` is canonical; unreachable means the branch
  waits, even for days. No `origin`: the repository's own `main` is canonical and F2 lands locally (still under
  `idh.mergeRoute=local`). Adding `origin` later moves canonicity to it; the first push fast-forwards or is refused.
- **Rejected: F3**, firmly on the rulings "the forge stays the central origin" (policy) and "the forge stays
  the default route" (1252) [M, quoted]. The other reasons are inferred: web sessions and laptops cannot reach
  `/srv` [I]; guard growth [I], which vanishes if `/srv` becomes `origin`. Reopen F3 on evidence: GitHub
  unreachable from both hosts for over a day while work had to land, or a forge policy change blocking landing.
- **Rejected: F4** (no canonical main, contradicts "one place to pull from").
- **No `/srv` mirror in this flow.** A mirror is an extra option to describe and own. If GitHub loss is a real
  worry, it belongs to the host's backup of the working clones, not to the review flow.
- **Reconciliation rule for F2's push failure** (the 1276 open item): `origin/main` is canonical, local main is a
  cache. **Fetch first**, then compare. If the fetched tip equals the base the landing read, retry the push
  (transient error). If it moved, reset local main to the fetched `origin/main` (guard path (i) [M, gaze
  reproduced `reset --hard`, `branch -f`]), keep the branch, rebase, re-gate, re-land. Fetch first because the
  guard accepts a stale `origin/main` too [M]: resetting to it drops the local merge without learning whether
  the remote moved. "Never reset main" then means never off a freshly fetched `origin/main`.

## 4. What changes in the tickets and the rule

- **1273 (C3)**: no change in substance. Simplification: `review_notes.py setup/sync/publish` talk to `origin`
  only; no hub selection, no per-remote refspecs.
- **1274 (C4)**: no change.
- **New small change, before 1276** (recommended over folding it into 1276): `get_forge` auto never returns
  `NoneForge`; landing without a forge requires `idh.mergeRoute=local`; callers and tests that relied on auto adjust.
  ~0.5-1 agent-hour (~$6-15) + 2 author-minutes [I]. Separate because it changes today's behaviour on every
  repo, needs its own review, and 1276 should exercise the corrected switch rather than build it.
- **1275 (merged)**: no code change now; its exit-6 state gets the reconciliation rule above, implemented with
  1276 (raid_land: on push failure, fetch, compare `origin/main` with the read base tip and report which branch
  of the rule applies; ~1 agent-hour, ~$12-15).
- **1276 (C6)**: unhold. Exercise F2 only, always under `idh.mergeRoute=local`, in two shapes: no remote (temp repo,
  existing criterion) and a local bare repo standing in as `origin` (push, a concurrent second landing,
  reconciliation per §3); plus auto with `gh` absent refuses, and the spec §8 rebase and concurrent-append
  cases. Do not exercise F3 or F4. F1 is covered by "forge path unchanged".
- **rules/git.md, line 9** (written at C5's merge per 1277 point 5; text proposed, the author's call):
  "Everything … lands via branch + PR on the forge. With `idh.mergeRoute` set to `local` deliberately, it lands via branch +
  local gated merge (merge skill) pushed to `origin`, which stays the one canonical main; offline, the branch
  waits; with no `origin` configured, the repository's own main is canonical."

## 5. The author's decisions, priced

| # | Decision | Recommended | Author | Agent |
|---|---|---|---|---|
| 1 | Two flows only (F1 default, F2 fallback by `idh.mergeRoute=local`); F3, F4 rejected | yes | 5 min | 0 |
| 2 | Offline never lands; no-remote boundary = `origin` configured or not | yes | 2 min | 0; the alternative is F2 failure (b) made normal |
| 3 | Auto never selects the local merge (small change before 1276) | yes | 2 min | 0.5-1 h, ~$6-15 |
| 4 | F2 push-failure rule: fetch, retry if unchanged, else reset to fetched `origin/main` and re-land | yes | 3 min | ~1 h in 1276, ~$12-15 |
| 5 | rules/git.md line 9 text above | yes | 3 min | 0.25 h, ~$3-4 |
| 6 | Later: notes as evidence store on the forge route too (one store for A) | wait for web legs | 15 min, after 1276 | ~4-6 h, ~$50-90 |

Basis, all [I]: agent-hours by analogy with 1275 (PR #1806: four implementation commits 17:33-17:48 [M,
`git log`]; earlier work untimed); USD at ~$12-15 per agent-hour, derived in
`conception/discussions/2026-10-14-1095-seats/r2-architect.md`, not measured here. 1276 as rescoped: ~3-4
agent-hours, ~$36-60. F3 and F4 stay unpriced: no design to size, and their cost is open-ended ownership.

**No probability is given**: there is no base rate to set one on. What would overturn the recommendation: (a)
the author needs to land for days with GitHub unreachable from both hosts (then F3, with `/srv` renamed
`origin`, is the next step, not F4); (b) the web legs show a web session cannot push to GitHub at all, which
weakens the hub argument less than it seems: such a session could not reach `/srv` either.
## Naming (author, 2026-10-27)
`IDH_FORGE=auto|gh|none` named a mechanism, not the decision. The one switch is the per-repository git config
`idh.mergeRoute = forge | local` (default `forge`), visible in `git config` like `idh.mainGuard`; an environment
variable could be inherited silently by a subshell or CI job, the wrong property for a deliberate choice. Review on
notes needs no setting. The fix in §3 renames the reader in scripts/forge.py and drops `IDH_FORGE`.

## Author's ruling (2026-10-27)
Accepted: **F1 is the default; F2 is for repositories without an upstream.** The route is read off the repository,
not set: with a remote named `origin`, landing is F1 only (forge PR; if `gh` or the forge is unavailable, the landing
refuses and waits, never lands locally); with no `origin` remote, landing is F2 (local gated merge; the repository's
own main is canonical). This supersedes the `idh.mergeRoute` switch proposed above: there is no setting. The §3 fix
becomes: auto selects the local merge only when the repository has no `origin` remote, and otherwise refuses without
`gh`. F3 and F4 stay rejected.
