<!-- last-reviewed: 2026-10-05 -->
# Guards

Both guards apply to every agent role — a main session and a spawned profile
alike, whatever runtime launched it. Rules only; hoisted from AGENTS.md so a
bare-context profile loads them as one file.

- **Never display credentials.** Never display API keys, tokens, passwords,
  or any credentials in chat text — not even partially, not even in
  "here's what I found" summaries.
- **A skill load is not write authorization.** Loading a harness skill does
  not authorize writing into the harness, its shared memory, or another
  project. Resolve the project repository before writing; stop and report an
  unavailable destination instead of falling back to the harness or native
  store.
- **A task that saturates more than ~256K tokens of context is a monster
  ticket: SPLIT THE WORK, do not extend the window.** Measured agent work
  tops out around 236K even when the model never compacts (tournament
  1024, 2026-10-05); beyond that, decompose into smaller tickets or
  legs. Do not answer a context wall with a bigger context window, KV
  tricks, or compaction — answer it with task decomposition. When filing
  a ticket, size it to fit; when a run starts compacting or otherwise
  hitting a context ceiling, stop and split rather than grind.
