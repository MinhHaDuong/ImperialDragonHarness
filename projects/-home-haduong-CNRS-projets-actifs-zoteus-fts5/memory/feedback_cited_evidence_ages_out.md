---
name: feedback_cited_evidence_ages_out
description: Evidence cited in a ticket goes stale as later work lands; a wrong-but-checked-looking citation is worse than none
metadata:
  type: feedback
---

Writing a verification command into a ticket as proof ("`grep X src/` returns
exactly one site, confirmed at the wave gate") creates a claim that decays. In
zoteus-fts5 (2026-08-21) three such citations were false by review time, each
true when written:

- 0003 cited `grep 'new Fts5PassageStore' src/` returning one site. 0005 later
  added two. The *conclusion* survived (neither new site wrapped the store in a
  bare `SearchIndex`) but the cited evidence did not.
- 0007 cited `index-manager.ts:374/587/602` for the `chunkText` call sites; the
  waves rewrote the file and the calls moved to 560/875/890. The cited lines
  pointed at unrelated code — a cold reader would have landed in the wrong place.
- STATE said "nothing is committed in `fork/` yet", which stopped being true 24
  minutes later.

**Why:** a citation that has aged out is worse than no citation, because it
reads as checked. The reviewer who catches it has to re-derive the whole claim.

**How to apply:** prefer citing the *invariant* over the command that happened
to prove it once ("no bare `SearchIndex` is constructed over an FTS5 store",
not "this grep returns 1"). Prefer symbol names over line numbers. When a wave
lands that touches a cited file, re-run the citations in the tickets that
reference it. Treat "confirmed at the gate" as a claim requiring a timestamp,
not a permanent fact. Related: [[feedback_gate_must_bite_before_trusted]].
