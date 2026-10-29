kind: review-attribution
pr: 1633 · merged 2026-10-26 · project: ImperialDragonHarness
writer: step=plan · runtime=codex · model-state=runtime-masked · model-evidence=docs/audits/2026-10-23-skills-metier/execution.md:15 · effort=low · route=native · independence=not-stated
writer: step=execute · runtime=codex · model-state=runtime-masked · model-evidence=docs/audits/2026-10-23-skills-metier/execution.md:15 · effort=medium · route=native-isolated-workers · independence=not-stated
reviewer: step=review · seat=simplify · runtime=codex · model-state=runtime-masked · model-evidence=tickets/reviews/b4b863c..9d8ac41/simplify-1.md:50 · effort=not-stated · route=gpt-6-luna/medium · independence=not-stated · status: ran
reviewer: step=review · seat=adherence · runtime=codex · model-state=runtime-masked · model-evidence=tickets/reviews/b4b863c..9d8ac41/correctness-1.md:73 · effort=not-stated · route=gpt-6-luna/medium · independence=not-stated · status: ran
reviewer: step=review · seat=correctness · runtime=codex · model-state=runtime-masked · model-evidence=tickets/reviews/b4b863c..9d8ac41/correctness-1.md:48 · effort=not-stated · route=gpt-6-luna/medium · independence=not-stated · status: ran
reviewer: step=review · seat=doc-propagation · runtime=codex · model-state=runtime-masked · model-evidence=tickets/reviews/b4b863c..9d8ac41/doc-propagation-1.md:42 · effort=not-stated · route=gpt-6-luna/medium · independence=not-stated · status: ran
reviewer: step=review · seat=semantic-adherence · runtime=codex · model-state=runtime-masked · model-evidence=tickets/reviews/b4b863c..9d8ac41/correctness-1.md:73 · effort=not-stated · route=gpt-6-luna/medium · independence=not-stated · status: ran
reviewer: step=review · seat=adherence · runtime=claude-code · model-state=runtime-masked · model-evidence=skills/route/routes-recommendations-claude-code.md:21 · effort=not-stated · route=haiku · independence=same-family · status: ran
reviewer: step=review · seat=correctness-engine · runtime=claude-code · model-state=runtime-masked · model-evidence=skills/route/routes-recommendations-claude-code.md:21 · effort=not-stated · route=sonnet · independence=same-family · status: ran
reviewer: step=review · seat=correctness-biblio · runtime=claude-code · model-state=runtime-masked · model-evidence=skills/route/routes-recommendations-claude-code.md:21 · effort=not-stated · route=haiku · independence=same-family · status: ran
  finding: verifiable · scripts/bib-merge.py:103 · adopted: yes
  finding: verifiable · scripts/validate-refs.py:98 · adopted: yes
  finding: verifiable · skills/ingest-decision-letter/ingest_letter.py:288 · adopted: yes
reviewer: step=review · seat=correctness-pdf-retire · runtime=claude-code · model-state=runtime-masked · model-evidence=skills/route/routes-recommendations-claude-code.md:21 · effort=not-stated · route=haiku · independence=same-family · status: ran
  finding: verifiable · skills/track-changes-pdf/track_changes_pdf.py:221 · adopted: yes
reviewer: step=review · seat=red-team · runtime=codex · model-state=runtime-masked · model-evidence=skills/route/routes-recommendations-claude-code.md:21 · effort=not-stated · route=gpt-6-luna/medium · independence=cross-family · status: ran
  finding: verifiable · skills/manuscript-review/manuscript_review.py:298 · adopted: yes
reviewer: step=review · seat=adherence-semantic · runtime=claude-code · model-state=runtime-masked · model-evidence=skills/route/routes-recommendations-claude-code.md:21 · effort=not-stated · route=sonnet · independence=same-family · status: ran
reviewer: step=review · seat=doc-propagation · runtime=claude-code · model-state=runtime-masked · model-evidence=skills/route/routes-recommendations-claude-code.md:21 · effort=not-stated · route=haiku · independence=same-family · status: ran
  finding: verifiable · docs/research-workflow.md:80 · adopted: yes
  finding: verifiable · skills/zotero/references/import.md:136 · adopted: yes
  finding: verifiable · skills/reading-note/references/template.md:32 · adopted: yes
  finding: verifiable · skills/biblio-saturation/SKILL.md:145 · adopted: yes
reviewer: step=review · seat=adherence · runtime=claude-code · model-state=runtime-masked · model-evidence=skills/route/routes-recommendations-claude-code.md:21 · effort=not-stated · route=haiku · independence=same-family · status: ran
reviewer: step=review · seat=adherence-semantic · runtime=claude-code · model-state=runtime-masked · model-evidence=skills/route/routes-recommendations-claude-code.md:21 · effort=not-stated · route=sonnet · independence=same-family · status: ran
reviewer: step=review · seat=correctness-fold · runtime=claude-code · model-state=runtime-masked · model-evidence=skills/route/routes-recommendations-claude-code.md:21 · effort=not-stated · route=sonnet · independence=same-family · status: ran
  finding: verifiable · skills/track-changes-pdf/track_changes_pdf.py:41 · adopted: no
  finding: verifiable · skills/manuscript-review/manuscript_review.py:301 · adopted: no
reviewer: step=review · seat=doc-propagation · runtime=claude-code · model-state=runtime-masked · model-evidence=skills/route/routes-recommendations-claude-code.md:21 · effort=not-stated · route=haiku · independence=same-family · status: ran
  finding: verifiable · docs/audits/2026-10-23-skills-metier/probes.py:32 · adopted: no
  finding: verifiable · skills/ingest-decision-letter/SKILL.md:8 · adopted: no
reviewer: step=review · seat=red-team · runtime=codex · model-state=runtime-masked · model-evidence=skills/route/routes-recommendations-claude-code.md:21 · effort=not-stated · route=gpt-6-luna/medium · independence=cross-family · status: failed
reviewer: step=review · seat=red-team · runtime=codex · model-state=runtime-masked · model-evidence=skills/route/routes-recommendations-claude-code.md:21 · effort=not-stated · route=gpt-6-luna/medium · independence=cross-family · status: ran
  finding: consider · skills/track-changes-pdf/track_changes_pdf.py:41 · adopted: no
context: two gaze rounds. Round 1 on def1528f8 (2026-10-26, FINDINGS, one blocking: bib-merge.py DOI prefix gap, ticket 1200 criterion 2) and round 2 on 98f72a8f (FINDINGS, zero blocking). The round-1 findings listed as adopted were fixed in commit 'review 1633: fold the gaze findings' (branch commit 3ad80334, rebased into the merged head 98f72a8f). Round-2 findings were not adopted before merge.
context: the verify-gate refused a third round (cap 2: rounds 1 and 2 APPROVED on 2026-10-23, session 99d143ad, tips 2484ea44 and f673d799) and found the round-1 gaze stale against the fix commit; the author merged on their own authority after the round-2 gaze, with a passing merge-gate record written on padme on this head. The red-team round-2 line with status failed is the first codex launch, which exited at 0s because seat_clock.py did not forward stdin to codex exec; the retry with the prompt as argv ran.
context: model ids are runtime-masked for every seat; routes are the requested tokens. Three round-2 Claude seats self-reported claude-haiku-5-5 or claude-sonnet-5-5 in the gaze result comment; those self-reports are not verbatim provider-observed ids and are not recorded as model=.
