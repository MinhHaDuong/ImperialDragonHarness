---
name: feedback_config_block_needs_an_end_marker
description: Replacing a dotfile block "from its start marker to EOF" drops whatever the author added after it; a managed block needs begin AND end markers, and the lines outside it must be diffed against the backup
metadata:
  type: feedback
---

2026-09-29, installing the final 0983 loader block into `~/.bashrc`: on doudou
the old block ended at EOF, so "head up to the marker + new block" was right.
On padme the same script silently dropped the three lines that followed the
block — a comment and the author's `zotero` alias. The script had even printed
the file's last line (the alias) and proceeded anyway. Restored within minutes
from the backup taken just before.

The block (`scripts/bashrc-loader.sh`) has a start marker and no end marker,
so any in-place update must guess its extent. The same file on two hosts is
two layouts.

**How to apply:** before rewriting a managed region of someone's dotfile,
locate BOTH ends from the old content (end marker, or the old block's known
last line), splice `head + new + tail`, and prove the lines outside the region
are byte-identical to the backup. A backup plus that diff is what made this a
two-minute repair instead of a lost alias. Tracked for `idh install` in 0987's
log. Related: [[feedback_verify_each_before_batch_action]].
