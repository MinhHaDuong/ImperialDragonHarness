---
name: project_sitter_install_paths_on_doudou
description: "A bare XPI dropped into the Zotero profile's extensions/ never registers on doudou; only GUI install-from-file has ever worked, and every prior sitter measurement was a replacement of an already-known id"
metadata: 
  node_type: memory
  type: project
  originSessionId: 6b5b468b-9d23-4a51-87cb-89cefd65f322
  modified: 2026-09-08T05:05:04.699Z
---

On doudou (Zotero 10.0.1_20260824184709, profile `~/.zotero/zotero/qr3b6poy.default`),
`bench/sdt_sitter_install.py install` — copy the XPI to
`<profile>/extensions/<id>.xpi` — does **not** register the add-on in
`extensions.json`. Measured 2026-09-08: dropped, quit Zotero, relaunched fresh
(pid 3389020), polled every 10 s for 260 s, zero transitions. The script's own
docstring claims this path "survives a restart"; that claim predates this build
and does not hold.

The one add-on that *is* registered there, `fulltext-control`, carries
`installTelemetryInfo.method: "install-from-file"` — the GUI path
(Tools → Add-ons → Install Add-on From File). So **every data point in tickets
0688/0727's logs was a REPLACEMENT of an id Zotero already knew**, not a
first-ever registration. The "first install survives, replacement dies"
hypothesis in 0727's log has never been tested with a true first install,
because nobody has achieved one by file drop.

Consequences for live sitter work here:

- **xdotool is useless on this host** — it enumerates no Zotero window at all
  (only GNOME Shell/mutter chrome), consistent with Zotero running as a native
  Wayland client. GUI automation is not a workaround.
- **No debug bridge in this build** — grepping both `/opt/zotero7/omni.ja` and
  `/opt/zotero7/app/omni.ja` for `debug-bridge`/`debugBridge` returns zero
  hits, so the plugin-dev HTTP eval endpoint does not exist to be enabled.
  `/connector/ping` answers 200 on 23119; `/debug-bridge/execute` is 404.
- **The devtools server IS shipped** — 250 `devtools/server/...` entries in
  `app/omni.ja`, and `zotero -h` lists `--start-debugger-server`. That is the
  one untried path to privileged eval (`AddonManager.installTemporaryAddon`,
  scripted disable/enable), and it needs an RDP client this repo does not have.

Before designing any live sitter experiment here, settle how the build will be
installed at all. See [[feedback_verify_the_load_bearing_claim]] — the install
path was the load-bearing claim nobody re-ran.
