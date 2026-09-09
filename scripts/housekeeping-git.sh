#!/usr/bin/env bash
# Run from project root. Handles repository sync and the erg DAG check.
#
# It also expired a per-repo skip list under .git/ until ticket 0882 removed the
# nightbeat block; nothing writes such a list any more, so that step went with
# its only producer.
set -euo pipefail

git fetch --all --prune --quiet || true
git gc --auto || true

ERG=${ERG:-tickets/erg}
"$ERG" check tickets/ 2>/dev/null || true

exit 0
