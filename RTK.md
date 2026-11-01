# RTK - Rust Token Killer

**Usage**: Token-optimized CLI proxy (60-90% savings on dev operations)

## Meta Commands (always use rtk directly)

```bash
rtk gain              # Show token savings analytics
rtk gain --history    # Show command usage history with savings
rtk discover          # Analyze Claude Code history for missed opportunities
rtk proxy <cmd>       # Execute raw command without filtering (for debugging)
```

## Installation Verification

```bash
rtk --version         # Should show: rtk X.Y.Z
rtk gain              # Should work (not "command not found")
which rtk             # Verify correct binary
```

⚠️ **Name collision**: If `rtk gain` fails, you may have reachingforthejack/rtk (Rust Type Kit) installed instead.

## Hook-Based Usage

All other commands are automatically rewritten by the Claude Code hook.
Example: `ls -la` → `rtk ls -la` (transparent, 0 tokens overhead). git is excluded
(ticket 1078): `exclude_commands` in `~/.config/rtk/config.toml`.

Full command reference: `rtk --help`.

## When you need unfiltered output

The hook compacts for a reader, not a parser: it can rewrite counts, drop
lines and truncate long output head-first. What it spares moves between
versions: ask `rtk hook check <cmd>`. Escape hatches: `RTK_DISABLED=1`,
`rtk proxy <cmd>`, or an absolute path such as `/usr/bin/git -C <worktree> …`;
`~/.local/share/rtk/tee/` keeps the unfiltered output of filtered runs.
