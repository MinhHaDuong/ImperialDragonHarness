---
name: reference_ticket_store_map
description: Which erg ticket store owns what on this machine (padme host vs IDH harness vs projects)
metadata: 
  node_type: memory
  type: reference
  originSessionId: 211826a9-1beb-4f8d-9a7a-952c56d075ef
---

This machine (padme) has several erg ticket stores; they are NOT
interchangeable -- file a ticket in the store that owns the concern:

- **`~/padme/tickets`** — the padme HOST: machine configuration, toolchain,
  OS/package state, host ops. A genuine host-toolchain or OS-config fix goes
  HERE, not in the harness store. (Note: the gofmt smart-quote episode that
  prompted this correction turned out NOT to be a host issue at all -- it is
  stock gofmt behavior; see [[feedback_gofmt_smartquotes_vs_ascii]]. The
  store-map distinction below still stands.)
- **`~/.claude/tickets`** — the Imperial Dragon Harness (IDH) itself: harness
  rules, skills, hooks, cross-project coordination. Per [[reference_idh_tickets]].
  NOT for host/machine config.
- **`~/git-erg/tickets`** — the erg tool's own development (source, tests, docs).
- Project stores (`~/Climate_finance`, `~/aedist-technical-report`,
  `~/fuzzy-corpus`, `~/cadens`, `~/chemin-de-voix`, ...) — each project's own
  tickets.

**Why:** corrected by the author 2026-06-03 after I proposed filing a
padme-toolchain fix in ~/.claude (the IDH store). "Padme conf belongs to
~/padme not ~/idh."
**How to apply:** classify by what the ticket FIXES (host vs harness vs tool
vs project), not by where you happen to be working.
