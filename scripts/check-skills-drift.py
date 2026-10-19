#!/usr/bin/env python3
"""Check the generated root skills catalog, including grouping and order."""

from pathlib import Path
import sys

import gen_skills_catalog


def main():
    path = Path("skills-catalog.md")
    actual = path.read_text(encoding="utf-8") if path.exists() else None
    if actual == gen_skills_catalog.catalog_document("."):
        print("OK: Skills catalog is in sync.")
        return
    print("DRIFT DETECTED: run 'make skills-catalog' to regenerate skills-catalog.md")
    sys.exit(1)


if __name__ == "__main__":
    main()
