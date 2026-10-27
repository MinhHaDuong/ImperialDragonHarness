The current plan is portable with conditions. Inline gaze is a useful simplification; installation transitions and collection still need explicit contracts. Findings below are from repository files, installed help and local links; runtime launches and forge queries were not performed.

- **Inline gaze — no objection:** dropping `context: fork` removes one delegation layer across Claude Code, Codex and Pi; also remove `background` and the fork-lifetime directives, and specify loading panel references as procedures rather than invoking their forked skills during child 2.

- **Seat depth — objection:** depth 2 under delegated hunt is a target, not a verified capability; `rules/claude-code.md` requires configurable nesting, this Codex session proves four slots but not universal depth, and Pi’s installed extension launches separate `pi --mode json -p --no-session` processes. Remove with transport preflight, explicit profile/cwd/revision delivery, verified worker registration, and detached fallback; failed launch must remain `no-report`.

- **Controller collection — objection:** “artifact-polling, controller-owned” remains ambiguous for read-only Codex seats, while existing panel instructions explicitly require reviewer-written artifacts and reject returned findings. Remove by letting transport adapters capture final responses/stdout and have the controller write artifacts; specify completion, failure and deadlines. Installed Claude, Codex and Pi help confirms headless transports, not their successful operation here.

- **Gaze return contract — no objection to separating review status from gate authority:** `CLEAN|FINDINGS|DEGRADED|NOT-RUN` is portable structured output; finalize a machine-validated schema with repository, reviewed head/base, plan identity, required-seat completeness, publication status and cause fields. Specify that publication failure cannot return `CLEAN`, and callers always run verify-gate against the anchored identity.

- **Numeric actor allow-list/edit extension — objection:** numeric IDs need forge-host namespace and an explicit mapping between API identity representations; “edit-flag query” alone does not define unedited semantics or supported evidence object types. Remove with a normalized `{forge_host, actor_id, object_type, unedited}` adapter contract, pinned IDs, fixtures for users/bots and rejection on unavailable or uncertain fields. Authentication identifies the poster, not the worker **[inference]**. Copilot’s unknown-family treatment is appropriate, pending the author’s confirmation.

- **Forge-readable reports — no objection:** controller publication supports all three runtimes and read-only workers; require full retrieval and hash verification at gate time, deterministic chunk manifests for size limits, pagination and incomplete-publication rejection. Local paths or expired artifacts cannot satisfy readability.

- **No-alias transition — objection:** installed Claude and Pi `review-pr` links point directly at the directory being deleted; they become dangling. `adapters/projections.json` registers skill children, but `validate-projections.py:310–321` enumerates current source children, so vanished names escape that inventory. Remove with explicit retirement cleanup and discovery checks in each moving child, including Codex’s shared root and non-default installations. Session discovery caches may retain retired entries **[inference]**; require refresh/restart before continuation.

- **Moving panels — objection:** both current panel bodies derive `IDH_ROOT` two levels above the loaded SKILL.md. An unchanged body moved to `skills/gaze/references/code.md` or `prose.md` has incompatible path assumptions **[inference]**. Remove skill frontmatter, standalone directives and root derivation; pass gaze’s resolved root explicitly. Bundle executable callers, installation retirement and their checks in the same child; stale operational text between 3a and 3b remains a failure path.

- **Retired-name lint — objection:** including `adapters/` is correct, but tracked text scanning cannot detect dangling links, installed copies or runtime caches. Remove with tracked-path lint plus a separate read-only installed-registration audit covering manifest-declared projection roots; test filenames, symlink targets and copied frontmatter names, with narrow historical exemptions.

Top three risks:

1. Retirement leaves installed discovery or moved panel procedures broken.
2. Unsupported depth or reviewer-write assumptions produce missing reports.
3. Underspecified forge identity/edit/report adapters admit unverifiable evidence or prevent valid reuse.