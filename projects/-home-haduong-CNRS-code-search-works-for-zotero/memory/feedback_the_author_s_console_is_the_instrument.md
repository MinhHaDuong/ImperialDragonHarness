---
name: the-authors-console-is-the-instrument
description: "Three host-contract defects in one night were each settled by one line the author pasted into Zotero's Browser Console; none was findable from the repository, and each of my code-reading theories was wrong"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d5b346ef-7983-4572-a95a-cf476a17df19
  modified: 2026-09-06T22:44:37.766Z
---

On 2026-09-06/07 the sitter plugin shipped a localization layer that had never
rendered a single string. Finding out why took an evening, and every step that
actually moved was a line the author pasted into Zotero's Browser Console.
Every step I took by reading source or unzipping `omni.ja` produced a plausible
theory that was wrong or incomplete.

What the console settled, in order, each in seconds:

* `ChromeUtils.importESModule` on the three plausible Fluent paths -> all three
  `Failed to load`. My static reading of `omni.ja` had got as far as "no such
  file", but not to what to do instead.
* `typeof FluentBundle` -> `"function"`. Ambient global, compiled into the
  binary, named in no archive entry. Nothing in the repo or the jars could have
  told me this; I had been about to build an `L10nRegistry` + `L10nFileSource`
  registration that was entirely unnecessary.
* Three read methods against the real `jar:` rootURI -> `getContentsFromURLAsync`
  fails inside URI parsing (`NS_ERROR_FAILURE [nsIURI.username]`). That one
  error string is the whole diagnosis of the second defect, and no amount of
  reading Zotero's `file.js` would have produced it, because the code looks
  fine.
* His diagnostics panel, pasted unprompted, showed
  `Add-on version: unreadable (NS_ERROR_FAILURE)` beside
  `Installed in: jar:file:///…`. Two lines that are one fact, and the third
  instance of the same defect -- in ticket 0688's own instrumentation, which
  had therefore never once recorded which build was running.

**Why:** this repository contains no statement of what the host provides that
is checked against a host. Its tests supply the host themselves, so they agree
with whatever the code assumes (see [[feedback_mock_that_invents_the_platform]]). The
application is right there on the machine, and the author is sitting in front
of it.

**How to apply:** when a symptom is in a running application and the question
is "what does the host actually do here", ask for the one line before building
anything. Write the snippet so each possible outcome names a different repair,
say which row you expect and why, and say it is the last one you need. Three
of mine did that and all three paid; the two I skipped in favour of reasoning
(the empty `update_url` theory, the 30-minute timer story) were both wrong and
one of them shipped as a fix that did not work.

Two traps inside the pattern, both of which bit:

* **A probe run against a vanished target proves nothing.** My `jar:` probe ran
  after the add-on had been deleted from disk; two of its three arms were
  confounded and only the URI-parse error survived as evidence. Check the
  target still exists at probe time.
* **The console's scope is not the plugin's scope.** `typeof FluentBundle` in
  the Browser Console answers for privileged chrome JS, which is strong
  evidence for a bootstrap sandbox and not proof. Say which scope the answer
  came from.

And do not send a second build on a theory the first build already refuted.
0.2.15 shipped a fix for a mechanism the watcher log had already shown was
wrong, because I had written the fix before reading the log properly.
