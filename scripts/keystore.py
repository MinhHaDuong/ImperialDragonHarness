"""Read one credential from a trusted provider file in an isolated shell.

Extracted from the retired review executor; no model or network dependency.
Returns None on unreadable, oversized, non-scalar or malformed values. Provider
files are trusted shell code; callers must never expose the returned value.
"""

import re
import subprocess
from pathlib import Path

_VALID_ENV_NAME = re.compile(r"^[A-Z][A-Z0-9_]*$")
_CREDENTIAL_COMPONENT = re.compile(r"(?:^|_)(?:API_KEY|KEY|TOKEN|PASSWORD|SECRET)(?:$|_)")
MAX_KEYSTORE_BYTES = 262_144

# Read ONE variable out of a trusted provider file. Passed to `bash -c`, with
# the file and the variable name supplied POSITIONALLY as $1 and $2 — never
# interpolated into this text, which is what keeps a CLI-supplied name out of
# the shell's parse. Exit 3 = unreadable file, 4 = name absent.
#
# The readability probe asks whether the file can be read. A sourced file's
# final status says only how its last command ended. Extracting in an EXIT trap
# also preserves an already-defined value if the provider calls `exit`.
_EXTRACT_SH = """
set -a
[ -r "$1" ] || exit 3
__idh_emit_credential() {
    [ -z "${!1+x}" ] && exit 4
    declaration="$(declare -p "$1" 2>/dev/null)" || exit 4
    case "$declaration" in
        "declare -a "*|"declare -A "*) exit 5 ;;
    esac
    printf "%s" "${!1}"
    exit 0
}
trap '__idh_emit_credential "$2"' EXIT
. "$1" >/dev/null 2>&1 || :
"""


def keystore_value(provider: Path, name: str) -> str | None:
    """Source trusted shell assignments, returning only the requested scalar.

    Retains the guards originally used by the review executor (tickets 0393,
    0943); the shell counterpart is scripts/coaching/replay.sh. The child gets
    an empty environment, so inherited credentials and BASH_ENV cannot affect
    resolution. Provider files are trusted executable code, never project .env
    files. Their other variables and output stay in the child.

    Never print, log, persist or place the returned value on an argv.
    """
    if not _VALID_ENV_NAME.fullmatch(name) or not _CREDENTIAL_COMPONENT.search(name):
        raise ValueError("not an allowed credential name")
    try:
        # Python owns the byte count, so an ambient PATH cannot replace the
        # guard with a permissive `wc`. Rechecking here narrows the check/use
        # race and keeps this helper safe when called directly.
        if not provider.is_file() or provider.stat().st_size > MAX_KEYSTORE_BYTES:
            return None
        proc = subprocess.run(
            ["bash", "-c", _EXTRACT_SH, "_", str(provider), name],
            capture_output=True,
            env={},
        )
    except OSError:
        # An empty `env` means bash is looked up on os.defpath, so a host that
        # keeps it elsewhere would raise here. Degrade to "not readable" so the
        # caller still fails loud and NAMED, rather than as a raw traceback.
        return None
    if proc.returncode != 0:
        return None
    try:
        # Decoded here rather than by `text=True`, which also turns on universal
        # newlines: that would silently rewrite a CR *inside* a value into LF.
        value = proc.stdout.decode("utf-8")
    except UnicodeDecodeError:
        # Not an OSError, so it needs its own arm, and it needs one: uncaught it
        # escapes the designed SystemExit, and its ``repr`` embeds the entire
        # raw undecoded buffer — one careless ``repr(e)`` from leaking the value.
        return None
    # A CRLF provider file ends the assignment's line with CR, which lands
    # INSIDE the value: a byte-wrong credential that looks present and fails
    # only at the API call. Stripping it is unconditional because no credential
    # legitimately ends in a carriage return; a value carrying CR internally is
    # out of scope, and would not survive an HTTP header anyway.
    value = value.rstrip("\r")
    if "\n" in value or "\r" in value:
        return None
    return value

