---
name: feedback_boolean_probe_must_not_expand_the_value
description: "A secret-presence probe must never place the variable in a substitution that can expand to it — `${VAR:-unset}` prints the VALUE when VAR is set; test, then print a literal"
metadata:
  type: feedback
---

Checking whether a credential is loaded is the single most common reason to
touch one, and the obvious idiom leaks it:

```bash
# WRONG — ":-" substitutes the VALUE when VAR is set, so this prints the key
printf '%-40s %s\n' "$v" "${!v:+SET}${!v:-unset}"

# CORRECT — the value appears in no substitution that can expand to it
if [ -n "${!v:-}" ]; then s=SET; else s=unset; fi
printf '%-40s %s\n' "$v" "$s"
```

`${VAR:+X}` yields `X` and is safe. `${VAR:-Y}` yields `Y` **only when unset** —
when set, it yields the value. Written side by side they read as a matched
pair; they are not.

**Why:** on 2026-09-07 this printed a live OpenRouter key into a session
transcript, from a probe whose entire and only job was to confirm a credential
without displaying it. `rules/coding-bash.md` already states the general form —
"the failure message *is* the leak" — and the leak still happened, because the
rule is filed under *failing assertions* and this was a passing report. The
category that leaks is any output touching the variable, not just an error path.

Two aggravating details worth keeping:
- The probe was correct about its finding (the `KEYS=provider:VAR` narrowing
  held; seven sibling keysets stayed unset). Being right about the measurement
  is no protection at all.
- Fixing the probe does not close the incident. Only rotation does. Say so
  plainly to the author in the same breath as the disclosure, and record it in
  the ticket rather than only in the conversation, because a transcript
  redaction and a rotation are different acts and only one of them is enough.

**How to apply:**
- Before running any command that reads a secret-bearing variable, re-read the
  substitution and ask which branch yields the value. If you cannot answer in
  one second, rewrite it as an `if`.
- Report presence, length class, and nothing else. `${#v}` is safe; `$v` is not.
- Disclose immediately and without hedging, name the rotation as the fix, and
  do not let "the probe is fixed now" stand in for it.

Related: [[project_bash_env_secret_loading]], [[reference_keys_config_dir]],
[[feedback_untrusted_env_export_is_code_execution]].
