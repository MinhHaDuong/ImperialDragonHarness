.PHONY: resident-budget skills-catalog check-skills-drift check-agnostic-tickets check-agnostic-skills check-agnostic-scripts check-agnostic-rules check-personal-data check check-fast check-tests lint

# Interpreter wrapper (uv adoption, author decision 2026-10-09): inside an
# activated env (VIRTUAL_ENV set, as in CI after `uv sync`) the env's python3
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
# -n 4 per the 1011 worker-safety audit: three parallel trials reproduced
# the serial pass/skip counts exactly, 81s -> 38.6s. check-fast and lint are
# deliberately serial (both sit at the pytest boot+collection floor).
# Falls back to serial when pytest-xdist is not installed (probe: import xdist).
HAVE_XDIST := $(shell $(RUN) python3 -c 'import xdist' 2>/dev/null && echo yes)
check-tests:
	$(RUN) python3 -m pytest tests/ $(if $(HAVE_XDIST),-n 4)

check: check-skills-drift check-agnostic-tickets check-agnostic-skills check-agnostic-scripts check-agnostic-rules check-personal-data check-tests
