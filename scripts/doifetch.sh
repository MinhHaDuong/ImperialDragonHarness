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
# Single DOI and ISBN lookups use the Zotero cascade by default. Keep explicit
# source selections and other DOIfetch modes as upstream pass-throughs.
fulltext=false
explicit_source=false
for arg in "$@"; do
    case "$arg" in
        --doi|--doi=*|--isbn|--isbn=*) fulltext=true ;;
        --source|--source=*|--help|--version) explicit_source=true ;;
    esac
done
if [[ "${1:-}" == "--fulltext" ]]; then
    shift
    fulltext=true
elif [[ "$explicit_source" == true ]]; then
    fulltext=false
fi
if [[ "$fulltext" == true ]]; then
    spec="doifetch[shadow] @ ${spec}"
    if ! uvx -q --from "$spec" python -c 'import doifetch, bs4' >/dev/null; then
        echo "doifetch: could not get DOIfetch with its shadow extra; nothing was fetched" >&2
        exit 69
    fi
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
    exec uvx -q --from "$spec" python "$script_dir/fulltext_cascade.py" "$@"
fi
# Get the tool first, so a failed download (uv exits 1, like a failed fetch)
# gets its own code: 69, EX_UNAVAILABLE. Cached after the first run (~0.1 s).
if ! uvx -q --from "$spec" doifetch --help >/dev/null; then
    echo "doifetch: could not get DOIfetch at ${DOIFETCH_REF:0:12} (network or uv); nothing was fetched" >&2
    exit 69
fi
exec uvx -q --from "$spec" doifetch "$@"
