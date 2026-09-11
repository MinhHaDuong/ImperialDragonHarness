> **NON-NORMATIVE.** A naming proposal, recorded for information. The names below
> were settled in conversation with the owner on 2026-09-11; that makes them the
> design's working vocabulary, not harness policy. The norms live in `rules/`,
> `CLAUDE.md` and the tickets — not in `docs/`. Nothing here allocates a ticket
> or modifies runtime code.

**Recorded:** 2026-09-11. **Subject:** [design v6](./2026-09-10-dragon-memory-design.md) §16.1.

# Dragon memory — nomenclature

## 1. What this fills

Design v6 leaves its own interface unnamed, deliberately: "exact module names,
CLI verbs and dependency selections remain choices for the implementation work"
(§16). Three surfaces need names — the internal Python library, its CLI verbs,
and the canonical store directory. The runtime adapters share one ownership
contract and expose no public name; the editorial pass is already `/dream`.

Three things are explicitly **not** named here. The delivery channels —
orientation, recent supplement, task recall — are "responsibilities, not
additional user-facing commands" (§1); naming them as commands would contradict
the design. The lifecycle values `active` / `superseded` / `retracted` are
frontmatter data fixed by §4.3, not verbs. And the decision-ledger role is
"a role, not a mandatory new store" (§5.1).

## 2. The constraints that bind

`rules/authoring-skills.md` carries two, one of them ratcheted:

1. **Discoverability first.** The first sentence of a skill `description:` states
   the plain function; "Skill *names* may stay themed — the opening sentence is
   what a user scans." Enforced by `tests/test_skill_descriptions.py`, whose
   `THEME_LEXICON` bans `imperial dragon|dragons?|draconic|maws?|jaws?|fangs?|claws?|talons?|wyrms?|beasts?|devour*`
   from that first sentence. The test's own comment states the permission
   precisely: words "that double as skill names or ordinary verbs (raid, roar,
   beat, dream, molt, perch, scry, hunt, gaze, lair)" are legitimate — "the ban
   targets pure lore vocabulary."
2. **"The Imperial Dragon is not a bird. No avian analogies, in names,
   explanations or rationale. Scale, power, taxonomy."**

The ratchet reaches only the first sentence of skill descriptions. It does not
reach module names or CLI verbs, and the CLI is not user-facing in any case:
§16.1 exposes it "to skills, hooks and shell workflows". The human types
`/dream` and `/lair`. The working criterion for the verbs is therefore
**exactness, not discoverability** — which is why they may be specific where a
user-facing name would have to be plain.

## 3. Why `hoard`

Not a coinage. Ticket 0070, which opened the memory arc, already used it:
"dragons in their lair, dreaming over the hoard." The word is an ordinary
English noun and verb, absent from `THEME_LEXICON`, non-avian, and unclaimed by
any skill or module.

It also carries §8 correctly. The Harry Potter comparison is the natural one —
a Pensieve is an external basin holding what will not fit in a head, reviewed in
bounded sessions, which is exactly v6's uncapped corpus against a capped
injection (1,500 / 500 / 2,000 tokens). But a Pensieve is a **delesting** device:
its point is relief from surplus, which implies that forgetting is the goal. A
hoard is the opposite relation to accumulation — possession and vigilance, the
dragon that notices one missing cup. That is §8 as written: "The persistent
corpus has no score- or count-driven deletion cap. Monitor growth, consolidation
duration and unresolved backlog."

**`hoard` names the store and the library. It does not name the system.** A
single-vessel image — basin or pile — implies one pool and one access mode, and
v6 refuses that: §1 gives "three delivery components [that] handle different
timescales" and §6 gives each its own allowance. The architecture is a room
holding several instruments with different access disciplines, and the harness
already has the word for that room: `lair`, whose step 11 already runs `/dream`.

Two cautions on the room image, recorded because they are easy to re-derive
wrongly. Fawkes is a bird, excluded by rule 2 above, which bans avian analogies
in rationale and not only in names. And the portraits of former headmasters —
otherwise an excellent figure for shared memory, since a portrait is a
*generalised* predecessor rather than a recording (§9.1) — carry **authority**:
they opine, contradict and rule. v6 declines exactly that. §3.1: "Neither storage
location nor a score establishes authority." §9.2: a semantic report "does not
autonomously declare which decision governs or which observation is false."
§13.2 excludes "memory-specific approval bureaucracy." The figure must not be
extended to license a governance layer the design refuses.

## 4. The verbs

| v6 | Verb | Note |
|---|---|---|
| §5 Admission and authority | `hoard assay` | |
| §6.1, §7.3 Catalogue and ranked manifest | `hoard reckon` | |
| §10.1 Snapshot and atomic handover | `hoard seal` | |
| §6.3 Task recall | `hoard sift` | |
| §4.3 Superseded | `hoard shed <uuid> --by <uuid>` | successor required |
| §4.3 Retracted | `hoard disown <uuid>` | no successor accepted |
| §8 Growth monitoring | `hoard weigh` | measures; never caps |
| §9 Editorial pass | `/dream` | exists |

**`assay`.** The obvious verb was `admit`, and it is wrong — it names the
outcome and hides the operation. §5.1 opens "Before admitting a candidate, ask
which existing artefact owns the information", and its routing table sends most
candidates elsewhere: STATE, the ticket, the decision record, a skill, a
knowledge hint. Memory is the residual destination, "Experiential lesson not
otherwise captured." The operation is a judgment of ownership whose common case
is refusal, plus structural validation and an audience check. To assay is to
test metal for its title before it is accepted into a treasury — the same shape,
including the refusal.

**`shed` and `disown` are two verbs, not one verb with a flag.** §4.3 separates
superseded ("replacement advice exists") from retracted ("withdrawn without
necessarily having a replacement"), and the two resolve differently against
replacement links. Carrying the distinction in a flag makes the malformed call
writable and rejected afterwards; carrying it in the verb makes it unwritable.
`shed` without `--by` does not parse; `disown` takes no successor. Neither has
an implicit inverse — §4.3: "A retracted or superseded memory cannot revive
merely because a tool version or path changes. Restoration is an explicit
editorial act" — so any restoration is a further verb, never an `--undo`.

`disown` also closes the ownership loop that `assay` opens: entry asks whether
the body is ours, retraction withdraws that claim without asserting a successor.

## 5. Rejected, with reasons

| Candidate | For | Rejected because |
|---|---|---|
| `stash` | admission | reads as `git stash` in a Git-centred harness |
| `admit` | admission | names the outcome, hides the routing judgment |
| `claim` | admission | defensible — §5.1 is titled "Canonical ownership at entry" — but prejudges the answer the command exists to compute |
| `keep` | admission | flat; carries no judgment |
| `recast` | supersession | implies the original is consumed; §4.3 retains it inactive |
| `supersede` / `retract` | lifecycle | correct and self-documenting against the schema; kept as the fallback pair if the verb should literally equal the value it writes |
| Pensieve / office furniture | channels | §1 forbids making the channels commands; the portrait figure imports authority the design rejects |

## 6. Open

The `hoard` package layout, the store's directory name inside a project repo
(§3.2 leaves "the concrete format/layout to specify"), and whether a restoration
verb is needed at all.
