# Temporary-candidate report runbook

When roar runs this: step 1, when reading the output of the `tmp_report.py` scan.

History attribution has a 20-second default budget. If the report says
history attribution is partial, unmatched candidates and descendant scope
are unknown; rerun with `--history-budget-seconds 0` when exhaustive history
evidence is needed.
The helper scans candidates across its configured host-wide roots. When
session flags are supplied, history attribution is limited to this session
and linked child sessions. A candidate without a scoped history match may
still show explicitly labelled test-source inference; otherwise it remains
unattributed. The reporting session is excluded from citation attribution,
not from test-source inference. If the runtime or session id cannot be
established, pass the known runtime and omit both session flags. It never
deletes candidate data. A citation is not proof of creation; `created`
appears only for a matching native Claude/Codex call and result id, explicit
zero exit status, and one direct command targeting the exact candidate. Do
not copy raw history commands into the wrap-up.
