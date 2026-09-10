# Project memory index — git-erg

- [Asset-edit CI gates](asset-edit-ci-gates.md) — ASCII-only embedded assets + archive-before-push; `make regen-assets` doesn't gate, run `make test`.
- [erg update fetches from the repo's own origin](reference-erg-update-fetches-from-the-repos-own-origin.md) — in an adopter it compares the binary to itself, says "already up to date", and can never move it forward; fix is `[update] url` in `.ergrc`.
- [Bare `gh pr merge` drops the close claim](feedback-bare-gh-pr-merge-drops-close-claim.md) — `**Ticket:**` is executed by `erg-pr-merge`, not GitHub; `erg check` passes either way, so the miss is invisible.
- [Sweeping for CLI callers](feedback-sweep-for-cli-callers-must-cover-variable-invocations.md) — a literal `erg log` grep misses `$ERG log` and returns a clean zero; fire a positive control before trusting it.
