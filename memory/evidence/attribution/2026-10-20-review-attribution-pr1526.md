kind: review-attribution
pr: 1526 · merged 2026-10-20 · project: ImperialDragonHarness
writer: step=execute · runtime=claude · model=anthropic/claude-sonnet-5-5 · effort=not-stated
reviewer: seat=builtin-review-manual · runtime=claude · model=anthropic/claude-sonnet-5-5 · status: ran
  finding: consider · skills/roar/runbooks/capture.md:59 · adopted: no
  finding: consider · skills/gaze/SKILL.md:728 · adopted: no
  finding: consider · scripts/attribution_record.py:246 · adopted: no
  finding: consider · scripts/attribution_record.py:183 · adopted: no
  finding: consider · skills/merge/erg-pr-merge:263 · adopted: no
reviewer: seat=consistency · runtime=claude · model=anthropic/claude-sonnet-5-5 · status: ran
  finding: consider · skills/gaze/SKILL.md:726 · adopted: no
  finding: consider · scripts/attribution_record.py:179 · adopted: no
reviewer: seat=doc-propagation · runtime=claude · model=anthropic/claude-sonnet-5-5 · status: ran
  finding: consider · docs/2026-10-02-reviewer-attribution-design.md:171 · adopted: no
  finding: consider · skills/merge/SKILL.md:44 · adopted: no
  finding: consider · skills/roar/runbooks/capture.md:52 · adopted: no
reviewer: seat=red-team · runtime=claude · model=anthropic/claude-sonnet-5-5 · status: ran
  finding: consider · scripts/attribution_record.py:183 · adopted: no
  finding: consider · scripts/attribution_record.py:246 · adopted: no
reviewer: seat=scope · runtime=claude · model=anthropic/claude-sonnet-5-5 · status: ran
  finding: consider · skills/gaze/SKILL.md:728 · adopted: no
  finding: consider · skills/roar/runbooks/capture.md:59 · adopted: no
reviewer: seat=correctness · runtime=claude · model=anthropic/claude-sonnet-5-5 · status: ran
  finding: consider · scripts/attribution_record.py:246 · adopted: no
  finding: consider · scripts/attribution_record.py:183 · adopted: no
  finding: consider · skills/merge/erg-pr-merge:263 · adopted: no
reviewer: seat=simplify · runtime=claude · model=anthropic/claude-sonnet-5-5 · status: ran
  finding: consider · scripts/attribution_record.py:179 · adopted: no
reviewer: seat=adherence · runtime=claude · model=anthropic/claude-sonnet-5-5 · status: ran
reviewer: seat=gate · runtime=claude · model=anthropic/claude-opus-5-5 · status: ran

Context: /gaze round 1 at tip 7860ad711cf115a7f87e456e69bfcdf4d791b438, verdict APPROVED (PR comment 6296495861, gate_session_id 5f1c7a52-3d0e-4b8e-9a61-2b7e4c1d9f10). Model ids are the verbatim assistant-message model fields of the session's subagent transcripts, prefixed with the provider; effort is not-stated because the runtime did not report it for any seat. The PR body carried no attribution block (first PR after the writers shipped), so this record was rebuilt from the review trail, not copied.
Context: Finding anchors: seats that cited a line use it; the red-team, correctness and simplify seats named a function or region only, anchored here to its line on the ruled tip. Builtin-review and consistency cite different lines (728, 726) for the one gaze paragraph, so no shared catch is claimed between them. All findings were consider or nofollow-class; none adopted and none ticketed (0 fixes applied, 4 non-blocking follow-ups listed in the verdict). Nofollow-class findings are not recorded here, only their consider-class counterparts with anchors.
Context: All reviewer seats and the writer share one model family (Sonnet 5.5); the gate seat is Opus 5.5, same provider. No independent cross-family agreement is claimed. The adherence seat's semantic worker was unavailable (no Skill tool in the seat); its mechanical pass is the recorded ran.
