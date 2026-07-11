---
name: feedback-cli-verb-in-subcommand
description: "For CLI scripts, the script name is the noun (what it manages); verbs live in sub-commands. Avoid `install-deps.sh uninstall` and other Démarrer-pour-Arrêter absurdities."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e29953e5-db9e-48c8-9b55-60f58cd5901a
---

When designing a CLI script with sub-commands, the script name should be a **noun** describing what it manages; the **verb** belongs to the sub-command. `idh-deps.sh install|update|remove|status` reads naturally; `install-deps.sh uninstall` is the Windows "click Start to Shut down" absurdity.

**Why:** User flagged `install-deps.sh uninstall` mid-ticket with the Windows analogy. The verb in the filename pre-commits the script to one action and makes any opposite sub-command paradoxical. Naming hygiene matters for the dev-Monday-before-coffee persona.

**How to apply:** Before naming a multi-action script, list its sub-commands and check that every sub-command reads coherently after the script name. If `<script> <verb>` produces an oxymoron for any verb, rename the script to a noun. Related: [[feedback-rename-sweep-full-unit]] — when fixing the script name, sweep all references in the ticket/spec/docs in the same edit.
