# Imperial Dragon Harness — State

Last updated: 2026-10-27

Live counts: `erg ready tickets/` · `erg list` · `/dashboard`.

## Handoff
Attribution #1423/#1425 unresolved; do not infer missing identities.
Original doc-refresh snapshot pushed as WIP; newer implementation is merged.
Main-update guard (1045): enforce on padme and doudou since 2026-10-27 16:20Z (1268 whitelists git's pack-refs; 1180 closed). Watch the journal for refused rows until 2026-11-03; back out with `git config --unset idh.mainGuard`.
Optimistic merge (1226) closed: cheap before-merge set; the main-update hook starts the full after-merge run (1265).
Gaze rebuild (1143) closed, with its follow-ups 1100 and 1213 and the review-brief successor 1225.
DOIfetch: `idh install` pins it as a uv tool at 3e074798; the zotero skill fetches missing fulltexts from open sources (1266; tracker 1249 closed).
Agent credential (1196): Claude Code shells use a fine-grained PAT through `~/.config/gh-agent` (no admin; owner login for the author's acts). Codex and Pi shells do not load it yet. `refs/notes/*`, `refs/notes/gate` included, is not protected by the forge ruleset.
Forge-less review (tracker 1252): every code child merged — adapter and callers (1271, 1272), notes review (1273), verify-gate on notes (1274), local gated merge (1275), landing route (1280), end-to-end F2 test (1276), review-notes hardening (1281). Flows ruled by the author (conception/2026-10-27-review-merge-flows.md): F1 default (notes review + forge PR merge); F2 only for repositories with no origin remote; no setting. Open: 1277 waits for the author's ChatGPT Work and Claude Code Web legs; 1282 (concurrent review-notes adds lose an entry) is a known defect, xfail in 1276's test.
Model-service transmission authorization now prints in every session's start context (PR #1783); whether Codex's managed approval reviewer reads it is untested.
