#!/usr/bin/env python3
"""Generate the root skills-catalog.md from skill frontmatter."""

from pathlib import Path

import gen_skills_catalog


def main():
    Path("skills-catalog.md").write_text(
        gen_skills_catalog.catalog_document("."), encoding="utf-8"
    )
    print("Done. Updated skills-catalog.md.")


if __name__ == "__main__":
    main()
