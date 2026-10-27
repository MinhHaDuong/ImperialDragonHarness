# Review, merge and propagation flows: fewer, not more

Status: ruled by the author, see "Author's ruling (2026-10-27)" at the end; the body below is rewritten in its terms.
Asked 2026-10-27 (tickets 1276, 1277 logs): "recalibrate the mental models … design note first, review for
practices and values; more choice is not always better."
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
| F2 local merge, no `origin` remote | notes | local | none (nothing to push) | the repository's own `main` |
| F3 local merge, `/srv` hub | notes | local | padme `/srv` | ambiguous: `/srv` or GitHub |
| F4 peer to peer | notes | local | none | none |

**F1.** Buys: today's practice; forge merge is atomic and serialised by GitHub; every environment, web
included, can take part; ruleset applies; nothing new to build. Costs: GitHub API and PR plumbing on the
landing path; evidence in comments is forge-bound (the reason for 1252). Failure modes: forge outage blocks
landing (not work); comment evidence lost with the forge. Needs from 1273-1276: nothing (it is the forge path
they must leave unchanged); notes as its evidence store would need extra work outside 1252.

**F2.** Applies only to a repository with no `origin` remote. Buys: the full chain (review on notes, gate record,
pinned head, local merge) runs with no forge and no network (1252's exit criteria). Costs: a second landing path
into main. The read-back is weaker than F1's: `NoneForge.read_back` reads the *local* base [I, code read of
`scripts/forge.py`, `scripts/raid_land.py`]. **Not deliberate today**: `get_forge` in auto mode returns `NoneForge`
whenever `gh` is not on PATH or the ref is not a number (`scripts/forge.py:365`) [I, code read here and by the
gaze; not run], so `raid_land.py branch:<name>` lands locally even on a repository that has an `origin` remote.
Failure modes: with nothing to push there is no push failure and no divergence from a remote; a second local
landing is serialised by the main CAS. Needs: 1273, 1274 (evidence), 1275 (done), 1280, 1276.

**F3.** Buys: a hub the author owns, independent of GitHub. Costs: padme is not always reachable, so the hub is
offline exactly when a laptop is; web sessions are excluded; the guard trusts only the remote named `origin`, so
either `/srv` becomes `origin` (GitHub becomes a second remote and the forge route must be re-plumbed) or every
catch-up from `/srv` must pass path (iii), one hop at a time with notes fetched first; no ruleset on `/srv`
(only `receive.denyNonFastForwards`/`denyDeletes`, and a pre-receive gate check would be a guard on the guard).
Failure modes: two hubs, two mains (GitHub and `/srv` diverge whenever a forge merge and a `/srv` landing
overlap); which one is canonical is decided per incident. Needs: 1273-1276 plus a remote-generalised guard,
helper refspecs per hub, a hub sync rule, an audit across hubs.

**F4.** Buys: no single point of failure. Costs: no canonical main by construction; every pull is path (iii)
with notes first, or a refusal; web sessions excluded; `main_sweep.py` has no reference. Failure modes: divergent
mains are the normal state. Needs: all of F3 and a reconciliation protocol.

## 2. Judged against the harness's values

- "**Trust** the delegate and the existing checks; a new round, seat or guard answers a named risk, not a
  reflex" (workflow.md, Trust, Verify, Monitor). F1 and F2 reuse the guard, the gate record and the ruleset
  as they are. F3 and F4 need new guard paths and hub checks for risks nobody has observed.
- "**No guards on guards**" and "when a guard misfires, prefer deleting the guard … over growing it" (workflow.md,
  Severity floor). F3 as an extra hub beside GitHub, and F4, grow the guard (remote-generalised on-origin path,
  pre-receive on `/srv`). F3 with `/srv` renamed `origin` would not (§3); its rejection then rests on the
  central-origin ruling below, not on guard growth.
- "**The forge stays the central origin: one place to pull from**" (policy, Direction) and "forge-independent,
  not forge-free — the forge stays the default route" (1252 ruling). F1 (where a remote exists) and F2 (where none does) each keep one
  place to pull from. F3 and F4 remove it. F2 never competes with it: it exists only where there is no origin.
- "**More choice is not always better**" (author). Each kept flow is a path the skills must describe, the
  guard must admit and 1276 must exercise; each costs reading time in every session forever.


## 3. Recommendation, as ruled

Proposed first: F1 default, F2 as a fallback chosen by a `idh.mergeRoute=local` setting, with a push to
`origin`. The author's ruling (last section) replaced the setting with a reading of the repository. Result:

- **F1 is the default.** Review locally, land by forge PR merge, GitHub is the hub. Evidence stays in forge
  comments on this route for now (spec §5: "the forge route is unchanged in 1252").
- **F2 applies only to repositories with no `origin` remote.** The trigger is `git remote get-url origin` failing,
  not a setting: reachability does not enter. Landing is the local gated merge; the repository's own `main` is
  canonical; there is nothing to push. Fix to the code (§1, F2): `get_forge` auto selects `NoneForge` only when the
  repository has no `origin` remote; otherwise it returns `GhForge` when `gh` is present and the ref is numeric.
- **`origin` present and no `gh`: landing refuses and waits.** The message names the cause ("this repository has an
  `origin` remote and `gh` is not available; landing waits for the forge"), not a key to set: there is none.
- **Offline is not a landing flow.** Work, review and gate locally; the branch waits. This is the single choice
  that keeps F3 and F4 unnecessary.
- **Adding `origin` to a repository later moves landing to F1**; the first push of main fast-forwards or is refused.
- **Rejected: F3**, firmly on the rulings "the forge stays the central origin" (policy) and "the forge stays the
  default route" (1252) [M, quoted]. Inferred reasons: web sessions and laptops cannot reach `/srv` [I]; guard
  growth [I], which vanishes if `/srv` becomes `origin`. Reopen on evidence: GitHub unreachable from both hosts for
  over a day while work had to land, or a forge policy change blocking landing.
- **Rejected: F4** (no canonical main, contradicts "one place to pull from").
- **Push-failure reconciliation is moot.** It was drafted for an F2 that pushed (1276's "exit 6 … who reconciles is
  unwritten"). F2 now has nothing to push; F1's forge merge is atomic. One finding survives for F1's local mirror of
  main: the guard accepts a *stale* `origin/main` [M, gaze on PR 1809], so a reset of local main must follow a fresh
  fetch, never the remembered tip.

## 4. What changes in the tickets and the rule

- **1273 (C3)**: no change in substance. `review_notes.py setup/sync/publish` talk to `origin` only; no hub
  selection, no per-remote refspecs.
- **1274 (C4)**: no change.
- **1280 (landing route read off the repository), before 1276**: implement "local only with no `origin` remote,
  else refuse without `gh`" in `get_forge`/`raid_land.py`; drop `IDH_FORGE`; adjust callers and tests that relied on
  auto. ~0.5-1 agent-hour (~$6-15) + 2 author-minutes [I]. Separate from 1276 because it changes today's behaviour
  on every repo and 1276 should exercise the corrected route, not build it.
- **1275 (merged)**: no code change. Its exit-6 reconciliation item is dropped as moot (§3).
- **1276 (C6)**: unhold after 1280. Exercise F2 on a repository with no `origin` remote (temp repo, existing
  criterion), plus the refusal when `origin` exists and `gh` is absent, plus the spec §8 rebase and
  concurrent-append cases. Do not exercise F3 or F4. F1 is covered by "forge path unchanged".
- **rules/git.md, line 9** (written at C5's merge per 1277 point 5; text proposed, the author's call):
  "Everything … lands via branch + PR on the forge. A repository with no `origin` remote lands via branch + local
  gated merge (merge skill), its own main canonical. With `origin` and no `gh`, landing waits; nothing lands
  locally."

## 5. The author's decisions, priced

| # | Decision | Recommended | Author | Agent |
|---|---|---|---|---|
| 1 | F1 default; F2 only with no `origin` remote; no setting; F3, F4 rejected (ruled) | yes | 5 min | 0 |
| 2 | Offline never lands; `origin` present and no `gh` refuses and waits | yes | 2 min | 0; the alternative is local landing diverging from the forge |
| 3 | Route read off the repository (1280): local only with no `origin`, else refuse | yes | 2 min | 0.5-1 h, ~$6-15 |
| 4 | rules/git.md line 9 text above | yes | 3 min | 0.25 h, ~$3-4 |
| 5 | Later: notes as evidence store on the forge route too (one store for A) | wait for web legs | 15 min, after 1276 | ~4-6 h, ~$50-90 |

Basis [I]: agent-hours by analogy with 1275 (PR #1806); USD at ~$12-15 per agent-hour
(`conception/discussions/2026-10-14-1095-seats/r2-architect.md`), not measured here. F3, F4 unpriced.

**No probability is given**: there is no base rate. What would overturn the recommendation: (a) the author needs to
land for days with GitHub unreachable from both hosts (then F3, with `/srv` renamed `origin`, is the next step, not
F4); (b) the web legs show a web session cannot push to GitHub at all, which weakens the hub argument less than it
seems: such a session could not reach `/srv` either.

## Naming

An earlier draft proposed one switch, `idh.mergeRoute = forge | local` (replacing `IDH_FORGE=auto|gh|none`). The
ruling dropped it: the route is read off the repository, so there is nothing to name, set or inherit. Review on
notes needs no setting either.

## Author's ruling (2026-10-27)
Accepted: **F1 is the default; F2 is for repositories without an `origin` remote.** The route is read off the
repository, not set: with a remote named `origin`, landing is F1 only (forge PR; if `gh` or the forge is
unavailable, the landing refuses and waits, never lands locally); with no `origin` remote, landing is F2 (local
gated merge; the repository's own main is canonical). This supersedes the `idh.mergeRoute` switch proposed above:
there is no setting. The fix becomes: auto selects the local merge only when the repository has no `origin` remote,
and otherwise refuses without `gh`. F3 and F4 stay rejected.
