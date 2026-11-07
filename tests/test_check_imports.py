"""Bounded controls for the doctor's instrument; no live-tree dependency gate."""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/check_imports.py"
SPEC = importlib.util.spec_from_file_location("check_imports", SCRIPT)
ci = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ci)


def test_direct_import_controls_and_no_execution(tmp_path):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "sibling.py").write_text("")
    path = scripts / "sample.py"
    path.write_text("import json\nimport sibling\ndef optional():\n    import unknown_sdk\nraise RuntimeError('must not execute')\n")
    report = ci.inspect_files([path], tmp_path)
    assert len(report["files"]) == 1
    item = report["files"][0]
    assert item["status"] == "inspected"
    assert item["perimeter"] == "harness-tool"
    assert [(r["module"], r["kind"], r["line"]) for r in item["imports"]] == [
        ("json", "stdlib", 1), ("sibling", "local", 2), ("unknown_sdk", "third-party-candidate", 4)]
    assert "transitive" in " ".join(report["limits"])


def test_local_package_and_relative_import(tmp_path):
    package = tmp_path / "pkg"
    package.mkdir()
    (package / "__init__.py").write_text("")
    path = tmp_path / "sample.py"
    path.write_text("from pkg import value\nfrom . import peer\n")
    rows = ci.inspect_files([path], tmp_path)["files"][0]["imports"]
    assert [r["kind"] for r in rows] == ["local", "local"]
    assert all(r["evidence"] for r in rows)


def test_local_roots_are_explicit_and_file_is_not_its_own_module(tmp_path):
    libs = tmp_path / "lib"
    libs.mkdir()
    (libs / "external_local.py").write_text("")
    path = tmp_path / "json.py"
    path.write_text("import json\nimport external_local\n")
    report = ci.inspect_files([path], tmp_path, [libs])
    assert [r["kind"] for r in report["files"][0]["imports"]] == ["stdlib", "local"]


def test_dynamic_import_is_limited_and_bundled_perimeter(tmp_path):
    path = tmp_path / "skills" / "example" / "helper.py"
    path.parent.mkdir(parents=True)
    path.write_text("import importlib\nimportlib.import_module(name)\n__import__(name)\n")
    item = ci.inspect_files([path], tmp_path)["files"][0]
    assert item["perimeter"] == "bundled-helper"
    assert item["dynamic_import_lines"] == [2, 3]
    assert any("dynamic" in s.lower() for s in item["limits"])


def test_missing_and_invalid_sources_are_unavailable(tmp_path):
    bad = tmp_path / "bad.py"
    bad.write_text("def broken(:\n")
    report = ci.inspect_files([tmp_path / "missing.py", bad], tmp_path)
    assert [r["status"] for r in report["files"]] == ["unavailable", "unavailable"]
    assert all(r["reason"] for r in report["files"])
    assert all("imports" not in r for r in report["files"])


@pytest.mark.integration
def test_cli_is_instrument_even_with_findings_or_missing_input(tmp_path):
    path = tmp_path / "sample.py"
    path.write_text("import unknown_sdk\n")
    result = subprocess.run([sys.executable, str(SCRIPT), "--root", str(tmp_path),
                             str(path), str(tmp_path / "missing.py")], capture_output=True, text=True)
    assert result.returncode == 0
    report = json.loads(result.stdout)
    assert report["files"][0]["imports"][0]["kind"] == "third-party-candidate"
    assert report["files"][1]["status"] == "unavailable"
