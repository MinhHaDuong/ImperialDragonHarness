# The Dragon's memory — design v5

**Publication date:** 11 September 2026  
**Status:** design draft for review; revised after three independent architectural reviews  
**Préparé par ChatGPT prompté par Ha-Duong Minh**  
**Repository baseline:** `a90a9f5e9be4f88889b180bd05ba0ef8aaa993f6`  
**Previous design:** [v4, frozen](./2026-09-10-dragon-memory-design-v4.md)
**Review:** runtime ownership, subsystem boundaries and integrity reviews applied;
initial v5 remains in Git history at `9804bbee`.

This is an architectural specification, not a report on implementation progress.
It replaces v4's architectural proposal. Historical measurements, runtime probes
and earlier reviews remain in the frozen versions; they are not revalidated here.
The established current-design filename is retained so existing references still
lead to the latest design.

## Contents

1. [Executive summary](#1-executive-summary)
2. [Purpose, boundaries and guarantees](#2-purpose-boundaries-and-guarantees)
3. [Stores, scope and portability](#3-stores-scope-and-portability)
4. [Identity, format and lifecycle](#4-identity-format-and-lifecycle)
5. [Admission and authority](#5-admission-and-authority)
6. [Orientation, recent supplement and task recall](#6-orientation-recent-supplement-and-task-recall)
7. [Applicability, retrieval and ranking](#7-applicability-retrieval-and-ranking)
8. [Capacity policy](#8-capacity-policy)
9. [Dreaming and generalisation](#9-dreaming-and-generalisation)
10. [Publication and synchronisation](#10-publication-and-synchronisation)
11. [Runtime adapters and graceful degradation](#11-runtime-adapters-and-graceful-degradation)
12. [Acceptance criteria](#12-acceptance-criteria)
13. [Migration and remaining choices](#13-migration-and-remaining-choices)
14. [Decision trace and references](#14-decision-trace-and-references)
15. [Comparison with other memory systems](#15-comparison-with-other-memory-systems)

## 1. Executive summary

Two knowledge scopes, one body format, one compiler and three delivery channels.
Dreaming exercises editorial judgment; compilation publishes accepted knowledge;
a small reader supplies context. These are responsibilities, not additional
user-facing commands.

The canonical store is readable Markdown bodies with structured frontmatter,
tracked with the project. Generated catalogues, rankings and retrieval caches
are views over those bodies. Dreaming may require a capable host; ordinary
consumption must work in disposable containers and across Codex, Pi and Claude
Code. Without the harness, a reader can still browse and assess the memory.

Project memory and shared memory are separate knowledge scopes. IDH itself has
ordinary project memory: maintaining the harness does not confer global scope.
A project combines its own memories with applicable shared memories, deduplicates
by UUID, and selects within one orientation budget. It does not allocate separate
fixed quotas to local and shared entries.

Three delivery components handle different timescales:

| Component | Purpose | Refresh |
|---|---|---|
| Orientation | Stable awareness through a ranked index | Ranked by dreaming; filtered and budgeted at loading |
| Recent supplement | Bridge the interval before changes are processed by dreaming | Derived from accepted memory revisions absent from the publication |
| Task recall | Supply relevant bodies or focused excerpts, including below-cut memories | When the task is clear and when it materially changes |

Memory has no mandatory-residency class. User emphasis can influence weight,
but requirements belong in rules, skills and, where machine-checkable, hooks.
Instruction injection can be deterministic; model adherence remains probabilistic.
Hooks enforce only conditions and action paths they actually intercept.

At entry, distinguish experience from decisions. Decisions, commitments and
authorisations go through the decision-ledger process. Memory can reference a
decision or provide evidence for reconsideration; it cannot become a parallel
ledger or determine which decision governs.

Scope expansion, generalisation and supersession are different operations.
Each rediscovery is only an opportunity to consider generalisation, never an
automatic trigger or a requirement to synthesise. An accepted generalisation
creates a new claim linked to its source memories; particulars
remain active unless explicitly superseded or retracted. Preserve history,
but exclude inactive advice from normal selection.

Fixed configurable ceilings, variable occupancy and measured recalibration
govern capacity. The proposed 1,500 / 500 / 2,000-token allocation is an engineering
starting point, not an adopted optimum or a literature-derived constant.

## 2. Purpose, boundaries and guarantees

Memory helps an agent reuse observations, experience and inferred lessons.
Its success is better task behaviour at a bounded cost, not a high count of
stored entries, reads or injected tokens.

| Mechanism | Contract |
|---|---|
| Decision ledger | Canonical record of adopted decisions and authorisations |
| Rules and contracts | Required text supplied through a defined loading mechanism |
| Skills | Procedure supplied when the relevant skill is loaded |
| Scripted hooks | Mechanically enforce checked conditions on intercepted paths |
| Memory | Ranked evidence and discovery aids that may improve behaviour |

Memory cannot guarantee awareness or obedience. V4 correctly distinguished
reachability from unprompted awareness, but its mandatory-residency remedy
created another instruction system and an impossible promise under unbounded
mandatory growth. V5 keeps the distinction and removes that remedy.

A preventive lesson may enter memory immediately. Periodic harvesting can propose
a rule, skill or hook amendment. Urgent explicit requirements use the normal
instruction-change path directly rather than waiting for dreaming.

Preservation means no automatic destruction merely because of age, score or
capacity. It does not prohibit explicit owner-directed removal or justify storing
secrets and unsuitable material in a travelling repository. Inactivity is normal;
historical preservation is distinct from eligibility for current advice.

No universal optimal budget, semantic-retrieval advantage or automatic runtime
discovery is claimed.

## 3. Stores, scope and portability

### 3.1 Project and shared scopes

Each project owns memory inside its repository. A user's home directory may hold
an installation, shared store or derived cache, but cannot be the sole canonical
home of project memory.

The shared store holds reusable knowledge with explicit applicability. It is not
automatically resident everywhere. IDH's implementation notes belong to the IDH
project unless a separate scope-expansion or generalisation process establishes
broader applicability.

Provenance answers where a lesson came from. Applicability answers where it is
useful. Neither storage location nor a score establishes authority.

A stable project identifier independent of checkout path is the proposed default.
Cloning or moving the same project preserves that identifier; creating a genuinely
independent project is an explicit identity decision. The identifier format and
fork policy remain schema decisions, not inferred from directory names.

### 3.2 Portable project layout

The following names are an illustrative layout, not a mandated migration path:

| Path under the project memory root | Role |
|---|---|
| `README.md` | Plain-language discovery and usage instructions |
| `*.md` | Active locally owned bodies, with reserved filenames for views |
| `inactive/` | Preserved superseded or retracted local bodies |
| `shared-snapshot/` | Committed readable replicas of relevant shared bodies |
| `index.md` | Generated complete catalogue of active available bodies |
| `MEMORY.md` | Generated bounded default orientation |
| `publication.json` | Publication inputs, processed revisions and ordered candidates; optional score diagnostics |
| `.cache/` | Ignored, disposable acceleration data |

All navigational links are relative. Generated catalogues use ordinary Markdown
links: a bare reader must not need a UUID resolver just to open a body. A link
validator distinguishes reserved view files from actual memories.

Inactive bodies display a conspicuous human-readable status notice as well as
machine-readable frontmatter. Moves must preserve historical navigability:
regenerate affected local links, resolve machine references by UUID, and provide
a redirect or equivalent repair for old path links where needed. Redirects are
not active memories and cannot enter rankings.

### 3.3 Shared snapshots

Each publication first fixes an explicit project-relevant shared candidate set:
bodies referenced by active local memories and a bounded selection for orientation,
optionally with a small refill reserve. Resolve required dependencies or report
them unavailable. Then rank local bodies plus this available set and commit its
readable shared snapshot. This avoids a circular promise to refill from bodies
that were ranked but never copied. Refilling is limited to this available set;
it does not promise access to the whole shared corpus. Candidate-set size is a
separate snapshot policy, not the resident token budget.

A replica preserves the UUID, upstream revision and content hash. It is not a new
memory and is not independently editable. Changes are proposed upstream, or an
explicitly distinct local observation is authored with provenance.

Dreaming refreshes the snapshot and publishes it with the project views. Ordinary
consumption needs no network. The manifest records the upstream revision and
refresh date. No secrets or access credentials are packaged with it.

When a live shared store is available, reconcile by UUID and proven revision
ancestry. A verified successor can replace a snapshot revision; divergent versions
must not be resolved by timestamp alone. Such updates enter the recent supplement
until processed by dreaming.

Offline recall covers local bodies and the snapshot. It cannot discover uncached
shared bodies or learn upstream retractions after the last synchronisation.
Expose this boundary; do not claim complete or current global knowledge.

## 4. Identity, format and lifecycle

### 4.1 Stable identities and readable files

Each memory receives an immutable UUIDv4 at creation. Filenames are readable
slugs and can change without changing identity. Scope and location are independent
of identity. Two distinct memories may have similar filenames; duplicate UUIDs
with conflicting bodies require explicit resolution.

Machine relations use UUIDs. A generated UUID-to-path map is rebuildable from
frontmatter, including inactive bodies and replicas. Clocks are not identity or
conflict-resolution mechanisms.

### 4.2 Body format and language

Canonical text is English with UK spelling: titles, descriptions, tags and prose.
Preserve quotations, proper names, code, paths and external identifiers exactly.
Schema keys retain their specified spelling.

Keep the portable base field names discussed in v4: `type`, `title`,
`description`, `tags`, `timestamp`. Add identity, scope, lifecycle and provenance
explicitly. Compatibility with an external convention must be validated against
its version before being claimed; runtime-specific aliases are derived, never
canonical alternatives.

The schema distinguishes the following concepts; exact field nesting is an
implementation decision. The base requirements and optional annotations are
separated below:

| Concept | Meaning |
|---|---|
| Identity | Immutable UUID and schema version |
| Description | Human title, retrieval description and useful keywords |
| Scope | Project associations and explicit applicability conditions |
| Lifecycle | Active, superseded or retracted |
| Provenance | Source references; user-stated, observed or inferred; author |
| Dates | Creation and semantic updates, separately from file migration time |
| Relationships | Generalises, superseded-by, challenges, decision references |
| Ranking inputs | Declared importance, user emphasis and supporting evidence |

A single `timestamp` does not collapse observation time, creation time and
last edit. Preserve their meanings where they differ. Mechanical reformatting
must not manufacture semantic freshness.

Computed scores and ranks do not belong in filenames or canonical bodies.
Annotated importance is a judgment with provenance, not an authoritative score.

The base contract requires identity, lifecycle, basic scope, source, meaningful
dates and readable content. Rich scoring annotations and detailed telemetry are
optional extensions. Carry a concise, audience-appropriate account of the
observation and its limitations in the body. Private trace IDs are audit pointers,
not portable evidence by themselves; label unavailable supporting evidence.

### 4.3 Lifecycle, applicability and provisional status

| Dimension | Values or meaning |
|---|---|
| Lifecycle | Active / superseded / retracted |
| Applicability | True / false / unknown in a named consuming context |
| Processing | Provisional relative to a publication, or processed by that publication |

Superseded means replacement advice exists. Retracted means withdrawn without
necessarily having a replacement. Set the status in frontmatter and move the
local body into `inactive/` in one committed operation. Frontmatter is
authoritative: a misplaced inactive body remains excluded and disagreement is
reported. Supersession references resolve to replacement UUIDs.

An inapplicable workaround remains active knowledge for another environment.
A retracted or superseded memory cannot revive merely because a tool version
or path changes. Restoration is an explicit editorial act.

Provisional is not a third knowledge scope. A body is provisional for a project
publication when its accepted revision is not in that publication's processed
manifest. The same shared body can be processed in one project and recent in
another. Losing a freshness allowance does not delete the body or claim it was
processed.

Normal selection excludes inactive bodies. Historical retrieval deliberately
includes them with their status and replacement links. Unknown applicability is
retained as uncertainty, never silently rewritten as true.

## 5. Admission and authority

### 5.1 Canonical ownership at entry

Before admitting a candidate, ask which existing artefact owns the information,
then distinguish what was decided from what was observed or learned.

| Candidate | Canonical destination |
|---|---|
| Current progress, blocker or handoff | STATE or the existing ticket |
| Adopted decision, commitment or authorisation | Project's declared decision records |
| Reusable code, corpus or procedure | Ordinary artefact location or skill |
| Proposed reuse work | Existing proposal/work tracking mechanism |
| Existing useful artefact needing discovery | Pointer or knowledge hint |
| Experiential lesson not otherwise captured | Memory, with provenance |
| Mixed decision and observation | Split; memory references the governing record |
| Ambiguous | Record the routing judgment as unresolved; do not assert adoption |

“Decision ledger” names a role, not a mandatory new store. Existing ticket
decision records, ADRs or other declared project records may fulfil it. Bind to
the project's actual convention; an unconfigured destination does not justify
inventing a ledger or putting the decision in memory. In IDH, ticket bodies
already carry decision records under [tickets/AGENTS.md](../tickets/AGENTS.md).

Do not copy information already obtainable from code, Git history, README,
STATE, rules or skills merely to populate memory. “Script X exists” needs a
pointer; “X failed under condition Y” can be a lesson citing X. This retains
the existing [memory admission exclusions](../skills/memory/SKILL.md).

Routing is an agent judgment. The entry mechanism can require a recorded routing
outcome; it cannot deterministically guarantee semantic classification. Evaluate
classification correctness behaviourally. Clarify with the user only when the
conversation cannot establish the distinction.

A candidate must also pass structural validation and a suitability check for the
repository's audience. Recording an observation does not grant permission to
publish confidential material. Unresolved scope or audience questions must not
silently expand access.

### 5.2 Existing knowledge subsystems

[Knowledge hints](../rules/knowledge-hints.md) already provide a vendor-neutral
`.knowledge.toml` catalogue and term-triggered pointers with caveats. Reuse that
discovery envelope where appropriate; do not convert canons, vocabularies,
decision registers or reusable assets into memory bodies. Content ownership
remains with their canonical subsystem, which dreaming cannot rewrite.

Deduplicate discovery of the same canonical artefact and preserve its caveat.
Account for hint exposure alongside memory in the total context census; do not
silently charge it twice or claim memory's budget includes an unmeasured hint
channel. Shared interface does not imply identical retention or ranking policy.

Lessons remain experiential memory when not captured elsewhere. Reuse
opportunities that request future work belong to the established work/proposal
tracker. This design creates no new lessons database, reuse ledger or evidence
store. Any separately maintained reuse subsystem must be identified before
migration, not assumed absent.

### 5.3 Editorial authority

Sessions may record experiential memories. Dreaming may consolidate, generalise,
rescope and retire experiential memories, preserving their originals and the
reason for semantic changes. Shared changes follow the established repository
review process.

Decisions and authorisations remain in the ledger. Memory may challenge a
decision with new evidence but cannot amend its governing status. Repeated
inferences do not become a user statement; repeated copies of one incident do
not become independent observations.

Budget changes, authority policy and harvested rules, skills or hooks follow
their normal decision and change processes. A self-authored `approved` field
cannot grant authority.

Admission is not ranking. Validating syntax does not establish truth, and a
deterministic score over model-authored inputs does not remove model judgment.
Judgment is recorded and reviewable; selection is reproducible for fixed inputs.

### 5.4 Harvesting requirements

During dreaming, identify experiential lessons that warrant an amendment to:

- a rule for broadly applicable behavioural requirements;
- a skill for a particular procedure;
- a hook for an invariant whose condition and action path can be checked.

Propose the amendment through the existing process. After acceptance, record a
reference to the adopted artefact and reduce redundant exposure where appropriate.
Do not automatically delete the supporting evidence or treat the harvesting
proposal as an adopted instruction. Preserve the incident and rationale, but
mark copied procedural advice as historical and governed by the linked artefact.
Recall should lead to the current procedure rather than let an old prescription
compete with a subsequently amended skill. This needs a reference and explicit
qualification, not another lifecycle state.

## 6. Orientation, recent supplement and task recall

### 6.1 Orientation

Dreaming combines local and applicable shared candidates, deduplicates replicas
by UUID, and publishes a ranked candidate order plus a bounded readable default
index. There is no fixed local N plus shared M allocation.

At loading, a lightweight adapter checks current lifecycle and applicability,
walks the published order and selects what fits the orientation budget. It need
not invoke a model, embed a query or recompute importance.

**V5 drafting default:** publish a full ranked candidate order rather than only
the budget-sized excerpt. This permits refilling after current-context filtering
without moving ranking into the container. It replaces the earlier discussion's
temporary acceptance of underfilling solely because the published excerpt was
too short. Genuine lack of useful applicable candidates still leaves the view
underfilled.

The manifest must describe the fixed, available pool it ranks. An absent uncached shared body is
not a locally available candidate. New or semantically changed revisions belong
to the supplement, rather than inheriting an obsolete content score.

### 6.2 Recent-memory supplement

Accepted revisions not processed by the published dream snapshot are immediately
discoverable. At the next supported loading boundary, applicable entries can
enter a small recent supplement even though the orientation remains frozen.

This supplement has its own reserved allowance inside the total memory allocation.
It does not grow with the backlog. Overflow remains searchable by task recall.
Use deterministic freshness/relevance ordering with a stable tie-break, no
mandatory status and no self-awarded global authority.

A configurable freshness interval limits preferential exposure. Entries losing
that preference remain provisional until processed and remain searchable. Report
an ageing backlog rather than hiding it through expiry.

Suppress UUID duplication between components; if a new revision replaces an old
orientation revision, expose the current revision at most once. Never fall back
to obsolete advice merely because its replacement did not fit.

Retractions and supersessions are processed before positive selection, independent
of the supplement's content budget. Their effect cannot depend on ranking.

### 6.3 Task recall

Once the task is sufficiently clear, retrieve before the first consequential
action relevant to that task. An explicit user request to remember is unnecessary.
Refresh on a material task change or newly relevant constraint.

Search the whole eligible local plus available shared pool, including entries
below the orientation cut and unprocessed entries. Return relevant bodies or
focused excerpts with source identity, scope, status and links. Avoid repeating
content already supplied; keep qualifications with the advice they constrain.

The task bundle has a separate bounded allowance. Refresh replaces the logical
active bundle rather than accumulating bundles indefinitely. If the runtime
cannot remove old messages, track cumulative injected tokens, avoid repeats and
preserve only the current bundle through supported compaction. Report the
difference between active allocation and actual retained transcript cost.

## 7. Applicability, retrieval and ranking

### 7.1 Consuming context

Evaluate applicability against the consuming project's identity, environment and
available tool versions, bound to the actual checkout/corpus revision, not the
host that ran dreaming. A home-directory runtime store shared across worktrees
does not establish equal accepted knowledge on their different branches.
Task recall additionally
uses the current task.

Begin with explicit scope and only the small closed predicate subset that
consumer tasks require. Paths, bounded text checks and tool version conditions
are possible extensions, not a requirement to build a broad evaluator first. It must not execute arbitrary memory-authored shell code.
Bind paths to explicit roots and bound evaluation cost.

False excludes current use. Unknown is explicit and may remain a candidate with
a qualification; it is not positive evidence of applicability. Keyword absence
is not a hard exclusion.

At entry, reject malformed predicates and unknown grammar operators. For an
intended local, currently applicable observation, flag an evaluable false
predicate as a mismatch to resolve. An unevaluable predicate in a lightweight
container must not prohibit recording the observation: retain it as unverified,
with provenance, for later evaluation. This deliberately replaces v4's universal
write-time requirement that every predicate evaluate true. A container need not
possess every environment a reusable lesson describes.

Environmental predicates express only a subset of obsolescence. Decisions
reversed and observations disproved need explicit relations or lifecycle changes;
they cannot be inferred reliably from filesystem state.

### 7.2 Lexical baseline and optional semantics

Keywords and tags help retrieval, alongside title, description and body text.
They are useful for tool names, concepts and aliases. They do not define the
whole applicability boundary.

Lexical retrieval is the portable baseline. Empty or weak evidence may yield
an empty bundle; capacity is not an obligation to provide advice.

Embeddings are optional, initially most useful to dreaming for proposing related
groups. Their use must justify identifiable lexical misses. Embeddings suggest
similarity, not equivalence or contradiction resolution.

If implemented, a disposable embedding cache is keyed by content hash,
embedding model/version and preprocessing configuration. It is ignored by git.
Deleting it changes cost, not canonical knowledge. Numerical-equivalence tests
belong to that optional implementation, not the base memory contract.

Task-time semantic retrieval additionally needs a compatible query embedder.
Precomputed body vectors alone do not make semantic search available offline.
Absence of the model or cache falls back to lexical retrieval and reports the
capability difference.

### 7.3 Ranking and reproducibility

Rank eligible candidates using declared importance, cost of rediscovery,
project/task relevance, user emphasis and evidence of use. Observed opens remain
secondary: a useful title may prevent an action without a body read.

Preventive value can contribute weight but never grants mandatory residency.
No blanket preference awards local origin precedence over a more useful shared
lesson.

Orientation uses a static dream ranking plus current eligibility filtering;
it does not promise the optimal bundle for every consuming environment. Do not
pre-penalise particulars on the assumption that their generalisation will survive
runtime filtering.

Task recall may adjust for length and redundancy during selection. Once a
generalisation is selected there, a related particular must justify its additional
context cost; local conditions can justify it. Do not permanently penalise every
generalised source or force every active memory to fill remaining capacity.

Exact weights, thresholds and redundancy functions are versioned calibration
choices. Start simple. Record the ordered UUIDs and policy version in generated
manifests, not filenames. Component-score diagnostics are optional.

Reproduction requires more than the bodies:

`selection = F(corpus revisions, policy version, consuming context, evaluation time, task where relevant)`

A dream publication records its scoring inputs and evaluation time. A runtime
records the context used for filtering. Stable tie-breaking is required. Model
judgments enter as recorded annotations; semantic consolidation is not claimed
to regenerate identical prose from identical prompts.

## 8. Capacity policy

Fixed ceilings, variable occupancy and periodic measured recalibration are the
capacity policy. Do not increase limits automatically because the corpus grew.
Do not allocate a constant percentage of an advertised context window without
evidence of utility.

| Channel | Proposed initial ceiling | Status |
|---|---:|---|
| Orientation | 1,500 tokens | Calibration proposal |
| Recent supplement | 500 tokens | Calibration proposal |
| Task recall | 2,000 tokens | Calibration proposal |
| Total active allocation | 4,000 tokens | Sum of proposals; not a measured optimum |

These figures were proposed in the discussion, not separately ratified as
permanent values. They bound IDH-controlled memory exposure, including any native
projection implementing an IDH component. They exclude rules, skills, knowledge
hints, independent native memory, conversation and task evidence. Report these
other channels separately; 4,000 tokens is not a total-runtime-context claim.
Leaving capacity unused is acceptable.

Count the rendered payload, including headings, status labels, links and
identifiers. A runtime tokenizer is preferred where available. A portable
character or byte profile must disclose its estimation rule; it cannot claim an
exact token guarantee across models. Publication can carry derived estimates
without treating them as measurements.

Keep profiles versioned and fixed within a run. Compare half, baseline and double
allocations on representative tasks, changing one component at a time. Prefer
the smallest allocation with comparable task quality, recording latency, actual
injected tokens and cumulative refresh cost.

The persistent corpus has no score- or count-driven deletion cap. Monitor growth,
consolidation duration and unresolved backlog. Memory bodies can be cheap to
store without being free to retrieve, judge or maintain.

## 9. Dreaming and generalisation

Dreaming may run on a strong host with model access, the shared store and optional
embeddings. A consuming container need not run it.

### 9.1 Three distinct operations

| Operation | Identity and consequence |
|---|---|
| Broaden an unchanged lesson's scope | Same UUID; reviewed applicability change |
| Generalise observations into a broader claim | New UUID with `generalizes` references to sources |
| Replace obsolete or redundant advice | Explicit supersession; source becomes inactive |

The wire key `generalizes` retains its specified spelling; human prose uses UK
spelling. Compute the reverse relation rather than maintaining both directions
by hand.

Particular observations remain active after generalisation unless explicitly
superseded or retracted. A generalisation can be wrong while its source
observation remains correct. Local exceptions and evidence must survive.

If several redundant bodies are replaced by a synthesis, create a new UUID,
retain the originals inactive and identify the replacement. Reject cyclic
supersession and dangling replacement claims; a disputed replacement is not
resolved by choosing the latest timestamp.

**Rediscovery creates an opportunity, not an obligation.** Every rediscovery may
prompt consideration of whether the observations support a useful broader claim.
There is no occurrence threshold that automatically generalises, broadens scope,
or creates a synthesis. Leaving the particular memories unchanged is a valid
outcome, and the pass need not manufacture a generalisation to show progress.

Similar wording is a candidate signal, not proof of one lesson. Neither two
projects nor repeated copies automatically establish global applicability.
Generalisation requires an explicit judgment about shared conditions, independent
evidence, exceptions and usefulness, followed by the applicable review process.
Record the rationale for accepted generalisations; do not equate the number of
rediscoveries with confidence. A single sufficiently grounded observation can
support a proposed broader claim, while many recurrences may still support only
particular claims.

### 9.2 Pass responsibilities

Dreaming performs editorial work: it considers rediscoveries, proposes groups
and harvests, and lands only authorised semantic edits. The deterministic
compiler publishes views of accepted bodies and the fixed shared snapshot set.
It does not wait for pending generalisation proposals or repository reviews.

A dreaming command may invoke the compiler after accepted edits, but editorial
completion and publication are separate transactions. Scheduling compilation
alongside dreaming does not make semantic change a prerequisite for fresh views.

Record source revisions, accepted judgments and the model/prompt identity for
semantic changes. Reproducible compilation does not imply repeatable model prose.

A pass works in isolation and refuses to overwrite uncommitted bodies. A local
lock prevents local overlap; it does not establish exclusivity across machines.
Concurrent edits to the same UUID require a merge or explicit conflict state.
Independent additions and per-body granularity reduce contention without
eliminating semantic conflicts.

Review contradictory claims as well as near duplicates. A semantic report can
identify possible conflicts; it does not autonomously declare which decision
governs or which observation is false.

## 10. Publication and synchronisation

### 10.1 Snapshot and atomic handover

A publication manifest identifies:

- input project revision and relevant shared revisions;
- each processed UUID and body revision/hash;
- included snapshot bodies and source provenance;
- schema, generator and ranking-policy versions;
- evaluation time, contextual assumptions and budget profile;
- the fixed available candidate set and full ordered candidates;
- optional component-score diagnostics;
- hashes of emitted views.

Bodies processed but below the cut are still processed. Selection and processing
are different sets.

Publish related catalogues, snapshots and manifests as one coherent generation.
On disk, stage a generation and switch its reference atomically; a reader pins a
generation for its load. In git, commit the corresponding change set together.
Exact packaging may vary, but readers must not mix generations.

New or changed accepted body revisions absent from the processed manifest remain
recent, including writes made while dreaming ran. A timestamp alone is
insufficient. Record the actual processed set after editorial changes as well as
the original snapshot; do not leave newly produced synthesis bodies accidentally
unprocessed.

Before publication, reconcile against the current branch. Reject or rebase
conflicting semantic updates; do not overwrite a concurrent retraction or
publish a misleading claim of having processed a newer body. This is a
revision check, not a filesystem-lock assumption.

### 10.2 Loading and withdrawal

Each load pins two inputs: publication generation **G**, and one current accepted
corpus revision **C** for the consuming checkout. Orientation uses bodies whose
revisions still match G; accepted new or changed revisions in C feed the recent
supplement; withdrawals in C filter both. This deliberate current-state overlay
is not an accidental mixture of publication files. A withdrawal after C becomes
visible at the next supported boundary.

For the base implementation, accepted means committed through the applicable
project change process. Uncommitted candidates are the authoring session's work,
not silently published cross-session knowledge. A future accepted local overlay
would need its own explicit revision and review contract.

Refresh at session start and task boundaries. Resume, fork/child creation and
compaction recovery are also capability boundaries. Check locally known
withdrawals before consequential actions on supported interception paths.

Keep a small delivery record outside model-authored summaries: component,
publication, UUID and revision. It is session bookkeeping, not another canonical
store. Rebuild current bundles after compaction where supported; reset duplicate
suppression according to what remains in context, not merely what was ever sent.

A withdrawal suppresses advice even if the replacement is unavailable. Where
old text cannot be removed, deliver an explicit correction at the next supported
boundary and prevent stale re-injection. Opaque runtime summaries can retain
unattributed paraphrases: deterministic removal is not guaranteed there.
Measure adherence separately from correction delivery.

Offline consumers cannot know later upstream withdrawals. Once synchronisation
reveals one in the accepted corpus, it takes effect without waiting for dreaming.

### 10.3 Missing or damaged publication

Proposed fallback: validate local frontmatter and offer deterministic catalogue
browsing or lexical search over available active bodies. Report unavailable
ranking, missing shared coverage or unresolved identity conflicts. A malformed
file is reported, not silently certified active.

Do not claim successful complete generation from an empty enumeration. Positive
controls must distinguish an empty store from a broken walker. A missing cache
requires rebuilding or a slower path; a missing publication must not destroy
access to readable bodies.

## 11. Runtime adapters and graceful degradation

### 11.1 Native memory ownership

Each runtime profile declares native persistence as **disabled for this project**,
**managed projection**, or **independent coexistence**. IDH owns its canonical
experiential bodies; native-authored notes are admission candidates, not accepted
canonical writes. Never give an unrestricted native writer an alias to the
canonical store or its generated views.

Managed projections are disposable delivery representations. Avoid bidirectional
synchronisation between two editorial stores. Independent coexistence is allowed
but must disclose incomplete deduplication, withdrawal coverage and accounting.

Assign one delivery owner to each IDH component so native loading and an IDH hook
do not both inject it. Count controlled projections in the IDH budget and report
unobservable native payloads separately. Native feature activation must neither
duplicate a component nor silently remove it.

### 11.2 Capability declaration

| Aspect | Adapter declares |
|---|---|
| Persistence | Disabled, managed projection or independent |
| Writes | Admission path and canonical ownership |
| Delivery | Owner of each component and observable payloads |
| Boundaries | Start, task change, pre-action, resume, child and compaction |
| Isolation | Project identity, checkout and accepted revision binding |
| Accounting | Controlled budget and separately reported exposure |

### 11.3 Degradation


| Capability | Full adapter | Lightweight container | No harness |
|---|---|---|---|
| Read canonical bodies | Yes | Yes | Plain Markdown |
| Discover through catalogue | Yes | Yes | Ordinary relative links |
| Filter and budget orientation | Yes | Small local loader | Published default only |
| Recent supplement | Automatic at supported boundaries | Small local loader | Manual discovery; catalogue may lag |
| Task recall | Lexical, optional semantic | Lexical baseline | Manual search |
| Dreaming | Available on capable host | Not required | Not required |
| Shared knowledge | Live store plus snapshot | Snapshot; optional synchronisation | Readable snapshot |
| Withdrawal propagation | At instrumented boundaries | At supported boundaries | Explicit body status; no automatic guarantee |

Codex, Pi and Claude Code adapters share canonical schema and lifecycle semantics.
Runtime aliases and injection packaging are generated. No adapter may silently
switch off one delivery channel because a native recall feature activates.
It must supply an equivalent path or report the reduced capability.

A plain checkout guarantees intelligibility and local access, not automatic
discovery, timely filtering or prompt injection. Offline, harness-free operation
cannot be advertised as full behavioural equivalence.

A reader should be able to inspect the evidence and its status without access
to embeddings, an external database, private session traces or the original host.

## 12. Acceptance criteria

### 12.1 Deterministic contracts

Each gate includes a fixture that fails when the relevant mechanism is removed.

| Fixture | Required result |
|---|---|
| Fresh clone in a relocated disposable container, no original home directory | Local bodies and committed shared snapshot readable; relative navigation works |
| Same corpus and declared context across adapters | Equivalent eligibility, lifecycle handling and policy inputs; tokenizer-dependent cuts disclosed |
| Retracted body still present in stale orientation | Excluded at next supported load, even if incorrectly placed outside `inactive/` |
| Replacement is unavailable or below budget | Superseded advice remains suppressed; unavailability is reported |
| New write during dreaming | Present in the unprocessed set after publication |
| Concurrent edit/retraction to a processed UUID | Publication detects revision mismatch; no silent overwrite |
| Interrupted publication | Reader sees a complete old or new generation |
| False and unknown applicability | False excluded; unknown retains its label |
| Rediscovery in several projects | Candidate consideration only; no automatic scope change or synthesis |
| Accepted generalisation from particulars | New identity, intact sources and resolvable relations |
| Duplicate UUID replicas and divergent revisions | Replicas deduplicated; divergence reported |
| Cold cache, missing embedding model, no network | Lexical baseline works and reduced capability is explicit |
| Ranking manifest absent or corrupt | Local inspection remains possible; no false completeness claim |
| Oversized pool and repeated task changes | Per-component bounds hold; retained cumulative injection is measured |
| Entry workflow omits a routing outcome | Reject incomplete admission; semantic correctness is evaluated below |
| Native loading plus adapter enabled | One delivery owner per component; controlled exposure deduplicated and counted |
| Inject, compact, retract, resume/child | Current correction delivered at supported boundary; no stale re-injection |
| Memory and knowledge hints present | Canonical pointers deduplicated; caveats preserved; costs attributed |
| Generalisation filtered out | Particular retains its static rank; no assumed selection penalty |
| Shared candidate absent from snapshot | Unavailable candidate cannot be used for refill |
| Pending editorial review | Compilation of accepted bodies still succeeds |

Tests of publication atomicity and conflict handling concern machine behaviour.
A test that merely checks whether a skill contains a required sentence does not
prove the runtime honours the contract.

### 12.2 Behavioural evaluation

Run matched task scenarios with memory disabled, orientation alone and the full
delivery design. Include representative IDH maintenance, consumer-project coding
and research tasks. Repeat runs and report denominators, model/runtime versions
and uncertainty.

Evaluate whether agents:

- use a relevant lesson without an explicit request to recall it;
- obtain below-cut evidence through task recall;
- preserve a local exception when applying a generalisation;
- recognise a correction rather than repeat superseded advice;
- correctly route observations, decisions, project state and reusable artefacts;
- consult the current canonical procedure after harvesting;
- avoid inventing applicability when the environment is unknown;
- maintain task quality as irrelevant memories accumulate;
- remain usefully informed from a bare clone and an offline snapshot.

Measure task success, costly mistakes, unsupported memory use, unnecessary
retrieval, latency and total memory-related tokens. Body opens and ranking
misses are diagnostics, not the objective.

Deterministic invariants are hard acceptance gates. Behavioural success is a
measured rate, not a guarantee from one green run. Define task-specific
non-inferiority margins and desired gains before comparing budgets; numeric
release thresholds require calibration and are not invented here.

## 13. Migration and remaining choices

### 13.1 Migration outline

This is a design dependency outline, not a claim that the existing tickets
implement v5.

1. Freeze v4 and reconcile the architecture decisions through the project's
   decision-ledger process. Preserve prior review citations.
2. Specify the minimal schema, stable project identity and portable layout.
   Preserve historical dates before bulk rewriting; assign UUIDs with an
   auditable old-path-to-ID mapping and repair links.
3. Separate IDH project memory from shared memory. Move project-owned bodies
   into their repositories and introduce readable versioned shared snapshots.
4. Establish ledger routing at entry, lifecycle handling and canonical validation.
   Remove mandatory-memory residency from the design and any later implementation.
5. Implement deterministic publication, ranked candidate manifests, local loading
   and the recent supplement before relying on model-assisted consolidation.
6. Add lexical task recall and the adapter capability contract. Exercise fresh
   containers and no-harness browsing.
7. Add reviewed generalisation, semantic consolidation and harvesting on the
   strong host. Add embeddings only when justified.
8. Calibrate capacity and behavioural acceptance with the preserved evaluation
   fixtures.

Existing tickets 0908–0919 must be reviewed against this outline before execution.
Their v4 premises concerning promotion, identity, write-time validity and index
ownership cannot simply be retained. This document does not allocate or close
tickets, and it does not modify runtime code.

### 13.2 Explicit proposal boundaries

The principal architecture follows the owner's discussion. The following are
drafting defaults or calibration work, not claims of separately ratified detail:

| Item | V5 position |
|---|---|
| 1,500 / 500 / 2,000 tokens | Proposed initial profile |
| Full ranked manifest for load-time refilling | Recommended resolution of the earlier underfill alternative |
| Project identifier and exact directory names | Stable identity required; concrete format/layout to specify |
| Unknown write-time predicates | Preserve unverified observation; reject malformed grammar |
| Ranking weights, freshness interval and relevance threshold | Versioned calibration choices |
| Predicate operators and context probing | Bounded portable grammar to specify |
| Adapter refresh/interception coverage | Must be declared and verified per runtime |
| Behavioural release thresholds | Set from representative trials before claiming improvement |

No new database service, globally unique human slug scheme, automatic capacity
growth or memory-specific approval bureaucracy is required.

## 14. Decision trace and references

This section explains design changes and points to their source discussion.
It is not a substitute decision ledger. Adoption and subsequent changes belong
in the project's established decision process.

| V4 premise | V5 resolution |
|---|---|
| Mandatory resident memories | Removed; requirements harvested to rules, skills and hooks |
| Harness tier conflates infrastructure and shared knowledge | Ordinary IDH project memory plus separate shared scope |
| Local and harness indexes have independent resident allocations | Combined eligible pool within one orientation allocation |
| Promotion moves a lesson up and tombstones the local source | Distinguish scope expansion, generalisation and supersession |
| Filename provides identity | UUID identity; readable mutable filenames |
| Bodies unavailable until periodic scoring | Recent supplement and task recall expose accepted unprocessed revisions |
| Ranking supplies admission control | Entry routing and provenance precede ranking |
| Nothing deleted implies current advice remains safe | Explicit lifecycle, status-aware retrieval and historical access |
| File portability is enough | Fresh-container, offline-snapshot and no-harness contracts |
| Store alone reproduces a view | Record revisions, policy, context, time and task inputs |
| A generated index cannot drift | Revision-aware publication plus current-state filtering |
| Memory can carry commitments | Route decisions to the ledger at entry |

**Historical design and evidence**

- [Frozen v4](./2026-09-10-dragon-memory-design-v4.md): historical measurements,
  earlier runtime observations, review record and previous ticket plan.
- [Portable-memory calibration note](./2026-09-10-portable-agent-memory-calibration.md):
  earlier research synthesis; its numerical analogies are not v5 budget mandates.
- [Validity-coverage ledger](./2026-09-10-valid-while-coverage-ledger.md):
  limits of environmental predicates for real experiential memories.

**Research informing the capacity prior, not specifying the architecture**

- [LongMemEval](https://arxiv.org/abs/2410.10813): evaluates long-term interactive
  memory and indexing/retrieval/reading choices; does not establish an IDH
  resident-token optimum.
- [LazyMem v2](https://arxiv.org/abs/2607.22690v2), under review: reports compact
  answer-context memory using a trained query-time compressor. Its token figure
  excludes upstream work and is not a general allocation rule.
- [Scale-conditioned evaluation of agent memory](https://arxiv.org/abs/2605.07313),
  preprint: motivates evaluating usable reliability and retrieval burden as
  irrelevant evidence accumulates.

The draft's acceptance suite must assess IDH's own workloads. External benchmark
results do not certify this design or its adapters.

## 15. Comparison with other memory systems

The [companion comparison](./2026-09-11-memory-systems-comparison.md) examines
MemU, Letta, Mem0 and Graphiti against this design's actual requirements, using
primary project documentation checked on 11 September 2026. It separates
documented capabilities from IDH's design judgments and does not compare
incompatible benchmark scores.

The recommendation is to borrow patterns and evaluate optional strong-host
components before adopting another canonical memory backend. MemU's adapter
boundaries and agent/service separation are relevant; Letta shows that Git-backed
memory and background dreaming are not unique to IDH. Neither observation removes
the need to verify project-owned offline delivery, ledger routing and native
runtime ownership.

Keep IDH's base small: admission, canonical bodies, a compiler and a reader.
Embeddings, rich temporal graphs and automated synthesis must earn their place
against observed failures, without turning a disposable checkout into a service
deployment. This comparison does not authorise installation or migration.
