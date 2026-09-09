---
name: measure-the-recommendation-you-wrote
description: "Two recommendations argued from mechanism were both wrong once measured; the author's \"what's wrong with X?\" is the prompt to go count, not to re-argue"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c237237f-abd3-4b9c-94b8-0f98e597a30a
  modified: 2026-09-06T22:09:02.599Z
---

On 2026-09-06 I wrote two recommendations in DECISIONS.md from mechanism alone: keep chunking in zoteus because Zotero's chunker merges sub-minimum sections, and retire ticket 0606 because pack coverage had arrived. The author asked "so 606 goes? what's wrong with using the plugin's chunks?" — and counting reversed one and undercut the other. The merge rule fires on 34% of section boundaries but touches 2,52% of text, and 42% of the sections it merges are heading stacks or ≤10 words where merging is *right* and our never-merge rule would orphan ~39 000 headings. Coverage was 5 255 of 9 108, not "arrived".

**Why:** a mechanism argument tells you a difference exists, never how big it is or which way it cuts. Both my recommendations named a real mechanism and got the sign or the magnitude wrong. The measurements took one script each and about ten minutes.

**How to apply:** when a recommendation rests on "X does A where we do B", find the number that prices A before writing the recommendation, not after he pushes back. His short challenge questions are reliably the signal that a number is missing. And when the number reverses you, rewrite the ledger entry rather than only saying so in chat. Related: [[decision-briefs]], [[the-metric-decides-the-verdict]], [[verify-the-load-bearing-claim]].
