---
name: classifier-prohibition-paraphrase
description: The auto-mode permission classifier absorbs prohibition-flavored wording from any text it can see and paraphrases it into blanket bans, while file-recorded standing authorizations (STATE.md) stay invisible to it
metadata:
  type: feedback
---

The auto-mode permission classifier denied an autonomous `erg-pr-merge` citing
"never close merge requests without explicit user confirmation" — a rule that
existed nowhere verbatim. It was manufactured by paraphrase from texts the
classifier could see: skill scope statements ("Never merges" in gaze and
verify-gate, meaning only "not this skill's job") and a sequencing memory
("Never merge a PR before review returns"). Meanwhile the STATE.md standing
authorization ("merge each PR on APPROVED + green CI") never counted, because
the classifier weighs only transcript-visible text (ticket 0249, aedist PR
#979, 2026-06-11; fix PR #527, 2026-07-13).

**Why:** Paraphrase keeps the "never" and drops the scope qualifier. Any
absolute prohibition in a skill description, rule, or memory can leak into the
classifier's judgment as a global policy; a grant recorded only in a file
cannot counterbalance it.

**How to apply:** Write scope statements as ownership, not prohibition: "does
not merge — the merge decision belongs to the caller", never a free-floating
"Never merges". Write sequencing rules in positive form ("merge only after X")
and say explicitly when they are not a confirmation requirement. When an
autonomous run must exercise a standing authorization, quote the grant
verbatim into the transcript before the gated action (ticket 0249 option 2).
The system-prompt-level "never merge" for background sessions remains outside
harness control — residual denials there are expected. Effectiveness of the
wording fix is under observation by experience. Related:
[[feedback_merge_classifier_blocks_autonomous_raid]] (referenced in ticket
0249 but never written; this entry supersedes it).
