<!-- last-reviewed: 2026-10-05 -->
# Guards

Both guards apply to every agent role — a main session and a spawned profile
alike, whatever runtime launched it. Rules only; hoisted from AGENTS.md for
bare-context profiles to load as one file.

- **Never display credentials.** Never display API keys, tokens, passwords,
  or any credentials in chat text — not even partially, not even in
  "here's what I found" summaries.
- **A skill load is not write authorization.** Loading a harness skill does
  not authorize writing into the harness, its shared memory, or another
  project. Resolve the project repository before writing; stop and report an
  unavailable destination instead of falling back to the harness or native
  store.
- **More than ~256K tokens of context is a monster ticket: SPLIT THE
  WORK, never widen the window.** Work tops out ~236K un-compacted
  (1024, 2026-10-05); decomposition mechanics in workflow.md. Answer a
  context wall with task decomposition, not a bigger window, KV
  tricks, or compaction.
- **More than ~256K tokens of context is a monster ticket: SPLIT THE
  WORK, never extend the window.** Work tops out ~236K un-compacted
  (1024, 2026-10-05). Answer context walls with decomposition — never
  bigger windows, KV tricks or compaction. Size tickets to fit; a run
  that starts compacting should split, not grind.
