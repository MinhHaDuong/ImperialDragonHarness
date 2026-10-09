"""Run a command and, on failure, raise with its stderr and stdout.

`subprocess.run(..., capture_output=True, check=True)` raises
CalledProcessError whose message omits the captured output, so a flake in a
fixture command is undiagnosable from the CI log. `run_checked` keeps the same
contract (returns the CompletedProcess) but the failure names the command,
return code, stderr and stdout.
"""

import subprocess

from child_env import child_env


def run_checked(cmd, **kwargs) -> subprocess.CompletedProcess:
    env = kwargs.pop("env", None) or child_env()
    kwargs.setdefault("text", True)
    kwargs["capture_output"] = True
    result = subprocess.run(cmd, env=env, **kwargs)
    if result.returncode != 0:
        raise RuntimeError(
            f"command failed (exit {result.returncode}): {cmd!r}\n"
            f"--- stderr ---\n{result.stderr}\n--- stdout ---\n{result.stdout}"
        )
    return result
