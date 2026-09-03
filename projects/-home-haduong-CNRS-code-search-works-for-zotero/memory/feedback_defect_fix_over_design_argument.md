---
name: defect-fix-over-design-argument
description: "Adapting to a maintainer's chosen design, framed as a fix he can review in one sitting, beats arguing that his settings should be one object — thirteen for thirteen PRs merged, none rebuilt"
metadata: 
  node_type: memory
  type: project
  originSessionId: 6c21d767-95a0-4e11-8ec4-b9730449bfdb
  modified: 2026-09-03T14:42:40.576Z
---

Ticket 0612 (pooling correction to zoteus's local embedding pipeline) was built,
reviewed, and shipped in one session, filed as `oscardvs/zoteus#52` and merged
verbatim nineteen minutes later — no review comments, no changes requested. It
closed issue #51, which the maintainer had opened himself, crediting this
project's finding, saying he was holding the next release for it.

**Why:** Two decisions shaped this, both made mid-session after the author
overruled an initial redirect. First: ship the fix as a focused correctness
patch that adapts to the maintainer's already-chosen configuration surface
(`ZOTEUS_EMBEDDING_PREFIXES`'s own two-part shape — inference layer plus
override), not as an argument that his separate settings are secretly one
record. Second: still ship the override (`ZOTEUS_EMBEDDING_POOLING`), because a
bare correctness fix with no escape hatch is itself a smaller version of the
same over-engineering risk. The `[[registry-not-knobs]]` ruling's ground
("precision cannot travel alone") had expired once the other axes were
settable — see `[[feedback_a_ruling_scope_is_its_reasoning]]`.

Every design-shaped proposal to this maintainer across the whole project has
come back as his own implementation (storage layer, model selection, dtype).
Every focused defect fix has been merged, now thirteen for thirteen, none
rejected, none rebuilt. This is the sharpest confirmation of that pattern yet:
the fix included a real design judgment (suffixing the pooling into the
embedder identity, closing a corrupted-index path an adversarial review found)
and he took it as offered, without discussion.

**How to apply:** When preparing any future upstream contribution to this
project, default to the smallest fix that adapts to his existing surface. State
design judgment calls explicitly and offer the alternative in one sentence
("if you'd rather X, it's one commit") rather than deciding unilaterally or
opening a design conversation about it. Reserve a broader design proposal
(a genuine registry, a new abstraction) for when he asks for it directly, the
way he did with dtype-in-identity — reached on his own, after seeing the pattern
in a related fix.
