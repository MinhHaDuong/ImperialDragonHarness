# DELETED 2026-09-25T16:00Z: feedback_raid_salvage_and_completion_detection_0728
# Reason: COVERED/ENFORCED. Salvage-first-on-kill is now a scripted, mandatory raid step (worktree-salvage.sh), and the monitor/pgrep-unreliability problem is structurally solved by tracking push/worktree-state timestamps via raid-breaker.py instead of relying on a Monitor callback or process-table matching. The remaining make -j4/NJOBS tip is generic and low-value on its own.
# Original content preserved in git history.
