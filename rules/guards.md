<!-- last-reviewed: 2026-10-05 -->
# Guards

These guards apply to every agent role — a main session and a spawned profile
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
- **More than ~256K tokens of context is a monster ticket: split the
  work.** Work tops out ~236K un-compacted. Never answer a context wall
  with a bigger window, KV tricks or compaction; a run that starts
  compacting should split, not grind.
