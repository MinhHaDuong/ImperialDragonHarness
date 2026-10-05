.PHONY: resident-budget skills-catalog check-skills-drift check-agnostic-tickets check-agnostic-skills check-agnostic-scripts check-agnostic-rules check-personal-data check check-fast check-tests lint

skills-catalog:
	./scripts/update-skills-catalog.py

# What a session pays before its first question, across every resident
# channel — auto-loaded rules, CLAUDE.md's imports, what the SessionStart
# hook prints, the project memory index, and the frontmatter of every
# skill and subagent. Reporting only; the ratchet is
# tests/test_resident_census.py under `make lint`.
resident-budget:
	./scripts/resident_census.py --detail

# Fast gate (coding-python.md): unit tests only — excludes the integration
# (subprocess/sleep), slow (network/real-data), and adherence (mechanical
# gate) tiers. Includes the static AST marker-hygiene check (ticket 0229),
# which dogfoods that very exclusion.
check-fast:
	python3 -m pytest tests/ -m "not integration and not slow and not adherence"

# Adherence gate (coding-python.md): the mechanical tier only — grep/AST
# ratchets and hygiene checks. Run apart from the logic loop so check-fast
# stays pure and quick.
lint:
	python3 -m pytest tests/ -m adherence

check-skills-drift:
	./scripts/check-skills-drift.py

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
check-tests:
	python3 -m pytest tests/ -n 4

check: check-skills-drift check-agnostic-tickets check-agnostic-skills check-agnostic-scripts check-agnostic-rules check-personal-data check-tests
