# I/O migration pattern for Phase 2 scripts

When wrapping module-level code in main() for parse_io_args():

1. **Extract helpers first** -- wrapping 200+ lines in main() will exceed complexity limits (PLR0912 > 25 branches, PLR0915 > 120 statements, C901 > 25). Extract data loading, computation, and rendering into separate functions before committing.

2. **Unicode preservation** -- when rewriting files, preserve Unicode characters (Delta, arrows, en-dashes) using escape sequences (`\u0394`, `\u2190`, `\u2192`, `\u2013`). The Write tool can silently ASCII-ify content.

3. **`.values` vs `.values()`** -- pandas Series from `groupby().apply()` uses `.values` (property) not `.values()` (method call). The latter crashes with `TypeError: numpy.ndarray is not callable`. This is a latent bug in several co-citation scripts (filed as #604).

4. **Smoke fixtures for multi-input scripts** -- scripts needing works+embeddings+citations: pass all 3 via `--input a.csv b.npz c.csv` with positional ordering. Create minimal fixture files for inputs that don't exist in the standard smoke set.

5. **Dynamic output filenames** -- for scripts producing data-dependent filenames (one figure per break year), use `--output` as a stamp file path. The script writes the stamp after generating all figures.

Created: 2026-03-31
TTL: 6 months
