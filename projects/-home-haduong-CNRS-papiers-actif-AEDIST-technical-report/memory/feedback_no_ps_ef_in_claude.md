---
name: Never use ps -ef / pgrep -a in this harness
description: Process listings with command-line args leak API keys because Claude Code inlines CLAUDE_ENV_FILE contents into bash -c command lines.
type: feedback
originSessionId: cdaa7a19-9651-4adf-ae9d-cf8d5e977b3b
---
`ps -ef`, `pgrep -a`, `ps auxw` and any other command that prints process command lines must never be invoked here. Claude Code's bash tool wraps every spawn as `bash -c "source <snapshot> && KEY1=v1 KEY2=v2 … : && shopt … && eval '<your command>'"` — even though the `KEY=v :` chain is bash idiom that doesn't persist past the `:`, those values appear in command-line listings. A single `ps -ef` dumps every API key in scope into the chat transcript.

**Why:** 2026-04-30 — I ran `ps -ef | grep :11434` to debug a curl. It surfaced ANTHROPIC_API_KEY, OPENAI_API_KEY, OPENROUTER_API_KEY (twice — global + repo), DEEPSEEK_API_KEY, MISTRAL_API_KEY, TAVILY_API_KEY, ZOTERO_API_KEY (×2), HF_TOKEN, ZENODO_TOKEN, AGENT_GH_TOKEN, and HAL_PASSWORD in plaintext. The user had to rotate every key.

**How to apply:**
- For port checks: `ss -tnlp | grep :PORT` (PID without args), `lsof -i :PORT` (PID + port).
- For process state: `pgrep -f PATTERN` (PID only, no `-a`), `ps -p PID -o pid,stat,etime,comm` (no command-line column).
- For "is X running": `pidof X` or `pgrep X` — no args column.
- The user-side leak path was patched in `~/.claude/scripts/on-start.sh` (commit `d4653eb`) so future sessions won't accumulate keys in `CLAUDE_ENV_FILE`. But the inline `KEY=v` chain may still appear from Claude Code's internal env handling. The rule stands either way: any process listing with command-line args is a potential leak.
- This is the *project* dimension of the safety rule "never display secrets" already in user_role memory. That rule was about *what I write*; this is about *what tools surface*.
