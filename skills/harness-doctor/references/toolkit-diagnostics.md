# Toolkit diagnostics

Use these reading procedures and instruments for a named concern during an
author-called harness-doctor visit. They are reusable diagnostic options;
they are never routine health checks, scheduled sweeps, or merge gates.
Follow `doctor-practice.md` and `diagnosis-discipline.md`, including the
harness precondition and a positive control before interpreting silence.

## Dependency inspection

**Question.** Does a named helper's dependency contract match where and how
its skill expects it to run? Inspect the skill's call site and the helper
together; an import inventory alone cannot settle that question.

**Existing owners.** `authoring-skills.md` § Toolkit principles governs
bundled helpers: standard library by default; a third-party specialized tool
is optional and has a working standard-library or manual route alongside.
Harness `scripts/` tools instead use the locked environment under
`rules/coding-python.md` § Environment. `tests/test_deps_declared.py` already
checks declarations using AST imports and `tests/repo_sources.py` owns that
gate's source inventory. This diagnostic does not replace or expand the gate.

**Inputs and cost.** Name a bounded set of Python source files, their skill
call sites, and the applicable checkout. Read-only, seconds, no model call,
credentials, package installation, or inspected-code execution. The helper
needs Python 3.10+ and readable files. Explicit paths also accept extensionless
Python; shell heredocs and other languages require reading their own sources.
Known extra Python search roots may be supplied with `--local-root <path>`.
The default local search is each inspected file's parent, not the whole repo.

**Control first.** Run the fixture-based behavior controls:
`python3 -m pytest tests/test_check_imports.py` from the locked development
environment. They include a third-party sentinel, stdlib and local imports,
unavailable sources, dynamic calls, and the CLI's exit-zero contract. These
controls test the instrument, not live-tree dependency compliance. If the
controls cannot run or do not fire, report inspection unavailable; a manual
reading control can still establish the reading procedure below.

**Instrument.** From the checkout, with `IDH_ROOT` set as in the skill:

```bash
python3 "$IDH_ROOT/scripts/check_imports.py" --root "$IDH_ROOT" \
  "$IDH_ROOT/scripts/skill_frontmatter.py" \
  "$IDH_ROOT/scripts/trace_events.py"
```

The JSON lists direct imports with line, classification, and evidence. It
identifies bundled-helper, harness-tool, or unclassified policy perimeters.
Findings and unavailable files exit zero: this is an instrument. Never read
its exit status as a clean dependency bill. An unclassified path needs a
human reading of its deployment contract before any policy judgment.

**Interpretation.** The example should identify `yaml` as a third-party
candidate in `skill_frontmatter.py` and direct stdlib imports in
`trace_events.py`. The former belongs to the harness's locked environment;
its presence is not itself a violation. Follow local import candidates to
establish their prerequisites if the complaint requires it. Record the
interpreter, required packages/versions, system commands, and services from
the actual call path and environment declarations; mark unexamined items
unavailable. Judge exceptions against existing guidance, without inventing a
registry. Propose the smallest correction only when evidence establishes a
gap; a compatible dependency contract is a valid outcome.

**Limits.** AST imports include lazy function imports, which do not establish
optional availability. Dynamic call sites are hints, not resolved targets;
aliases and custom loaders can escape them. Local paths are candidates, not
verified runtime resolution. Transitive dependencies, installed packages,
versions, system tools, and services remain unexamined. Even a file with only
stdlib imports has these limits. Missing/unreadable/invalid sources are
unavailable and have no empty import list standing in for inspection.

**Manual route.** Without the helper or newly written code, read a small
known source containing `import json`, a real sibling import, and a known
third-party import. Locate each import, including those inside functions,
and verify those three cases remain distinguishable. Then read each named
source the same way: list module and line; classify against the inspecting
Python's stdlib documentation and concrete sibling/search-root paths; retain
unresolved names as candidates. Read dynamic loaders and the skill's launch
contract separately. Compare prerequisites with the existing policy above,
report inspected scope and unknowns, and propose only established fixes.
This takes minutes per source rather than seconds for a batch; it preserves
the same authorization and verification requirements.
