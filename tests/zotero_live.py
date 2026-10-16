"""A real Zotero desktop client for the tests, on a throwaway profile.

Author decision, 2026-10-16: "In tests up Zotero as a fixture or skip --
no mock". The fixtures here start the installed Zotero, found by the
helper's own launch discovery, with everything it writes under one
temporary directory:

- a fresh profile (`-profile`), whose `user.js` moves the HTTP server to an
  ephemeral port (`extensions.zotero.httpServer.port`), enables or disables
  the local API (`extensions.zotero.httpServer.localAPI.enabled`) and turns
  off sync and updates;
- a fresh data directory (`-datadir`, read by Zotero.DataDirectory);
- HOME, TMPDIR and the XDG directories pointed inside it, and `-no-remote`,
  so the client neither finds nor signals another Zotero. TMPDIR matters:
  Zotero stages its bundled translators in $TMPDIR/zotero, and two clients
  sharing it (two xdist workers, or a test client and the author's Zotero)
  break each other's translator install, after which a connector import
  hangs.

The author's profile, ~/Zotero and a Zotero on port 23119 are never read,
written or contacted. When isolation cannot be guaranteed (a flatpak
launcher, a temporary directory inside the real Zotero directories) or
Zotero cannot run here (no installation, a container, CI, no display),
the fixtures skip with the reason. Test items are created through the real
connector; the tests read them back through the real local API.

Each pytest process (each xdist worker) starts its own clients; they are
stopped and their directories deleted at the end of the session.

`write_launch_wrapper` lays out the same isolation behind a `zotero`
script, for tests that let the helper launch the client itself through its
own discovery and Popen: the script, like a distribution's wrapper, only
adds the throwaway profile, data directory and environment, records its
pid and execs the real binary.
"""

import importlib.util
import json
import os
import shlex
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
START_WAIT = 60.0
DEFAULT_PORT = 23119
# Variables the client needs to reach the display and the session bus; the
# rest of the environment, HOME included, is replaced.
PASSED_ENV = ("PATH", "DISPLAY", "WAYLAND_DISPLAY", "XAUTHORITY",
              "XDG_RUNTIME_DIR", "DBUS_SESSION_BUS_ADDRESS")

_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


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
    command = zi.find_zotero_launcher()
    if command is None:
        return "no Zotero installation found by the helper's launch discovery"
    if len(command) != 1:
        return (f"launcher {' '.join(command)} is not a plain binary: a "
                f"sandboxed client cannot be confined to a throwaway profile")
    home = Path.home()
    tmp = Path(tempfile.gettempdir()).resolve()
    for real in (home / "Zotero", home / ".zotero", home / ".mozilla"):
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


def write_profile(profile: Path, data: Path, port: int, local_api: bool) -> None:
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


def isolated_env(home: Path) -> dict[str, str]:
    env = {k: os.environ[k] for k in PASSED_ENV if k in os.environ}
    env.update(HOME=str(home), TMPDIR=str(home / "tmp"),
               XDG_CONFIG_HOME=str(home / ".config"),
               XDG_DATA_HOME=str(home / ".local" / "share"),
               XDG_CACHE_HOME=str(home / ".cache"), MOZ_NO_REMOTE="1",
               LANG="en_US.UTF-8", LC_ALL="en_US.UTF-8")
    return env


def isolated_command(binary: str, profile: Path, data: Path) -> list[str]:
    return [binary, "-profile", str(profile), "-datadir", str(data), "-no-remote"]


def prepare(root: Path, port: int, local_api: bool = True
            ) -> tuple[Path, Path, Path]:
    """Lay out home, profile and data directory under `root`."""
    home, profile, data = root / "home", root / "profile", root / "data"
    (home / "tmp").mkdir(parents=True)
    data.mkdir(parents=True)
    write_profile(profile, data, port, local_api)
    return home, profile, data


def answers(url: str, timeout: float = 2.0) -> bool:
    """Is the client ready to save? The ping answers before the libraries
    are loaded; getSelectedCollection answers 200 only once they are."""
    try:
        with _OPENER.open(f"{url}/connector/ping", timeout=timeout) as resp:
            if b"Zotero is running" not in resp.read(4096):
                return False
        req = urllib.request.Request(f"{url}/connector/getSelectedCollection",
                                     data=b"{}", method="POST",
                                     headers={"Content-Type": "application/json"})
        with _OPENER.open(req, timeout=timeout) as resp:
            return resp.status == 200
    except (urllib.error.URLError, OSError):
        return False


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
    home, profile, data = prepare(root, port, local_api)
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
    """One running throwaway client: its URL, version and seeding helpers."""

    def __init__(self, root: Path, *, local_api: bool = True) -> None:
        zi = helper_module()
        self.binary = zi.find_zotero_launcher()[0]
        self.version = zotero_version(self.binary)
        self.root = root
        self.port = free_port()
        assert self.port != DEFAULT_PORT
        self.url = f"http://127.0.0.1:{self.port}"
        home, self.profile, self.data = prepare(root, self.port, local_api)
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
        if local_api and not self._items_loaded(started):
            self.stop()
            pytest.skip(f"the throwaway Zotero {self.version} did not load its "
                        f"items within {START_WAIT:.0f} s")
        self.startup = time.monotonic() - started
        # The data directory is the one given: the client did not fall back
        # to a default location.
        if not (self.data / "zotero.sqlite").exists():
            self.stop()
            pytest.skip("the throwaway Zotero ignored -datadir; isolation "
                        "not guaranteed")

    def _items_loaded(self, started: float) -> bool:
        """Wait for the client's initial item load: a local API read is
        answered only once it is done. A connector save that arrives during
        that load can leave it unfinished (Zotero 10.0.6), after which every
        local API read hangs, so no test writes before this returns."""
        try:
            self.get("/api/users/0/items", limit=1,
                     timeout=max(1.0, START_WAIT - (time.monotonic() - started)))
        except (urllib.error.URLError, OSError):
            return False
        return True

    def stop(self) -> None:
        stop_client(self.process)

    # -- reads (straight HTTP, independent of the helper) ------------------

    def get(self, path: str, timeout: float = 60.0, **params) -> object:
        url = f"{self.url}{path}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"Zotero-API-Version": "3"})
        with _OPENER.open(req, timeout=timeout) as resp:
            return json.loads(resp.read())

    def find(self, title: str) -> dict:
        """The one top-level item with this title."""
        hits = self.titled(title)
        assert len(hits) == 1, f"{len(hits)} items titled {title!r}"
        return hits[0]

    def children(self, key: str) -> list[dict]:
        return self.get(f"/api/users/0/items/{key}/children")

    def titled(self, title: str) -> list[dict]:
        """Every top-level item with this title (none, one or several)."""
        return [i for i in self.get("/api/users/0/items/top", q=title)
                if i["data"].get("title") == title]

    def collection_key(self, name: str) -> str:
        """The local API key of the one collection with this name."""
        keys = [c["key"] for c in self.get("/api/users/0/collections")
                if c["data"]["name"] == name]
        assert len(keys) == 1, f"{len(keys)} collections named {name!r}"
        return keys[0]

    # -- writes, through the real connector --------------------------------

    def post(self, endpoint: str, body: bytes, content_type: str,
             headers: dict[str, str] | None = None) -> tuple[int, bytes]:
        req = urllib.request.Request(f"{self.url}/connector/{endpoint}",
                                     data=body, method="POST")
        req.add_header("Content-Type", content_type)
        req.add_header("X-Zotero-Connector-API-Version", "3")
        for name, value in (headers or {}).items():
            req.add_header(name, value)
        try:
            with _OPENER.open(req, timeout=120) as resp:
                return resp.status, resp.read()
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read() or b""

    def save(self, title: str, *, item_type: str = "journalArticle",
             creators: tuple[str, ...] = (), pdf: Path | None = None,
             pdfs: tuple[Path, ...] = (), target: str | None = None,
             **fields) -> str:
        """Create one item (and stored PDFs: `pdf`, then each of `pdfs`) as
        a connector would; its key. Zotero renames each stored file after
        the parent's metadata."""
        session = uuid.uuid4().hex
        item = {"id": "item0", "itemType": item_type, "title": title,
                "creators": [{"creatorType": "author", "lastName": c,
                              "firstName": ""} for c in creators],
                "attachments": [], "notes": [], "tags": [], **fields}
        status, body = self.post("saveItems", json.dumps(
            {"sessionID": session, "uri": "", "items": [item]}).encode(),
            "application/json")
        assert status == 201, (status, body)
        if target:
            status, body = self.post("updateSession", json.dumps(
                {"sessionID": session, "target": target, "tags": []}).encode(),
                "application/json")
            assert status == 200, (status, body)
        for file in ((pdf,) if pdf is not None else ()) + tuple(pdfs):
            meta = {"sessionID": session, "parentItemID": "item0",
                    "title": file.name, "url": file.resolve().as_uri()}
            status, body = self.post("saveAttachment", file.read_bytes(),
                                     "application/pdf",
                                     {"X-Metadata": json.dumps(meta)})
            assert status == 201, (status, body)
        return self.find(title)["key"]

    def collections(self, *names: str) -> dict[str, str]:
        """Create nested collections names[0] > names[1] > ... with a Zotero
        RDF import through the connector; {name: connector target id}.

        The import lands in the collection selected in the client, and the
        client then selects what it imported: successive calls nest.
        """
        return self._import_collections(names, nested=True)

    def twin_collections(self, name: str) -> dict[str, str]:
        """Two sibling collections both called `name`, in one import."""
        return self._import_collections((name, name), nested=False)

    def _import_collections(self, names: tuple[str, ...], nested: bool
                            ) -> dict[str, str]:
        tag = uuid.uuid4().hex[:8]
        parts = []
        for n, name in enumerate(names):
            child = (f'<dcterms:hasPart rdf:resource="#c{n + 1}-{tag}"/>'
                     if nested and n + 1 < len(names) else "")
            parts.append(f'<z:Collection rdf:about="#c{n}-{tag}">'
                         f'<dc:title>{name}</dc:title>{child}</z:Collection>')
        rdf = ('<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"'
               ' xmlns:z="http://www.zotero.org/namespaces/export#"'
               ' xmlns:dc="http://purl.org/dc/elements/1.1/"'
               ' xmlns:dcterms="http://purl.org/dc/terms/">'
               + "".join(parts) + "</rdf:RDF>")
        status, body = self.post(f"import?session={uuid.uuid4().hex}",
                                 rdf.encode(), "text/plain")
        assert status == 201, (status, body)
        status, body = self.post("getSelectedCollection", b"{}",
                                 "application/json")
        targets = json.loads(body)["targets"]
        return {t["name"]: t["id"] for t in targets if t["name"] in names}


class ZoteroFactory:
    """Starts named throwaway clients on demand, one per name per session."""

    def __init__(self, base: Path) -> None:
        self.base = base
        self.clients: dict[str, LiveZotero] = {}

    def __call__(self, name: str = "main", *, local_api: bool = True
                 ) -> LiveZotero:
        if name not in self.clients:
            if reason := why_not_here():
                pytest.skip(reason)
            self.clients[name] = LiveZotero(self.base / name,
                                            local_api=local_api)
        return self.clients[name]

    def close(self) -> None:
        for client in self.clients.values():
            client.stop()
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


@pytest.fixture
def use_live(live_zotero, monkeypatch) -> LiveZotero:
    """Point the helper at the shared throwaway client for one test."""
    monkeypatch.setenv("ZOTERO_CONNECTOR_URL", live_zotero.url)
    return live_zotero


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
