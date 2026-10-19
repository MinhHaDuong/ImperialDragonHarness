# Contributing

Run checks from the checkout:

```bash
make check-fast       # fast development loop
make lint             # adherence checks
make check            # full gate
make resident-budget  # report startup context cost
```

Setup: `uv sync` creates `.venv` from `pyproject.toml` and `uv.lock`
(development dependencies, `dev` group). Activate it, or let `make` call
`uv run --frozen` for you. Credentials
belong in the external keystore and are resolved by task-specific tools.

## Ticket management

The preferred ticket system is [git-erg](https://github.com/MinhHaDuong/git-erg), an offline `tickets/` directory that lives inside each project's git repo. Install it per-project following its README. When git-erg is available, use it. Fall back to GitHub issues or any other forge when needed (e.g., for cross-team coordination).


## Skills catalog

Set each public skill's `metadata.category` frontmatter to a key in
`scripts/gen_skills_catalog.py`. The generated catalog has Generalist and
Research sections, purpose subgroups, and alphabetical commands within each
subgroup. Run `make skills-catalog` after changing a skill's name, description
or category, or adding or removing one. `make check-skills-drift` checks the
complete generated document, including order. Private skill symlinks are excluded.
