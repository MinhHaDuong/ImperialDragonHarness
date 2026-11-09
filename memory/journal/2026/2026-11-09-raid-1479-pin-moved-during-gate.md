# Raid 1479: erg pin file, yawn drift check; the pin moved during the gate

Date: 2026-11-09. PR 2303 (ticket 1479), merged at 4ee51ec7 (main 8e984793), read back MERGED at the ruled head.

Context: author ruling (option a) that git-erg is optional; the raid lead skipped
the Imagine and Plan agents for this one small ticket and put the plan in the
coder's brief (coder: claude-sonnet-5-5, hunt inline).

Events: the pin lives in `scripts/erg-pin`; `scripts/project-state.py` gained an
`erg` collector (yawn check 10b); molt step 0.7 lists the repairs. The lead
amended the gazed head twice (legacy-block repair wording, then two gaze
suggestions: strip only a hook under the git common dir, install only when
`tickets/erg` exists); each amendment took a delta gaze.

Events: during the first verify-gate run, PR 2304 moved the pin to 89952604
(git-erg rev 4f2326e) and merged. The gate had admitted the tip as bookkeeping
over the gazed head; `review_notes.py verdict` then refused it because the tip
no longer merged cleanly with the new base. No round was spent. The lead rebased
(1478 log conflict, both lines kept), recorded the new pin, re-gazed, and the
same gate session ruled APPROVED in round 1.

Outcome: on padme after merge, yawn's probe reports the harness's own
`tickets/erg` and the PATH `erg` (both 513cd3c4) as drifted against 89952604,
by design until the refresh PR; AEDIST-technical-report and chemin-de-voix
also report a superseded legacy `--- git-erg ---` pre-commit block.
