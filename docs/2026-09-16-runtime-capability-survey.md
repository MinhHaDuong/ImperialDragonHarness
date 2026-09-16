# Runtime capability survey: subagent definitions and lifecycle hooks

Evidence for ticket 0924, action 1 ("inspect primary current runtime
interfaces") and its first exit criterion ("all three named targets have
evidence-backed capability declarations"). Surveyed 2026-09-16. Two axes only:
how each runtime defines a custom agent, and what lifecycle boundaries it
exposes. Storage, tokenizer and resume semantics are out of scope here.

Method: web search plus direct fetch of primary documentation. Each claim below
cites where it came from, and the unverified rows say so rather than guessing.

## Axis 1 — custom agent definitions

| Runtime | Location | Format | Context inheritance | Verified |
|---|---|---|---|---|
| Claude Code | `~/.claude/agents/*.md` | Markdown + YAML frontmatter | `subagent_type: "fork"` | tree |
| Pi + `@tintinweb/pi-subagents` | `.pi/agents/*.md`, `.agents/agents/*.md`, `~/.pi/agent/agents/*.md` | Markdown + YAML frontmatter | `inherit_context: true` | docs |
| Codex | `~/.codex/agents/*.toml` | TOML | not documented | docs |
| Gemini CLI | project/global agent dir | Markdown + YAML frontmatter | not documented | docs |
| OpenCode | `~/.config/opencode/agents/`, `.opencode/agents/` | Markdown + YAML frontmatter | not documented | docs |

The capability is now general; the format is not. Every CLI wants a different
frontmatter shape and a different directory, which is why a third-party
compiler (`fmind/agent-supagents`) exists to emit one persona into six target
formats. There is no `AGENTS.md`-style convergence on this axis.

Pi's frontmatter fields, from the extension's documentation: `name`,
`description`, `tools`, `model`, `thinking`, `max_turns`, `isolated`,
`allowed_subagents`, `inherit_context`. The dispatch key is spelled
`subagent_type`, as in Claude Code. `allowed_subagents` is the nesting-depth
lever that `rules/claude-code.md` records as
`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` here.

Two caveats on the Pi row. Subagents are not core: they come from a
third-party npm extension pinned to a pi version, and at least three competing
implementations exist (`tintinweb/pi-subagents`, `mjakl/pi-subagent`,
`nicobailon/pi-subagents`). And `model:` takes a fully qualified provider id
(`anthropic/claude-opus-4-6`), not the short enum token that
`tests/test_model_rightsizing.py` pins.

## Axis 2 — lifecycle hooks (Pi)

Pi exposes 36 events to `pi.on()`. The five classes this harness actually
registers all have a counterpart:

| Harness registration | Script | Pi event | Can block |
|---|---|---|---|
| `SessionStart` | `on-start.sh` | `session_start` (bind), `before_agent_start` (inject) | injection |
| `SessionEnd` | `on-end.sh` | `session_shutdown` | no |
| `UserPromptSubmit` | `knowledge_hints.py` | `input` | no |
| `PreToolUse` ×11 | `guard-*.sh`, `pretooluse-worktree-path-guard.sh`, `inject_rule_on_edit.py`, `rtk hook` | `tool_call` | yes |
| `PostToolUse Write\|Edit` | `lint-on-edit.sh` | `tool_result` | no |
| `PreCompact` (unused here) | — | `session_before_compact`, `session_compact`, `session_compact_failed` | no |

A `tool_call` handler blocks by returning
`{ block: true, reason: "...", terminate?: boolean }`. The `reason` field has no
Claude Code equivalent — the harness encodes refusal motives in stderr today.

`before_agent_start` returns
`{ message: {...}, systemPrompt: event.systemPrompt + "..." }`, so an adapter
injects the resident rule set explicitly.

Events with no Claude Code counterpart: `before_provider_request`,
`before_provider_headers`, `after_provider_response`, `resources_discover`,
`session_before_fork`, `project_trust`, `model_select`,
`thinking_level_select`, `agent_settled`, `session_before_switch`,
`session_tree`.

Counts in this section come from `settings.shared.json`, the tracked file. The
untracked `settings.json` on this machine has drifted from it, holding ten
PreToolUse entries instead of eleven and pointing one of them at a retired
script, so counting from whichever file happens to be local gives a wrong
answer. Memory
`feedback_hook_rename_is_a_two_phase_deploy` records why the two diverge.

## What this implies for the port

**The boundary is not the obstacle; the calling convention is.** Claude Code
hooks are external executables with a JSON-on-stdin, exit-code-out contract.
Pi extensions are TypeScript modules in `~/.pi/agent/extensions/*.ts` or
`.pi/extensions/*.ts`, loaded through jiti without a compile step. Porting
therefore does not mean rewriting the fifteen registrations one by one. One
shim extension can re-implement the Claude Code hook contract: subscribe to
`tool_call`, spawn the existing script with the same JSON, map exit code 2 onto
`{ block: true, reason }`. The scripts and their tests stay as they are.

**The matchers are where it will break.** `Bash(git commit*)`,
`Write|Edit|NotebookEdit` and `EnterWorktree|Skill` are declarative in
`settings.json`; in Pi they become filter code inside the shim. That matching
semantics has already bitten this harness twice (memory
`feedback_guard_flags_match_across_compound`,
`feedback_allow_rule_bare_invocation`), so the shim's matcher is the one part
that needs its own tests. The existing suite pins the behaviour to port against.

## Corrections this survey forces

`rules/README.md` § Resident rules states that a runtime without the rules
auto-load "gets none of it". For Pi the conclusion holds but the reasoning
misleads: the adapter must indeed inject the resident set, and
`before_agent_start` is a more controllable injection point than Claude Code's
built-in auto-load, which the harness cannot inspect. `resources_discover` is
the seam for the `paths:`-conditional bodies. Memory
`reference_rules_tree_is_resident.md` records the same conclusion in different
words, so it needs the same correction.

## Not verified

- **Codex hooks.** Only the subagent axis was checked for Codex. The assumption
  recorded at `docs/2026-09-10-dragon-memory-design-review-fable-acceptance.md`
  ("that Codex and Pi expose boundaries comparable to the Claude Code hooks")
  is now settled for Pi and still open for Codex.
- **Context inheritance** in Codex, Gemini CLI and OpenCode: absent from the
  documentation read, which is a gap in coverage, not evidence of absence.
- Nothing here was executed. No pi, codex or gemini binary is installed on this
  host; every row rests on documentation, not on a smoke run. Ticket 0924's
  test section requires actual smoke evidence, which this survey does not
  provide.

## Sources

- <https://raw.githubusercontent.com/earendil-works/pi/main/packages/coding-agent/docs/extensions.md>
- <https://pi.dev/docs/latest/extensions>
- <https://deepwiki.com/earendil-works/pi/6.1-extension-api-and-lifecycle-events>
  (secondary; it misattributes context injection to `session_start`, corrected
  above against both primary sources)
- <https://github.com/tintinweb/pi-subagents>
- <https://github.com/earendil-works/pi>
- <https://simonwillison.net/2026/Mar/16/codex-subagents/>
- <https://codex.danielvaughan.com/2026/04/27/codex-cli-custom-agent-definitions-toml-specialised-subagents/>
- <https://github.com/google-gemini/gemini-cli/blob/main/docs/core/subagents.md>
- <https://github.com/fmind/agent-supagents>
