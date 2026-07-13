#!/usr/bin/env python3
"""Generic byte forwarder between a Unix-domain socket and a TCP endpoint.

Listens on one address; for every accepted connection it opens a fresh
connection to the target and pumps raw bytes both ways until either side
closes. Address syntax (both --listen and --connect):

    unix:/path/to/socket
    tcp:HOST:PORT          (a bare HOST:PORT is also accepted)

The relay understands no protocol — it moves bytes. The SAME forwarder serves
both ends of the seat-runner sandbox (ticket 0217): host-side it listens on a
Unix socket and connects to the model endpoint (TCP); container-side it listens
on loopback TCP and connects to the bind-mounted Unix socket. Under
`--network=none` the container reaches the endpoint through that one socket —
a filesystem object, not a network route — and nothing else.
"""

import argparse
import os
import socket
import threading


def parse(spec: str):
    if spec.startswith("unix:"):
        return socket.AF_UNIX, spec[len("unix:") :]
    body = spec[len("tcp:") :] if spec.startswith("tcp:") else spec
    host, port = body.rsplit(":", 1)
    return socket.AF_INET, (host, int(port))


def make_listener(spec: str) -> socket.socket:
    fam, addr = parse(spec)
    s = socket.socket(fam, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    if fam == socket.AF_UNIX and os.path.exists(addr):
        os.unlink(addr)
    s.bind(addr)
    s.listen(64)
    return s


def connect(spec: str) -> socket.socket:
    fam, addr = parse(spec)
    s = socket.socket(fam, socket.SOCK_STREAM)
    s.connect(addr)
    return s


def pump(src: socket.socket, dst: socket.socket) -> None:
    """Forward src→dst until src closes, then half-close dst's write side.

    Half-close (SHUT_WR) propagates EOF downstream without tearing down the
    reverse direction, so a client that stops sending its request does not
    truncate the response still arriving on the other pump.
    """
    try:
        while True:
            data = src.recv(65536)
            if not data:
                break
            dst.sendall(data)
    except OSError:
        pass
    finally:
        try:
            dst.shutdown(socket.SHUT_WR)
        except OSError:
            pass


def handle(client: socket.socket, target_spec: str) -> None:
    try:
        upstream = connect(target_spec)
    except OSError:
        client.close()
        return
    t = threading.Thread(target=pump, args=(client, upstream), daemon=True)
    t.start()
    pump(upstream, client)
    t.join()
    for s in (client, upstream):
        try:
            s.close()
        except OSError:
            pass


def main() -> None:
    ap = argparse.ArgumentParser(description="seat-runner network relay")
    ap.add_argument("--listen", required=True, help="unix:PATH or tcp:HOST:PORT")
    ap.add_argument("--connect", required=True, help="unix:PATH or tcp:HOST:PORT")
    args = ap.parse_args()
    listener = make_listener(args.listen)
    while True:
        client, _ = listener.accept()
        threading.Thread(
            target=handle, args=(client, args.connect), daemon=True
        ).start()


if __name__ == "__main__":
    main()
