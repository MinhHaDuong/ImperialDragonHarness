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


def test_pool_failure_count_is_exact_over_many_short_items(tmp_path):
    # The count comes from one status file per item, not from wait -n's status, which
    # can read 127 when jobs end together and over-reported failures on a loaded host.
    script = (
        "f() { sleep 0.0$((RANDOM % 3)); case $1 in 3|7|11|19) return 1;; esac; }; "
        "for r in $(seq 10); do run_pool 4 f $(seq 24); echo $pool_failed; done | sort | uniq -c"
    )
    assert _bash(script).split() == ["10", "4"]


def test_pool_keeps_errexit_live_inside_the_pooled_function(tmp_path):
    # Callers run under set -e; a failing command mid-body must stop the function.
    script = (
        f'set -e; f() {{ false; echo reached >> {tmp_path}/seen; }}; '
        "run_pool 2 f a; echo $pool_failed"
    )
    assert _bash(script) == "1"
    assert not (tmp_path / "seen").exists()


def test_pool_counts_a_job_killed_before_it_wrote_its_status():
    script = (
        "f() { case $1 in 2) kill -9 $BASHPID;; 3) return 1;; esac; }; "
        "run_pool 4 f 1 2 3 4; echo $pool_failed"
    )
    assert _bash(script) == "2"


def test_pool_with_no_items_fails_nothing():
    assert _bash("pool_failed=9; run_pool 4 true; echo $pool_failed") == "0"


def test_pool_does_not_wait_for_the_callers_other_background_jobs(tmp_path):
    # The podman service is a background job of the caller and must outlive the pool.
    script = (
        "sleep 30 & svc=$!; f() { :; }; "
        "start=$SECONDS; run_pool 2 f a b c d; "
        "echo $((SECONDS - start)); kill $svc"
    )
    assert int(_bash(script)) < 10


def test_tagged_workflow_renames_only_the_workflow(tmp_path):
    src = tmp_path / "CI.yml"
    src.write_text("name: CI\non: push\njobs:\n  a:\n    name: keep\n")
    dst = tmp_path / "out.yml"
    _bash(f"tagged_workflow {src} {dst} r42")
    assert dst.read_text() == "name: CI-r42\non: push\njobs:\n  a:\n    name: keep\n"


def test_dedupe_args_keeps_first_occurrence_in_order():
    assert _bash("dedupe_args b a b c a").split() == ["b", "a", "c"]
    assert _bash("dedupe_args") == ""


def test_kill_groups_reaches_the_whole_group(tmp_path):
    script = (
        f"work={tmp_path}; "
        f"group_run j bash -c 'sleep 30 & echo $! > {tmp_path}/child; wait' & "
        f"for _ in $(seq 50); do [ -s {tmp_path}/child ] && break; sleep 0.1; done; "
        "kill_groups; wait; "
        f"sleep 0.2; kill -0 $(cat {tmp_path}/child) 2>/dev/null && echo alive || echo dead"
    )
    assert _bash(script) == "dead"
