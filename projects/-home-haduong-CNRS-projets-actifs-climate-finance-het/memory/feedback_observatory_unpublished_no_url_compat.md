---
name: feedback_observatory_unpublished_no_url_compat
description: "The JETP observatory has never been published: old page addresses need no redirects or mention; renames are free until go-live (ticket 0915)"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 93dc4598-7818-4bb8-b7ae-fc2584b8e87b
  modified: 2026-09-24T14:35:41.849Z
---

The JETP observatory (`deliverables/jetp-observatory/`) is unpublished work in
progress. The author said on 2026-09-24, after I noted that `#entries`,
`#on-the-record` and `#whos-who` redirect to their renamed pages: "Forget the
old addresses, this is WIP never published."

**Why:** no external reader holds a link, so backward compatibility for page
addresses protects nobody and adds code and prose to maintain.

**How to apply:** refer to pages only by their current names and addresses;
don't report redirects or old names; don't add aliases when renaming pages
before go-live.

Update 2026-09-30: GitHub Pages is on and the site is live at
minhhaduong.github.io/climate-finance-het (gh-pages branch, published by
`make jetp-observatory-publish JETP_PAGES_REF=origin/main`). The author rules it
still counts as unpublished: "only advertised through a private mail, so obscure
it does not count." The no-compat rule holds until the author announces it;
`gh-pages` is the live site, never a stale branch to sweep. Related: [[project_jetp_three_stages_m1a]].
