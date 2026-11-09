# Ruling-register manual consolidation fixture

Project: synthetic River study, isolated under this task worktree’s `.tmp/river-study`.
This is a manual model-behavior demonstration of the shared instructions, not
production consolidation automation or a prose-wording test. No other project
was accessed. Smelt/Brood guidance was read before the editorial decisions.

The first pass rebuilt a legacy register, retained its temperature decision,
and carried an author qualification about calibration metadata. It updated the
chart decision with its distinct final-paper scope. Matching was verified
against the fixture’s rules/matching.md before retirement. Retirements were
grouped by integration, supersession, and completed history, with reasons and
source links. The completed export was not called a rule integration.

The second manual pass reread the same source and existing retirement record.
Every retirement was already recorded, so no further append was warranted.
Byte comparisons confirmed all fixture files unchanged on that pass and the
original source bytes intact across both passes. This demonstrates the
editorial procedure on one synthetic project; it does not establish how an
unattended model would behave across arbitrary repositories.

## Input register

```markdown
# River study rulings

## Data handling

> pinned 2026-10-01 Convert measured temperatures to Celsius, retaining the original instrument export. The author’s later edit preserves instrument calibration metadata too. [source](../journal/2026/decisions.md)

## Charting

Use blue for treatment sites in pilot charts. [source](../journal/2026/decisions.md)

## Matching

Two reviewers sign off manual station matches. [source](../journal/2026/decisions.md)

## Retired

Pilot export delivered on 3 October. [source](../journal/2026/decisions.md)
```

## First-pass active register (unchanged on second pass)

```markdown
# River study rulings

## Data handling

Convert measured temperatures to Celsius, retaining the original instrument export. This applies to measured temperatures; the author’s later edit preserves instrument calibration metadata too. [context](../journal/2026/decisions.md)

## Charting

Use labelled shapes for treatment sites in the final paper, following accessibility review. Blue remains useful in archived pilot charts. [context](../journal/2026/decisions.md)
```

## Appended journal record (reused on second pass)

```markdown
# River study retirement causes

## Integrated into the matching protocol

Two reviewers sign off manual station matches. The adopted [protocol](../../../rules/matching.md) records the two sign-offs, so this ruling leaves the active register. [context](decisions.md)

## Superseded for the final paper

Blue identified treatment sites in pilot charts. Accessibility review replaces that convention with labelled shapes for the final paper; the pilot archive keeps its original convention. [context](decisions.md)

## Completed work

The pilot export was delivered on 3 October. This dated observation remains history; no rule integration is claimed. [context](decisions.md)
```

## Source preservation and repeat-pass measurements

Generated from fixture bytes by SHA-256 and direct equality comparisons:

- Original journal SHA-256: `f61d763a4666082a21eb8a8f701c8573c99d79314b1ad0c84c5af4cda3588353`.
- Original journal unchanged after both passes: `True`.
- First-pass and second-pass file maps byte-equal: `True`.
- Retirement journal files after each pass: `1`, `1`.
- Added retirement bytes on the second pass: `0`.

The source journal remains the original fixture input. The
fixture uses project decisions about river data, charting, and station matching;
it imports no harness rulings. The live reviewed harness register remains
byte-identical to the branch base.

## Raw fixture source journal

```markdown
# River study decisions

The author requires measured river temperatures in Celsius; the instrument export supplies Fahrenheit. Preserve the original export beside the conversion. The author’s later edit preserves instrument calibration metadata too.

The pilot chart uses blue for treatment sites. A later accessibility review selects labelled shapes for the final paper, while blue remains useful in the pilot archive.

The author requires two reviewers for manual station matching. The adopted matching protocol now records both sign-offs in rules/matching.md.

The pilot export was delivered on 3 October. This records completed work, not a standing rule.
```

The existing input register above already carries the author’s calibration
qualification before the rebuild. The raw source supports it; consolidation
introduces no new author decision. The matching destination contains:

```markdown
# Station matching

Manual station matches require two recorded reviewer sign-offs.
```
