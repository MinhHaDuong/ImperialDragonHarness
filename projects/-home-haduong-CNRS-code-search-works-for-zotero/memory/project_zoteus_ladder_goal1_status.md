---
name: project-zoteus-ladder-goal1-status
description: "Where zoteus stands on the acceptance ladder's goal 1 (R10/R15/R22) as of 2026-09-08 — all three upstream items resolved: #54 shipped, #55 merged, #56 accepted-but-deferred to the Sept 21 distribution checkpoint"
metadata: 
  node_type: memory
  type: project
  originSessionId: dc5e15a4-edc1-4528-b6bf-d9afd95441c1
  modified: 2026-09-08T20:14:25.341Z
---

Tracker: ticket 0613. Goal 1's three terms are R10 (no-egress), R15
(uninstall), R22 (durable pause).

**Gap A (R10, phone-home) — closed, sent.** `ZOTEUS_UPDATE_CHECK` defaults
true, phones home at startup. Attribution confirmed by a live measured run
(ticket 0629), not just source reading. Sent as
[oscardvs/zoteus#54](https://github.com/oscardvs/zoteus/issues/54), a soft
proposal (default off, or first-run consent), not a demand.

**Gap B (R15, uninstall) — closed, sent.** No host uninstall lifecycle to
hook, so the surface is a published removal procedure. Proven end-to-end for
real (build, download a model, delete exactly the declared root, zero
residue). Sent as [oscardvs/zoteus#55](https://github.com/oscardvs/zoteus/pull/55)
(a docs PR, README `## Uninstall` + `docs/uninstall.md`).

**Gap C (R22, durable pause) — now DECIDED, and it's a FAIL, for a real
reason.** Was `not-run` for lack of two things: durable work counters
(ticket 0642 built them — real, sqlite-transactional, not the in-memory
`metrics.ts` shortcut a first pass tried and the author rejected — see
[[feedback-validate-utility-before-sending-upstream]]) and a perturbation
zoteus would accept (ticket 0643 wired `action:"build"` against a seeded
incomplete index, since the harness's only prior perturbation,
`EDIT_ONE_ITEM`, zoteus correctly refuses). With both landed, R22 reaches a
real verdict: **FAIL** — `stop` durably cancels the current job but doesn't
gate a subsequent explicit `build`, confirming a tension the adapter's own
docstring had already flagged as open. Sent as
[oscardvs/zoteus#56](https://github.com/oscardvs/zoteus/issues/56).

**A dropped path, worth remembering why.** Ticket 0636 proposed sidestepping
the missing perturbation with a zoteus-private sqlite read instead of a real
counter. Author's "high road" call: reject it even though it was internally
disciplined (read-only, no fabrication) — it would have been zoteus-only and
coupled the harness to undeclared internal storage rather than a contract.
0033 (real target-side counters) stayed the standing target instead.

**Update, 2026-09-08 — all three items resolved upstream.**

- **#54 (R10)** — maintainer shipped the fix in zoteus 1.14.0:
  `ZOTEUS_UPDATE_CHECK` now defaults `false`, plus a new `.mcpb` manifest
  toggle so desktop installs can reach the same switch. Closed 2026-09-04.
- **#55 (R15)** — merged 2026-09-06, ships in zoteus 1.15.0. Two review
  rounds: maintainer caught a wrong API-key claim and an `XDG_DATA_HOME`
  bug in the uninstall snippet, both fixed and re-reviewed before merge.
  Post-merge the maintainer extended the doc further himself (OAuth
  file-store key path, Zotero's own "Always Allow" grant persisting
  independent of our copy).
- **#56 (R22)** — maintainer's verdict, 2026-09-04: "accepted and
  deferred," not declined. Zoteus is in a September code-freeze for
  distribution work (checkpoint 21 September); anything that's a feature
  rather than a defect/privacy/packaging fix is deferred by default, and
  he scoped the real cost of option (1) at six or seven files with tests,
  plus a synchronous/async wrinkle in `requestStop()`. He said he'd take
  a PR if we wrote it. We acknowledged and said we'd hold off on the
  larger feature work until after the checkpoint. The issue itself was
  then closed by the maintainer on 2026-09-06 (same timestamp as the #55
  merge), with no comment attached explaining the closure — cause not
  established; may be routine triage of a deferred item rather than a
  reversal of "accepted."

**Next real step:** nothing pending upstream right now. R22 stays FAIL
until 0033 (real target-side counters, upstream-built or ours as a PR) or
zoteus's own post-checkpoint work lands and gets re-measured. The staged
counters PR (`verification/UPSTREAM-PR-WORK-COUNTERS-0642.md`) stays
unsent — decide after 21 September whether to offer it, given the
maintainer said he'd take a PR for this shape.
