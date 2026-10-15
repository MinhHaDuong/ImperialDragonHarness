#!/usr/bin/env python3
"""Migrate one project's memory paths, preserving historical evidence bytes.

The caller owns the Git branch. Plans are read-only; application refuses changed
inputs and rolls back ordinary I/O failures. This is not crash-atomic. Symlinks
are deliberately refused, including internal ones, rather than followed.
"""
import argparse
from dataclasses import dataclass
import logging
import os
from pathlib import Path
import re
import shutil
import tempfile


class MigrationError(Exception):
    """Unsafe input or failed application (with any rollback errors included)."""


@dataclass(frozen=True)
class MigrationPlan:
    project: Path
    references: tuple[str, ...]
    snapshot: dict[str, bytes | None]
    moves: tuple[tuple[str, str], ...]
    edits: dict[str, bytes]


def _relative(value):
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise MigrationError(f"Expected project-relative path: {value}")
    return path


def _snapshot(root, references):
    """Read through actual I/O; permission bits alone do not prove readability."""
    result = {}

    def visit(path):
        if path.is_symlink():
            raise MigrationError(f"Filesystem indirection refused: {path}")
        name = str(path.relative_to(root))
        if path.is_dir():
            result[name] = None
            for child in sorted(path.iterdir()):
                visit(child)
        elif path.is_file():
            result[name] = path.read_bytes()
        elif path.exists():
            raise MigrationError(f"Unsupported input: {path}")

    try:
        visit(root / "memory")
        for reference in references:
            path = root / reference
            for parent in path.relative_to(root).parents:
                if (root / parent).is_symlink():
                    raise MigrationError(f"Filesystem indirection refused: {parent}")
            if not path.is_file():
                raise MigrationError(f"Missing reference: {reference}")
            visit(path)
    except OSError as error:
        raise MigrationError(f"Cannot read migration inputs: {error}") from error
    return result


def _rewrite(data):
    text = data.decode("utf-8")
    # Match complete path components and command tokens, never substrings such
    # as daydreams/, /dreamlike, or DREAM.md.backup.
    for pattern, replacement in (
        (r"(?<![\w.-])DREAM\.md(?![\w.-])", "HOARD.md"),
        (r"(?<![\w.-])dreams/", "hoards/"),
        (r"(?<![\w.-])skills/dream(?=/|[^\w.-]|$)", "skills/hoard"),
        (r"(?<![\w./-])/dream(?![\w./-])", "/hoard"),
    ):
        text = re.sub(pattern, replacement, text)
    return text.encode("utf-8")


def plan_migration(project, references=()):
    """Preflight without writes; references are an explicit active-file inventory."""
    root = Path(project).absolute()
    # Refuse indirection in the supplied root as well as beneath it.
    if any(path.is_symlink() for path in (root, *root.parents)):
        raise MigrationError("Project path contains a symlink")
    if not root.is_dir() or not (root / "memory").is_dir():
        raise MigrationError("Project must contain a memory directory")
    refs = tuple(str(_relative(value)) for value in references)
    for name in refs:
        if any(part in {".git", "journal", "dreams", "hoards"}
               for part in Path(name).parts) or name.endswith(".age"):
            raise MigrationError(f"Historical/immutable reference refused: {name}")
    for name in refs:
        parts = Path(name).parts
        if parts[:1] == ("memory",) and (
            len(parts) < 2 or parts[1] not in ("MEMORY.md", "DREAM.md", "HOARD.md", "topics")
        ):
            raise MigrationError(f"Historical/immutable reference refused: {name}")
    before = _snapshot(root, refs)
    if "memory/DREAM.md" not in before and "memory/HOARD.md" not in before:
        raise MigrationError("Missing memory consolidation prompt (DREAM.md or HOARD.md)")
    moves = []
    for old, new, directory in (("memory/DREAM.md", "memory/HOARD.md", False),
                                ("memory/dreams", "memory/hoards", True)):
        if old in before and new in before:
            raise MigrationError(f"Coexistence conflict: {old} and {new}")
        for name in (old, new):
            if name in before and (before[name] is None) != directory:
                raise MigrationError(f"Wrong input type: {name}")
        if old in before:
            moves.append((old, new))
    edits = {}
    # Already-new projects are an exact no-op, including prompt revision.
    if moves:
        active = {name for name, data in before.items()
                  if data is not None and (name == "memory/MEMORY.md" or
                     (name.startswith("memory/topics/") and name.endswith(".md")))}
        active.update(refs)
        active.discard("memory/DREAM.md")
        active.discard("memory/HOARD.md")
        try:
            for name in sorted(active):
                data = before[name]
                if data is None:
                    raise MigrationError(f"Reference is not a file: {name}")
                edited = _rewrite(data)
                if edited != data:
                    edits[name] = edited
            if "memory/DREAM.md" in before:
                text = _rewrite(before["memory/DREAM.md"]).decode("utf-8")
                text, count = re.subn(
                    r"(?m)^(Prompt revision: v\d+-r)(\d+)(\b.*)$",
                    lambda match: match[1] + str(int(match[2]) + 1) + match[3], text)
                if count != 1:
                    raise MigrationError("Expected exactly one versioned Prompt revision")
                text = text.replace("# DREAM", "# HOARD", 1)
                edits["memory/HOARD.md"] = text.encode("utf-8")
        except UnicodeError as error:
            raise MigrationError(f"Active reference is not UTF-8: {error}") from error
    return MigrationPlan(root, refs, before, tuple(moves), edits)


def apply_migration(plan):
    """Apply staged edits; undo completed operations on ordinary failures."""
    root = plan.project
    if _snapshot(root, plan.references) != plan.snapshot:
        raise MigrationError("Migration inputs changed since planning")
    if not plan.moves:
        return
    stage = Path(tempfile.mkdtemp(prefix=".hoard-migrate-", dir=root))
    undo = []
    failure = None
    residual = []
    try:
        for index, (name, data) in enumerate(plan.edits.items()):
            staged = stage / str(index)
            staged.write_bytes(data)
            original = "memory/DREAM.md" if name == "memory/HOARD.md" else name
            os.chmod(staged, (root / original).stat().st_mode & 0o777)
        # Staging can take time; validate again immediately before mutation.
        if _snapshot(root, plan.references) != plan.snapshot:
            raise MigrationError("Migration inputs changed during staging")
        for old, new in plan.moves:
            os.replace(root / old, root / new)
            undo.append((root / new, root / old))
        for index, name in enumerate(plan.edits):
            destination = root / name
            backup = stage / f"backup-{index}"
            os.replace(destination, backup)
            undo.append((backup, destination))
            os.replace(stage / str(index), destination)
    except (OSError, MigrationError) as error:
        failure = error
        for source, destination in reversed(undo):
            try:
                os.replace(source, destination)
            except OSError as rollback_error:
                residual.append(f"{source} -> {destination}: {rollback_error}")
    finally:
        if not residual:
            try:
                shutil.rmtree(stage)
            except OSError as error:
                residual.append(f"cleanup {stage}: {error}")
    if failure or residual:
        detail = f"Migration failed: {failure}" if failure else "Migration applied; cleanup failed"
        if residual:
            detail += f"; residual recovery files in {stage}: " + "; ".join(residual)
        raise MigrationError(detail) from failure


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--reference", action="append", default=[], metavar="RELATIVE_PATH")
    args = parser.parse_args()
    try:
        plan = plan_migration(args.project, args.reference)
        if not args.dry_run:
            apply_migration(plan)
        logging.basicConfig(level=logging.INFO, format="%(message)s")
        logging.info("%s: %d moves, %d active reference edits",
                     "Planned" if args.dry_run else "Applied",
                     len(plan.moves), len(plan.edits))
    except MigrationError as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
