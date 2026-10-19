"""Pin the catalog seam: what gen_skills_catalog prints is what skills-catalog.md
publishes in a public repo. Private skills are symlinked into skills/
(gitignored) — the runtime discovers them, but repo files carry no pointers
to them; a catalog that globs through the symlinks publishes their
descriptions (2026-09-28: three private skills landed in the README catalog,
carrying T2 topology — hosts, machines, credential locations)."""

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import gen_skills_catalog  # noqa: E402

FRONTMATTER = "---\nmetadata:\n  category: build\nname: {}\ndescription: \"{}\"\n---\n\nbody\n"


def _make_skill(root: Path, name: str, description: str) -> Path:
    d = root / "skills" / name
    d.mkdir(parents=True)
    f = d / "SKILL.md"
    f.write_text(FRONTMATTER.format(name, description))
    return d


def test_catalog_skips_symlinked_private_skills(tmp_path):
    _make_skill(tmp_path, "public-skill", "A public skill description.")
    private_dir = tmp_path / "private-skills" / "private-skill"
    private_dir.mkdir(parents=True)
    (private_dir / "SKILL.md").write_text(
        FRONTMATTER.format("private-skill", "Private infrastructure map.")
    )
    (tmp_path / "skills" / "private-skill").symlink_to(private_dir)

    lines = gen_skills_catalog.catalog_lines(str(tmp_path))

    rows = [line for line in lines if line.startswith("| `/")]
    assert rows == ["| `/public-skill` | A public skill description. |"]


def test_catalog_lists_all_public_skills(tmp_path):
    _make_skill(tmp_path, "beta", "Second.")
    _make_skill(tmp_path, "alpha", "First.")

    lines = gen_skills_catalog.catalog_lines(str(tmp_path))

    assert lines[-2:] == [
        "| `/alpha` | First. |",
        "| `/beta` | Second. |",
    ]


def test_catalog_rejects_missing_category(tmp_path):
    import pytest

    directory = _make_skill(tmp_path, "uncategorized", "Description.")
    path = directory / "SKILL.md"
    path.write_text(path.read_text().replace("metadata:\n  category: build\n", ""))
    with pytest.raises(ValueError, match="missing or unknown category"):
        gen_skills_catalog.catalog_lines(str(tmp_path))


def test_catalog_groups_before_sorting_names(tmp_path):
    _make_skill(tmp_path, "zebra", "Build.")
    directory = _make_skill(tmp_path, "alpha", "Session.")
    path = directory / "SKILL.md"
    path.write_text(path.read_text().replace("category: build", "category: session"))
    lines = gen_skills_catalog.catalog_lines(str(tmp_path))
    assert lines.index("### Build and ship") < lines.index("### Session and maintenance")
    assert lines.index("| `/zebra` | Build. |") < lines.index("| `/alpha` | Session. |")


def test_catalog_separates_generalist_and_research(tmp_path):
    _make_skill(tmp_path, "hunt", "Build.")
    directory = _make_skill(tmp_path, "zotero", "Research.")
    path = directory / "SKILL.md"
    path.write_text(path.read_text().replace("category: build", "category: research"))
    lines = gen_skills_catalog.catalog_lines(str(tmp_path))
    assert lines.index("## Generalist") < lines.index("### Build and ship")
    assert lines.index("## Research") < lines.index("### Research and bibliography")
    assert lines.index("| `/hunt` | Build. |") < lines.index("## Research")


def test_catalog_document_is_reproducible(tmp_path):
    _make_skill(tmp_path, "hunt", "Begin work.")
    document = gen_skills_catalog.catalog_document(str(tmp_path))
    assert document.startswith("# Skills catalog\n")
    assert "## Generalist" in document
    assert document.endswith("| `/hunt` | Begin work. |\n")
    assert document == gen_skills_catalog.catalog_document(str(tmp_path))


def test_catalog_rejects_unknown_category(tmp_path):
    import pytest

    directory = _make_skill(tmp_path, "misclassified", "Description.")
    path = directory / "SKILL.md"
    path.write_text(path.read_text().replace("category: build", "category: typo"))
    with pytest.raises(ValueError, match="missing or unknown category"):
        gen_skills_catalog.catalog_lines(str(tmp_path))
