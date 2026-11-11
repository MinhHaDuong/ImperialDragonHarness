# Reading note template

The single template for reading notes, published as an HTML child note under
the work's Zotero item, whether written alone, delegated by
`critical-lit-review`, or drafted in batch. Keep the section headers verbatim:
notes are compared and searched across a corpus.

Two lengths, same headers; the project sets the word caps, the harness fixes
none:
- **full** (deep-read tier): Summary and Critical analysis carry roughly equal
  weight.
- **short** (skim tier): Summary, Research relevance and the
  frontmatter are complete, Critical analysis is cut to Position in debates and
  Naturalized assumptions, two quotations.

The draft file is a YAML frontmatter block followed by the HTML body. The
frontmatter stays in the repository (draft and snapshot); the published child
note carries the body. Use plain HTML Zotero's note editor keeps: `h1`-`h2`,
`p`, `ul`/`li`, `blockquote`, `em`, `strong`; no scripts, styles or classes.

The frontmatter is data, not decoration: it is what a synthesis across many
notes queries. Leave a field empty (`""` or `[]`) rather than guess.

````html
---
title: "Reading note: <work title>"
# --- the work
work_title: "<exact title, from the first page>"
authors: "<Last, First; Last, First>"
affiliations: ["<institution at publication time>"]
year: YYYY
venue: "<journal, publisher or series>"
volume: ""
issue: ""
pages: ""
doi: ""
url: ""
zotero_item: "<key of the work's item>"
work_key: "<project corpus id, e.g. doi:… or openalex:W…; otherwise zotero:<library>:<work item key>"
open_access: "gold | green | hybrid | bronze | closed | unknown"
oa_url: "<URL of the open copy, if any>"
# --- reproducibility (empirical and quantitative works; "n/a" otherwise)
replication_package: "none | announced | available | n/a"
replication_url: "<archive, repository or journal supplement URL>"
replication_accessed: "no | yes (YYYY-MM-DD)"
replication_verified: "not attempted | inspected | partially reproduced | reproduced | failed"
replication_effort: "<hours spent, and what blocked or what was run>"
# --- the reading
full_text: "read | abstract only (<why>)"
date_read: YYYY-MM-DD
length: "full | short"
tier: "deep | skim"
deliverables: ["<project or manuscript this note serves>"]
drafted_by: "<author | model id and version>"
status: "draft | quotes verified | author revised"
# --- coding (project vocabularies; free text where none is defined)
coding:
  period: ""
  method: ""
  data_sources: []
  instruments: []
  actors: []
  region: []
  arcs: []
  controversies: []      # entries "controversy: position"
---

<h1>Reading note: &lt;work title&gt;</h1>

<h2>Summary</h2>
<ul>
<li><strong>Question and approach</strong>: what the work asks, how it goes about it.</li>
<li><strong>Main arguments or findings</strong>: three to five, in your own words, each with its anchor [Qn].</li>
<li><strong>Evidence and method</strong>: sources, data, analytical procedure.</li>
<li><strong>Concepts and framework</strong>: theory mobilized, central concepts.</li>
</ul>

<h2>Critical analysis</h2>
<ul>
<li><strong>Strengths</strong>: what it contributes, what it does well.</li>
<li><strong>Limitations and blind spots</strong>: what is unexamined, which questions are not asked, which actors, cases or data are absent.</li>
<li><strong>Position in debates</strong>: the conversation it joins; whom it agrees and disagrees with; the gap it claims.</li>
<li><strong>Assumptions</strong>
  <ul>
  <li><em>Explicit</em>: acknowledged starting points.</li>
  <li><em>Implicit</em>: taken for granted without discussion.</li>
  <li><em>Naturalized</em>: presented as technical or self-evident when contingent or political. Each with its anchor [Qn].</li>
  </ul>
</li>
<li><strong>Innovations</strong>: new concepts, tools or methods it introduces, if any.</li>
</ul>

<h2>Research relevance</h2>
<p>One entry per deliverable listed in the frontmatter:</p>
<ul>
<li><strong>&lt;deliverable&gt;</strong>: connection to its guiding question; axes informed; controversy clarified; gaps revealed.</li>
</ul>

<h2>Key quotations</h2>
<blockquote>[Q1] "Exact quotation." (p. N)</blockquote>
<p>Why it matters, one line. Two to four quotations in a full note; every anchor used above has its quotation here; page read on the page.</p>

<h2>Notes for future writing</h2>
<p>Where and how to cite it; which argument it supports or opposes.</p>
````
