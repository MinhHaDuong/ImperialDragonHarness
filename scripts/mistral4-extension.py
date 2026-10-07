import concurrent.futures
import datetime
import json
import os
import pathlib
import subprocess

arena = pathlib.Path(os.environ.get("ARENA", pathlib.Path.home() / "arena"))
plan = json.loads((arena / "mistral4-extension-plan.json").read_text())
logs = arena / "mistral4-extension-logs"
logs.mkdir(exist_ok=True)


def leg(tid):
    arm = "m"
    name = f"{tid}-{arm}"
    record = arena / "runs" / name / "run.json"
    if record.exists():
        print("PRESERVED", name, flush=True)
    else:
        print("START", name, datetime.datetime.now(datetime.timezone.utc).isoformat(), flush=True)
        with (logs / (name + "-runner.log")).open("w") as out:
            try:
                subprocess.run(
                    ["python3", "runner.py", "run", tid, arm],
                    cwd=arena, stdout=out, stderr=subprocess.STDOUT, timeout=9000,
                )
            except subprocess.TimeoutExpired:
                print("RUNNER TIMEOUT", name, flush=True)
                return
    if not record.exists():
        print("NO RECORD", name, flush=True)
        return
    r = json.loads(record.read_text())
    print("RESULT", name, r.get("verdict"), r.get("seconds"), r.get("cost_usd"), flush=True)
    if r.get("verdict") != "OK":
        return
    for seat in plan["panel"]:
        f = arena / "runs" / name / "judges" / (seat + ".json")
        for attempt in range(2):
            try:
                if f.exists() and json.loads(f.read_text()).get("parsed") is not None:
                    break
                with (logs / (name + "-" + seat + f"-{attempt}.log")).open("w") as out:
                    subprocess.run(
                        ["python3", "judge.py", tid, arm, seat],
                        cwd=arena, stdout=out, stderr=subprocess.STDOUT, timeout=420,
                    )
            except subprocess.TimeoutExpired:
                continue
        print("JUDGE", name, seat, "recorded", f.exists(), flush=True)


with concurrent.futures.ThreadPoolExecutor(max_workers=plan["max_parallel"]) as pool:
    for future in concurrent.futures.as_completed([pool.submit(leg, t) for t in plan["tickets"]]):
        try:
            future.result()
        except Exception as e:
            print("LEG ERROR", type(e).__name__, flush=True)
print("MISTRAL4 EXTENSION COMPLETE", flush=True)
