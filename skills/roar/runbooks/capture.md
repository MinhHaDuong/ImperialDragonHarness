# Capture runbook

When roar runs this: roar steps 2-3, in the wrap-up worktree, before the worktree is removed.

`<loaded-SKILL.md>` below is roar's own SKILL.md, the file that points here.

2. **Review completed merges**: identify each reviewed merged PR from the
   project's git history and forge, then capture its review attribution in
   step 3. Report a capture failure if the review trail lacks required facts.
3. **Capture significant project experiences**, if any, before removing the
   worktree. Write and commit an append-only entry under the project's
   `memory/journal/YYYY/YYYY-MM-DD-<slug>.md`. Record context, observable events,
   outcome and decisions already made, with references. Include positive and
   negative experiences: novelty, surprise, a consequential failure or success,
   a near miss, or a departure from an existing principle are candidate signals.
   Routine completion alone does not require an entry. Keep it factual, without
   judgment, inferred lessons, rule proposals or interpreted memories.

   Resolve the project repository first. Use the single
   wrap-up branch/worktree described in the bundle section of SKILL.md. Capture only there; never in the
   harness because the loaded skill lives there. There is no private companion
   store — the encrypted-in-repo policy
   supersedes it: judge the audience at capture, before the first byte is
   written, and material not cleared for the repository's public audience
   enters that same repository as age ciphertext through the project's pinned
   capture mechanism (in the harness, `$IDH_ROOT/scripts/memory-capture.sh`, which pins
   the encrypt command, the per-project key under ~/.config/keys/memory/ and
   the judgment point; plaintext never lands in the working tree). Include the
   capture in the single wrap-up bundle, preserve unrelated
   changes, and follow the project's branch/integration policy. A refused write
   or failed commit remains a visible pending capture; do not switch to the
   harness or a native memory directory. An unintegrated capture branch must be
   preserved and reported before worktree cleanup. Do not load the hoard skill
   to derive lessons or propose rules during roar.

   **Capture review attribution for every reviewed merged PR**, even when
   routine completion produces no significant-experience entry. Use the fixed
   lines in [the attribution contract](../../../conception/2026-10-02-reviewer-attribution-design.md#4-the-attribution-record):
   first line `kind: review-attribution`, PR/date/project, writer runtime,
   verbatim provider-qualified full model id and effort, then one named
   `reviewer:` line per review attempt with `status: ran|failed|skipped`.
   Include `model-version=` whenever the provider exposes it. Record findings
   as repository-relative `path:line` with `adopted: yes|no`; identical anchors
   across reviewers are shared catches. Keep a stable name-or-role value for each actual reused reviewer context,
   including repeated rounds and regression checks; retain every raw attempt.
   Use distinct values only for genuinely separate contexts or processes. The
   exact seat/runtime/model/model-version identity unions repeated-attempt anchors;
   source revision, round and evidence references belong in opaque context.
   A failed authentication is a named failed attempt, not a clean review.
   No initial `defect-confirmed:` placeholder is written.

   **One call for the common case**: the block lives on the review's notes
   (ticket 1307), writer entries and the gaze answers' attribution, for a PR
   and a no-forge unit alike. `attribution_record.py --capture-unit pr:<N>
   --capture "$PROJECT_REPO" --audience public|private --project <name>`
   (no forge: `--capture-unit branch:<name>`) assembles it, swaps `pending` for
   the merge date (the forge's, or the landing merge commit's) and captures it.
   It refuses an unmerged unit and a unit with no review on notes.

   **A PR merged before the switch** carries its block in the body only:
   `attribution_record.py --capture-pr <N> --capture
   "$PROJECT_REPO" --audience public|private --project <name>
   [--masked-evidence <path>:<line>]` runs the seats join, the extract with the
   forge's merge date and the capture below, in that order. It refuses an
   unmerged PR and captures nothing while a seat fails; fix the cause and rerun
   (appended seats are not repeated). The steps below remain the contract for
   such a PR and the path for a record that needs hand completion.

   Before reading the body, run `attribution_record.py --seats-pr <N>
   --project <name> [--masked-evidence <path>:<line>]` (ticket 1155): it joins
   the gaze answers of the PR's review on notes (ticket 1301; a merged PR gazed
   before notes evidence: its `/gaze result` comments; an open PR with no notes
   review is refused), each `seat:` line one attempt, appends
   the `reviewer:` lines the block lacks (creating the block if absent), and
   exits 1 naming each capture failure; carry them into step 11's report. The
   evidence anchor is the durable runtime-masked evidence described below;
   without it, a seat whose model was `not observed` is a capture failure.

   When the merged PR body carries an `attribution` block (ticket 1151), copy
   it instead of rebuilding it: read the merged PR's final body from the forge,
   not the commit message, which predates late appends
   (`python3 "$IDH_ROOT/scripts/forge.py" resolve <N>` prints it as the JSON `body`)
   and pipe the body through
   `attribution_record.py --extract --merged <merge-date>`, which swaps
   `pending` for the merge date; stream its output to `--capture` below.
   Complete only what the block lacks, from the review trail.

   Read identities, attempt outcomes and adoption decisions from the actual
   review trail (session outputs or durable PR review comments), never from
   memory or the example template. Do not reconstruct a full model id from an
   alias. When the runtime conceals the verbatim id, use the contract's explicit
   `model-state=runtime-masked · model-evidence=<repo-relative-path>:<positive-line>`
   instead of `model=` on each affected writer or reviewer; omit `model-version=`.
   Preserve durable evidence connecting that limitation to the actual attempts.
   This preserves factual capture while leaving model re-audition impossible:
   the whole PR game is excluded from model estimates and visibly counted as
   runtime-masked. Never use this state to cover unrelated missing facts.
   A reviewed PR whose record cannot name its reviewers or establish
   required facts is a **capture failure**: report the PR and missing facts in
   step 11's summary; preserve the pending capture, never silently omit it.
   Validate the complete record before writing: stream its text on stdin to
   `IDH_ROOT="${IDH_ROOT:-$(p="<loaded-SKILL.md>"; [ -d "$p" ] || p=$(dirname "$p"); cd -P "$p/../.." && pwd -P)}" && python3 "$IDH_ROOT/scripts/attribution_record.py" --capture "$PROJECT_REPO" --audience public`
   Replace `<loaded-SKILL.md>` with the absolute path supplied when loading
   this Roar skill; resolve the helper root in the same shell invocation.
   (use `private` for uncleared material). `PROJECT_REPO` is the resolved
   project's wrap-up worktree; the helper writes the dated
   `review-attribution-prNNNN` journal entry through `memory-capture.sh`.
   Judge the audience before constructing any file; private text stays in the
   stream, never a plaintext working-tree file. Report validation, encryption,
   overwrite or integration failures visibly. Commit successful capture in
   the same wrap-up bundle. Project installations with their own pinned capture
   mechanism must apply that mechanism with the same validated record and
   audience policy; no fallback store is authorized.
