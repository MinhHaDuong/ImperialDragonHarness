---
name: Harness architecture: git-erg vs IDH
description: Two independent upstreams with different distribution models — git-erg travels with repo, IDH is user-level
type: reference
originSessionId: 30c50dd1-64cd-4e23-af67-7793edace30b
---
Two plugin dependencies, different distribution:
- **git-erg** (MinhHaDuong/git-erg): project-level, travels with repo, works in web/isolated environments. Provides ticket-* skills.
- **IDH** (MinhHaDuong/ImperialDragonHarness): user-level, graceful degradation. Provides workflow skills (review-pr, celebrate, etc.). Moving to plugin architecture (untested as of 2026-04-10).

**Why:** git-erg must work everywhere (its essence is portability). IDH is evolving and may become stock Claude Code — vendoring it into projects creates duplication and staleness.

**How to apply:** Never vendor IDH skills into project `.claude/skills/`. AGENTS.md declares both dependencies. Orchestrator skill belongs at user-level or upstream in IDH (ImperialDragonHarness#31).

**Author-workflow skills go to IDH, not project-level** — even when the first consumer is one specific repo. Skills for paper drafting (related-work-note, future bib-merge and related-work-note-validate), citation audit, journal choice, etc. serve *every* manuscript the author writes, across any repo. First-consumer specificity is not a reason to vendor.

**IDH has both %erg tickets and GH issues, with different purposes.** IDH's `~/.claude/tickets/` holds local %erg files tracked in git (same format as AEDIST; see IDH's `~/.claude/skills/harness-rules/tickets.md`). GH issues on the IDH repo are reserved for *inter-agent* coordination — work that needs external visibility or cross-repo handoff. When opening tracking for build work on IDH (write a skill, fix a hook, etc.), prefer a local .erg ticket; only file a GH issue if a second agent or a human collaborator needs to see it.

(2026-04-17: both rules exercised. First I vendored related-work-note into AEDIST's `.claude/skills/`; corrected → IDH. Then I filed follow-ups as IDH GH issues #32/#33; corrected → IDH .erg tickets 0011 and 0012. Two rounds of the same "vendoring / forum" mistake in the same day.)
