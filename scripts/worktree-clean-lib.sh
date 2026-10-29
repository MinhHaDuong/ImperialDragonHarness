#!/usr/bin/env bash
set -euo pipefail
# Sourced by worktree-gc.sh and worktree-exit-preflight.sh: one definition of
# what a worktree may hold and still be removed without losing work.
#
# worktree_residue <path> prints, one per line, every status entry that
# removing the tree would destroy and that is not disposable: anything
# modified, staged or untracked, and any ignored path except regenerable
# caches (the root .venv/, rebuilt from the lock, tool caches anywhere, and
# the *.egg-info/ setuptools rebuilds on every `uv run`) and .tmp/ (its own
# guard decides). Git prints an ignored directory as one `!! build/` entry, so
# that entry is expanded: only its lib*, bdist.* and temp.* children (setuptools
# output) are tolerated, a hand-made build/notes.txt stays residue. An untracked
# root .venv holding a regular pyvenv.cfg is tolerated too, provided its
# top level holds only usual venv entries (pyvenv.cfg, bin, Scripts, lib, lib64,
# include, share, .gitignore, CACHEDIR.TAG); any other entry is residue and the
# whole .venv is kept. worktree_scrub deletes it, since git refuses to remove a
# tree holding untracked files. A build/ child (lib*, bdist.*, temp.*) is
# regenerable only when every file in it looks like build output: extension
# py pyc so pyd pyi typed o a c h, or a basename that some tracked file has
# (package data copied by setuptools); else the child is residue. Symlinks
# inside are never build output. Ignored files count: a repo may ignore `*`, and
# `git worktree remove` deletes them. --no-optional-locks keeps the status
# from rewriting the index, which would restart the tree's idle clock.
# Returns 1 when git cannot answer (an unreadable tree is never "clean").
# _build_child_regenerable <name>: a setuptools output directory name.
_build_child_regenerable() {
    case "$1" in lib|lib.*|bdist.*|temp.*) return 0 ;; esac
    return 1
}

# _venv_disposable <path>: the root .venv is a real directory with a regular
# pyvenv.cfg (venv, virtualenv and uv all write it) and nothing in it is tracked.
_venv_disposable() {
    local v="$1/.venv" tracked
    [ -d "$v" ] && [ ! -L "$v" ] && [ -f "$v/pyvenv.cfg" ] && [ ! -L "$v/pyvenv.cfg" ] || return 1
    tracked=$(git -C "$1" ls-files -- .venv 2>/dev/null) || return 1
    [ -z "$tracked" ] || return 1
    local e
    for e in "$v"/* "$v"/.[!.]*; do
        [ -e "$e" ] || [ -L "$e" ] || continue
        case "${e##*/}" in
            pyvenv.cfg|bin|Scripts|lib|lib64|include|share|.gitignore|CACHEDIR.TAG) ;;
            *) return 1 ;;
        esac
    done
}

# _build_child_disposable <path> <name>: build/<name> is a real directory whose
# files all look like build output (see header); symlinks disqualify it.
_build_child_disposable() {
    local d="$1/build/$2" f base names
    [ -d "$d" ] && [ ! -L "$d" ] || return 1
    [ -z "$(find "$d" -type l -print -quit)" ] || return 1
    names=$(git -C "$1" ls-files 2>/dev/null | sed 's|.*/||') || return 1
    while IFS= read -r -d '' f; do
        base="${f##*/}"
        case "$base" in
            *.py|*.pyc|*.so|*.pyd|*.pyi|*.typed|typed|*.o|*.a|*.c|*.h) continue ;;
        esac
        printf '%s\n' "$names" | grep -qxF -- "$base" || return 1
    done < <(find "$d" -type f -print0)
    return 0
}

worktree_residue() {
    local out line p c name venv_ok=0
    _venv_disposable "$1" && venv_ok=1
    out=$(git -C "$1" --no-optional-locks status --porcelain=v1 \
        --untracked-files=all --ignored=matching 2>/dev/null) || return 1
    while IFS= read -r line; do
        [ -z "$line" ] && continue
        p="${line:3}"
        case "$line" in
            "?? "*)
                case "/$p" in
                    /.venv/*) [ "$venv_ok" -eq 1 ] && continue ;;
                esac ;;
            "!! "*)
                if [ "$p" = "build/" ] && [ ! -L "$1/build" ]; then
                    for c in "$1"/build/* "$1"/build/.[!.]*; do
                        [ -e "$c" ] || [ -L "$c" ] || continue
                        name="${c##*/}"
                        if _build_child_regenerable "$name" && _build_child_disposable "$1" "$name"; then continue; fi
                        if [ -d "$c" ] && [ ! -L "$c" ]; then printf '!! build/%s/\n' "$name"
                        else printf '!! build/%s\n' "$name"; fi
                    done
                    continue
                fi
                case "/$p" in
                    /.tmp/*|/.venv/*|*/__pycache__/*|*/.pytest_cache/*|*/.ruff_cache/*|*/.mypy_cache/*|*.egg-info/*) continue ;;
                esac ;;
        esac
        printf '%s\n' "$line"
    done <<<"$out"
    return 0
}

# worktree_scrub <path>: delete what worktree_residue tolerates but git would
# refuse to remove (untracked): the recognised root .venv, and untracked and ignored
# root build/lib*, bdist.*, temp.* (never through a symlinked build/).
worktree_scrub() {
    local c name tracked
    if _venv_disposable "$1"; then rm -rf -- "$1/.venv"; fi
    [ -d "$1/build" ] && [ ! -L "$1/build" ] || return 0
    for c in "$1"/build/*; do
        [ -d "$c" ] && [ ! -L "$c" ] || continue
        name="${c##*/}"
        _build_child_regenerable "$name" || continue
        _build_child_disposable "$1" "$name" || continue
        tracked=$(git -C "$1" ls-files -- "build/$name") || continue
        [ -z "$tracked" ] || continue
        # Unignored output is untracked work in git's eyes: residue reports it, never the scrub.
        git -C "$1" check-ignore -q -- "build/$name/" || continue
        rm -rf -- "$c"
    done
    rmdir "$1/build" 2>/dev/null || true
    return 0
}

# ownerless_tree_clean <path>: true when worktree_residue finds nothing.
ownerless_tree_clean() {
    local residue
    residue=$(worktree_residue "$1") || return 1
    [ -z "$residue" ]
}
