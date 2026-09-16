---
name: feedback_gofmt_smartquotes_vs_ascii
description: "gofmt's stock doc-comment smart-quotes ('' -> U+201D) collide with git-erg's ASCII-only src/go rule; reword '' out of Go comments, don't blame the toolchain"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 211826a9-1beb-4f8d-9a7a-952c56d075ef
---

CORRECTION of an earlier wrong claim (2026-06-03): gofmt turning `''` in a
comment into a UTF-8 right curly quote `"` (U+201D) is **stock, documented,
intended Go behavior**, NOT a corrupt/broken toolchain and NOT padme-specific.

Go's doc-comment formatter (proposal #51082, shipped Go 1.19; in go/printer +
gofmt) applies Markdown-style smart quotes everywhere, in every Go >= 1.19:
``` `` ``` -> U+201C (left), and `''` -> U+201D (right). So `'\''` ends in
`''` and gofmt rewrites it to `'\"`. The community dislikes it (open golang/go
issues #61365 "cmd/gofmt: smart quotes are not" and #76975 Dec-2025 "proposal:
don't rewrite into smart quotes") but it is by design. Evidence that should
have stopped the "corrupt" label: `dpkg --verify` showed the binary INTACT,
the behavior is deterministic, and the stdlib `go/format.Source` reproduces it.

**RESOLVED (ticket 0217, merged 2026-06-03).** Two parts, both landed:
1. POLICY: the ASCII guard now ALLOWS U+201C/U+201D in `*.go` only (assets stay
   strictly ASCII) -- so gofmt and the guard no longer fight. `gofmt -w src/go`
   is now the intended fixer on every machine, padme included; its smart quotes
   are legal in `.go`. There is NO ~/padme toolchain ticket -- reinstalling Go
   changes nothing (it was never broken).
2. SOURCE: `version.go`'s shellSingleQuote comment was ALSO reworded to drop
   the literal `''`, so a comment ABOUT quote-escaping is not smart-quoted into
   misdocumentation. Net: the production tree currently has ZERO smart quotes;
   the allowlist + negative controls protect future gofmt runs.
A `gofmt -l` + `go vet` ratchet (`tests/test_gofmt.sh`) now enforces
gofmt-cleanliness in `make check`.

**How to apply going forward:**
- `gofmt -w src/go` is safe; its U+201C/U+201D output is allowed in `.go`.
- Keep assets (`*.md`, `.ergrc`) strictly ASCII -- the exception is `.go` only.
- To keep a specific comment plain-ASCII, avoid the literal `''` / two-backtick
  pair (the ratchet + encoding controls will tell you if it matters).
- Recover an unwanted smart quote: `perl -i -pe 's/\xe2\x80\x9d/'\'''\''/g'`
  then `grep -RP '[^\x00-\x7F]'` to confirm.
Refs: golang/go#61365, #76975; proposal #51082; go.dev/doc/comment.
See [[feedback_ascii_only_src_go]].
