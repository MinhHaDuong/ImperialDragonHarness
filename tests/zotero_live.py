"""A real Zotero desktop client for the tests, on a throwaway profile.

Author decision, 2026-10-16: "In tests up Zotero as a fixture or skip --
no mock". The fixtures here start the installed Zotero, found by the
helper's own launch discovery, with everything it writes under one
temporary directory:

- a fresh profile (`-profile`), whose `user.js` moves the HTTP server to an
  ephemeral port (`extensions.zotero.httpServer.port`), enables or disables
  the local API (`extensions.zotero.httpServer.localAPI.enabled`) and turns
  off sync and updates, and whose `localAPIKeys.json` holds one local API
  key granted with "Always Allow" (the file Zotero itself writes when the
  user answers its dialog), so writes are authorized without a dialog;
- a fresh data directory (`-datadir`, read by Zotero.DataDirectory);
- HOME, TMPDIR and the XDG directories pointed inside it, and `-no-remote`,
  so the client neither finds nor signals another Zotero. TMPDIR matters:
  Zotero stages its bundled translators in $TMPDIR/zotero, and two clients
  sharing it (two xdist workers, or a test client and the author's Zotero)
  break each other's translator install.

The helper is pointed at the client with ZOTERO_CONNECTOR_URL and at a key
file of its own under the same directory with ZOTERO_LOCAL_KEY_FILE, never
at ~/.config/keys. The author's profile, ~/Zotero and a Zotero on port 23119
are never read, written or contacted. When isolation cannot be guaranteed (a
flatpak launcher, a temporary directory inside the real Zotero directories)
or Zotero cannot run here (no installation, a container, CI, no display),
the fixtures skip with the reason. Test data is created through pyzotero's
local client, the same library the helper uses, and read back through it.

Each pytest process (each xdist worker) starts its own clients; they are
stopped and their directories deleted at the end of the session.

`write_launch_wrapper` lays out the same isolation behind a `zotero`
script, for tests that let the helper launch the client itself through its
own discovery and Popen: the script, like a distribution's wrapper, only
adds the throwaway profile, data directory and environment, records its
pid and execs the real binary.
"""

import atexit
import importlib.util
import json
import os
import secrets
import shlex
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

import httpx2
import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
START_WAIT = 60.0
DEFAULT_PORT = 23119
# The only variable taken from the caller. The author's display, Wayland
# socket, X authority and session bus never reach a throwaway client: it
# draws on a private Xvfb (author's order, 2026-10-16: no Zotero windows or
# key dialogs on the author's screen).
PASSED_ENV = ("PATH",)
_XVFB: subprocess.Popen | None = None
_XVFB_DISPLAY: str | None = None


def private_display() -> str:
    """A private Xvfb display for this test session, started once; skips the
    test when none can be started. Never the caller's DISPLAY."""
    global _XVFB, _XVFB_DISPLAY
    if _XVFB_DISPLAY is not None and _XVFB is not None and _XVFB.poll() is None:
        return _XVFB_DISPLAY
    xvfb = shutil.which("Xvfb")
    if xvfb is None:
        pytest.skip("no Xvfb: a throwaway Zotero never draws on the author's display")
    read_fd, write_fd = os.pipe()
    _XVFB = subprocess.Popen(
        [xvfb, "-displayfd", str(write_fd), "-nolisten", "tcp",
         "-screen", "0", "1280x800x24"],
        pass_fds=(write_fd,), stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True, env={"PATH": os.environ.get("PATH", "")})
    os.close(write_fd)
    with os.fdopen(read_fd) as pipe:
        number = pipe.readline().strip()
    if not number.isdigit():
        stop_xvfb()
        pytest.skip("Xvfb did not report a display number")
    _XVFB_DISPLAY = f":{number}"
    atexit.register(stop_xvfb)
    return _XVFB_DISPLAY


def stop_xvfb() -> None:
    global _XVFB, _XVFB_DISPLAY
    if _XVFB is not None and _XVFB.poll() is None:
        _XVFB.terminate()
        try:
            _XVFB.wait(timeout=10)
        except subprocess.TimeoutExpired:
            _XVFB.kill()
    _XVFB, _XVFB_DISPLAY = None, None


def helper_module():
    """scripts/zotero.py, loaded once (shared with the test modules)."""
    if "zotero_import" not in sys.modules:
        spec = importlib.util.spec_from_file_location("zotero_import",
                                                      SCRIPTS / "zotero.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules["zotero_import"] = module
        spec.loader.exec_module(module)
    return sys.modules["zotero_import"]


def free_port() -> int:
    """An ephemeral loopback port nothing listens on (bound, never contacted)."""
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def why_not_here() -> str | None:
    """Why a real Zotero cannot be started here with guaranteed isolation."""
    zi = helper_module()
    # in_container() also honours ZOTERO_NO_LAUNCH: an unattended run that
    # opts out of launching gets no fixture client either.
    reason = zi.in_container()
    if reason:
        return f"no real Zotero in this environment ({reason})"
    if shutil.which("Xvfb") is None:
        return "no Xvfb: a throwaway Zotero never draws on the author's display"
    command = zi.find_zotero_launcher()
    if command is None:
        return "no Zotero installation found by the helper's launch discovery"
    if len(command) != 1:
        return (f"launcher {' '.join(command)} is not a plain binary: a "
                f"sandboxed client cannot be confined to a throwaway profile")
    home = Path.home()
    tmp = Path(tempfile.gettempdir()).resolve()
    for real in (home / "Zotero", home / ".zotero", home / ".mozilla",
                 home / ".config" / "keys"):
        if tmp == real or real in tmp.parents:
            return f"temporary directory {tmp} lies inside {real}"
    return None


def zotero_version(binary: str) -> str:
    """The client's version from its application.ini."""
    base = Path(binary).resolve().parent
    for ini in (base / "app" / "application.ini", base / "application.ini"):
        if ini.is_file():
            for line in ini.read_text().splitlines():
                if line.startswith("Version="):
                    return line.split("=", 1)[1].strip()
    return "unknown"


def write_profile(profile: Path, data: Path, port: int, local_api: bool,
                  key: str, one_time_key: str | None = None) -> None:
    prefs = {
        "extensions.zotero.httpServer.enabled": True,
        "extensions.zotero.httpServer.port": port,
        "extensions.zotero.httpServer.localAPI.enabled": local_api,
        "extensions.zotero.useDataDir": True,
        "extensions.zotero.dataDir": str(data),
        "extensions.zotero.sync.autoSync": False,
        "extensions.zotero.firstRun2": False,
        "extensions.zotero.firstRunGuidance": False,
        "extensions.zotero.showConnectorVersionWarning": False,
        "extensions.zoteroOpenOfficeIntegration.skipInstallation": True,
        "extensions.zotero.automaticScraperUpdates": False,
        "app.update.enabled": False,
        "app.update.auto": False,
        "intl.locale.requested": "en-US",
    }
    profile.mkdir(parents=True, exist_ok=True)
    (profile / "user.js").write_text("".join(
        f"user_pref({json.dumps(k)}, {json.dumps(v)});\n" for k, v in prefs.items()))
    # The key store Zotero writes when the user answers "Always Allow"
    # (server_localAPI.js): this throwaway client trusts `key` from the start.
    # A `one_time_key` is stored as the "Allow" answer stores one: Zotero
    # consumes it with the first keyed request it accepts.
    keys = [{"key": key, "appName": "tests", "remember": True,
             "createdAt": "2026-10-16T00:00:00Z"}]
    if one_time_key:
        keys.append({"key": one_time_key, "appName": "tests", "remember": False,
                     "createdAt": "2026-10-16T00:00:00Z"})
    (profile / "localAPIKeys.json").write_text(json.dumps({"keys": keys}))


def isolated_env(home: Path) -> dict[str, str]:
    env = {k: os.environ[k] for k in PASSED_ENV if k in os.environ}
    runtime = home / "run"
    runtime.mkdir(mode=0o700, parents=True, exist_ok=True)
    env.update(DISPLAY=private_display(), GDK_BACKEND="x11",
               MOZ_ENABLE_WAYLAND="0", XDG_RUNTIME_DIR=str(runtime),
               HOME=str(home), TMPDIR=str(home / "tmp"),
               XDG_CONFIG_HOME=str(home / ".config"),
               XDG_DATA_HOME=str(home / ".local" / "share"),
               XDG_CACHE_HOME=str(home / ".cache"), MOZ_NO_REMOTE="1",
               LANG="en_US.UTF-8", LC_ALL="en_US.UTF-8")
    return env


def isolated_command(binary: str, profile: Path, data: Path) -> list[str]:
    return [binary, "-profile", str(profile), "-datadir", str(data), "-no-remote"]


def prepare(root: Path, port: int, local_api: bool = True,
            one_time_key: str | None = None) -> tuple[Path, Path, Path, Path]:
    """Lay out home, profile, data directory and the helper's key file under
    `root`; the key file holds the key the profile trusts."""
    home, profile, data = root / "home", root / "profile", root / "data"
    (home / "tmp").mkdir(parents=True)
    data.mkdir(parents=True)
    key = secrets.token_hex(16)
    write_profile(profile, data, port, local_api, key, one_time_key)
    key_file = root / "keys" / "zotero-local.env"
    key_file.parent.mkdir(mode=0o700)
    key_file.write_text(f"ZOTERO_LOCAL_API_KEY={key}\n")
    key_file.chmod(0o600)
    return home, profile, data, key_file


def answers(url: str, timeout: float = 2.0) -> bool:
    """Does the client's local API root answer (any status)?"""
    try:
        httpx2.get(f"{url}/api/", timeout=timeout, trust_env=False)
    except httpx2.TransportError:
        return False
    return True


def stop_pid(pid: int) -> None:
    """Stop a client the helper launched (a session leader), helpers included."""
    for sig, wait in ((signal.SIGTERM, 20.0), (signal.SIGKILL, 5.0)):
        try:
            os.killpg(pid, sig)
        except ProcessLookupError:
            return
        deadline = time.monotonic() + wait
        while time.monotonic() < deadline:
            try:  # the helper's Popen made it a child of this process
                if os.waitpid(pid, os.WNOHANG)[0] == pid:
                    break
            except ChildProcessError:
                try:
                    os.kill(pid, 0)
                except ProcessLookupError:
                    break
            time.sleep(0.1)
        else:
            continue
        try:
            os.killpg(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        return


def write_launch_wrapper(root: Path, binary: str, port: int,
                         local_api: bool = True) -> tuple[Path, Path]:
    """A `zotero` script under root/bin that writes its pid to root/pid and
    execs `binary` on a throwaway profile listening on `port`; (script, pid
    file). Put root/bin first on PATH to have the helper find it."""
    assert port != DEFAULT_PORT
    home, profile, data, _key_file = prepare(root, port, local_api)
    env = " ".join(shlex.quote(f"{k}={v}") for k, v in isolated_env(home).items())
    command = " ".join(shlex.quote(a) for a in isolated_command(binary, profile, data))
    pidfile = root / "pid"
    script = root / "bin" / "zotero"
    script.parent.mkdir(parents=True)
    script.write_text(f"#!/bin/sh\necho $$ > {shlex.quote(str(pidfile))}\n"
                      f"exec /usr/bin/env -i {env} {command}\n")
    script.chmod(0o755)
    return script, pidfile


def stop_client(process: subprocess.Popen) -> None:
    """Stop a client started in its own session, its helpers included."""
    for sig, wait in ((signal.SIGTERM, 20.0), (signal.SIGKILL, 5.0)):
        try:
            os.killpg(process.pid, sig)
        except ProcessLookupError:
            return
        try:
            process.wait(timeout=wait)
        except subprocess.TimeoutExpired:
            continue
        try:  # helpers the client left in its group
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        return


class LiveZotero:
    """One running throwaway client: its URL, key file and seeding helpers."""

    def __init__(self, root: Path, *, local_api: bool = True,
                 one_time_key: bool = False) -> None:
        zi = helper_module()
        self.binary = zi.find_zotero_launcher()[0]
        self.version = zotero_version(self.binary)
        self.root = root
        self.port = free_port()
        assert self.port != DEFAULT_PORT
        self.url = f"http://127.0.0.1:{self.port}"
        # A key the profile trusts for one write only, never in key_file.
        self.one_time_key = secrets.token_hex(16) if one_time_key else None
        home, self.profile, self.data, self.key_file = prepare(
            root, self.port, local_api, self.one_time_key)
        self.log = root / "zotero.log"
        started = time.monotonic()
        with open(self.log, "wb") as log:
            self.process = subprocess.Popen(
                isolated_command(self.binary, self.profile, self.data),
                env=isolated_env(home), stdin=subprocess.DEVNULL, stdout=log,
                stderr=subprocess.STDOUT, start_new_session=True)
        while not answers(self.url):
            if self.process.poll() is not None or (
                    time.monotonic() - started > START_WAIT):
                self.stop()
                pytest.skip(f"the throwaway Zotero {self.version} did not answer "
                            f"on {self.url} within {START_WAIT:.0f} s")
            time.sleep(0.2)
        if local_api:
            # The local API answers reads only once the client's initial item
            # load is done; no test writes before that.
            try:
                self.client().items(limit=1)
            except (httpx2.TransportError, OSError) as exc:
                self.stop()
                pytest.skip(f"the throwaway Zotero {self.version} did not load "
                            f"its items: {exc}")
        self.startup = time.monotonic() - started
        # The data directory is the one given: the client did not fall back
        # to a default location.
        if not (self.data / "zotero.sqlite").exists():
            self.stop()
            pytest.skip("the throwaway Zotero ignored -datadir; isolation "
                        "not guaranteed")

    def stop(self) -> None:
        stop_client(self.process)

    def env(self) -> dict[str, str]:
        """What points the helper at this client and its key file."""
        return {"ZOTERO_CONNECTOR_URL": self.url,
                "ZOTERO_LOCAL_KEY_FILE": str(self.key_file)}

    def client(self):
        """pyzotero's local client for this Zotero's user library, with the
        key this profile trusts."""
        zi = helper_module()
        z = zi.zotero.Zotero(0, "user", local=True,
                             local_api_key=self.key_file.read_text()
                             .strip().split("=", 1)[1],
                             client=zi.http_client())
        z.endpoint = f"{self.url}/api"
        return z

    # -- reads -------------------------------------------------------------

    def item(self, key: str) -> dict:
        return self.client().item(key)

    def find(self, title: str) -> dict:
        """The one top-level item with this title."""
        hits = self.titled(title)
        assert len(hits) == 1, f"{len(hits)} items titled {title!r}"
        return hits[0]

    def children(self, key: str) -> list[dict]:
        return self.client().children(key)

    def titled(self, title: str) -> list[dict]:
        """Every top-level item with this title (none, one or several)."""
        z = self.client()
        return [i for i in z.everything(z.top(q=title, limit=100))
                if i["data"].get("title") == title]

    def versions(self) -> dict[str, int]:
        """Every item's version: a write anywhere changes it."""
        z = self.client()
        return {i["key"]: i["version"] for i in z.everything(z.items(limit=100))}

    # -- writes, through pyzotero's local client ---------------------------

    def save(self, title: str, *, item_type: str = "journalArticle",
             creators: tuple[str, ...] = (), pdf: Path | None = None,
             pdfs: tuple[Path, ...] = (), collection: str | None = None,
             notes: tuple[str, ...] = (), **fields) -> str:
        """Create one item, with stored copies of `pdf` then each of `pdfs`
        and child `notes`; its key."""
        z = self.client()
        item = {"itemType": item_type, "title": title,
                "creators": [{"creatorType": "author", "lastName": c,
                              "firstName": ""} for c in creators],
                "collections": [collection] if collection else [], **fields}
        created = z.create_items([item])
        assert created["successful"], created
        key = created["successful"]["0"]["key"]
        for file in ((pdf,) if pdf is not None else ()) + tuple(pdfs):
            result = z.upload_attachments([{
                "itemType": "attachment", "linkMode": "imported_file",
                "title": file.name, "filename": str(file.resolve()),
                "contentType": "application/pdf", "tags": [], "relations": {}}],
                parentid=key)
            assert result["success"], result
        for note in notes:
            assert z.create_items([{"itemType": "note", "parentItem": key,
                                    "note": note}])["successful"]
        return key

    def collections(self, *names: str) -> list[str]:
        """Nested collections names[0] > names[1] > ...; their keys."""
        z = self.client()
        keys: list[str] = []
        for name in names:
            spec = {"name": name, "parentCollection": keys[-1] if keys else False}
            created = z.create_collections([spec])
            assert created["successful"], created
            keys.append(created["successful"]["0"]["key"])
        return keys


class ZoteroFactory:
    """Starts named throwaway clients on demand, one per name per session."""

    def __init__(self, base: Path) -> None:
        self.base = base
        self.clients: dict[str, LiveZotero] = {}

    def __call__(self, name: str = "main", *, local_api: bool = True,
                 one_time_key: bool = False) -> LiveZotero:
        if name not in self.clients:
            if reason := why_not_here():
                pytest.skip(reason)
            self.clients[name] = LiveZotero(self.base / name,
                                            local_api=local_api,
                                            one_time_key=one_time_key)
        return self.clients[name]

    def close(self) -> None:
        for client in self.clients.values():
            client.stop()
        stop_xvfb()
        shutil.rmtree(self.base, ignore_errors=True)


@pytest.fixture(scope="session")
def zotero_factory():
    base = Path(tempfile.mkdtemp(prefix="zotero-fixture-"))
    factory = ZoteroFactory(base)
    yield factory
    factory.close()


@pytest.fixture(scope="session")
def live_zotero(zotero_factory) -> LiveZotero:
    """The shared throwaway client, local API on. Tests seed it with their
    own unique titles and assert only on what they seeded."""
    return zotero_factory("main")


@pytest.fixture(scope="session")
def api_off_zotero(zotero_factory) -> LiveZotero:
    """A throwaway client whose local API is disabled, as Zotero ships."""
    return zotero_factory("api_off", local_api=False)


@pytest.fixture(scope="session")
def zotero_binary() -> str:
    """The real client binary the helper's discovery finds, for a launch
    wrapper; skips where a throwaway client cannot run. Session-scoped, so
    it sees the shell's environment, not a test's ZOTERO_NO_LAUNCH."""
    if reason := why_not_here():
        pytest.skip(reason)
    return helper_module().find_zotero_launcher()[0]


def point_helper_at(zotero: LiveZotero, monkeypatch) -> LiveZotero:
    for name, value in zotero.env().items():
        monkeypatch.setenv(name, value)
    return zotero


@pytest.fixture
def use_live(live_zotero, monkeypatch) -> LiveZotero:
    """Point the helper at the shared throwaway client for one test."""
    return point_helper_at(live_zotero, monkeypatch)


def unique(text: str = "Work") -> str:
    """A string no other test uses, for a library shared across tests."""
    return f"{text} {uuid.uuid4().hex[:10]}"


_LETTERS = str.maketrans("0123456789", "ghijklmnop")


def unique_title(words: int = 4) -> str:
    """A title sharing no word with any other test's title.

    The duplicate guard scores title-word overlap, so two titles with a
    common stem ("Paper 1a2b", "Paper 3c4d") already read as a weak match;
    every word here is random letters.
    """
    return " ".join(uuid.uuid4().hex[:9].translate(_LETTERS).capitalize()
                    for _ in range(words))
