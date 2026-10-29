#!/usr/bin/env bash
# Run DOIfetch on demand at a pinned ref for the zotero skill (ticket 1343).
#
# Nothing is installed: uv caches the tool after the first run, which needs the
# network. The pin lives here only; bump it after a DOIfetch merge worth taking.
set -euo pipefail

DOIFETCH_REF=v0.2.0  # DOIfetch v0.2.0, annotated unsigned tag c66a2e5 on fc85d31 (author ruling 2026-10-29)

if ! command -v uvx >/dev/null 2>&1; then
    echo "doifetch: uvx not found; install uv (https://docs.astral.sh/uv/) and retry" >&2
    exit 127
fi
spec="git+https://github.com/MinhHaDuong/DOIfetch@${DOIFETCH_REF}"
# Get the tool first, so a failed download (uv exits 1, like a failed fetch)
# gets its own code: 69, EX_UNAVAILABLE. Cached after the first run (~0.1 s).
if ! uvx -q --from "$spec" doifetch --help >/dev/null; then
    echo "doifetch: could not get DOIfetch at ${DOIFETCH_REF:0:12} (network or uv); nothing was fetched" >&2
    exit 69
fi
exec uvx -q --from "$spec" doifetch "$@"
