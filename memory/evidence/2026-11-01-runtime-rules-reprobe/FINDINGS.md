# 1413 sentinel re-probe, 2026-11-01, padme

After `idh install` wrote `~/.codex/AGENTS.md` and `~/.pi/agent/AGENTS.md`.
Runtimes: codex-cli 0.166.0 (model gpt-6.1-sol, provider openai), pi 1.4.0
(model qwen3.8-flash-next-iq3_s, provider padme). Run from a harness worktree
(project AGENTS.md loads), `</dev/null`, no tools. Prompt: prompt.txt.

| Item | Source | Codex | Pi |
|---|---|---|---|
| 1 guards.md sentence | rules | found | found |
| 2 git.md sentence | rules | found | found |
| 3 workflow.md sentence | rules | found | found |
| 4 HTML comment (workflow.md Module) | comment | NONE | NONE |
| 5 `last-reviewed:` comment | comment | NONE | NONE |
| 6 project AGENTS.md (control) | AGENTS.md | found | found |
| 7 fake sentence (control) | none | NONE | NONE |

Generated files contain 0 `<!--`. Pi's reply to item 1 omitted the leading
"split it." (continuation quoted from the next sentence); sentinel still found.
Outputs: codex.out, pi.out.
