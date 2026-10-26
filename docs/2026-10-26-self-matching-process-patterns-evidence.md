# Self-matching process patterns: evidence for ticket 1216, and a defense in depth

Written 2026-10-26 from an arena session (project `code/arena`, model Sonnet 5.5, runtime Claude Code). Everything
below is what that session observed; what it did not verify is marked.

## 1. Specimens, all from one session after the 0889 guard was deleted

**A. The self-wait.** The agent needed to know when a background `padme-llm.py manifest` run ended, and sent:

```bash
until ! pgrep -u $USER -f 'padme-llm.py manifest' >/dev/null; do sleep 5; done; python3 ...
```

`pgrep -f` matches full command lines, and the Bash tool runs the command as `bash -c '<the whole text>'`, so the
waiting shell's own command line contains `padme-llm.py manifest`. The loop waited for itself. Nothing in the harness
objected. The call ended only at the timeout the agent had set on it (300 s), when the runtime moved it to the
background; the agent then had to find out why it had not finished. Cost: about 5 minutes and a stranded waiter. Same family as the 105 waiters of ticket 0889.

**B. The self-kill.** To stop that waiter the agent sent:

```bash
for p in $(pgrep -u $USER -f 'until ! pgrep -u'); do kill $p; done; ...
```

The pattern occurs in the text of this very command, so the shell killed itself: exit code 144, the rest of the
command never ran. This is the same bug as A, aimed at `kill` instead of `until`. The 0889 memory note already
records that "a sweep that greps command lines for the waiter matches itself".

**C. The wide pattern (a near miss, not a self-match).** Earlier the agent sent
`pkill -f 'bin/make|gmake|cicc|nvcc'` to stop its own build. Those names also belong to other sessions' compilers
on the same machine. The Claude Code permission classifier refused it ("Interfere With Workloads"); no harness
guard did. The agent then identified its own processes by `readlink /proc/<pid>/cwd` and walked their descendants,
which worked. Same root: a name pattern is not an identity.

## 2. One root cause

`-f` selects processes by a regular expression over their full command line. The caller is a process, its command line
carries the caller's own text, and that text contains the pattern. A pattern that appears literally in the command that
uses it matches the caller. Any pattern broad enough to catch its target by name can also catch other owners' processes.

What worked in the same session, in order of robustness: waiting on a PID (`until ! kill -0 "$pid"`); the bracket
idiom `pgrep -f '[p]adme-llm.py manifest'` (the regex `[p]adme` does not match the literal text `[p]adme`); selecting
by `/proc/<pid>/cwd` and killing the descendant tree of a PID the agent started.

## 3. Why the existing barriers did not reach the agent

| Barrier | State on 2026-10-26 |
|---|---|
| Memory note `feedback_pgrep_waiter_matches_itself` | Exists, but in the harness project's memory (`-home-haduong--claude`), not the arena project's index the session loaded. This is the failure the note itself describes: recalled by relevance, it reached none of the 105 waiters. |
| Guard `scripts/guard-pgrep-waiter.sh` (ticket 0889) | Deleted by commit 90a62683 (ticket 0976, 2026-09-24): "never wired live, 0 firings". |
| Resident rule | None for waiting or killing by pattern. Not in the arena night's pinned Pi snapshot either (ticket 1216 says it grepped). |
| Hooks configured | `~/.claude/settings.json` and `settings.shared.json` have no `hooks`; the wired ones come from the adapter plugin. |
| Runtime backstop | A Bash call that exceeds its timeout is moved to the background (here the 300 s the agent had set; the default is shorter). It limits the waste, it does not prevent or explain the bug. |

## 4. Do we already pay for hooks? Yes, in all three runtimes

- Claude Code: `adapters/claude-code/hooks/hooks.json` wires `PreToolUse(Bash)` to `guard-destructive-bash.sh`
  (plus SessionStart and SessionEnd hooks).
- Codex: `adapters/codex/hooks.json` wires the same script; Codex skips non-managed hooks until their hash is
  trusted (README, section on trust).
- Pi: `adapters/pi/extensions/idh-guard.ts` registers a `tool_call` handler for bash and feeds the same payload to
  the same script.
- Measured on this machine: `idh-hook guard-destructive-bash.sh` costs about 33 ms per call (5 calls, 163 ms wall).

So a new rule folded into the guard that already runs adds no process and no wiring; a separate new hook would add
one process per Bash call in each runtime. Not verified: the Codex trust step for a changed hook definition, and
whether the arena's pinned Pi snapshot loads `idh-guard.ts` (ticket 1216's first step covers this).

## 5. Defense in depth

Three layers, each cheap alone, each covering the others' hole. None is chosen by this note; it states what each
would be and what exists.

**Layer 1: a runtime-independent instruction.** One or two lines in a file all three runtimes read (the shared
`AGENTS.md` rules), teaching the primitive, not the prohibition: wait on a PID or use a `waitfor <pid|log-line>
--timeout N` helper; never `-f` a pattern that appears in your own command; stop only processes you started, by PID.
It reaches Pi and Codex where no hook may. Its weakness is recorded: the 0889 note had the right recipe for 105 misses.

**Layer 2: a hard guard in the existing bash guard.** Replace shape matching (0889 needed three review rounds for
`for` loops and heredocs) with a semantic test: for each `pgrep|pkill|pidof ... -f PATTERN` in the command, compile
PATTERN as the tool would and test it against the command text itself; if it matches, the call is a self-match and
is denied with the remedy named. The same test covers specimens A and B and needs no loop-shape recognition. A
second check, for C, denies `pkill -f` unless it is scoped by `-P`, `-u` plus an exact pattern, or a PID list.
Open: ERE versus Python `re` differences; how the tool's wrapper quotes the command in Pi and Codex; false positives
on a command that only quotes the text (for example `echo 'pgrep -f x'`).

**Layer 3: a watchdog for what slips through.** A periodic sweep for processes that are loops waiting on
themselves: command line contains `sleep` and `pgrep`, parent is init or the user manager, age beyond N minutes.
Report first; kill only with the kill guard's rules. The 0889 note already named the signal (reparenting under a
session path) and ticket 1214 (stall watchdog) is the natural home. Unverified: whether the arena's watchdog timer
could host it unchanged.

## 6. What this ticket should demand before accepting any layer (the lesson of 0976)

The guard was deleted with 0 firings because it was never wired. A guard that is not wired live cannot have firings,
so "no firing" must not be read as "no value". Each layer therefore ships with:

1. a wiring proof per runtime: a known-bad command fired in Claude Code, Codex and Pi, and denied;
2. a positive control (specimens A, B and C above are three ready-made inputs) and a replay over the trace corpus
   with the would-fire count and a sample of false positives;
3. an owner and a deletion rule that distinguishes "wired and never fires" from "never wired".
