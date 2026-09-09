---
name: project_sitter_install_paths_on_doudou
description: "How the sitter installs (and does not) on doudou, and the three deliberate arms of 2026-09-08 that refuted both of ticket 0727's standing hypotheses"
metadata: 
  node_type: memory
  type: project
  originSessionId: 6b5b468b-9d23-4a51-87cb-89cefd65f322
  modified: 2026-09-08T08:29:42.449Z
---

Zotero 10.0.1 on doudou, profile `~/.zotero/zotero/qr3b6poy.default`.

## Installing

`bench/sdt_sitter_install.py install` — copy the XPI to
`<profile>/extensions/<id>.xpi` — **does not register the add-on**. Measured
2026-09-08: dropped, quit Zotero, relaunched fresh, polled every 10 s for 260 s,
zero transitions. The script's docstring claims it "survives a restart"; that
predates this build and does not hold.

**Only the GUI path works**: Tools → Add-ons → ⚙ → Install Add-on From File.
`fulltext-control`'s record shows `installTelemetryInfo.method:
"install-from-file"`, and the sitter registered within seconds of that gesture
on 2026-09-08. So every data point in tickets 0688/0727 came through the menu,
which nobody had noticed.

No headless route exists here: no `debug-bridge` in either `omni.ja`, and
`xdotool` enumerates no Zotero window (native Wayland client). The devtools
server IS shipped (250 `devtools/server/…` entries in `app/omni.ja`) and
`--start-debugger-server` is offered, so a Firefox-RDP client is the one untried
path to scripted control. The author's own window remains the instrument — see
[[feedback_the_author_s_console_is_the_instrument]].

## The three arms of 2026-09-08, and what they killed

Run deliberately for the first time, timings anchored on Zotero's `updateDate`,
state sampled every 2 s from `extensions.json`, liveness judged on the cache
compact write (`bootstrap.js:1209` makes it unconditional on an activation's
first save).

- **Arm 1** — first install into a process that never held the add-on: held
  45 min.
- **Arm 2** — replacement over the live build, same process, no removal,
  `bootstrap.js`/`scheduler.js` byte-identical so only the act of replacing
  varies: **held 15 min**, 40x the predicted 20 s. This REFUTES 0727's sharpest
  hypothesis ("first install survives, a replacement does not").
- **Arm 3** — the pre-fix payload with its 12 top-level `const`/`let`: **held**,
  and fully alive (asked the launch question, pulsed, finished its census, wrote
  its cache). This REFUTES the candidate that PR #444's `const`→`var` fix was
  what stopped the deaths, and it answers ticket 0730's open question **for the
  upgrade path**: Zotero gives a replaced add-on a fresh scope. 0730 asked about
  *disable/re-enable*, which is a different path and still unmeasured.

**Arm 1 alone proved nothing, and that was stated before running it**: "first
installs survive" and "the phenomenon stopped" emit the same empty log. Arm 2
had to die for arm 1 to mean anything; it did not.

What still distinguishes 2026-09-06 from 2026-09-08 is unknown. Three untested
candidates: last night's builds differed from each other; last night's install
gesture is not reconstructable; or it is intermittent.

**Do not re-run arms 2 or 3 without a new reason.** They were run with controls
and they answered.
