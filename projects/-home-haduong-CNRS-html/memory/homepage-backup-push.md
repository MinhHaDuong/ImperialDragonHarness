---
name: homepage-backup-push
description: "At the end of a homepage-repo session with commits, propose pushing the off-machine backup to padme."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 0cda7768-577a-43b3-8a82-679d31d99a91
---

The `~/CNRS/html` homepage repo is local, direct-to-master, with **no forge
remote** — the only off-machine copy is a bare git backup on host `padme`:

```
git push padme master      # run from ~/CNRS/html (upstream tracking is set, so plain `git push` works too)
```

Remote `padme` → `padme:projets/homepage` (bare repo, created 2026-06-16, ticket 0021).

**Why:** commits live only on doudou plus this backup; they are not safe
off-machine until pushed. The user asked (2026-06-16) to be reminded each session.

**How to apply:** when wrapping up a session that committed to this repo (during
`/lair`, `/roar`, or any natural end-of-session), propose running the backup
push. The ~1.5 GB of assets (`files/`, legacy dirs) are gitignored and are **not**
in this backup — they keep syncing by FTP (`make sync`), a separate concern.
