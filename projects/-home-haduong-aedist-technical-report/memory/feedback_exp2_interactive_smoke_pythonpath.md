---
name: feedback_exp2_interactive_smoke_pythonpath
description: exp2_interactive_smoke.py requires PYTHONPATH=. to find the experiments package
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 4ce9fb20-3b79-41a4-90ba-e2b94004e133
---

`experiments/sota/exp2_interactive_smoke.py` imports `from experiments.sota import ...` but `experiments/` has no `__init__.py` and is not an installed package. Running it directly gives `ModuleNotFoundError: No module named 'experiments'`.

**Why:** The script uses `experiments.sota` as a dotted import path, which requires the repo root on `sys.path`. `uv run` adds the project's installed packages but not the repo root itself.

**How to apply:** Always prefix with `PYTHONPATH=.` when invoking this script:

```bash
PYTHONPATH=. uv run python experiments/sota/exp2_interactive_smoke.py ...
```

Also applies to any other script in `experiments/` that imports sibling modules with dotted paths.
