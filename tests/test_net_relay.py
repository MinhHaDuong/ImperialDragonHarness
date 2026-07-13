"""Round-trip tests for scripts/seat-runner/net-relay.py (ticket 0217).

The relay is the one channel the network-denied reviewer seat reaches out
through, so a byte-forwarding regression would silently break every seat. These
exercise the generic forwarder both ways — the two orientations the seat-runner
actually uses — without podman: a plain TCP echo server on one end, the relay in
between, a client on the other.

Integration-tier: each test spawns the relay as a subprocess.
"""

import socket
import subprocess
import sys
import threading
import time
from collections.abc import Callable
from pathlib import Path

import pytest

RELAY = Path(__file__).resolve().parent.parent / "scripts" / "seat-runner" / "net-relay.py"


def _serve_echo(srv: socket.socket) -> None:
    """Accept connections on srv and echo every byte until each peer closes.

    Shared by the TCP and Unix echo servers — the only difference between them
    is the address family of the listening socket, which the caller sets up.
    """
    while True:
        try:
            conn, _ = srv.accept()
        except OSError:
            return
        with conn:
            while True:
                data = conn.recv(4096)
                if not data:
                    break
                conn.sendall(data)


def _tcp_echo_server() -> tuple[socket.socket, int]:
    """A TCP echo server bound to an ephemeral port. Returns (sock, port)."""
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", 0))
    srv.listen(8)
    port = srv.getsockname()[1]
    threading.Thread(target=_serve_echo, args=(srv,), daemon=True).start()
    return srv, port


def _spawn_relay(listen: str, connect: str) -> subprocess.Popen:
    proc = subprocess.Popen(
        [sys.executable, str(RELAY), "--listen", listen, "--connect", connect],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return proc


def _wait_until(predicate: Callable[[], bool], what: str, timeout: float = 5.0) -> None:
    """Poll predicate until it is true, or fail after timeout seconds."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return
        time.sleep(0.05)
    raise AssertionError(f"{what} never appeared")


def _round_trip(client: socket.socket, payload: bytes) -> bytes:
    """Send payload, half-close the write side, and drain the echoed reply."""
    client.settimeout(5)
    client.sendall(payload)
    client.shutdown(socket.SHUT_WR)
    echoed = b""
    while True:
        chunk = client.recv(4096)
        if not chunk:
            break
        echoed += chunk
    client.close()
    return echoed


def _free_tcp_port() -> int:
    """Pick a concrete free port (the relay's --listen needs an explicit one)."""
    probe = socket.socket()
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()
    return port


@pytest.mark.integration
def test_relay_unix_to_tcp_round_trip(tmp_path):
    """listen unix ⇄ connect tcp — the host-side orientation."""
    srv, port = _tcp_echo_server()
    sock_path = tmp_path / "relay.sock"
    relay = _spawn_relay(f"unix:{sock_path}", f"tcp:127.0.0.1:{port}")
    try:
        _wait_until(sock_path.exists, f"relay socket {sock_path}")
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.connect(str(sock_path))
        assert _round_trip(client, b"ping-through-the-socket") == b"ping-through-the-socket"
    finally:
        relay.terminate()
        srv.close()


@pytest.mark.integration
def test_relay_tcp_to_unix_round_trip(tmp_path):
    """listen tcp ⇄ connect unix — the container-side orientation."""
    # A Unix-domain echo server standing in for the bind-mounted socket.
    echo_path = tmp_path / "echo.sock"
    usrv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    usrv.bind(str(echo_path))
    usrv.listen(8)
    threading.Thread(target=_serve_echo, args=(usrv,), daemon=True).start()

    port = _free_tcp_port()
    relay = _spawn_relay(f"tcp:127.0.0.1:{port}", f"unix:{echo_path}")
    try:
        client: socket.socket | None = None

        def _connected() -> bool:
            nonlocal client
            try:
                client = socket.create_connection(("127.0.0.1", port), timeout=1)
                return True
            except OSError:
                return False

        _wait_until(_connected, "relay TCP listener")
        assert client is not None
        assert _round_trip(client, b"pong-through-the-tcp") == b"pong-through-the-tcp"
    finally:
        relay.terminate()
        usrv.close()
