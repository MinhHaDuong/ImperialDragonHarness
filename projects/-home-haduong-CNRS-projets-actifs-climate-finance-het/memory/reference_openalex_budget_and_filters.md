---
name: reference_openalex_budget_and_filters
description: "OpenAlex API: 1 USD/day budget in the response headers, prepaid top-up, language and country filter traps, benign count drift"
metadata:
  node_type: memory
  type: reference
  originSessionId: defcd2ff-c1d3-4c08-b691-d9c570f60034
  modified: 2026-09-29T16:01:48.172Z
---

Measured 2026-09-29 with the project key (`OPENALEX_API_KEY` in `~/.config/keys/openalex.env`).

- **Budget.** Every response carries `X-RateLimit-Limit-USD` (1 per day here), `Remaining-USD`, `Prepaid-Remaining-USD` and `Reset` (seconds). Three complete search passes plus two half passes used the day's 10,000 credits; one more request returns 429 until the reset. The author tops up prepaid credit on openalex.org (5 USD took a few minutes to show; 11.53 USD prepaid after that). Poll a `per_page=1` request to see it arrive. A full 88-query pass costs roughly 0.25 to 0.30 USD (derived, not measured per pass).
- **Language filter.** The `language` tag is null on some 2026 works and wrong on others (Indonesian and Russian titles tagged `en`). Dropping the filter is worse: Latin tokens inside non-English phrase lists (REDD, JETP, Green Climate Fund) then match every work in the world (11,700 hits, record cap, rate limit). Use `language:pt|null`, which returned 324 works against 282 for `language:pt` and 331 unfiltered.
- **Country filter.** `authorships.institutions.country_code` is missing on most non-English works (Chinese, 260 hits by language, 4 with the country filter), and it drops Northern-authored work about the South. Use it on English runs only and add a global English gap-fill query.
- **No stemming, no folding.** Bengali `য়` exists as one code point or two, Russian `ё`/`е` and inflected forms differ, so send every spelling variant. `REDD` and `REDD+` are the same token.
- **Count drift.** The announced `meta.count` differs from the records received by a few units on 20 to 25% of queries; the author calls the API unstable and the drift benign.
- **Two silent traps in my own tooling.** `ssh host 'pkill -f pattern'` kills its own remote shell (exit 255, no message) because the command line contains the pattern; write `pkill -f "[p]attern"`. And the worktree isolation guard rejects compound commands, heredocs and computed names: write a script file and run it, or use literal paths.
