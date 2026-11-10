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
has_output_dir=false
informational=false
for arg in "$@"; do
    case "$arg" in
        --doi|--doi=*|--isbn|--isbn=*) fulltext=true ;;
        --source|--source=*) explicit_source=true ;;
        --help|--version) explicit_source=true; informational=true ;;
        --output-dir|--output-dir=*) has_output_dir=true ;;
    esac
done
if [[ "${1:-}" == "--fulltext" ]]; then
    shift
    fulltext=true
elif [[ "$explicit_source" == true ]]; then
    fulltext=false
fi
# Every fetch names its staging folder: docs/ unless the caller gave one.
# Neither DOIfetch's own default nor this script's is relied on (ticket 1503,
# author ruling 2026-11-10).
if [[ "$has_output_dir" == false && "$informational" == false ]]; then
    set -- "$@" --output-dir docs
fi
if [[ "$fulltext" == true ]]; then
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
    if ! uvx -q --from "$spec" python -c 'import doifetch' >/dev/null; then
        echo "doifetch: could not get DOIfetch; nothing was fetched" >&2
        exit 69
    fi
    open_rc=0
    open_result=$(uvx -q --from "$spec" python "$script_dir/fulltext_cascade.py" --phase open "$@") || open_rc=$?
    if [[ "$open_rc" -ne 1 ]]; then
        printf '%s\n' "$open_result"
        exit "$open_rc"
    fi
    # A valid open result carries the target for the shadow phase; keep the
    # same name even when metadata services answer differently on retry.
    if ! target=$(printf '%s\n' "$open_result" | python3 -c 'import json,sys; print(json.loads(sys.stdin.readlines()[-1])["path"])'); then
        printf '%s\n' "$open_result" >&2
        echo "doifetch: could not read open-phase result; shadow fetch skipped" >&2
        exit 1
    fi
    shadow_spec="doifetch[shadow] @ ${spec}"
    if ! uvx -q --from "$shadow_spec" python -c 'import doifetch, bs4' >/dev/null; then
        printf '%s\n' "$open_result" >&2
        echo "doifetch: open sources failed; could not get DOIfetch shadow extra" >&2
        exit 69
    fi
    exec uvx -q --from "$shadow_spec" python "$script_dir/fulltext_cascade.py" --phase shadow --output-path "$target" "$@"
fi
# Get the tool first, so a failed download (uv exits 1, like a failed fetch)
# gets its own code: 69, EX_UNAVAILABLE. Cached after the first run (~0.1 s).
if ! uvx -q --from "$spec" doifetch --help >/dev/null; then
    echo "doifetch: could not get DOIfetch at ${DOIFETCH_REF:0:12} (network or uv); nothing was fetched" >&2
    exit 69
fi
exec uvx -q --from "$spec" doifetch "$@"
