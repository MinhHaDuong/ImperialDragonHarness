# Reading note template

The single template for reading notes, whether written alone, delegated by
`critical-lit-review`, or drafted in batch. Keep the section headers verbatim:
notes are compared and searched across a corpus.

Two lengths, same headers:
- **full** (deep-read tier): 1000–1500 words excluding quotations; Summary and
  Critical analysis carry roughly equal weight.
- **short** (skim tier): 300–500 words; Summary, Research relevance and the
  frontmatter are complete, Critical analysis is cut to Position in debates and
  Naturalized assumptions, two quotations.

The frontmatter is data, not decoration: it is what a synthesis across many
notes queries. Leave a field empty (`""` or `[]`) rather than guess.

````markdown
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
work_key: "<project corpus id, e.g. doi:… or openalex:W…; empty outside a corpus>"
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

# Reading note: <work title>

## Summary

- **Question and approach**: what the work asks, how it goes about it.
- **Main arguments or findings**: three to five, in your own words, each with
  its anchor [Qn].
- **Evidence and method**: sources, data, analytical procedure.
- **Concepts and framework**: theory mobilized, central concepts.

## Critical analysis

- **Strengths**: what it contributes, what it does well.
- **Limitations and blind spots**: what is unexamined, which questions are not
  asked, which actors, cases or data are absent.
- **Position in debates**: the conversation it joins; whom it agrees and
  disagrees with; the gap it claims.
- **Assumptions**
  - *Explicit*: acknowledged starting points.
  - *Implicit*: taken for granted without discussion.
  - *Naturalized*: presented as technical or self-evident when contingent or
    political. Each with its anchor [Qn].
- **Innovations**: new concepts, tools or methods it introduces, if any.

## Research relevance

One sub-entry per deliverable listed in the frontmatter:

- **<deliverable>**: connection to its guiding question; axes informed;
  controversy clarified; gaps revealed.

## Key quotations

> [Q1] "Exact quotation." (p. N)

Why it matters, one line. Two to four quotations in a full note; every anchor
used above has its quotation here; page read on the page.

## Notes for future writing

Where and how to cite it; which argument it supports or opposes.
````
