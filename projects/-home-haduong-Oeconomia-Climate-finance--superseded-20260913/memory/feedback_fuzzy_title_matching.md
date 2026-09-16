# Fuzzy Title Matching — Lessons Learned

## rapidfuzz metric choice matters enormously

- **token_set_ratio** has a containment bias: if title A's tokens are a subset of title B's tokens, score is ~100 regardless of how much extra content B has. This makes short domain phrases ("Climate Change") match everything.
- **token_sort_ratio** is symmetric and better for comparing titles of different lengths. It penalizes extra words proportionally.
- **token_set_ratio at 80** on 909 titles: created a 45-member cluster via transitive chaining.
- **token_sort_ratio at 75** on same data: largest cluster is 5, all genuine variants.

## Single-linkage chaining is the main risk

Even with a good metric, single-linkage clustering can chain unrelated works through intermediate titles. At threshold 70 with token_sort_ratio: "Principles of Sustainable Finance" -> "Lectures Notes in Sustainable Finance" (71) -> "Sustainable Finance and Investments" (78) -> ... -> "Climate Change and Justice". Raising threshold to 75 broke all such chains in the real data.

## Short titles need special handling

Titles under 4 words ("Climate Change", "The Stern Review", "Investments") are too generic for any fuzzy matching approach. They either match too many things (token_set_ratio) or nothing useful (token_sort_ratio). CrossRef DOI enrichment (already in stage_normalize) is the right tool for these.

## Test on real data early

Unit tests with handcrafted examples passed immediately. Running on the actual 909-title dataset revealed the over-merging problem that no unit test would catch. Always test fuzzy/ML features on production data during development.
