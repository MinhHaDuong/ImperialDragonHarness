.PHONY: skills-catalog check-skills-drift check

skills-catalog:
	./scripts/update-skills-catalog.py

check-skills-drift:
	./scripts/check-skills-drift.py

check: check-skills-drift
