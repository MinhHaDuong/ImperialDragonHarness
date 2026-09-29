#!/usr/bin/env python3
"""Rehearse the whole .idh cutover in a disposable HOME (ticket 0985).

Builds a HOME under a fresh temp directory whose native root is a clone of
this repository, re-keyed to the rig's own paths, then drives the operator
command exactly as the live window will: `idh install`, `idh check`,
`idh relocate harness`, `idh relocate harness --rollback`. Every child runs
with HOME set to the rig; nothing is launched against the account's HOME.

The rig mirrors the live layout without copying live content: the native
root's top-level names and the project-store slug names are read from the
account's native root (names only) and recreated as empty placeholders, so
the cutover's classification meets the real census. It also carries two
worktrees with uncommitted work (one inside the checkout, one outside), a
minimal ~/.claude.json keyed by path, and a `systemctl` stub whose timer
state lives in the rig; XDG_RUNTIME_DIR points inside the rig, so even a real
systemctl could not reach the account's user manager.

Run A: cutover, idempotent rerun, rollback; the rollback must restore the
pre-state byte for byte. Run B (with --session): cutover, then one headless
`claude -p` session from the relocated checkout, which must report six
sentinels planted in CLAUDE.md, RTK.md (imported by CLAUDE.md), a rule, a
skill, a SessionStart hook and the project memory; then rollback, reporting
what the session added. Auth for the session is the probe's (scripts/
probe-memory-symlink.py): ANTHROPIC_API_KEY from the keys directory, in the
child's environment only, never printed; no key reads "could not look".

Usage: rehearse-cutover.py [--session] [--keep]
"""

import argparse
import hashlib
import importlib.util
import json
import os
import pwd
import secrets
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ACCOUNT_HOME = Path(pwd.getpwuid(os.getuid()).pw_dir)
LAYOUT = json.loads((REPO / "adapters" / "cutover-layout.json").read_text())
TIMERS_ON = ("claude-refresh.timer", "claude-telemetry-prune.timer")


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, REPO / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PROBE = _load("probe_memory_symlink", "scripts/probe-memory-symlink.py")
slug = PROBE.slug_for


def git(*args, cwd=None) -> str:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    r = subprocess.run(["git", "-c", "user.name=rehearsal", "-c",
                        "user.email=rehearsal@example.invalid", "-c", "commit.gpgsign=false",
                        *args], cwd=cwd, env=env, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout


class Rig:
    def __init__(self, root: Path):
        self.root, self.home = root, root / "home"
        self.old = self.home / LAYOUT["native_root"]
        self.new = self.home / LAYOUT["checkout"]
        live_old = ACCOUNT_HOME / LAYOUT["native_root"]
        self.live_slug, self.rig_slug = slug(live_old), slug(self.old)
        self.home.mkdir(parents=True)
        self.env = {
            "HOME": str(self.home),
            "PATH": f"{root / 'bin'}:/usr/bin:/bin",
            "XDG_RUNTIME_DIR": str(self.home / "run"),
            "LANG": "C.UTF-8",
        }
        (self.home / "run").mkdir(mode=0o700)
        self.sentinels = {k: f"SENT-{secrets.token_hex(6)}" for k in
                          ("claude_md", "rtk_import", "rule", "skill", "hook", "memory")}

    def remap(self, name: str) -> str:
        """A live project slug, re-keyed to the rig's native root."""
        if name == self.live_slug or name.startswith(self.live_slug + "-"):
            return self.rig_slug + name[len(self.live_slug):]
        return name

    def build(self, census: Path | None) -> dict:
        git("clone", "-q", str(REPO), str(self.old))
        self._rekey_tracked_memory()
        self._plant_sentinels()
        counts = self._placeholders(census) if census else {}
        self._native_fixtures()
        self._worktrees()
        self._stub_systemctl()
        self.new.symlink_to(self.old)
        claude_json = self.home / ".claude.json"
        claude_json.write_text(json.dumps({"projects": {
            str(self.old): {"hasTrustDialogAccepted": True},
            str(self.wt_in): {"hasTrustDialogAccepted": True},
            str(self.root / "unrelated"): {},
        }}, indent=2) + "\n")
        claude_json.chmod(0o600)
        return counts

    def _rekey_tracked_memory(self) -> None:
        projects = self.old / "projects"
        for name in sorted(os.listdir(projects)):
            if self.remap(name) != name:
                git("mv", f"projects/{name}", f"projects/{self.remap(name)}", cwd=self.old)
        git("commit", "-qm", "rehearsal: re-key the harness project store to the rig", cwd=self.old)

    def _plant_sentinels(self) -> None:
        s, old = self.sentinels, self.old
        with open(old / "CLAUDE.md", "a") as f:
            f.write(f"\nThe rehearsal CLAUDE.md codeword is {s['claude_md']}.\n")
        with open(old / "RTK.md", "a") as f:
            f.write(f"\nThe rehearsal imported-file codeword is {s['rtk_import']}.\n")
        (old / "rules" / "zz-rehearsal.md").write_text(
            f"# Rehearsal\n\nThe rehearsal rule codeword is {s['rule']}.\n")
        skill = old / "skills" / "rehearsal-sentinel"
        skill.mkdir()
        (skill / "SKILL.md").write_text(
            "---\nname: rehearsal-sentinel\ndescription: Rehearsal sentinel skill. "
            f"Its codeword is {s['skill']}.\n---\n\nNothing to do.\n")
        hook = old / "scripts" / "rehearsal-hook.sh"
        hook.write_text("#!/bin/sh\ntouch \"$HOME/../hook-fired\"\n"
                        f"echo 'The rehearsal session-start hook codeword is {s['hook']}.'\n")
        hook.chmod(0o755)
        mem = old / "projects" / self.rig_slug / "memory"
        mem.mkdir(parents=True, exist_ok=True)
        with open(mem / "MEMORY.md", "a") as f:
            f.write(f"\n- The project codeword is {s['memory']}\n")
        git("add", "-A", cwd=old)
        git("commit", "-qm", "rehearsal: sentinels", cwd=old)

    def _placeholders(self, census: Path) -> dict:
        """Empty stand-ins for every live top-level name and project slug:
        names only, never content."""
        made = {"top": 0, "slugs": 0}
        for name in sorted(os.listdir(census)):
            p = self.old / name
            if name in (".git", ".credentials.json", "settings.json") or os.path.lexists(p):
                continue
            if (census / name).is_dir():
                p.mkdir()
            else:
                p.touch()
            made["top"] += 1
        live_projects = census / "projects"
        if live_projects.is_dir():
            for name in sorted(os.listdir(live_projects)):
                d = self.old / "projects" / self.remap(name)
                d.mkdir(parents=True, exist_ok=True)
                (d / "placeholder.jsonl").touch()
                made["slugs"] += 1
        return made

    def _native_fixtures(self) -> None:
        old = self.old
        (old / "settings.json").write_text(json.dumps({"hooks": {"SessionStart": [{
            "matcher": "", "hooks": [{"type": "command",
                                      "command": '"$HOME/.idh/scripts/rehearsal-hook.sh"'}]}]}},
            indent=2) + "\n")
        (old / "history.jsonl").write_text('{"display": "fixture"}\n')
        (old / "projects" / self.rig_slug / "fixture-transcript.jsonl").write_text("{}\n")
        private = self.home / ".config" / "harness" / "private" / "skills" / "email"
        private.mkdir(parents=True)
        (private / "SKILL.md").write_text("---\nname: email\ndescription: fixture\n---\n")
        if not os.path.lexists(old / "skills" / "email"):
            (old / "skills" / "email").symlink_to(private)

    def _worktrees(self) -> None:
        self.wt_in = self.old / ".claude" / "worktrees" / "rehearsal-in"
        self.wt_out = self.root / "elsewhere" / "rehearsal-out"
        git("worktree", "add", "-q", "-b", "rehearsal-in", str(self.wt_in), cwd=self.old)
        git("worktree", "add", "-q", "-b", "rehearsal-out", str(self.wt_out), cwd=self.old)
        for wt in (self.wt_in, self.wt_out):
            with open(wt / "STATE.md", "a") as f:
                f.write("\nuncommitted rehearsal work\n")

    def _stub_systemctl(self) -> None:
        (self.root / "bin").mkdir()
        self.timer_state = self.root / "timers"
        self.timer_state.mkdir()
        for t in TIMERS_ON:
            (self.timer_state / t).touch()
        self.log = self.root / "systemctl.log"
        stub = self.root / "bin" / "systemctl"
        stub.write_text(f"""#!/bin/sh
echo "$*" >> "{self.log}"
[ "$1" = --user ] && shift
case "$1" in
  is-active) [ -e "{self.timer_state}/$2" ] && {{ echo active; exit 0; }}; echo inactive; exit 3 ;;
  is-enabled) [ -e "{self.timer_state}/$2" ] && echo enabled || echo disabled ;;
  stop) rm -f "{self.timer_state}/$2" ;;
  start) touch "{self.timer_state}/$2" ;;
  enable) [ "$2" = --now ] && touch "{self.timer_state}/$3" ;;
esac
exit 0
""")
        stub.chmod(0o755)

    # --- actions ---------------------------------------------------------

    def run(self, argv, **kw):
        return subprocess.run(argv, env={**self.env, **kw.pop("env", {})},
                              capture_output=True, text=True, timeout=600, **kw)

    def idh(self, *args):
        idh = self.new / "bin" / "idh"
        if not idh.exists():
            idh = self.old / "bin" / "idh"
        return self.run([sys.executable, str(idh), *args])

    def validate(self, runtime, manifest=None):
        extra = ["--manifest", str(manifest)] if manifest else []
        return self.run([sys.executable, str(self.new / "scripts" / "validate-projections.py"),
                         runtime, *extra])

    def snapshot(self) -> dict:
        out = {}
        for base in (self.home, self.root / "elsewhere"):
            for top, dirs, files in os.walk(base):
                for name in dirs + files:
                    p = Path(top) / name
                    rel = p.relative_to(self.root).as_posix()
                    if rel.endswith("/.git/index") or "__pycache__" in rel \
                            or rel.startswith("home/.local/state"):
                        continue
                    st = p.lstat()
                    if stat.S_ISLNK(st.st_mode):
                        out[rel] = ("link", os.readlink(p))
                    elif stat.S_ISDIR(st.st_mode):
                        out[rel] = ("dir", stat.S_IMODE(st.st_mode))
                    else:
                        out[rel] = ("file", stat.S_IMODE(st.st_mode),
                                    hashlib.sha256(p.read_bytes()).hexdigest())
                dirs[:] = [d for d in dirs if not (Path(top) / d).is_symlink()]
        return out

    def session(self, key: str, cwd: Path) -> dict:
        """One headless session from `cwd`; which sentinels came back."""
        (self.root / "hook-fired").unlink(missing_ok=True)
        labels = {"claude_md": "the CLAUDE.md codeword",
                  "rtk_import": "the imported-file codeword",
                  "rule": "the rule codeword", "skill": "the skill codeword",
                  "hook": "the session-start hook codeword",
                  "memory": "the project codeword from your memory"}
        PROBE.PROMPT = ("Your context holds rehearsal codewords. Reply with six lines, in "
                        "this order, each the exact codeword or NONE: "
                        + "; ".join(labels.values()) + ".")
        launch = PROBE._launch(self.home, cwd=cwd, pwd=cwd, key=key)
        if not launch.clean:
            return {"status": f"could not look ({launch.status})"}
        found = {k: PROBE.detect_loaded(launch.stdout, s) for k, s in self.sentinels.items()}
        return {"status": "ok", "found": found,
                "hook_fired": (self.root / "hook-fired").exists()}


def diff(a: dict, b: dict) -> list:
    return sorted(k for k in a.keys() | b.keys() if a.get(k) != b.get(k))


class Report:
    def __init__(self):
        self.rows, self.ok = [], True

    def row(self, label: str, passed, detail: str = "") -> None:
        mark = {True: "PASS", False: "FAIL", None: "----"}[passed]
        if passed is False:
            self.ok = False
        self.rows.append(f"{mark}  {label}{': ' + detail if detail else ''}")
        print(self.rows[-1], flush=True)


def rehearse(rig: Rig, report: Report, session: bool) -> None:
    for step in ("install", "check"):
        r = rig.idh(step)
        report.row(f"pre-state: idh {step}", r.returncode == 0, (r.stderr or "").strip()[-300:])
    pre = rig.snapshot()
    pre_manifest = rig.root / "pre-projections.json"
    shutil.copy2(rig.old / "adapters" / "projections.json", pre_manifest)

    # Run A: cutover, rerun, rollback.
    r = rig.idh("relocate", "harness")
    report.row("A cutover: idh relocate harness", r.returncode == 0,
               (r.stdout + r.stderr).strip().replace("\n", " | ")[-600:])
    if r.returncode:
        return
    for runtime in ("claude", "codex", "pi"):
        v = rig.validate(runtime)
        report.row(f"A validator on the rewritten manifest: {runtime}", v.returncode == 0,
                   v.stderr.strip()[-300:])
    v = rig.validate("claude", pre_manifest)
    report.row("A unrewritten manifest refuses the launch",
               v.returncode == 1 and f"FOREIGN: {rig.old} is a real directory" in v.stderr,
               v.stderr.strip().splitlines()[1].strip() if v.returncode else "it passed")
    layout_ok = (rig.new / ".git").is_dir() and not (rig.old / ".git").exists() and all(
        (rig.old / n).is_symlink() for n in LAYOUT["claude_links"])
    report.row("A layout: checkout at ~/.idh, per-entry links in the native root", layout_ok)
    mem = rig.old / "projects" / slug(rig.new) / "memory"
    report.row("A harness memory renamed to slug(~/.idh) and linked", mem.is_symlink() and
               mem.resolve() == rig.new / "projects" / slug(rig.new) / "memory")
    links = sum(1 for p in (rig.old / "projects").glob("*/memory") if p.is_symlink())
    report.row("A project-memory links in the native root", links > 0, f"{links}")
    keys = set(json.loads((rig.home / ".claude.json").read_text())["projects"])
    wt_in = rig.new / ".claude" / "worktrees" / "rehearsal-in"
    report.row("A ~/.claude.json re-keyed (checkout and worktree only)",
               keys == {str(rig.new), str(wt_in), str(rig.root / "unrelated")}, str(len(keys)))
    for label, wt in (("inside", wt_in), ("outside", rig.wt_out)):
        st = git("status", "--porcelain", cwd=wt)
        report.row(f"A worktree {label} the checkout survives with its WIP", "STATE.md" in st)
    report.row("A no prunable worktree", "prunable" not in git("worktree", "list", cwd=rig.new))
    log = rig.log.read_text()
    paused = all(f"--user stop {t}" in log and f"--user start {t}" in log
                 and log.index(f"--user stop {t}") < log.index(f"--user start {t}")
                 for t in TIMERS_ON)
    report.row("A timers paused, then resumed, by the script", paused and
               set(TIMERS_ON) <= {p.name for p in rig.timer_state.iterdir()})
    post = rig.snapshot()
    r = rig.idh("relocate", "harness")
    report.row("A second cutover is a no-op", r.returncode == 0 and not diff(post, rig.snapshot()))
    r = rig.idh("relocate", "harness", "--rollback")
    report.row("A rollback", r.returncode == 0, (r.stdout + r.stderr).strip()
               .replace("\n", " | ")[-400:])
    changed = diff(pre, rig.snapshot())
    report.row("A after rollback, bytes, modes and link targets match the pre-state",
               not changed, f"{len(pre)} paths compared" + (f"; differ: {changed[:8]}"
                                                            if changed else ""))
    r = rig.idh("relocate", "harness", "--rollback")
    report.row("A second rollback is a no-op", r.returncode == 0 and not diff(pre, rig.snapshot()))

    # Run B: cutover, one real session, rollback.
    if not session:
        report.row("B session sentinels", None, "skipped (pass --session)")
        return
    key = PROBE.resolve_api_key(PROBE.KEY_FILE)
    if shutil.which("claude") is None or key is None:
        report.row("B session sentinels", None, "could not look: no claude or no API key")
        return
    r = rig.idh("relocate", "harness")
    report.row("B cutover", r.returncode == 0)
    v = rig.validate("claude")
    report.row("B validator passes before the first launch", v.returncode == 0)
    report.row(f"B runtime {PROBE._version()}", None)
    # From an unrelated repository, only the native root can supply the
    # instruction, rule, skill and hook sentinels (the checkout's own
    # CLAUDE.md would otherwise load as project instructions), and the
    # harness memory must NOT load there: a negative control. From the
    # checkout, the harness project memory must load through its link.
    work = rig.root / "work"
    PROBE._git_init(work)
    expect = {"work": {k: k != "memory" for k in rig.sentinels},
              "checkout": {"memory": True}}
    for label, cwd in (("work", work), ("checkout", rig.new)):
        result = rig.session(key, cwd)
        if result["status"] != "ok":
            report.row(f"B session from {label}", None, result["status"])
            continue
        for k, want in expect[label].items():
            got = result["found"][k]
            what = "sees" if want else "does not see"
            report.row(f"B session from {label} {what} the {k} sentinel", got == want)
        report.row(f"B session from {label}: SessionStart hook ran (marker file)",
                   result["hook_fired"])
    r = rig.idh("relocate", "harness", "--rollback")
    report.row("B rollback after a real session", r.returncode == 0,
               (r.stdout + r.stderr).strip().replace("\n", " | ")[-400:])
    after = rig.snapshot()
    changed = [k for k in diff(pre, after) if k in pre]
    added = [k for k in diff(pre, after) if k not in pre]
    report.row("B pre-state paths changed by the session", None,
               f"{len(changed)}: " + ", ".join(changed[:12]))
    report.row("B paths the session added", None, f"{len(added)}: " + ", ".join(added[:12]))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--session", action="store_true",
                    help="run B: one real headless claude session (API key, a few cents)")
    ap.add_argument("--keep", action="store_true", help="keep the rig for inspection")
    args = ap.parse_args(argv)
    root = Path(tempfile.mkdtemp(prefix="rehearse-0985-")).resolve()
    root.chmod(0o700)
    if str(root).startswith(str(ACCOUNT_HOME.resolve()) + os.sep):
        print(f"rehearse: refusing a rig inside the account's HOME: {root}", file=sys.stderr)
        return 2
    report = Report()
    try:
        rig = Rig(root)
        census = ACCOUNT_HOME / LAYOUT["native_root"]
        counts = rig.build(census if census.is_dir() else None)
        report.row("rig", None, f"{root} (placeholders from the live census, names only: "
                               f"{counts.get('top', 0)} top-level, {counts.get('slugs', 0)} slugs)")
        rehearse(rig, report, args.session)
    finally:
        if args.keep:
            print(f"rig kept: {root}")
        else:
            shutil.rmtree(root, ignore_errors=True)
    print("rehearsal: " + ("PASS" if report.ok else "FAIL"))
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
