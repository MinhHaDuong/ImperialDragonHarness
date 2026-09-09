---
name: feedback-ship-simple-fallback-first
description: "when a design pairs a simple baseline path with a more capable one, this author wants the simple one built first to solve integration"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e37b49a7-3ac7-49b2-883b-481b96af87f8
  modified: 2026-09-01T13:48:20.449Z
---

When two segmentation paths were on the table -- seg/1 (a simple,
already-designed flat-text heuristic, ticket 0028) and a new, more
capable PDF-layout segmenter (freshly ruled the same session, tracker
0557 plus seven children) -- the instinct was to treat the newest
decision as the next thing to build. The author redirected: "I would
start with the fallback. A simple segmenter working on the text file. To
solve integration, and so that other work can build on it. The rest is
improvement" (2026-09-01).

**Why:** the simple path is valuable specifically *because* it is simple
enough to expose the integration surface (chunk keys, confidence/fallback
plumbing, how the rest of the pipeline consumes a segmenter's output)
that every more sophisticated path would otherwise have to solve a second
time -- or solve once, badly, under the extra load of also being novel.
Building the sophisticated path first means integrating twice.

**How to apply:** when a design has a simple/baseline component and a
more capable/complex one and both are newly decided, propose sequencing
the simple one first, explicitly framed as "this solves integration and
gives the rest something to build on" -- rather than defaulting to
whichever decision is freshest or most interesting. Record the
sophisticated path's tickets as `Blocked-by` the simple one, not as
parallel work, so the sequencing survives past the conversation that
decided it.
