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

Categories, order and regeneration: `AGENTS.md` § Skills catalog.
