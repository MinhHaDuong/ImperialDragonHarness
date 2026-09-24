---
name: reference-offinity
description: "Offinity Diaries, Minh's shared project journal for the realf blog, lives at diaries.offinity.io"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 83b9f18e-f976-4e1a-89c8-7f8630493baa
  modified: 2026-09-17T16:20:11.289Z
---

Offinity is Offinity Diaries, <https://diaries.offinity.io/>: a project journal
shared with a small circle of trusted people, in a spirit of mutual support.
Minh keeps the realf.hypotheses.org launch journal there and asks that circle
for feedback ("Avis demandé sur Offinity", journal 2026-09-08). Not the offshore
wind platform nor the workplace tool of the same name.

Register for an Offinity entry: first person, progress, doubts, decisions,
learnings, ending with one concrete request to the readers. Public
announcements (LinkedIn, Mastodon, Bluesky) are a different register. Drafts
of both live next to the billet they promote (`diffusion-<date>.md`).

**Scripted access: none, as of 2026-09-17.** Login is OAuth through an
Authentik identity provider (account.offinity.io), no application password, no
documented API; the Next.js app talks to a backend under `/api/` from a browser
session only. No credentials in `~/.config/keys/`, no browser automation on
the machine. Entries are pasted by Minh from the `diffusion-<date>.md` draft.
Revisit only if he stores Authentik credentials or hands over a session token.
