---
name: feedback_bash_env_reinjects_secrets
description: "BASH_ENV re-runs the harness loader in every child bash, so unsetting a credential in a parent shell is a no-op — clear BASH_ENV or use env -i"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: bccc95ab-da2d-4c1a-a8b2-f2eb43af511e
  modified: 2026-07-27T12:37:14.518Z
---

`BASH_ENV=~/.claude/scripts/bash-env.sh` is loaded at the startup of **every**
non-interactive bash subprocess. It re-runs the `KEYS=` selection and re-exports
the real credential, **overriding whatever the parent set**. So this does
nothing:

```bash
unset OPENAI_API_KEY        # parent only — the child gets it back
bash -c 'echo "$OPENAI_API_KEY"'   # prints the REAL key
```

**Why:** two live keys leaked on 2026-07-27 through exactly this. Test suites
injected a fixture credential, but their stub scripts (bash, so BASH_ENV fired)
received the real key instead; when an assertion failed it printed what it
found. Both suites were also *red* because of it — the ambient key overrode the
injected fixture, so scrub assertions compared against a value the scrub was
never given. The leak and the failure had one cause.

**How to apply:** to make a child hermetic, `export BASH_ENV=` or spawn with
`env -i HOME=... PATH=... bash -c`. Assert against a **child**, never the
current shell — a parent-scope check passes while the leak is alive, which made
a first attempt at the fix a silent no-op. Verify with a *fake sentinel* loader,
never the real key: point `BASH_ENV` at a script exporting a recognisable dummy
and grep the output for it. Related: [[reference_keystore_keys_selection]],
[[feedback_no_ci_local_merge_gate]].
