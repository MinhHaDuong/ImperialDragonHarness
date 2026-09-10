---
name: feedback_he_rules_the_class_delegates_the_wording
description: He rules the class and the tone and leaves the exact sentence to the implementer — so a spec that restates the shipped sentence takes the delegation back
metadata: 
  node_type: memory
  type: feedback
  modified: 2026-09-10T08:29:09.945Z
  originSessionId: 161c1566-9746-4993-905f-d66e4024c82c
---

The author, 2026-09-10, on a `SPEC.md` table that had been made to quote the
plugin's eleven explanation sentences verbatim, with a test behind them:
"Je me souviens avoir donné des directives en comptant sur toi pour peaufiner
les mots justes." Then, on being shown the table nothing read: "Mais alors à
quoi sert la table que personne ne lit ?"

Both sentences are the same instruction. On ticket 0744 he had ruled the
classes ("No attachment, Need sync, Missing file / broken link…") and the tone
("do not frame anything as a problem anywhere in this feature, only facts —
every heading, subsection title and control label"), and stopped there. The
shipped strings that disagreed with SPEC — *Extraction not completed this
session* for *failed*, *Recorded format differs* for *Mismatched type* — were
that ruling applied, not drift to be corrected.

**Why:** a contract that pins the exact sentence takes back what he delegated.
The next person to improve a word would have to amend the spec to do it, which
is precisely the loop he was avoiding by ruling on the class instead. The
mistake is not the duplication alone — it is duplicating the layer he chose not
to own.

**How to apply:** when a document and the code disagree on user-facing text,
first ask which layer he ruled on. He rules the *class*, the *tone*, and the
*invariant*; the sentence is yours. So the spec keeps the class names (it
refers to them elsewhere, and a contract that cannot name its own classes is
not one) and the admission rule for each, and states the constraints the
wording must satisfy — factual, conditional, obstacle plus possible remedy,
never an obligation or a backlog. It does not carry the sentence.

The corollary settles a choice [[feedback_guard_budget_is_net_negative]] leaves
open. Facing a duplicate, the options are delete it or hold it with a test; the
exact-quotation option is real but costs a guard forever, and here it also
re-owned delegated ground. Delete beat guard on both counts. The test that
survived holds eleven short class names and one negative assertion — that no
quoted sentence reappears in that column, since a restatement is the shape the
drift came in.

The failure it repairs is worth remembering on its own: `SPEC.md` §5.2.7 and
`bootstrap.js` were written into ONE commit six hours apart, contract first,
and disagreed on arrival in ten strings across six of eleven rows. Not drift
over time — a copy nobody read is free to be wrong from the day it is written.
See [[feedback_verify_the_load_bearing_claim]].
