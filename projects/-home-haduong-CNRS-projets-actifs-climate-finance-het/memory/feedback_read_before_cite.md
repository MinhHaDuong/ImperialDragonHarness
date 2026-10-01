---
name: feedback_read_before_cite
description: "A reference enters a manuscript only after it is actually read and its relevance to the paper's core is argued — no referee-appeasing citation padding"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 2f6c6c7e-67d0-4265-a5f7-bfdc0a1ccdd1
  modified: 2026-10-01
---

When a referee names works to engage, do NOT add the citation on reputation. The
author's bar (2026-07-08): **"find and read the book, and convince me of its
relevance for the core of the paper"** — else keep the existing refs.

**Why:** a name-dropped citation the author has not read is padding and erodes
credibility. This is stronger than "cite only what you have read": you must also
*argue core relevance* and be willing to report "does not fit here".

**How to apply:** read the actual text, then give a differentiated verdict, and
log it in the owning ticket. Worked example: ticket 0143 (Mitchell 1998/2002
read and placed, Escobar deferred unread). Reject a referee's mis-attribution
early: a named work that does not exist gets no citation.

- Place a requested citation at the passage that already makes the point, where it carries a load no adjacent citation carries.
- Letters to editors and referees get the same adversarial claim check as the paper; an attribution ("you asked for X") gets the strictest one.
- Includes marked "AI-generated, not human-reviewed" can hold phantom references: resolve every attribution before reuse (ticket 0244).
- Grep the staged primary PDF (pdftotext, joined lines) for the exact phrase before finalizing a citation.
- Before calling a paper done, read the rendered PDF (captions, bibliography): valid keys and DOIs can still name the wrong work or author.
