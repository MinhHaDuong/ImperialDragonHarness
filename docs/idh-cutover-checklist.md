# The old move is retired

The plan to move the live checkout out of `~/.claude` and reconstruct Claude
Code's profile is retired. Leave the existing `~/.claude` profile in place.
The installation direction is a separate clone at `~/.idh`, registered
additively with each runtime as described in
[idh-install-strategy.md](idh-install-strategy.md).

On this machine, `~/.idh` is still a symlink to the old checkout. Removing
that symlink is a separate, simple step before cloning. It must not remove or
move the directory it points to. The current `idh install` is not the command
for that fresh installation; it still performs all-runtime host setup.

The Claude Code 2.1.285 probes and the old cutover findings remain in ticket
0985 for reference. No live migration has been performed by this document.
