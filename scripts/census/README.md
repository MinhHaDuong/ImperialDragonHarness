# Harness usage census

The instruments that produced the 2026-09-09 usage report, vendored so the
question *what does this harness actually use?* stays answerable instead of
reconstructible. They read the local session traces, which never leave the
machine; every output is an aggregate.

Nothing here runs on a schedule and nothing here deletes anything. The census
reports; the decisions were, and stay, the author's.

## Why this is one directory

Ten files is real surface, added by a pass whose whole subject was removing
surface. They are grouped here rather than scattered through `scripts/` so the
whole instrument can be deleted in one move when it stops earning its keep —
which is the test it should be held to, like everything else it measures.

## The pipeline

```bash
C=~/.claude/scripts/census
OUT=/tmp/census

python3 $C/traces.py          --out $OUT/census.json         # the main pass
python3 $C/deps.py            --root ~/.claude --out $OUT/deps.json
python3 $C/memory-recall.py   --out $OUT/memory.json         # does the resident index get followed?
python3 $C/report.py --census $OUT/census.json --gitmeta $OUT/gitmeta.json \
                     --start 2026-06-01 --end 2026-09-09 --out $OUT/report.json
```

`report.py` needs a `gitmeta.json` mapping each artifact to its first commit,
last commit and commit count; `traces.py` does not produce it. Generate it with
`git log --follow --format=%ad --date=short -- <path>` per artifact, or pass a
file of `{}` if the creation dates are not needed.

`traces.py` takes about 50 s over 3.4 GB. The others are seconds.

| Script | Answers |
|---|---|
| `traces.py` | how often was each skill entered, each rule injected, each guard fired, each tool called |
| `human-commands.py` | which slash commands the author typed, over a longer window than the traces retain |
| `report.py` | aggregate the above into one ranked table per artifact class |
| `deps.py` | who references what — a skill at zero invocations may still be load-bearing |
| `denials.py` | which command each guard denial actually blocked, joined on `tool_use_id` |
| `exec-vs-mention.py` | was a script run, or merely `cat`-ed |
| `file-access.py` | was a rule consulted, or only edited |
| `permissions.py` | which allow rules name something that no longer exists |
| `portability.py` | how much of each skill depends on a runtime-specific primitive |

## Reading the output honestly

**A zero is two claims, and the counter cannot separate them**: the thing was
not used, or the probe could not see it. Before a zero becomes a verdict, run
the same query against a case known to be positive. On 2026-09-09 that was
`gaze` (147 trace files) and `roar` (109) against eleven skills at zero (none) —
and independently, `mammoth-audit.py` from ticket 0876, a separate
implementation, split the same 37 skills identically.

**A count is not a verdict on value.** `guard-destructive-bash.sh` fired 697
times; `block-pr-merge-in-worktree.sh` fired 176 times *on a single day*, its
own regression, and never in the 99 days before. Same order of magnitude,
opposite meanings. Read the date distribution, and read what was blocked.

**Rare by nature is not abandoned.** A skill for submission events legitimately
shows one or two invocations. The test that separates them is the missed
occasion: `ingest-decision-letter` existed on the day of a resubmission and was
not called.

**A textual reference graph does not see what a test imports.** `deps.py`
missed `test_fewer_permission_prompts_helper.py`, whose subject was deleted
without it. Run the suite before editing callers and let the failures name them.
