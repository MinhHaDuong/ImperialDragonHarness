---
name: end-session
description: Deprecated — renamed to /lair. Warns, then delegates to the new name.
disable-model-invocation: true
user-invocable: true
---

# end-session → lair (renamed)

This skill was renamed in ticket 0067. This stub exists for muscle memory only.

1. FIRST, before any tool call, write this line as plain visible response text (it is the point of this stub — do not skip it): **"Skill end-session renamed lair. Retreating to the lair."**
2. Only after that line is emitted, invoke the `lair` skill via the Skill tool, passing along any arguments.

Do not perform any wrap-up steps here — `/lair` owns the procedure.
