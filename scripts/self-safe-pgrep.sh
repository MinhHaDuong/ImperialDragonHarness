#!/bin/sh
# pgrep/pkill wrapper (ticket 1216). Projected as ~/.local/bin/pgrep and
# ~/.local/bin/pkill; the tool run is the basename of the name it was called by.
# A `pgrep -f PATTERN` inside a shell whose own command line holds PATTERN
# matches that shell, so a wait loop never sees the job end and `pkill -f` can
# kill its caller. procps-ng >= 4.0 has -A (--ignore-ancestors), which fixes
# both; older procps lacks it, so the wrapper passes through unchanged there.
# It never execs itself: the real tool is the first PATH entry that is not
# this file (compared by inode, symlinks followed). No `set -e`: exit codes
# are the real tool's, passed through by exec.
name=${0##*/}
case $name in pgrep | pkill) ;; *) name=pgrep ;; esac
real=
oldifs=$IFS
IFS=:
for d in $PATH; do
	[ -n "$d" ] || d=.
	c=$d/$name
	if [ -x "$c" ] && [ ! -d "$c" ] && ! [ "$c" -ef "$0" ]; then
		real=$c
		break
	fi
done
IFS=$oldifs
if [ -z "$real" ]; then
	echo "$name: no real $name found on PATH behind the wrapper" >&2
	exit 127
fi
case $("$real" --version 2>/dev/null) in
*procps-ng*)
	v=$("$real" --version 2>/dev/null | sed -n 's/.*procps-ng \([0-9][0-9]*\).*/\1/p' | head -n 1)
	if [ -n "$v" ] && [ "$v" -ge 4 ]; then
		exec "$real" -A "$@"
	fi
	;;
esac
exec "$real" "$@"
