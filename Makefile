.PHONY: skills-catalog check-skills-drift check-agnostic-tickets check-agnostic-skills check check-fast

skills-catalog:
	./scripts/update-skills-catalog.py

# Fast gate (coding-python.md): unit tests only — excludes the integration
# (subprocess/sleep) and slow (network/real-data) tiers. Includes the static
# AST marker-hygiene check (ticket 0229), which dogfoods that very exclusion.
check-fast:
	python3 -m pytest tests/ -m "not integration and not slow"

check-skills-drift:
	./scripts/check-skills-drift.py

check-agnostic-tickets:
	./scripts/check-agnostic.sh tickets

check-agnostic-skills:
	./scripts/check-agnostic.sh skills

check: check-skills-drift check-agnostic-tickets check-agnostic-skills
