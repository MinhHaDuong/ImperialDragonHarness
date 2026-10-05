#!/usr/bin/env python3
"""Refuse to launch a runtime whose harness projections are broken (ticket 0983).

A runtime whose projected link dangles does not fail: Claude Code drops the
instructions and hooks it cannot read and still answers (0978's disposable-HOME
probe), Codex runs no guard when ~/.codex/hooks.json dangles, Pi loads no
extension. No hook can report that, because the hook vanishes with the link.
So the check runs in the shell, before the runtime starts: the wrappers in
scripts/shell-init.sh call this script and launch only on exit 0.

The expected projections come from one declared manifest,
adapters/projections.json, never from a glob of what happens to exist: a
required entry that is absent is itself a failure.

Usage: validate-projections.py RUNTIME [--root DIR] [--manifest FILE]
Exit 0: every entry for RUNTIME resolves to its target. Exit 1: at least one
is missing, dangling or foreign; each culprit is named on stderr with the
exact repair (or HOME is unset). Exit 2: usage error.
"""

import argparse
import json
import os
import re
import shlex
import sys
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parent.parent


def expand(spec: str, root: Path) -> Path:
    """Expand a manifest spec using the selected checkout root."""
    if spec == "$IDH_ROOT":
        return root.resolve()
    if spec.startswith("$IDH_ROOT/"):
        return Path(str(root) + spec[len("$IDH_ROOT") :])
    if spec == "~" or spec.startswith("~/"):
        return Path(os.environ["HOME"] + spec[1:])
    raise ValueError(f"manifest spec must start with ~ or $IDH_ROOT: {spec!r}")


def expand_words(command: str, root: Path) -> str:
    """Expand the leading ~ / $IDH_ROOT spec of each word of an installer command."""
    words = []
    for word in command.split():
        if word.startswith(("~/", "$IDH_ROOT")):
            word = shlex.quote(str(expand(word, root)))
        words.append(word)
    return " ".join(words)


def resolved(path: Path):
    """The fully resolved path, or None when it does not resolve to anything."""
    try:
        real = path.resolve(strict=True)
    except (OSError, RuntimeError):
        return None
    return real


def managed_hooks(document):
    """Only harness hooks are registered; RTK is owned by its installer."""
    return {
        event: [b for b in blocks if not any(
            h.get("command") == "rtk hook claude" for h in b.get("hooks", [])
        )]
        for event, blocks in document.get("hooks", {}).items()
    }


# Hook-command translation, moved here when the derivation generator was
# retired (ticket 0887 activation: the adapter plugin became the single hook
# source and settings.shared.json dropped its hooks key). It normalizes the
# hook commands a live settings file may still carry to the plugin launcher
# form, so merge_hooks can recognize an installed predecessor and replace it
# instead of appending a duplicate. Every registered form is recognized, the
# retired pre-portable layout included: an older live file is not an error,
# it is the exact case registration exists to repair.
LAUNCHER = '"${CLAUDE_PLUGIN_ROOT}/bin/idh-hook"'
# `$HOME/.idh/scripts/x.sh a` and `python3 $HOME/.idh/scripts/x.py a`
HARNESS_SCRIPT = re.compile(
    r"^(?:python3\s+)?\$HOME/\.idh/scripts/(?P<name>[\w.-]+)(?P<rest>\s.*)?$"
)
# The fail-loud pre-0982 form: refuse with exit 2 when the ~/.idh pointer is missing,
# else exec the script. Exactly
# `[ -x SCRIPT ] || { echo "MSG" >&2; exit 2; }; exec SCRIPT [args]`:
# anything else in the prefix fails to match and stays unrecognized, so the
# merge reports it instead of silently replacing it.
POINTER_CHECKED = re.compile(
    r'^\[ -x "\$HOME/\.idh/scripts/(?P<name>[\w.-]+)" \]'
    r' \|\| \{ echo "(?:[^"`$\\]|\$HOME\b)*" >&2; exit 2; \}; '
    r'exec "\$HOME/\.idh/scripts/(?P=name)"(?P<rest>\s.*)?$'
)
# The portable fail-loud form the shipped adapters carry today.
PORTABLE_CHECKED = re.compile(
    r'^\[ -x "\$HOME/\.local/bin/idh-hook" \]'
    r' \|\| \{ echo "[^"`$\\]*" >&2; exit 2; \}; '
    r'exec "\$HOME/\.local/bin/idh-hook" (?P<name>[\w.-]+)(?P<rest>\s.*)?$'
)
BARE_LAUNCHER = re.compile(
    r'^"\$HOME/\.local/bin/idh-hook" (?P<name>[\w.-]+)(?P<rest>\s.*)?$'
)
LEGACY_CODEX = re.compile(
    r'^bash "\$HOME/\.(?:idh|claude)/scripts/(?P<name>[\w.-]+)"(?P<rest>\s.*)?$'
)


def translate(command: str) -> str:
    """Map every registered hook-command form onto the plugin launcher."""
    stripped = command.strip()
    for pattern in (PORTABLE_CHECKED, BARE_LAUNCHER, LEGACY_CODEX, POINTER_CHECKED, HARNESS_SCRIPT):
        if (m := pattern.match(stripped)):
            return f"{LAUNCHER} {m.group('name')}{m.group('rest') or ''}"
    return command


def hook_identity(block):
    normalized = json.loads(json.dumps(block))
    for hook in normalized.get("hooks", []):
        if "command" in hook:
            hook["command"] = translate(hook["command"])
    return normalized


def merge_hooks(actual, wanted):
    if not isinstance(actual, dict):
        raise ValueError("configuration must be an object")
    hooks = actual.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError("hooks must be an object")
    for event, blocks in managed_hooks(wanted).items():
        current = hooks.setdefault(event, [])
        if not isinstance(current, list):
            raise ValueError(f"{event} hooks must be a list")
        for block in blocks:
            identity = hook_identity(block)
            updated, found = [], False
            for existing in current:
                if hook_identity(existing) == identity:
                    # Replace only an exact recognized predecessor, keeping
                    # matcher, timeout, and other hook semantics identical.
                    if not found:
                        updated.append(block)
                        found = True
                else:
                    updated.append(existing)
            if not found:
                updated.append(block)
            current[:] = updated
    return actual


def check_entry(entry: dict, root: Path):
    """Return None when the entry is healthy, else (kind, detail, repair)."""
    path = expand(entry["path"], root)
    target = expand(entry["target"], root)
    if entry.get("registration") == "hooks":
        try:
            actual = json.loads(path.read_text())
            wanted = json.loads(target.read_text())
            merged = merge_hooks(json.loads(json.dumps(actual)), wanted)
            if merged == actual:
                return None
            reason = "harness hooks missing"
        except (OSError, ValueError, TypeError, AttributeError) as exc:
            reason = str(exc)
        return ("MISSING", f"{path}: {reason}",
                f"{shlex.quote(str(root / 'bin/idh'))} install")
    q_path, q_target = shlex.quote(str(path)), shlex.quote(str(target))
    link = f"ln -s {q_target} {q_path}"
    inspect = (
        f"inspect {q_path} and preserve its contents; resolve ownership explicitly, "
        f"then rerun {shlex.quote(str(root / 'bin/idh'))} install"
    )
    real_target = resolved(target)
    if real_target is None:
        prefix = f"restore {q_target} (the expected target is gone), then "
    else:
        prefix = ""

    if not path.is_symlink() and not path.exists():
        if not entry["required"]:
            return None
        # The parent may be absent too (~/.codex, ~/.pi/agent/extensions).
        repair = f"mkdir -p {shlex.quote(str(path.parent))} && {link}"
        if entry.get("installer"):
            repair += f"   (or: {expand_words(entry['installer'], root)})"
        return ("MISSING", f"{path} does not exist", prefix + repair)

    real = resolved(path)
    if real is None:
        return (
            "DANGLING",
            f"{path} -> {os.readlink(path)} resolves to nothing",
            prefix + inspect,
        )

    if real_target is not None and real == real_target:
        if entry["path"].startswith("~/.local/bin/") and not os.access(path, os.X_OK):
            return ("UNUSABLE", f"{path} is not executable", f"restore executable mode on {q_target}")
        return None

    if path.is_symlink():
        return ("FOREIGN", f"{path} resolves to {real}, not {target}", prefix + inspect)
    # Existing user resources need an explicit ownership decision, not a
    # command that replaces them or overwrites a fixed backup path.
    return (
        "FOREIGN",
        f"{path} is a real {'directory' if path.is_dir() else 'file'}, not {target}",
        prefix + inspect,
    )


FIELDS = ("path", "target", "runtimes", "required", "why")


class ManifestError(Exception):
    pass


def load_entries(manifest: Path, runtime: str, root=None):
    try:
        entries = json.loads(manifest.read_text())["entries"]
        for e in entries:
            missing = [f for f in FIELDS if f not in e]
            if missing:
                raise ManifestError(
                    f"entry {e.get('path', '?')!r} lacks {', '.join(missing)}"
                )
            if not isinstance(e["required"], bool):
                raise ManifestError(
                    f"entry {e['path']!r}: required must be true or false"
                )
    except ManifestError:
        raise
    except (OSError, UnicodeDecodeError, ValueError, KeyError, TypeError) as exc:
        raise ManifestError(f"{type(exc).__name__}: {exc}") from exc
    expanded = []
    root = root or manifest.resolve().parent.parent
    for entry in entries:
        if entry.get("children"):
            source = expand(entry["target"], root)
            if not source.is_dir():
                raise ManifestError(f"registration source {source} is missing")
            children = source.rglob("*.md") if entry["children"] == "markdown" else source.iterdir()
            for child in sorted(children):
                if child.name.startswith(".") or child.name == "__pycache__":
                    continue
                if not child.is_dir() and child.suffix != ".md":
                    continue
                item = dict(entry)
                item.pop("children")
                suffix = child.relative_to(source).as_posix()
                item["path"] += "/" + suffix
                item["target"] += "/" + suffix
                expanded.append(item)
        else:
            expanded.append(entry)
    entries = list({e["path"]: e for e in expanded}.values())
    runtimes = {r for e in entries for r in e["runtimes"]}
    if runtime is None:  # `idh check`: every entry, operator-only ones included
        return entries
    if runtime not in runtimes:
        raise SystemExit(
            f"validate-projections: unknown runtime {runtime!r} (manifest declares: "
            f"{', '.join(sorted(runtimes))})"
        )
    return [e for e in entries if runtime in e["runtimes"]]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("runtime")
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    ap.add_argument("--manifest", type=Path)
    args = ap.parse_args(argv)
    if not os.environ.get("HOME"):
        print(
            f"idh: refusing to launch {args.runtime}: HOME is unset, so no projection "
            f"can be checked. Set HOME, or launch anyway (logged): "
            f"IDH_SKIP_VALIDATE=1 {args.runtime} ...",
            file=sys.stderr,
        )
        return 1
    root = args.root.absolute()
    manifest = args.manifest or root / "adapters" / "projections.json"

    try:
        entries = load_entries(manifest, args.runtime, root)
    except ManifestError as exc:
        print(
            f"idh: refusing to launch {args.runtime}: manifest {manifest} is unusable "
            f"({exc}); repair: restore adapters/projections.json in the harness "
            f"checkout {shlex.quote(str(root))}. To launch anyway (logged): "
            f"IDH_SKIP_VALIDATE=1 {args.runtime} ...",
            file=sys.stderr,
        )
        return 1
    failures = []
    for entry in entries:
        problem = check_entry(entry, root)
        if problem:
            failures.append((entry, problem))

    if not failures:
        return 0

    err = sys.stderr
    print(
        f"idh: refusing to launch {args.runtime}: {len(failures)} harness "
        f"projection(s) broken (manifest {manifest})",
        file=err,
    )
    for entry, (kind, detail, repair) in failures:
        print(f"  {kind}: {detail}", file=err)
        print(f"    why:    {entry['why']}", file=err)
        print(f"    repair: {repair}", file=err)
    print(
        f"  Run the repair from a plain terminal, then relaunch. To launch anyway "
        f"(logged): IDH_SKIP_VALIDATE=1 {args.runtime} ...",
        file=err,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
