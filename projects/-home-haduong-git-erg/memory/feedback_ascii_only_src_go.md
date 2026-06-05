---
name: ascii-only-src-go
description: "src/go/ is ASCII-only EXCEPT *.go may contain U+201C/U+201D (gofmt smart quotes, ticket 0217); assets (*.md, .ergrc) stay strictly ASCII; em-dashes still fail."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ab5e5447-d280-4bd4-b5f3-9b0f3f0d028e
---

The encoding test (`tests/test_encoding.sh`) rejects non-ASCII bytes in `src/go/**` — including `.md` asset files, not just `.go` source. Trojan-Source / encoding corruption guards (ticket 0167).

**SCOPED EXCEPTION (ticket 0217, author-authorized 2026-06-03).** The guard now ALLOWS exactly two non-ASCII code points — `U+201C` and `U+201D` (gofmt's doc-comment smart quotes for two-backtick / `''` pairs, Go 1.19+) — in **`*.go` only**. Assets (`*.md`, `.ergrc`) stay **strictly ASCII** (incident 0160); every other non-ASCII byte (em-dash, bidi, etc.) is still rejected in `.go`. So em-dashes still fail; only those two curly quotes are tolerated, only in `.go`. Author chose this to stop fighting gofmt (verify #253 ESCALATED on the security-control change; author confirmed "yes merge"). A `gofmt`+`go vet` ratchet (`tests/test_gofmt.sh`) now enforces gofmt-cleanliness, so `gofmt -w src/go` is the intended fixer on padme too. See [[feedback_gofmt_smartquotes_vs_ascii]].

During raid 188-193, two agents used em-dashes (—) in their edits:
- `src/go/log.go` (0191 agent): needed a fixup commit
- `src/go/assets/integration.md` (0192 agent): needed a fixup commit

**Why:** Unicode in Go source enables homoglyph attacks; non-ASCII in embedded assets can corrupt under encoding round-trips.

**How to apply:** When editing any file under `src/go/`, use ASCII-only punctuation. Replace em-dashes (—) with double hyphens (--). Check with `grep -P '[^\x00-\x7F]' <file>` before committing.
