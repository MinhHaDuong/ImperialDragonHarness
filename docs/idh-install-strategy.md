# Install IDH alongside existing agent configuration

Clone the repository to `~/.idh`. Do not replace `~/.claude`, `~/.agents`, or
any runtime's `skills` directory. Each runtime should register IDH through its
own additive mechanism, and only for skills and wiring reviewed for that
runtime.

| Runtime | Target installation mechanism |
|---|---|
| Claude Code | A native plugin containing the reviewed skills and Claude hooks. Keep the user's `~/.claude` profile. |
| Codex | A local plugin containing the reviewed skills and Codex hooks, registered through a personal marketplace. |
| Pi | A Pi package loaded from the local IDH checkout, with an explicit resource list. |
| Mistral Vibe Code | Add `~/.idh/skills` to `skill_paths` in `~/.vibe/config.toml`, after reviewing which skills work in Vibe. |

For a skills-only installation, none of these paths needs a link replacing a
shared directory, a shell loader, or a timer. A same-name skill in an existing
installation needs an explicit choice; installation must not silently take it
over. Keep host-level setup, such as shell integration and scheduled audits,
separate and opt-in.

This is the target design, not a claim that all four packages exist today.
The current `idh install` is a legacy all-runtime host setup: it creates
declared links, edits `~/.bashrc`, and enables a timer when systemd is
available. It has no dry run or target selector. `idh check` and `idh status`
are read-only diagnostics, not an install plan. Do not use `idh install` as a
fresh skills-only install while the installer is being split.

Implementation sequence:

1. Make a read-only install plan that lists exact actions and conflicts, with
   a selected runtime. Preflight all selected actions before writing.
2. Package and probe one portable skill in each runtime's native mechanism.
   Extend the package only as more skills pass a runtime review.
3. Put shell setup and timers behind separate explicit commands. Retire the
   legacy all-runtime default once native registration covers its useful work.

References: [Claude Code plugins](https://code.claude.com/docs/en/plugins),
[Codex local plugins](https://developers.openai.com/plugins/build/plugins),
[Pi packages](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/packages.md),
[Vibe skill paths](https://docs.mistral.ai/vibe/code/cli/skills).
