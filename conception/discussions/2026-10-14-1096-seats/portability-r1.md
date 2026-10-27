**Verdict: A, B and C are portable with conditions. The shared evidence core is also portable with conditions, but its proposed schema and reuse test are insufficient.** None should depend on hooks, native commands, fork lifetime or nested subagents.

**Runtime constraints applying to every option**

- **Claude Code:** `Agent` launches and `claude -p` provide worker transports; the recorded native door supplies Anthropic seats, so required cross-family review needs another transport (`skills/route/routes.json:66–76`; `references/decorrelation.md:32`). Nesting is configurable, not guaranteed: the repository names depth/concurrency knobs and requires depth ≥2 for team-lead delegation (`rules/claude-code.md:43–46`). `context: fork` and background-completion behavior are Claude-specific lifecycle assumptions (`skills/review-pr/SKILL.md:39–66`). Installed CLI help confirms headless execution, resume/background support and a bare mode that skips hooks. Consequently, neither hooks nor keeping a fork alive may establish review completeness.
- **Codex:** this session exposes `spawn_agent`, model overrides for fresh-context forks, child management and four concurrency slots. That verifies this session’s capabilities, not every Codex installation or nesting limit. Installed 0.162.1 help confirms `exec`, native `review`, resume/fork, sandbox controls, managed worktrees and hook trust. The recorded headless route is OpenAI-only under the tested account (`skills/route/routes.json:91–100`). A read-only child cannot write the proposed panel artifact; its controller must collect output and perform the atomic publication. `agents/*.md` tool lists are not Codex capability grants.
- **Pi:** core has no subagents; the installed example extension launches separate `pi --mode json -p --no-session` processes, passing model, tools and cwd (`~/.pi/agent/extensions/subagent/index.ts:300–349`). It therefore provides process delegation, not a portable nested-agent guarantee. Current code also inherits dispatch model/thinking when agent frontmatter lacks a model, qualifying the route record’s “pinned per agent file” description. Pi exposes lifecycle/tool events through extensions; its harness guard is an optional, partly fail-open adapter (`adapters/pi/extensions/idh-guard.ts:50–85`). Installed help confirms ephemeral and resumable sessions, skill discovery switches and headless output.

For **all three**, explicit `git worktree` operations, absolute repository paths, pinned revisions and controller-owned collection can provide the common basis. Hooks may add checks or cleanup. Worktree ownership must not rely solely on `$PPID`: identifying it as the long-lived runtime is an unverified cross-runtime assumption (`skills/hunt/SKILL.md:92–96`). Session termination must yield incomplete evidence, never approval.

Forge access is a controller capability requiring available authentication, network and permissions; it is not supplied by a skill or profile. The existing anchor hardcodes GitHub’s `gh` (`scripts/review-pr-anchor.py:26`), contrary to the generic authoring rule (`rules/authoring-skills.md:20–25`). This is cross-runtime on a suitably configured GitHub host, but not forge-neutral.

**Names**

The categorical claim “`review` is runtime-bound” needs qualification. Codex has a native `review` CLI command. Gaze documents Claude’s built-in `/review`, but I did not independently verify its current interactive registration (`skills/gaze/SKILL.md:423–428`). Installed Pi’s built-in list contains none of `review`, `review-pr` or `gaze` (`…/dist/core/slash-commands.js:2–26`); Pi skills use `/skill:<name>` (`…/dist/modes/interactive/interactive-mode.js:530–536`). Harness documentation gives Claude `/name`, Codex `$name`, Pi `/skill:name` (`adapters/README.md:52–56`). No native `review-pr` or `gaze` binding was found; exhaustive extension/plugin collision checks remain unverified. Literal slash-command prompts cannot be the shared invocation contract.

**A — portable with conditions**

Claude can use forked skill convenience plus native or detached reviewers; Codex can use fresh-context children or `exec`; Pi can use its extension or direct headless processes. Removing Gaze’s intermediary reduces the documented chain, but does not guarantee sufficient nesting once hunt itself is delegated.

Conditions: capability discovery instead of checking specifically for `Agent`; explicit profile delivery; controller-published artifacts; bounded collection independent of fork notifications; optional native review/simplify; explicit arguments and cwd. The Gaze alias must delegate to the same plan/evidence mechanism and propagate failures. Raid should request continuation of hunt’s plan after rebase, not independently select another panel. Mixed code/prose changes need a composed plan—an exclusive `auto` mode could omit required coverage **[inference]**.

**B — portable with conditions**

Its runtime mechanisms and degradations are the same as A; separate helper names introduce no inherent transport dependency. Claude skill loading, Codex explicit skill invocation and Pi namespaced skills can all reach the helpers.

The main defect is contractual: standalone helpers can bypass planning and reuse. Make one shared deterministic planning/evidence implementation mandatory for both helpers and every caller, including standalone invocation. This requires no third skill or runtime hook. Rename profile references and runtime projections, and validate name collisions. Hunt’s length and rename cost are maintenance concerns, not portability failures.

**C — portable with conditions**

Claude retains both forked panels; Codex and Pi require the same transport-neutral execution corrections as A. Keeping both skills **“as is”** preserves Claude-specific `Agent` preflight, fork-lifetime language and invocation assumptions (`skills/review-pr/SKILL.md:116–138`; prose frontmatter:7–12).

Conditions: share the executable evidence/reuse implementation rather than copying rules; normalize prose verdicts; remove mandatory native-command expectations; adapt both panels’ collection and invocation. Prose currently requires its AI-tells auditor every round (`skills/review-pr-prose/SKILL.md:161–163`); unchanged-head zero-seat reuse requires an explicit policy revision.

**Shared evidence core — portable with conditions**

Git objects and structured forge comments are runtime-independent. Claude, Codex and Pi controllers can read/write the same record; detached reviewers need no forge credentials. Outages, unreadable history or failed publication must block reuse (`skills/review-pr/SKILL.md:213–217`).

However, post-image blobs plus disjoint base changes do not prove unchanged review meaning. File modes, deletions, renames, relevant dependencies, ticket criteria and policy can change without altering recorded blobs **[inference]**. Record repository/forge identity, old/new tree entries, reviewed diff, dependency scope, criteria/policy versions, producer identity/family, actual reviewer identity, effort, report provenance and applicable checks. A mutable YAML comment is a claim requiring validated authorship and linked reports. Select evidence per seat, not merely the latest block; recheck final head/base before ruling and merging.

Verified: duplicate orchestration, count-based rounds, prose duplication, degraded Pi native-review attempts and historical blob checks match the cited files. Correction: Gaze already offers portable simplify (`skills/gaze/SKILL.md:561–576`); both native commands are not mandatory. Unverified: universal nesting depth, current launch success, exact savings/costs and historical behavior on installed versions. Those require runtime integration trials; no model calls or forge writes were performed.