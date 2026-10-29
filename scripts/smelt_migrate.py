#!/usr/bin/env python3
"""Migrate one project's memory paths to the smelt names, preserving historical evidence bytes.

Legacy names (DREAM.md and dreams/, HOARD.md and hoards/) move to SMELT.md and
smelts/. The legacy names stay in this file because they are what it detects.

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


LEGACY_PROMPTS = ("memory/DREAM.md", "memory/HOARD.md")
LEGACY_DIRS = ("memory/dreams", "memory/hoards")
NEW_PROMPT = "memory/SMELT.md"
NEW_DIR = "memory/smelts"


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


def _check_root(root):
    # Refuse indirection in the supplied root as well as beneath it.
    if any(path.is_symlink() for path in (root, *root.parents)):
        raise MigrationError("Project path contains a symlink")
    if not root.is_dir() or not (root / "memory").is_dir():
        raise MigrationError("Project must contain a memory directory")


def _snapshot(root, references):
    """Read through actual I/O; recheck root indirection at every validation."""
    _check_root(root)
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


def _rewrite(data, reference, moves, root):
    """Rewrite moved targets relative to the reference file, without I/O."""
    text = data.decode("utf-8")
    parent = root / Path(reference).parent

    def moved_path(match):
        token = match[0]
        # Markdown destinations resolve from their file. Bare/code memory/
        # spellings conventionally describe paths from the project root.
        prefix = text[:match.start()]
        link = re.search(r"\]\(\s*<?$|(?m:^\s{0,3}\[[^\]\n]+\]:\s*<?$)", prefix)
        base = root if token.startswith("memory/") and not link else parent
        target = Path(os.path.normpath(base / token))
        for old, new in moves:
            old_path = root / old
            if target != old_path and not (
                old in LEGACY_DIRS and old_path in target.parents
            ):
                continue
            destination = root / new / target.relative_to(old_path)
            if token.startswith("memory/") and not link:
                result = destination.relative_to(root).as_posix()
            elif token.startswith("/"):
                result = str(destination)
            else:
                result = os.path.relpath(destination, parent)
                if token.startswith("./"):
                    result = "./" + result
            if token.endswith("/"):
                result += "/"
            return result
        return token

    text = re.sub(
        r"(?<![\w./:-])/?(?:[\w.-]+/)*(?:(?:DREAM|HOARD)\.md(?![\w.-])|(?:dreams|hoards)/[\w./-]*)",
        moved_path, text,
    )
    # Only the current skill directory/entrypoint is renamed. Retired helpers
    # keep the path under which they historically existed.
    text = re.sub(
        r"(?<![\w./:-])(?P<prefix>/?(?:[\w.-]+/)*)skills/(?:dream|hoard)"
        r"(?P<entry>/SKILL\.md|/)?(?![\w/-]|\.(?!\s|$))",
        lambda match: match["prefix"] + "skills/smelt" + (match["entry"] or ""), text,
    )
    text = re.sub(r"(?<![\w./-])/(?:dream|hoard)(?![\w./-])", "/smelt", text)
    return text.encode("utf-8")


def plan_migration(project, references=()):
    """Plan without writes. Default edits cover the prompt, index and Markdown
    topics; references explicitly add active project-relative files. Historical
    reports, journal entries and ciphertext are never rewritten.
    """
    root = Path(project).absolute()
    refs = tuple(str(_relative(value)) for value in references)
    for name in refs:
        if any(part in {".git", "journal", "dreams", "hoards", "smelts"}
               for part in Path(name).parts) or name.endswith(".age"):
            raise MigrationError(f"Historical/immutable reference refused: {name}")
    for name in refs:
        parts = Path(name).parts
        if parts[:1] == ("memory",) and (
            len(parts) < 2 or parts[1] not in ("MEMORY.md", "DREAM.md", "HOARD.md", "SMELT.md", "topics")
        ):
            raise MigrationError(f"Historical/immutable reference refused: {name}")
    before = _snapshot(root, refs)
    legacy_prompts = [name for name in LEGACY_PROMPTS if name in before]
    legacy_dirs = [name for name in LEGACY_DIRS if name in before]
    if not legacy_prompts and NEW_PROMPT not in before:
        raise MigrationError("Missing memory consolidation prompt (DREAM.md, HOARD.md or SMELT.md)")
    moves = []
    for olds, new, directory in ((legacy_prompts, NEW_PROMPT, False),
                                 (legacy_dirs, NEW_DIR, True)):
        if len(olds) > 1 or (olds and new in before):
            raise MigrationError(f"Coexistence conflict: {', '.join(olds + [new])}")
        for name in (*olds, new):
            if name in before and (before[name] is None) != directory:
                raise MigrationError(f"Wrong input type: {name}")
        if olds:
            moves.append((olds[0], new))
    if (NEW_PROMPT in before and legacy_dirs) or (legacy_prompts and NEW_DIR in before):
        raise MigrationError("Mixed old/new memory layout: prompt and reports disagree")
    targets = list(moves)
    if legacy_prompts and not legacy_dirs and NEW_DIR not in before:
        # A project with no reports still needs the new output convention.
        # This changes references only; no absent directory is created/moved.
        old_dir = LEGACY_DIRS[LEGACY_PROMPTS.index(legacy_prompts[0])]
        targets.append((old_dir, NEW_DIR))
    edits = {}
    # Already-new projects are an exact no-op, including prompt revision.
    if moves:
        active = {name for name, data in before.items()
                  if data is not None and (name == "memory/MEMORY.md" or
                     (name.startswith("memory/topics/") and name.endswith(".md")))}
        active.update(refs)
        active.difference_update(LEGACY_PROMPTS)
        try:
            for name in sorted(active):
                data = before[name]
                if data is None:
                    raise MigrationError(f"Reference is not a file: {name}")
                edited = _rewrite(data, name, targets, root)
                if edited != data:
                    edits[name] = edited
            for legacy in legacy_prompts:
                text = _rewrite(before[legacy], legacy, targets, root).decode("utf-8")
                text, count = re.subn(
                    r"(?m)^(Prompt revision: v\d+-r)(\d+)(\b.*)$",
                    lambda match: match[1] + str(int(match[2]) + 1) + match[3], text)
                if count != 1:
                    raise MigrationError("Expected exactly one versioned Prompt revision")
                text = re.sub(r"^# (?:DREAM|HOARD)", "# SMELT", text, count=1)
                edits[NEW_PROMPT] = text.encode("utf-8")
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
    try:
        stage = Path(tempfile.mkdtemp(prefix=".smelt-migrate-", dir=root))
    except OSError as error:
        raise MigrationError(f"Cannot stage migration: {error}") from error
    origin = {new: old for old, new in plan.moves}
    undo = []
    failure = None
    residual = []
    try:
        for index, (name, data) in enumerate(plan.edits.items()):
            staged = stage / str(index)
            staged.write_bytes(data)
            original = origin.get(name, name)
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
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog="By default, applies the migration and updates the prompt, "
               "memory/MEMORY.md and Markdown topics. Reports, journal entries "
               "and ciphertext retain their bytes. No Git operations are performed.",
    )
    parser.add_argument("project", type=Path, help="selected project repository to migrate")
    parser.add_argument("--dry-run", action="store_true",
                        help="preflight and describe planned moves/edits without writing")
    parser.add_argument("--reference", action="append", default=[], metavar="RELATIVE_PATH",
                        help="add an active project-relative reference file to update; "
                             "repeat for each additional file (defaults remain included)")
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
