---
name: feedback_untrusted_env_export_is_code_execution
description: "Exporting names/values from an untrusted .env into the environment is a code-execution class, not just a guard-var concern; refusing GUARD_ vars is insufficient — the process/interpreter-critical namespace is the real surface."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a645ef77-f8e4-4301-bc40-961e61b43b5b
---

Loading an untrusted project `.env` into the shell environment is a remote-code-execution surface, not merely a "don't clobber my GUARD_ vars" hygiene issue. Refusing `GUARD_*`/`_GUARD_*` covers the harness's own guards but leaves the dangerous namespace open. The names that grant code execution when an attacker controls them:

- **`GCONV_PATH`** — glibc/iconv loads a module from this path; arbitrary code execution, reproduced live during the hardening.
- **`LD_PRELOAD`, `LD_AUDIT`** — dynamic-linker injection into every spawned binary.
- **`BASH_ENV`, `ENV`** — shell re-entry: the value is sourced on the next non-interactive `bash`.
- **Interpreter hijacks** — `PYTHONPATH`, `NODE_OPTIONS`, `NODE_PATH`, `PERL5LIB`, `RUBYOPT`.
- **`PATH`** — clobber to shadow real binaries with attacker copies.

**Exploitability ranking:** the direct strict-parse loop (attacker controls *both* the variable name and its value in the `.env`) is more exploitable than a selection/rename path (`KEYS=provider:SRC=DST`, where the value comes from a *trusted* provider file and only the mapping is attacker-influenced). Harden the strict-parse loop first.

**Defense:** default-deny — parse the untrusted `.env` in a restricted grammar and never *source* it; export only an allowlisted key namespace; denylist the critical names above on every export path including renames. Tracked in ticket 0345 (policy decision pending: full denylist vs RCE-only subset vs allowlist — recommended the RCE-only subset). See [[project_bash_env_secret_loading]] and [[feedback_bash_env_tests_real_invocation_path]]. (bash-env.sh hardening, PRs #588/#604, 2026-07-14)
