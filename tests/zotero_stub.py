"""An offline stand-in for the running Zotero: local API and connector.

It serves, on 127.0.0.1 and an ephemeral port, the slice of the desktop
client's HTTP server that scripts/zotero.py uses: /connector/ping and the
connector POST endpoints, and the read-only local API (/api/, item lists
with itemType filters and paging, single items, file URLs, groups,
collections, itemTypeFields). Item JSON follows the local API's shape
(server_localAPI.js, Zotero 10). Every call is recorded. Nothing here
touches ~/Zotero or a real client.
"""

import json
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ITEM_TYPE_FIELDS = {
    "journalArticle": ["title", "date", "DOI", "ISBN", "url", "extra"],
    "book": ["title", "date", "ISBN", "url", "extra", "publisher"],
}


class StubZotero:
    def __init__(self, account=1):
        self.account = account
        self.items = {"users/0": []}
        self.groups = {}
        self.collections = {}
        self.targets = [{"id": "L1", "name": "My Library", "level": 0}]
        self.api_enabled = True
        self.status = {}
        self.calls = []
        self.on_save = None
        self.server = None

    # -- fixture builders --------------------------------------------------

    def _library(self, prefix):
        if prefix == "users/0":
            return {"type": "user", "id": self.account, "name": "me"}
        gid = int(prefix.split("/")[1])
        return {"type": "group", "id": gid, "name": self.groups[gid]}

    def add_group(self, gid, name, editable=True):
        self.groups[gid] = name
        self.items.setdefault(f"groups/{gid}", [])
        if editable:
            self.targets.append({"id": f"L{100 + gid}", "name": name, "level": 0})

    def add_collection(self, key, name, prefix="users/0", parent=None,
                       target=None, level=1):
        self.collections[(prefix, key)] = {
            "key": key, "data": {"key": key, "name": name,
                                 "parentCollection": parent or False}}
        if target:
            root = next(n for n, t in enumerate(self.targets)
                        if t["id"] == ("L1" if prefix == "users/0"
                                       else f"L{100 + int(prefix.split('/')[1])}"))
            pos = root + 1
            while pos < len(self.targets) and self.targets[pos]["level"] > 0:
                pos += 1
            self.targets.insert(pos, {"id": target, "name": name, "level": level})

    def add_work(self, key, title="", prefix="users/0", item_type="journalArticle",
                 creators=(), trashed=False, **fields):
        data = {"key": key, "itemType": item_type, "title": title,
                "creators": [{"creatorType": "author", "lastName": c}
                             for c in creators], **fields}
        self.items[prefix].append({"key": key, "library": self._library(prefix),
                                   "links": {}, "meta": {}, "data": data,
                                   "_trashed": trashed})

    def add_attachment(self, key, parent=None, *, path=None, filename=None,
                       md5=None, prefix="users/0", link="imported_file",
                       content_type="application/pdf", length=True,
                       raw_path=None, title=""):
        data = {"key": key, "itemType": "attachment", "linkMode": link,
                "contentType": content_type, "title": title}
        if parent:
            data["parentItem"] = parent
        links = {}
        if link.startswith("imported"):
            data["filename"] = filename or (Path(path).name if path else "")
            data["md5"] = md5
            if path:
                links["enclosure"] = {"href": Path(path).as_uri(),
                                      "title": data["filename"]}
                if length:
                    links["enclosure"]["length"] = Path(path).stat().st_size
        elif link == "linked_file":
            data["path"] = raw_path or str(path)
        self.items[prefix].append({"key": key, "library": self._library(prefix),
                                   "links": links, "meta": {}, "data": data,
                                   "_path": path, "_trashed": False})

    # -- server ------------------------------------------------------------

    def start(self):
        stub = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def _reply(self, code, body=b"", ctype="application/json",
                       headers=None):
                if isinstance(body, (dict, list)):
                    body = json.dumps(body).encode()
                elif isinstance(body, str):
                    body = body.encode()
                self.send_response(code)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(body)))
                for name, value in (headers or {}).items():
                    self.send_header(name, str(value))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                url = urllib.parse.urlsplit(self.path)
                query = dict(urllib.parse.parse_qsl(url.query))
                stub.calls.append(("GET", url.path, query))
                if url.path == "/connector/ping":
                    return self._reply(stub.status.get("ping", 200),
                                       "Zotero is running", "text/plain")
                if not url.path.startswith("/api/"):
                    return self._reply(404, "No endpoint found", "text/plain")
                if not stub.api_enabled:
                    return self._reply(403, "Local API is not enabled",
                                       "text/plain")
                code, body, headers = stub.api(url.path[5:], query)
                headers = {"Zotero-API-Version": "3", **(headers or {})}
                ctype = ("text/plain" if isinstance(body, str)
                         else "application/json")
                return self._reply(code, body, ctype, headers)

            def do_POST(self):
                body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
                endpoint = self.path.rsplit("/", 1)[-1]
                stub.calls.append((endpoint, body, dict(self.headers)))
                if endpoint == "getSelectedCollection":
                    return self._reply(stub.status.get(endpoint, 200),
                                       {"libraryID": 1, "targets": stub.targets})
                if endpoint == "saveItems" and stub.on_save:
                    stub.on_save(json.loads(body))
                default = 201 if endpoint in ("saveItems", "saveAttachment") else 200
                return self._reply(stub.status.get(endpoint, default))

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        return f"http://127.0.0.1:{self.server.server_port}"

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()

    # -- local API ---------------------------------------------------------

    def _public(self, item):
        return {k: v for k, v in item.items() if not k.startswith("_")}

    def api(self, path, query):
        path = path.strip("/")
        if path == "":
            return 200, "Nothing to see here.", None
        if path == "itemTypeFields":
            fields = ITEM_TYPE_FIELDS.get(query.get("itemType"), [])
            return 200, [{"field": f, "localized": f} for f in fields], None
        if path == "users/0/groups":
            return 200, [{"id": gid, "data": {"id": gid, "name": name}}
                         for gid, name in self.groups.items()], None
        parts = path.split("/")
        prefix = "/".join(parts[:2])
        rest = parts[2:]
        if parts[0] == "users" and parts[1] not in ("0", str(self.account)):
            suffix = f" or {self.account}" if self.account else ""
            return (400, "Only data for the logged-in user is available "
                    f"locally -- use userID 0{suffix}", None)
        if prefix not in self.items:
            return 404, "Not found", None
        if not rest:
            gid = int(parts[1])
            return 200, {"id": gid, "data": {"id": gid, "name": self.groups[gid]}}, None
        live = [i for i in self.items[prefix] if not i["_trashed"]]
        if rest == ["items"]:
            wanted = query.get("itemType", "")
            if wanted.startswith("-"):
                live = [i for i in live if i["data"]["itemType"] != wanted[1:]]
            elif wanted:
                live = [i for i in live if i["data"]["itemType"] == wanted]
            start = int(query.get("start", 0))
            limit = int(query.get("limit", 0)) or len(live)
            page = [self._public(i) for i in live[start:start + limit]]
            return 200, page, {"Total-Results": len(live)}
        if rest[0] == "items" and len(rest) >= 2:
            item = next((i for i in live if i["key"] == rest[1]), None)
            if item is None:
                return 404, "Not found", None
            if rest[2:] == ["file", "view", "url"]:
                return 200, Path(item["_path"]).as_uri(), None
            return 200, self._public(item), None
        if rest[0] == "collections" and len(rest) == 2:
            coll = self.collections.get((prefix, rest[1]))
            return (200, coll, None) if coll else (404, "Not found", None)
        return 404, "Not found", None
