---
name: feedback-execute-authorized-outward-actions
description: "Once the author authorizes an outward action, execute it — never hand him a URL to click or text to paste"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 6f316c3e-3800-40bd-bb02-33c301abd583
  modified: 2026-08-29T08:35:14.442Z
---

When the author authorizes an outward-facing action (open the upstream PR, file
the issue, post the comment), **do it and report the result**. Do not produce a
pre-filled link for him to open, or a body for him to paste.

**Why:** he is the paying customer and the agent does the mechanical work. On
2026-08-29 an authorized upstream PR (oscardvs/zoteus#31) was reduced to a
pre-filled compare URL plus a markdown body to paste by hand. He opened and
pasted both; the paste carried a two-space indent and CRLF into a public PR,
which then had to be fixed anyway. His words: "I resent that you have me make
this mechanical work. You are the agent, I am the paying customer."

**How to apply:** probe the capability before declaring it absent. A local
session's forge CLI acts on a cross-owner repo directly with a `repo`-scoped
token — opening a PR from the fork and editing a PR you authored need no push
rights on the upstream repo. A note saying an action "cannot run in this
session" may describe a *remote* session's repo-attachment mechanism; read its
scope before obeying it. Same discipline as any other check: run it against a
case known to be positive rather than assuming the negative.

This does not weaken the authorization rule — each outward action still needs
his say-so, and the result is still verified publicly before being recorded.
It governs what happens *after* the yes. Related: [[reference-zotero]].
