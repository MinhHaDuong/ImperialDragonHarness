# Ticket 1279: headless Vibe reads files; the 2.25.8 "denied" finding is superseded

On 2026-10-27, a probe on Vibe 2.26.0 and a live control through
`scripts/gaze_seat.py` showed that headless `vibe -p` reads files under the
`plan`, `ask` and `auto-approve` agents and can serve as a read-only gaze seat.
The 2026-10-02/03 trial on Vibe 2.25.8 had recorded that headless sessions deny
file tools (ticket 1017); that finding is superseded.

Observed: launched without a terminal, `vibe -p` blocks on inherited stdin and
prints nothing until killed; `</dev/null` fixes it. Cause not isolated to the
2.25.8 symptom, but it matches. With `--enabled-tools read_file` the seat read a
planted nonce and its write attempts left the tree unchanged. The model is
pinned by a seat agent TOML in a disposable `VIBE_HOME`; Vibe leaves read-only
plugin files in read-only directories there, so removal needs a chmod.
