"""Inspect foreign blockers and release an asker after result verification."""

import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote, urlparse


def headers(text, name):
    return re.findall(rf"^{re.escape(name)}: (.+)$", text.split("--- log ---")[0], re.M)


def project_root(project):
    """Relative sibling references belong to the repository, also in worktrees."""
    result = subprocess.run(
        ["git", "-C", str(project), "rev-parse", "--path-format=absolute", "--git-common-dir"],
        capture_output=True, text=True,
    )
    return Path(result.stdout.strip()).parent if result.returncode == 0 else project


def find_ticket(project, number):
    matches = list((project / "tickets").glob(f"{number}-*.erg"))
    matches += list((project / "tickets/closed").glob(f"{number}-*.erg"))
    if len(matches) != 1:
        raise ValueError(f"expected one ticket {number} in {project}, found {len(matches)}")
    return matches[0]


def inspect_reference(project, reference):
    result = {"reference": reference, "state": "unavailable"}
    try:
        uri = urlparse(reference)
        if uri.scheme and (uri.scheme != "file" or uri.netloc not in ("", "localhost")):
            raise ValueError("only local sibling paths and file URIs are supported")
        path = Path(unquote(uri.path) if uri.scheme else reference)
        if not path.is_absolute():
            path = project_root(project) / path
        path = path.resolve()
        match = re.fullmatch(r"(\d{4})(?:-[^/]+\.erg)?", path.name)
        if not match:
            raise ValueError("reference must end in a four-digit ticket ID or ticket filename")
        root = path.parent
        if root.name == "closed":
            root = root.parent
        if root.name == "tickets":
            root = root.parent
        target = find_ticket(root, match[1])
        text = target.read_text()
        closed = headers(text, "Closed")
        replacement = headers(text, "Superseded-by")
        state = "closed" if closed or target.parent.name == "closed" else "open"
        if replacement:
            state = "replaced"
        commit = subprocess.run(
            ["git", "-C", str(root), "log", "--follow", "-1", "--format=%H", "-G", "^Closed:",
             "--", str(target)],
            capture_output=True, text=True,
        )
        result.update(state=state, receiver=str(root), ticket=match[1], path=str(target),
                      closure=closed, replacement=replacement, result=text,
                      commit=commit.stdout.strip() or "uncommitted/unavailable")
    except (OSError, ValueError) as error:
        result["error"] = str(error)
    return result


def release(project, number, reference, verified_result):
    path = find_ticket(project, number)
    text = path.read_text()
    if reference not in headers(text, "Blocked-by"):
        raise ValueError("asker does not carry that Blocked-by reference")
    report = inspect_reference(project, reference)
    if report["state"] != "closed":
        raise ValueError(f"dependency is {report['state']}; keep asker parked")
    if report["commit"] == "uncommitted/unavailable":
        raise ValueError("closure commit unavailable; keep asker parked and inspect receiver history")
    head, tail = text.split("--- log ---", 1)
    head = "\n".join(line for line in head.split("\n")
                     if line != f"Blocked-by: {reference}")
    if not headers(head, "Blocked-by"):
        head = "\n".join(line for line in head.split("\n") if line != "Label: deferred")
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    entry = (f"{stamp} molt note unblocked by {report['receiver']} {report['ticket']}, "
             f"closed in {report['commit']}; verified result: {verified_result}\n")
    log, body = tail.split("--- body ---", 1)
    path.write_text(head + "--- log ---" + log.rstrip() + "\n" + entry + "\n--- body ---" + body)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--release")
    parser.add_argument("--reference")
    parser.add_argument("--verified-result")
    args = parser.parse_args()
    project = Path(args.project).resolve()
    if args.release:
        if not args.reference or not args.verified_result or "\n" in args.verified_result:
            parser.error("release requires --reference and a one-line --verified-result assessment")
        try:
            reports = [release(project, args.release, args.reference, args.verified_result)]
        except (OSError, ValueError) as error:
            parser.error(str(error))
    else:
        reports = []
        for path in sorted((project / "tickets").glob("[0-9][0-9][0-9][0-9]-*.erg")):
            text = path.read_text()
            if "deferred" not in headers(text, "Label") or headers(text, "Closed"):
                continue
            for reference in headers(text, "Blocked-by"):
                if "/" in reference:
                    reports.append({"asker": str(path), **inspect_reference(project, reference)})
    sys.stdout.write(json.dumps(reports, indent=2) + "\n")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    main()
