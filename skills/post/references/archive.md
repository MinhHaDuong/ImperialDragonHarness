# archive

The post is live; make it citable and findable. Steps 1-7 run in order; 3
stops for the author, 4 and 5 for the author's go-ahead on the outward act.

A post already on the personal page and in the open archive is done: report
"nothing to do except the roadmap check", check the roadmap row, and stop.
Otherwise walk every step; a dry run lists each one with its evidence or
"missing".

## Registers

- Roadmap: yes, the row in the communications section carries the archive
  link once it exists.
- Publications list: yes, a `@misc` entry for a post or an op-ed, per
  `/update-publist`.
- For a blog post, the blog's journal and backlog files.

## Provenance

The companion PDF is built from the Markdown source, never from the rendered
page. The deposited metadata and the archive's response are kept beside the
print file. Frozen outputs go in `release/<AAAA-MM-JJ>/` with their hashes,
where the local `AGENTS.md` asks for one.

## Filesystem

1. Print Markdown, derived from the published text, beside the working
   drafts, using the project's shared PDF template (never a per-post fork of
   it). Every image checked against the live post, not against a file name.
2. Render the companion PDF by the project's recipe; `/pdf-finish` for a PDF
   leaving the machine.

## Outward gates (who clicks)

3. Human validation: the author reads the PDF (margins, images, tables). No
   deposit on an unreviewed PDF.
4. Open-archive deposit, after the prior-record check and the pre-upload
   review of `/update-publist`. A blog post deposits by the blog's own
   recipe (doctype BLOG), which is authoritative. An op-ed goes through
   `/update-publist` with doctype OTHER, unless the venue fits another
   doctype; `/update-publist` carries no op-ed row yet, so name that gap to
   the author rather than inventing a recipe. Validate first with the
   archive's test mode, keep the deposited metadata, record the returned
   identifier. The final deposit is the author's go-ahead.
5. Personal bibliography: a `@misc` entry in the bibliography the local
   `AGENTS.md` names (url of the live post, eprint of the archive, file of
   the PDF), the PDF copied to the page's files, the page rebuilt and shown
   to the author; commit and deploy on the author's go-ahead.
6. Back-link from the live post to the PDF on the personal page, by the
   blog's publishing recipe, at the end of the body; no media attachment.
   A newspaper or partner page: nothing to do.
7. Log it: a blog post gets a line in the blog's journal (PDF, archive
   identifier, date) and its backlog status updated; an op-ed gets a line in
   its folder's README. Then the roadmap row: the agent edits the local
   roadmap file with the archive link.

## Delegates

- `/update-publist` for steps 4 and 5 and their gates.
- `/pdf-finish` for step 2.
- `/paper` if the post grows into a manuscript.

## Author-only (ask, do not drop)

- PDF approved (step 3).
- Follow-up of the archive's moderation.
- Whether the archive identifier goes into the PDF itself (render again) or
  the archived copy predates its own citation.

## Done when

Steps 1-7 done or explicitly waived by the author; the archive link is in
the roadmap row; every author-only item has an answer.
