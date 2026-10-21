"""Pure helpers of the parallel local CI runner (ticket 1158).

The act/podman runs themselves are opt-in elsewhere; these check the
concurrency rule and the per-runner workflow name that prevents container-name
clashes between two runners on one host.
"""

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMMON = ROOT / "ci-local" / "common.sh"


def _bash(script: str, **env) -> str:
    out = subprocess.run(
        ["bash", "-c", f". {COMMON}; {script}"],
        capture_output=True, text=True, check=True, env={"PATH": "/usr/bin:/bin", **env},
    )
    return out.stdout.strip()


def test_concurrency_is_min_of_jobs_and_half_the_threads():
    assert _bash("concurrency 10", LOCAL_CI_CONCURRENCY="12") == "10"
    assert _bash("concurrency 20", LOCAL_CI_CONCURRENCY="12") == "12"
    assert _bash("concurrency 3", LOCAL_CI_CONCURRENCY="0") == "1"
    half = int(_bash("echo $(( $(nproc) / 2 ))"))
    assert _bash("concurrency 1000") == str(max(half, 1))


def test_pool_runs_every_item_and_counts_failures(tmp_path):
    script = (
        f'f() {{ [ "$1" != b ] && echo "$1" >> {tmp_path}/seen; }}; '
        "run_pool 2 f a b c d; echo $pool_failed"
    )
    assert _bash(script) == "1"
    assert sorted((tmp_path / "seen").read_text().split()) == ["a", "c", "d"]


def test_tagged_workflow_renames_only_the_workflow(tmp_path):
    src = tmp_path / "CI.yml"
    src.write_text("name: CI\non: push\njobs:\n  a:\n    name: keep\n")
    dst = tmp_path / "out.yml"
    _bash(f"tagged_workflow {src} {dst} r42")
    assert dst.read_text() == "name: CI-r42\non: push\njobs:\n  a:\n    name: keep\n"
