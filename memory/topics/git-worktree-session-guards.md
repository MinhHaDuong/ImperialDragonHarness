# git in a worktree session

Scope: running git from inside a worktree session of this harness — which
guards refuse which command forms, and which remedy reaches which checkout.
An attributed operational note consolidated and re-tested 2026-09-06; assess
against the current rules and evidence before relying on any specific refusal
message.

## Supported observations

The source note distinguishes two independent guards, not one. The first is
the rtk rewrite: `git <verb>` is rewritten to `rtk git <verb>` before the guard
inspects it, and the refusal text says so; both `\git <verb>` and
`/usr/bin/git <verb>` defeat this one. The second is the containment rule
about redirecting git to the shared checkout via `-C`: neither escaped form
defeats it — only calls held in a script file reach another checkout. The note
reports that conflating the two guards is the trap, and that one deleted note
advised exactly the conflation (`\git -C <path>`) as its headline remedy.

## Sources and exceptions

- [git in a worktree session](../reference_git_in_a_worktree_session.md) — attributed operational note, re-tested 2026-09-06.
- Provenance: [source inventory](../../docs/memory-v8/source-inventory.md);
  revisions in [source-revisions.tsv](../../docs/memory-v8/source-revisions.tsv).
