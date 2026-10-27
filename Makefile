.PHONY: resident-budget skills-catalog check-skills-drift check-agnostic-tickets check-agnostic-skills check-agnostic-scripts check-agnostic-rules check-personal-data check check-fast check-tests lint

# Interpreter wrapper (uv adoption, author decision 2026-10-09): inside an
# activated env (VIRTUAL_ENV set) the env's python3
# is already first on PATH, so run bare. Otherwise, when uv is present, go
# through `uv run --frozen` so a plain `make check` uses the locked .venv and
# never rewrites uv.lock. Without uv, fall back to the ambient interpreter.
RUN := $(if $(or $(VIRTUAL_ENV),$(shell command -v uv >/dev/null 2>&1 || echo nouv)),,uv run --frozen)

skills-catalog:
	$(RUN) ./scripts/update-skills-catalog.py

# What a session pays before its first question, across every resident
# channel — auto-loaded rules, CLAUDE.md's imports, what the SessionStart
# hook prints, the project memory index, and the frontmatter of every
# skill and subagent. Reporting only; the ratchet is
# tests/test_resident_census.py under `make lint`.
resident-budget:
	$(RUN) ./scripts/resident_census.py --detail

# Fast gate (coding-python.md): unit tests only — excludes the integration
# (subprocess/sleep), slow (network/real-data), and adherence (mechanical
# gate) tiers. Includes the static AST marker-hygiene check (ticket 0229),
# which dogfoods that very exclusion.
check-fast:
	$(RUN) python3 -m pytest tests/ -m "not integration and not slow and not adherence"

# Adherence gate (coding-python.md): the mechanical tier only — grep/AST
# ratchets and hygiene checks. Run apart from the logic loop so check-fast
# stays pure and quick.
lint:
	$(RUN) python3 -m pytest tests/ -m adherence

check-skills-drift:
	$(RUN) ./scripts/check-skills-drift.py

check-agnostic-tickets:
	./scripts/check-agnostic.sh tickets

check-agnostic-skills:
	./scripts/check-agnostic.sh skills

check-personal-data:
	bash scripts/check-personal-data.sh

check-agnostic-scripts:
	./scripts/check-agnostic.sh scripts

check-agnostic-rules:
	./scripts/check-agnostic.sh rules

# Full gate (coding-python.md): the whole suite, integration + slow included.
# Parallelism comes from one rule, scripts/pytest_workers.py (ticket 1215): it
# prints `-n N` for this host, or nothing for serial (pytest-xdist missing, or
# IDH_TEST_WORKERS=0). Measurements and the reasoning live in that ticket and
# the script's docstring, not here. check-fast and lint are deliberately serial
# (both sit at the pytest boot+collection floor).
check-tests:
	$(RUN) python3 -m pytest tests/ $(shell $(RUN) python3 scripts/pytest_workers.py)

check: check-skills-drift check-agnostic-tickets check-agnostic-skills check-agnostic-scripts check-agnostic-rules check-personal-data check-tests

# Daily audit of main (tickets 1157, 1179): does each commit that entered
# origin/main in the last 24 h carry a gate receipt? Exit 1 on a finding, 2 when
# it could not look in full. --after (ticket 1244): tips with no after-merge
# record, and the full set run on the latest; that run executes the gate's
# checks and pushes a note to refs/notes/gate. Git-only otherwise, never in the merge path
# (conception/2026-10-21-main-update-guard.md).
.PHONY: main-sweep
main-sweep:
	$(RUN) ./scripts/main_sweep.py --fetch --after
