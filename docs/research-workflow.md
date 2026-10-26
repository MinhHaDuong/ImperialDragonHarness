# Research workflow

Use this map to choose a skill for an article project. The
[skills catalog](../skills-catalog.md#research) lists all research commands;
each linked skill contains its operating instructions. Start in the article's
project so its sources, review artifacts and revision history stay together.

## Choose the entry point

| Need | Skill | Result or next step |
|------|-------|---------------------|
| Frame the article's central message | [`/message-framing`](../skills/message-framing/SKILL.md) | A message to guide drafting or revision. |
| Build a critical literature review | [`/critical-lit-review`](../skills/critical-lit-review/SKILL.md) | Scoped corpus, consultation table and synthesis, drawing on reading notes. |
| Read one work closely | [`/reading-note`](../skills/reading-note/SKILL.md) | Critical note archived in Zotero with its source provenance. |
| Defend the citations of one manuscript paragraph | [`/related-work-note`](../skills/related-work-note/SKILL.md) | Due-diligence note, source checks and justified nearby references. |
| Test a precise novelty or factual claim against prior work | [`/biblio-saturation`](../skills/biblio-saturation/SKILL.md) | Claim-specific search and adversarial assessment; blocked coverage stays explicit. |
| Import sources or archive finished notes | [`/zotero`](../skills/zotero/SKILL.md) | Existing or new library items, stored attachments and verified receipts. |
| Review a complete draft | [`/manuscript-review`](../skills/manuscript-review/SKILL.md) | Original review, separate verification of major criticisms and a ledger awaiting author decisions. |
| Obtain independent external perspectives | [`/external-peer-review`](../skills/external-peer-review/SKILL.md) | Explicit reader selection, separate verified reviews and synthesis preserving dissent. |
| Process a journal decision letter | [`/ingest-decision-letter`](../skills/ingest-decision-letter/SKILL.md) | Archived comments, a remark ledger and coverage check. |
| Inspect a LaTeX revision | [`/track-changes-pdf`](../skills/track-changes-pdf/SKILL.md) | Revision-marked PDF between two pinned git versions. |
| Finish a PDF for delivery | [`/pdf-finish`](../skills/pdf-finish/SKILL.md) | Mechanical checks and visual inspection, with remaining limits reported. |

These are entry points, not a checklist to run on every article. A targeted
reference search does not require a full saturation exercise. A review of an
existing draft can start directly with `/manuscript-review`.

## Review and revise an article

The core cycle is sequential: the verifier needs the original review, and
the author needs both before deciding what to change.

1. **Pin the input.** Supply the manuscript PDF, annexes, exact revision and
   review question. Record expected but missing annexes and whether the
   contents may be processed by a hosted model. The skill uses `/route` to
   select workers and records the reason.
2. **Read the whole manuscript.** `/manuscript-review` adapts
   King–Worthington's Appendix C, with
   [provenance and adaptations](../skills/manuscript-review/references/reader-prompt.md).
   One reader inspects every supplied page's text and image, searches the
   literature and retrieves relevant sources. The runner checks actual tool
   events and retains the original report.
3. **Check major criticisms.** One bounded verification pass records factuality,
   severity, uncertainty and localized evidence. For decisive external sources,
   it distinguishes accessibility, identity, relevance and support for the
   criticism. Corrections appear alongside the unchanged review; scientific
   disagreement remains visible.
4. **Decide as author.** Inspect the original review and verification together.
   The runner exports remarks into the existing R&R ledger schema, with author
   decisions pending. Accept, contest with reasons, defer or record an already
   satisfied remark; link the resulting work and evidence through the
   [revision workflow](../skills/ingest-decision-letter/SKILL.md). A remark's
   coverage and its resolution are separate states. Do not re-ingest the AI
   report as a new decision letter to create a second ledger.
5. **Revise and inspect.** Apply the author's decisions in the manuscript
   project. Use `/track-changes-pdf` when a revision-marked LaTeX PDF is useful,
   then `/pdf-finish` before delivery. A new review uses a new attempt directory
   and revision identifier, linked to the previous run; it needs an actual
   revision or an explicit author request.

In a runtime that registers the skill, begin with `/manuscript-review` and
the manuscript path, annexes and question. For direct execution, the
[skill's command example](../skills/manuscript-review/SKILL.md) documents the
required flags. It also documents `--resume-review`: after a valid reader and
failed verification, a fresh attempt can reuse the validated reader and rerun
only the verifier. The original attempts remain unchanged.

## Optional second look with Coarse

When a plan or draft would benefit from another critique of its architecture,
argument or consistency between sections, mention
[Coarse](https://pypi.org/project/coarse-ink/1.9.6/) and explain what it could
help examine in this particular manuscript. Offer it selectively, without
automatically launching it or making it a required review step. It is an
external tool recommendation; the harness includes no Coarse skill, vendored
code or runtime dependency.

Explain how to use it from the manuscript project. Check availability with
`command -v coarse-review`. If unavailable, give the isolated installation
command for the pinned version (Python 3.12+, with
[uv](https://docs.astral.sh/uv/getting-started/installation/) installed):

```bash
uv tool install --python 3.12 'coarse-ink==1.9.6'
coarse-review --help
```

For an authenticated CLI, choose the host and model through `/route`, then
adapt this example to the actual input and selected route:

```bash
coarse-review paper.pdf --host '<selected-host>' --model '<selected-model>'
```

State the machine's missing prerequisites and how to obtain them rather than
assuming installation or authentication. The subscription route needs a logged-in
supported CLI; PDF processing also needs an OpenRouter key. Existing project
credential configuration should supply it without putting secrets in commands
or reports. Keep the review and input provenance in the manuscript project.
For a plan, explain its stage and the intended review question in the supplied
input so future work is not mistaken for completed analysis.

Coarse produces advisory objections to triage and verify. It does not provide
the manuscript-review verifier's source checks or establish independent model
perspectives. Section/comment caps and selective PDF extraction QA limit its
coverage. Explain these practical limits and potential subscription/API usage
when proposing it; no automatic installation or skill registration is needed.

## Keep references and evidence together

Zotero is the bibliographic system of record. Import sources at intake and
archive finished notes when produced. Attach a missing file to an existing
item rather than creating a duplicate. Notes are Documents with stored
Markdown and source provenance; retain live hash-based storage receipts.
The document staging sweep excludes Markdown, so notes need their own
explicit reconciliation, described in
[Markdown intake](../skills/zotero/references/import.md#markdown-research-notes).

For a note's bibliography, the existing
[reference validator](../skills/related-work-note/runbooks/validate.md) checks
identifier accessibility. The
[bibliography merge helper](../skills/conference-submission-prep/runbooks/bib-merge.md)
preserves existing keys and entries and deduplicates DOI matches. A successful
HTTP response does not establish that a reference is the intended work or
supports the manuscript's claim. Those judgments need source reading.
An inaccessible source stays unresolved; it is not evidence that no prior
work exists.

Review runs retain pinned inputs, page images, raw streams, reports and
source traces under the project's run directory. Inspect these artifacts for
manuscript quotations and sensitive queries before sharing them. The runner
does not automatically commit, publish or import them into Zotero; archive
the intended deliverables through the existing Zotero workflow and retain
their receipts.

## Current execution limits

The executable review runner currently uses an authenticated Claude CLI,
with explicit model and effort, read/search/fetch tools and bounded execution.
It has no Albert backend or local-model backend. Uncleared full text is
refused before preparation; the skill describes a separate local/private
lane to carry out from the session when available.

The verifier is a check in a fresh context, not an independent-family review.
For independent perspectives, use `/external-peer-review`; unavailable readers
or missing independence must be reported. The retired `peer_review.py` is no
longer an executable entry point.

Execution checks do not certify scientific truth. In particular, manuscript
evidence is checked for valid page location and a nonempty passage, without
mechanically establishing quotation fidelity. External passages are matched
to retrieved tool text, which may itself be model-processed. For downloaded
PDFs, an observed download and subsequent page read can instead support a
match against a hashed snapshot's text layer; the matching page and native
events are retained. Image-only passages remain unverified by that check.
The author retains the final scientific judgment.
