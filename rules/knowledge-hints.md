<!-- last-reviewed: 2026-08-19 -->
# Project domain-knowledge hints

Loaded when a project declares or maintains domain knowledge an agent cannot
be expected to have and cannot search for: a canon, a controlled vocabulary,
a map of a field, a register of settled decisions.

## What this is, and why it is not another rule file

`rules/` answers *how to work*. This answers *what is known here*. The two look
alike from a distance and differ in the one place that matters: **ownership
inverts**.

A rule keeps its text global — `rules/lang/fr.md` is the same file for every
project — and lets a project supply only *mappings*, through
`.claude/rules-map.toml`. That is deliberate: the rulebook must stay shared or
it stops being a rulebook. Domain knowledge cannot work that way. A canon of
economic thought means nothing in a climate-finance repo, and the body is
inherently project-specific. So here the body lives **in the repo** and only
the **mechanism** is shared. Trying to express that as another `rules/` file
would put project-specific text in the shared rulebook, which is the one thing
the axis model exists to prevent.

## The manifest

`<repo>/.knowledge.toml`, at the repository root. The name carries no vendor:
the repo outlives the tool, and a file named for this year's assistant is a
file someone deletes in three years without knowing what it did.

```toml
[[hint]]
id      = "carte-het"
summary = "History of economic thought: the 196 entries of the Elgar Handbook on the History of Economic Analysis (2016) — economists, schools, fields — with page addresses and 1613 cross-references"
pointer = "conception/handbook-canon.md"
full    = "conception/handbook-map.md"
caveat  = "records this editorial team's 2016 classification, not source content; a missing entry proves no absence. Route to pages, open the page before asserting, cite the page and not the map."
terms   = ["Handbook", "Cournot", "Walras", "history of economic"]
paths   = ["article-het/**", "conception/*het*"]
```

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | Stable short name. Appears in both channels; keep it greppable. |
| `summary` | yes | One line, **context-free** (see below). Truncated at 200 characters. |
| `pointer` | yes | Repo-relative path to the *small* body, read on demand. A hint whose pointer does not resolve is dropped, not advertised. |
| `full` | no | A larger body, named but never auto-read. |
| `caveat` | no | What the artifact does **not** establish. Emitted with the pointer in the term channel. |
| `terms` | no | Words that, appearing in a user prompt, surface the hint once per session. |
| `paths` | no | Reserved for the edit channel; parsed and validated, not yet wired. |

Repeat `[[hint]]` for each. Order is preserved in the catalog.

## The two channels

**Catalog — session start.** `knowledge_hints.py catalog` prints one line per
hint, from `on-start.sh`, beside the rules index and under the same discipline:
pointers, not bodies. This is the only resident cost, and it is why `summary`
has a length cap.

**Terms — `UserPromptSubmit`.** `knowledge_hints.py prompt` reads the hook's
JSON on stdin and, when a declared term appears in the prompt, emits the
summary, the pointer, `full` if present, and the caveat. Matching is
case-folded and **word-bounded**: `Handbook` does not fire on `handbookish`. A
hint fires **once per session**, deduplicated by a marker under
`$TMPDIR/claude-knowledge-hints` keyed on `session_id` + `id`, both sanitised
so neither can escape the directory.

The catalog is not optional, and this is the part worth arguing. Term triggers
require the user to write "Cournot"; asked instead about "this paragraph on
duopoly", nothing fires — and an agent cannot grep for vocabulary it does not
yet have. The resident line is what makes the artifact discoverable to someone
outside the field, which is precisely the reader it exists for.

## Silent no-ops

Every one of these produces no output and exit 0:

- no `.knowledge.toml` between the working directory and the filesystem root;
- malformed TOML;
- a `[[hint]]` missing `id`, `summary`, or `pointer`, or with a non-string one;
- a `pointer` that does not resolve to a file — advertising a dead path costs
  the reader a turn to discover, so the hint is dropped instead;
- for the term channel: unparseable stdin, or no term match.

The manifest is authored by hand and read on every session start; a parse error
that halted the session, or a hook that failed loudly on a typo, would be worse
than the hint being briefly absent.

## Writing a good hint

**The summary is read from outside the field.** That is its entire job, and it
is the constraint most easily missed by whoever writes it, who is by definition
an insider. "196 entries of Faccarello & Kurz 2016" identifies nothing to a
reader who does not already know those names; lead with the domain and the
object — "History of economic thought: the 196 entries of the Elgar Handbook on
the History of Economic Analysis (2016)". A summary that presumes membership in
the field cannot route someone into it. (Author's remark, 2026-08-19, on the
first hint written.)

**The pointer is the small body; the payload is never injected.** On the first
real hint the split was 157 tokens of pointer, 1.7k for the roster it points
at, 14.5k for the full map. Only the first can be resident. Size `pointer` so
an agent can afford to read it on suspicion, and put the rest behind `full`.

**The caveat states what the artifact does not establish.** Measured on that
same hint: a caveat does **not** buy refusal of bad inferences — a model with no
access at all already refuses those, and argues them well. What it buys is
provenance discipline. The agent holding the map flagged, unprompted, which of
its answers rested on the map rather than on a page it had opened, and said so.
Write the caveat for that: what the artifact *is*, versus what a reader will be
tempted to treat it as.

**Terms are a sharpening, not the mechanism.** Choose words that are unusual in
the repo's ordinary traffic. A term that fires on routine work trains the model
to skim the hint.

## Verifying locally

```bash
python3 ~/.claude/scripts/knowledge_hints.py --cwd <repo> catalog
printf '{"prompt":"...","session_id":"probe","cwd":"<repo>"}' \
  | python3 ~/.claude/scripts/knowledge_hints.py prompt
```

The second is not idempotent — the session marker persists. Use a fresh
`session_id` per probe, or point `TMPDIR` at a scratch directory.

`tests/test_knowledge_hints.py` drives both channels through the real CLI and
the real stdin protocol rather than importing the helpers, because the catalog
reaches the model through `on-start.sh` and the term channel through a hook: a
test calling the functions directly would be blind to the argument wiring, to
the stdin contract, and to the silent paths above, which are most of the
behaviour. The module is in the integration tier for that reason.

## Not yet

`paths` is parsed and validated but nothing consumes it. Wiring it into the
existing `Edit|Write` injection hook is the obvious next step, and it is not
sufficient on its own: every agent measured on the first hint was **read-only**,
so an edit-triggered channel would have reached none of them. It sharpens the
catalog; it cannot replace it.
