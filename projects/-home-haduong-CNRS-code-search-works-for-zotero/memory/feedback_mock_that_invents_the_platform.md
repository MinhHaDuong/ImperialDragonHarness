---
name: mock-that-invents-the-platform
description: A mock answering a host API the real host never provides makes the feature untestable by construction -- 40 green tests over a locale layer that was dead in production from its first commit
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d5b346ef-7983-4572-a95a-cf476a17df19
  modified: 2026-09-06T21:35:42.686Z
---

Ticket 0692 shipped Fluent localization for the SDT sitter: ~60 strings, four
locales, six acceptance criteria, a five-seat review panel, two approvals and
three comment verdicts. It had never worked. The author installed the XPI and
the toolbar button read `index-coverage` -- the raw message id -- with every
string in the window the same and no `$percent` ever interpolating, because an
id that resolves to nothing carries no pattern to interpolate into.

`loadSDTLocalization` opened with
`ChromeUtils.importESModule('resource://gre/modules/Fluent.sys.mjs')`. No such
module exists in Zotero 10.0.1 (nor `Localization.sys.mjs`, nor
`L10nRegistry.sys.mjs`; neither omni.ja carries any of them). The import threw
on every startup, the function fell to its documented catch, and the fallback
"every string renders as its own id" ran permanently in production.

**Why nothing caught it:** every test served Fluent through a *mocked*
`ChromeUtils.importESModule`. The mock supplied the module, so the import
always succeeded under test. A mock that answers a call the real host never
answers cannot be wrong about it -- the suite was asserting the code kept
making a call that has never once succeeded, and one assertion message even
read "the sitter no longer loads Gecko's own Fluent". Forty green tests, a
mutation probe, and five review seats all sat above a platform that only the
test file provided.

**Why:** a mock defines the boundary the test believes in. Where the mock is
*derived from* the real host it constrains the code; where it is *invented* it
constrains nothing and quietly certifies the invention. The failure is not
"insufficient coverage" -- more tests against the same mock add more green.
Reviewers cannot catch it either: the diff is internally consistent, and every
seat that read it approved.

**How to apply:** when code calls a host/platform API you cannot exercise in
the test environment, the API's *existence and shape* is a separate claim from
the code's logic, and only the real host can settle it. Before mocking a
platform call, confirm the real thing: read it out of the shipped binary
(`unzip -l /opt/zotero7/omni.ja`), grep the host's own source for how it calls
the same API, or have the human run one line in the host's console. One
console line settled this in seconds --
`for (const p of [...]) { try { ChromeUtils.importESModule(p) } catch (e) {...} }`
then `typeof FluentBundle` -- and the answer was that `FluentBundle`,
`FluentResource`, `L10nRegistry` and `L10nFileSource` are all *ambient
globals* in privileged Gecko JS, imported from nowhere. Zotero's own devtools
code calls `L10nRegistry.getInstance()` with no import above it.

The repair is to make the mock model the host, then watch the suite go red
against the unfixed code before fixing anything: changing the mocks to expose
the globals reddened both driven suites with `actual: 'en', expected: 'fr'` --
the production symptom, reproduced in the test harness at last. That red is
the evidence the mock is now load-bearing. See
[[positive-control-before-waiting]] and
[[probe-needs-discriminating-control]]: same family, one level lower -- there
the probe could not discriminate, here the harness could not either, because
it was measuring a world it had made up.

A live-window verification the headless lane "cannot do" is not optional
diligence; it is the only check that can fail. Ticket 0693 carried exactly
that open item, and the wave merged anyway.
