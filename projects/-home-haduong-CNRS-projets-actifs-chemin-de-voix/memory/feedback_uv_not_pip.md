---
name: Python tooling: uv not pip
description: Always use uv + pyproject.toml for Python dependencies, never pip install
type: feedback
originSessionId: 06412290-2998-434a-8efa-7054c7857af7
---
Use `uv` and `pyproject.toml` for all Python dependency management in this project. Never use `pip install`.

**Why:** User explicitly corrected during 0014 execute phase (2026-04-27): "Use uv and pyproject.toml pas pip install".

**How to apply:** When an agent or script needs Python packages, use `uv add <package>` to add to pyproject.toml, or `uv run python script.py` to run in the uv environment. Check if pyproject.toml exists at repo root first; create it if absent.
