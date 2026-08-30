---
name: feedback-execute-authorized-outward-actions
description: "Once the author authorizes an outward action, execute it — never hand him a URL to click or text to paste; but show him the artifact itself before publishing under his name"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 6f316c3e-3800-40bd-bb02-33c301abd583
  modified: 2026-08-29T11:21:53.766Z
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

## Approving attributes is not approving the artifact

The complement, learned the same day on the same issue. Answering questions
*about* a document is not the same as having read it, and only the second
authorizes publishing it under his name.

Comment D for oscardvs/zoteus#30 was put to him as two questions — include a
design section? post at ~2050 words? He answered "include it" and "post at this
length", and 12 017 characters went to a public issue under his account within
the minute. He had never seen the text. His next message was "Let me validate
before posting", and it arrived after the API call returned.

**Why it is not a timing accident:** the questions asked about *properties* —
length, whether a section is present — and properties are what you ask about a
thing the reader already has. Asking them instead of showing the text is what
created the gap. A 12k-character document published in someone's name is not
authorized by their opinion of its word count.

**How to apply:** for an outward action carrying a *document*, put the document
(or the exact replacement text, for an edit) in front of him and wait, even when
an authorization already exists. This costs one turn. The recovery cost is
higher and incomplete: a GitHub comment can be edited in place and the URL
survives, but the maintainer's notification email carries the first version and
deletion does not unsend it. Both later edits to that comment went to him as
exact before/after text first, and both were cheap.

The two halves are not in tension: **execute the action without him, but never
publish the artifact without him.** Do the mechanical work; show the words.

Related: [[reference-zotero]], [[feedback-decision-briefs]].
