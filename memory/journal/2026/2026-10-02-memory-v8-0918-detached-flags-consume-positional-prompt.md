# Detached CLI flags consumed positional prompts on two runtimes

Context: memory-v8 acceptance trial (ticket 0918), conductor session driving
all four runtimes detached on 2026-10-02, each with the same common
instruction passed as a positional argument or stdin.

Observation: on Claude Code 2.1.286, launching with
`claude -p --output-format stream-json --verbose --allowedTools "Read Grep
Glob Bash Write" "$(cat prompt.md)"` failed with exit 1 and "Input must be
provided either through stdin or as a prompt argument when using --print" —
the multi-value --allowedTools flag consumed the positional prompt. Passing
the prompt via stdin fixed it. On Vibe CLI 2.25.8, `vibe -p --trust
"$(cat prompt.md)"` failed with "Error: No prompt provided for programmatic
mode" — the --trust flag consumed the positional prompt; placing the prompt
immediately after -p fixed it. Codex CLI 0.159.3 accepted the prompt as a
positional argument directly.

Consequence: two of four runtime legs failed their first detached launch on
the same failure class (a flag with an optional value silently absorbing
the next positional argument), costing one relaunch each; both were fixed
by reordering arguments rather than by any repository change. The failed
launches wrote nothing.

Evidence: /tmp/mem0918/claude/stream.jsonl (first, failed run's tail) and
/tmp/mem0918/vibe/stream.jsonl (first failed run's error line), against the
successful relaunches of the same commands reordered. Whether other flag
combinations show the same absorption was not tested.
