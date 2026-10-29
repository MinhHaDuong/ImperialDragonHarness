#!/usr/bin/env bash
# Run DOIfetch on demand at a pinned ref for the zotero skill (ticket 1343).
#
# Nothing is installed: uv caches the tool after the first run, which needs the
# network. The pin lives here only; bump it after a DOIfetch merge worth taking.
set -euo pipefail

DOIFETCH_REF=3f6507c7d66a43341fe57d8caee4391be00fa367  # DOIfetch PR 1: core is requests only

if ! command -v uvx >/dev/null 2>&1; then
    echo "doifetch: uvx not found; install uv (https://docs.astral.sh/uv/) and retry" >&2
    exit 127
fi
exec uvx --from "git+https://github.com/MinhHaDuong/DOIfetch@${DOIFETCH_REF}" doifetch "$@"
