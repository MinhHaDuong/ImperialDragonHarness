"""A worktree-keyed heartbeat shared by the raid gate and its breaker."""

import hashlib
import json
import os
import tempfile
from pathlib import Path


def marker_path(worktree: Path) -> Path:
    digest = hashlib.sha256(os.fsencode(str(worktree.resolve()))).hexdigest()[:20]
    return Path(tempfile.gettempdir()) / "idh-raid-gates" / f"{digest}.json"


def write_marker(path: Path, started: float, heartbeat: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps({"started": started, "heartbeat": heartbeat}))
    os.replace(temporary, path)


def read_marker(path: Path) -> tuple[float, float] | None:
    try:
        data = json.loads(path.read_text())
        return float(data["started"]), float(data["heartbeat"])
    except (OSError, ValueError, KeyError, TypeError):
        return None


def classify(now: float, last_progress: float, gate: tuple[float, float] | None,
             stall_seconds: int, gate_max_seconds: int) -> str:
    if gate is not None:
        started, heartbeat = gate
        if 0 <= now - heartbeat <= 30 and started <= heartbeat:
            return "GATE_TIMEOUT" if now - started > gate_max_seconds else "GATE_RUNNING"
    return "STALL" if now - last_progress > stall_seconds else "ACTIVE"


def evaluate(now: float, state: tuple | None, snapshot: object,
             gate: tuple[float, float] | None, stall_seconds: int,
             gate_max_seconds: int) -> tuple[str, tuple]:
    """One poll of wait mode: fold a worktree snapshot into the progress clock.

    `state` is None on the first poll (the snapshot is the baseline) or the
    tuple returned by the previous call. A changed snapshot, or a gate marker
    that disappeared since the last poll, restarts the stall window.
    """
    previous, was_gating, last_progress = state or (snapshot, False, now)
    gating = classify(now, last_progress, gate, stall_seconds,
                      gate_max_seconds).startswith("GATE")
    if snapshot != previous or (was_gating and not gating):
        last_progress = now
    status = classify(now, last_progress, gate, stall_seconds, gate_max_seconds)
    return status, (snapshot, gating, last_progress)
