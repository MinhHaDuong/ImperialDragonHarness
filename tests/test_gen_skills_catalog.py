"""Pin the catalog seam: what gen_skills_catalog prints is what README
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

FRONTMATTER = "---\nname: {}\ndescription: \"{}\"\n---\n\nbody\n"


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

    assert lines == ["| `/public-skill` | A public skill description. |"]


def test_catalog_lists_all_public_skills(tmp_path):
    _make_skill(tmp_path, "beta", "Second.")
    _make_skill(tmp_path, "alpha", "First.")

    lines = gen_skills_catalog.catalog_lines(str(tmp_path))

    assert lines == [
        "| `/alpha` | First. |",
        "| `/beta` | Second. |",
    ]
