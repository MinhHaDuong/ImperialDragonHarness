# Raid — autonomous-day brief

Loaded from `skills/raid/SKILL.md` § Autonomous-day brief and from
`agents/team-lead.md`.

A team lead run unattended for a day carries four standing terms that no
other raid reference holds. The rest is cited, not restated: watchdogs
(`circuit-breakers.md`), sitreps read from side effects (`sitrep.md`), the
verbatim-retry ban (`merge-permission-denial.md`), the advisor model
(`rules/workflow.md` § Escalation protocol).

1. **A hard USD cap that includes child spend.** The cap the brief names
   binds the lead and every agent it launches together. At each wave
   boundary write one ledger line, the arithmetic shown:
   `spent so far + estimate of in-flight = projected` against the cap, e.g.
   `1.10 + 0.60 = 1.70 of 5.00 USD`; in a raid, append it as
   `raid_log.py append LEDGER raid=<id> spent=<usd> inflight=<usd> projected=<usd> cap=<usd>`.
   A projected figure above the cap launches nothing new: finish or park
   what is in flight and report. Estimates are labelled as estimates.
2. **The author's by-right decisions are queued, never forked.** Scope,
   money and irreversible acts wait for the author. Each one becomes one
   line in a queue, `decision · default · price (author-hours, USD)`, the
   run continues on everything else, and the queue is delivered in the
   final report, not as a mid-run question.
3. **Context rule.** At about 75% of the context ceiling
   (`rules/guards.md`), stop growing the window: write a handoff note on the
   branch (state, next step, open PRs, ledger), and hand any bounded risky
   window still ahead (a rebase series, a long gate) to a fresh agent with
   that note as its brief. Never answer the ceiling by compacting.
4. **Broadcast before taking a shared resource.** Before taking a GPU, a
   production service or any other resource a live agent may be using,
   tell every live agent the runtime can reach, through the runtime's agent
   messaging where it offers one. Where it offers none, write the claim in
   the raid log instead,
   `raid_log.py append CLAIM raid=<id> resource=<name> until=<epoch>`, and
   read the log for other raids' claims first.
