.PHONY: skills-catalog check-skills-drift

skills-catalog:
	./scripts/update-skills-catalog.py

check-skills-drift:
	./scripts/check-skills-drift.py
