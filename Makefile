.PHONY: skills-catalog check-skills-drift check-agnostic-tickets check

skills-catalog:
	./scripts/update-skills-catalog.py

check-skills-drift:
	./scripts/check-skills-drift.py

check-agnostic-tickets:
	./scripts/check-agnostic.sh tickets

check: check-skills-drift check-agnostic-tickets
