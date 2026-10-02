# Background runtime launch without cwd started in the primary checkout path

Context: memory-v8 acceptance trial (ticket 0918), conductor session
relaunching the nested Vibe CLI probe on 2026-10-02 after a first attempt
whose --trust flag consumed the prompt argument.

Observation: the relaunch was sent to the background-process launcher
without a working-directory argument. The probe command
(vibe -p ... --trust --yolo) therefore started in the launcher's default
working directory rather than in the disposable trial clone. The run exited
1 having produced no output and no session work; whether a session started
at all in that directory is not established. A status check immediately
after (git status --porcelain in the primary checkout, plus a scan of its
journal directory) found the primary checkout clean, untouched, and
carrying no new entries.

Consequence: no unauthorized write occurred. The intended guarantee for
this trial — runtime probes run --yolo only inside disposable clones — was
violated by the launch command and held only because the misdirected run
crashed before doing anything. The relaunch was repeated with the clone as
explicit working directory.

Evidence: the empty /tmp/mem0918/vibe/stream.jsonl and its exit=1 status
file from that attempt, and the clean primary-checkout status output taken
right after. The crash's cause is not established; the absence of writes
is established.
