#!/usr/bin/env python3
"""Migrate one project's memory paths to the smelt names, preserving historical evidence bytes.

Legacy report directories (dreams/, hoards/) move to smelts/. A per-project
consolidation prompt (DREAM.md, HOARD.md or SMELT.md) is retired: the generic
text lives in the smelt skill (ticket 1451), and no prompt is the default. The
helper names each retired prompt and each active file still naming one; the
agent carries the prompt's local location facts into memory/MEMORY.md and
edits those mentions. The legacy names stay in this file because they are
what it detects. A prompt is retired only when HEAD holds its exact bytes, so
its text stays recoverable with git show.

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
import subprocess
import tempfile


LEGACY_PROMPTS = ("memory/DREAM.md", "memory/HOARD.md")
LEGACY_DIRS = ("memory/dreams", "memory/hoards")
RETIRED_PROMPTS = (*LEGACY_PROMPTS, "memory/SMELT.md")
NEW_DIR = "memory/smelts"
PROMPT_TOKEN = re.compile(r"(?<![\w./:-])/?(?:[\w.-]+/)*(?:DREAM|HOARD|SMELT)\.md(?![\w.-])")


class MigrationError(Exception):
    """Unsafe input or failed application (with any rollback errors included)."""


@dataclass(frozen=True)
class MigrationPlan:
    project: Path
    references: tuple[str, ...]
    snapshot: dict[str, bytes | None]
    moves: tuple[tuple[str, str], ...]
    edits: dict[str, bytes]
    retired: tuple[str, ...] = ()
    stale: tuple[str, ...] = ()


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


def _committed(root, name, data):
    """True when HEAD of root's repository holds exactly these bytes at name."""
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "show", f"HEAD:./{name}"],
            capture_output=True, check=False,
        )
    except OSError:
        return False
    return result.returncode == 0 and result.stdout == data


def _target(text, match, reference, root):
    """Resolve a path token: (target, is_markdown_link)."""
    token = match[0]
    # Markdown destinations resolve from their file. Bare/code memory/
    # spellings conventionally describe paths from the project root.
    prefix = text[:match.start()]
    link = bool(re.search(r"\]\(\s*<?$|(?m:^\s{0,3}\[[^\]\n]+\]:\s*<?$)", prefix))
    base = root if token.startswith("memory/") and not link else root / Path(reference).parent
    return Path(os.path.normpath(base / token)), link


def _names_retired(data, reference, retired, root):
    """True when the text names a retired prompt path (resolved, not by basename)."""
    text = data.decode("utf-8")
    paths = {root / name for name in retired}
    return any(_target(text, match, reference, root)[0] in paths
               for match in PROMPT_TOKEN.finditer(text))


def _rewrite(data, reference, moves, root):
    """Rewrite moved targets relative to the reference file, without I/O."""
    text = data.decode("utf-8")
    parent = root / Path(reference).parent

    def moved_path(match):
        token = match[0]
        target, link = _target(text, match, reference, root)
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
        r"(?<![\w./:-])/?(?:[\w.-]+/)*(?:dreams|hoards)/[\w./-]*",
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
    """Plan without writes. Default edits cover the index and Markdown topics;
    references explicitly add active project-relative files. Any per-project
    prompt is planned for retirement. Historical reports, journal entries and
    ciphertext are never rewritten.
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
            len(parts) < 2 or parts[1] not in ("MEMORY.md", "topics")
        ):
            raise MigrationError(f"Historical/immutable reference refused: {name}")
    before = _snapshot(root, refs)
    retired = tuple(name for name in RETIRED_PROMPTS if name in before)
    for name in retired:
        if before[name] is None:
            raise MigrationError(f"Wrong input type: {name}")
        if not _committed(root, name, before[name]):
            raise MigrationError(
                f"Cannot retire {name}: commit it unchanged first, so its local "
                "facts stay recoverable with git show HEAD:<path>")
    legacy_dirs = [name for name in LEGACY_DIRS if name in before]
    if len(legacy_dirs) > 1 or (legacy_dirs and NEW_DIR in before):
        raise MigrationError(f"Coexistence conflict: {', '.join(legacy_dirs + [NEW_DIR])}")
    for name in (*legacy_dirs, NEW_DIR):
        if name in before and before[name] is not None:
            raise MigrationError(f"Wrong input type: {name}")
    moves = [(legacy_dirs[0], NEW_DIR)] if legacy_dirs else []
    targets = list(moves)
    legacy_prompts = [name for name in LEGACY_PROMPTS if name in before]
    if legacy_prompts and not legacy_dirs and NEW_DIR not in before:
        # A project with no reports still needs the new output convention.
        # This changes references only; no absent directory is created/moved.
        targets.append((LEGACY_DIRS[LEGACY_PROMPTS.index(legacy_prompts[0])], NEW_DIR))
    active = {name for name, data in before.items()
              if data is not None and (name == "memory/MEMORY.md" or
                 (name.startswith("memory/topics/") and name.endswith(".md")))}
    active.update(refs)
    edits = {}
    stale = []
    try:
        for name in sorted(active):
            data = before[name]
            if data is None:
                raise MigrationError(f"Reference is not a file: {name}")
            # Already-new projects are an exact no-op: rename rewrites run
            # only when a legacy name is being migrated.
            edited = (_rewrite(data, name, targets, root)
                      if targets or legacy_prompts else data)
            if edited != data:
                edits[name] = edited
            if retired and _names_retired(edited, name, retired, root):
                stale.append(name)
    except UnicodeError as error:
        raise MigrationError(f"Active reference is not UTF-8: {error}") from error
    return MigrationPlan(root, refs, before, tuple(moves), edits, retired, tuple(stale))


def apply_migration(plan):
    """Apply staged edits; undo completed operations on ordinary failures."""
    root = plan.project
    if _snapshot(root, plan.references) != plan.snapshot:
        raise MigrationError("Migration inputs changed since planning")
    if not (plan.moves or plan.edits or plan.retired):
        return
    try:
        stage = Path(tempfile.mkdtemp(prefix=".smelt-migrate-", dir=root))
    except OSError as error:
        raise MigrationError(f"Cannot stage migration: {error}") from error
    undo = []
    failure = None
    residual = []
    try:
        for index, (name, data) in enumerate(plan.edits.items()):
            staged = stage / str(index)
            staged.write_bytes(data)
            os.chmod(staged, (root / name).stat().st_mode & 0o777)
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
        for index, name in enumerate(plan.retired):
            # Retire into the stage so a later failure can restore it.
            os.replace(root / name, stage / f"retired-{index}")
            undo.append((stage / f"retired-{index}", root / name))
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
        epilog="By default, applies the migration: moves legacy report directories, "
               "updates memory/MEMORY.md and Markdown topics, and retires any "
               "per-project prompt. Reports, journal entries and ciphertext retain "
               "their bytes. No Git operations are performed.",
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
        logging.info("%s: %d moves, %d active reference edits, %d retired prompts",
                     "Planned" if args.dry_run else "Applied",
                     len(plan.moves), len(plan.edits), len(plan.retired))
        for name in plan.retired:
            logging.info("Retired prompt: %s (carry its local location facts "
                         "into memory/MEMORY.md; read it with git show HEAD:%s)", name, name)
        for name in plan.stale:
            logging.info("Names a retired prompt: %s", name)
    except MigrationError as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
