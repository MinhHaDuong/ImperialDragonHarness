# 2026-11-09: one session, from landing PR 2277 to a multi-repo erg claims rollout

Context: the session opened on "Land PR 2277" (ticket 1472 filing). Through author requests and
peer-session messages it grew into: the erg ID-claims rollout across ~20 stores on padme and
doudou (tracker 1478), the conception/ -> design/ rename decision (1477, plus 15 per-project
alignment tickets), memory v8 deployment in three projects, and the erg pin file (1479).

Events, in order:
- The pin moved four times in one day by author decision: 9ab13c9 (never taken), dafb1d48,
  6a104262 (never landed), 513cd3c4, 89952604. Ten repos landed on dafb1d48 and stay there until
  their next refresh; the harness landed 513cd3c4 (PR #2297) then 89952604 (PR #2307).
- JETP-observer's migration raced a ticket that this session had filed there for the design/
  alignment (2127, PR #284): it merged between JETP's migrate and its merge, leaving JETP main
  failing erg check. JETP fixed it (PR #286); the recipe gained "re-run migrate right before
  merge", and 1472's own gaze round 2 then caught the same race on ticket 1479.
- The quiet-wave agent left three padme clones with dead core.hooksPath; re-enabling hooks in
  fuzzy-corpus surfaced a legacy pre-commit block that refused every ticket commit (removed by
  hand, .bak kept); 1479 now has yawn report such blocks.
- A wave-3 agent ran search-works-for-zotero's `make check` in a migration clone; its acceptance
  bench passed the whole environment to `sudo --preserve-env`, and sudo logged HF_TOKEN in
  padme's system journal (14:05:52). Traced and ticketed in that repo (0829, PR #640). The author
  chose to leave the token as it is.
- The chemin-de-voix memory raid noticed that the public harness repo tracks 1,085 native-memory
  copies of 44 projects under projects/, user_bio notes included; the author chose to stop
  publishing them (ticket 1480).
- The agent PAT could not push a workflow-file deletion (author pushed it) nor close or delete
  GitHub issues (author deleted three with the personal login).
- 1477 was handed to another session, started on this session's "go" after PR #2307.

Outcome: harness on required claims and pin 89952604; 16 stores migrated; remaining items on
tracker 1478's log; follow-ups filed in fuzzy-corpus (0055), chemin-de-voix (0261),
aedist-technical-report (0688) and here (1480, 1481). Review attribution for PR #2286 not
derivable (script-only review, no reviewer line).
