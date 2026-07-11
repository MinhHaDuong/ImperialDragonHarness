# Memory index — chemin-de-voix

- [Project data path](project_data_path.md) — data lives at ~/data/projets/chemin-de-voix, not ~/data/chemin-de-voix
- [Python tooling: uv](feedback_uv_not_pip.md) — use uv + pyproject.toml, never pip install
- [Infra PADME](infra_padme.md) — hostname=padme, repo=~/chemin-de-voix, corpus=/data/projets/…
- [Format preference](feedback_format_preference.md) — demander le format avant d'implémenter, ne pas sur-ingénier
- [Corpus exclusions](feedback_corpus_exclusions.md) — third-party dirs excluded via scripts/exclude-paths.conf, watch case-sensitivity
- [Real billing for cost analysis](feedback_real_billing_not_estimates.md) — use OR dashboard/activity, never `$/Mtok × tokens` estimates
- [OpenRouter billing sources](reference_openrouter_billing.md) — dashboard vs activity log vs `/api/v1/credits/activity`
