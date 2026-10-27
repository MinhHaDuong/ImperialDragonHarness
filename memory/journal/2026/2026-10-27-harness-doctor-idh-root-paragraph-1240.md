# Harness doctor visit: the IDH_ROOT helper paragraph (ticket 1240)

Date: 2026-10-27. Project: Imperial Dragon Harness. Audience: public.

Measured on commit cd127a9e (raid wave base). Run as a raid executor on
ticket 1240. The ticket body is the author's complaint, and the author named
1240 in the raid, so the visit counts as called. No probe spent model usage,
so the visit needed no consent stop.

## Complaint

Sixteen `skills/*/SKILL.md` open with the same paragraph, "For helper
commands, set `IDH_ROOT=...`". Is this a skill restating what another owns
(checklist item 2), and what should be done?

## Precondition and controls

- `scripts/harness_here.sh`: exit 0.
- Lint control (`tests/fixtures/harness-doctor/trace-doctor-SKILL.md`): fired.
  It raised `body_lines`, `date`, `history_phase` and `long_fence`.
- Reading control: found the known overlap with test-doctor
  (`skills/harness-doctor/SKILL.md:18` and `:100`, recorded in
  `references/checklist.md`). Fired.
- Runtime-supply control: in this session, Claude Code 2.1.311 injected the
  hunt skill with the header `Base directory for this skill:
  /home/haduong/.claude/skills/hunt`. That is a directory, not a SKILL.md
  path (see F1).

## Recount (cd127a9e)

- 38 SKILL.md files. Sixteen carry the paragraph: 14 verbatim (325 bytes),
  plus hoard (the seam line, then its own three-line wording) and
  verify-gate (207 bytes, without the last sentence). Roar spells the same
  derivation in two steps, without the paragraph. In total about 5 KB.
- All 16 use `$IDH_ROOT`, from 1 use (release) to 8 (molt). None carries the
  paragraph without using it.
- All 16 contain the exact `SEAM_LINE` code fragment (65 bytes), the hoard
  and verify-gate variants included.
- Per-load cost (derived, not measured): 325 bytes is about 80 tokens per
  loaded skill, 1.2 to 5.4 % of a seam-bearing body (bodies run 5976 to
  26276 bytes). The paragraph is not resident; each load pays it once.

## Hypotheses and what separated them

| H | Prior | Separating observation | Result |
|---|-------|------------------------|--------|
| H1: necessary per-skill cost (each runtime supplies only the loaded skill's own location; bodies load alone) | 0.55 | `adapters/README.md` § seam; `pilot-support.json` `healthcheck-each-runtime-supplies-the-loaded-path` | Confirmed for the seam *code* |
| H2: some carriers never run helpers | 0.10 | grep `$IDH_ROOT` per carrier | Excluded: all 16 use it |
| H3: the prose around the code could be shorter; the tests do not pin it | 0.25 | `tests/test_skill_seam.py`: `SEAM_RE` matches only the code fragment; hoard and verify-gate already differ and pass | Confirmed |
| H4: the runtime could supply the root itself | 0.10 | 0803 gate ("no IDH_HOME, zero of three runtimes needed it"); Claude Code supplies a directory, not a root | Excluded without new runtime work |

The raid annotation says that shortening one verbatim copy fails
`test_the_canonical_one_line_spelling_dominates`. That holds only if the
copy loses the code fragment. Rewording the prose leaves both seam tests
green, as hoard and verify-gate show.

## Diagnosis

The duplication is mostly necessary, and the seam tests encode it on purpose.
Each body must carry the 65-byte derivation because only the loading runtime
knows where that body lives. The 260 bytes of prose around it are
convention, not a constraint the tests enforce. They are also load-bearing in
one way the contract does not record (F1).

Checklist item 2 does not apply as written. No skill owns the seam, so no
owner can drift away from the copies. The owner is the adapters contract and
the test file, and the copies are ratcheted to them.

Confidence: high (0.85) that the code must stay per-skill. Medium (0.6) that
the prose is worth editing at all, given about 80 tokens per load.

Unexplained:
- Why Claude Code's injection names a directory when the adapters contract
  (measured 2026-09-28 on 2.1.283) says it supplies the SKILL.md path.
  Either the runtime changed or the contract was always loose; not isolated.
- What Codex and Pi supply today was not checked (see the runtime table).
- How often sessions load several seam-bearing skills was not measured, so
  the session-level cost stays a per-load figure.

## Findings

- **F1, below the floor (reported, not ticketed).**
  `skills/hunt/SKILL.md:7` (and the 13 other verbatim copies) tells the model
  to "Replace `<loaded-SKILL.md>` with the absolute path the runtime supplied
  for this skill". `adapters/README.md:126-127` states that the runtime
  supplies the SKILL.md path. On Claude Code 2.1.311 the supplied value is the
  skill *directory*.
  - Substituting it literally gives `IDH_ROOT=/home/haduong` instead of
    `/home/haduong/.agents` (reproduced in this visit). The first helper call
    then fails with "No such file".
  - The failure is visible and recoverable, so it sits below the floor. It is
    still a plausible wrong root, which `test_skill_seam.py` says the idiom
    never yields.
  - Smallest fix: one clause in the shared sentence, "the SKILL.md path; on a
    runtime that names the skill directory, append `/SKILL.md`", plus a
    line in `adapters/README.md`.
- Lint on the 17 seam-bearing bodies: 61 hits (history_phase 39, body_lines
  10, project_name 5, ticket_word 2, long_fence 2, history_used_to 2,
  date 1). None touches the paragraph. They are outside this complaint and
  were not judged one by one; a triage visit should take them. The lint does
  not detect cross-file duplication, so its silence on the complaint is not
  evidence.

## Runtime evidence

| Runtime | Diagnostic | Ran | Showed |
|---------|------------|-----|--------|
| Claude Code 2.1.311 | This session's skill injection; seam substitution with both values | ran | Supplies the base directory. The SKILL.md path resolves to the harness root; the directory resolves one level too high |
| Codex | Probe-skill smoke (`pilot-support.json`, manual) | unavailable (spends model usage, consent not sought in a raid) | Last evidence: 0.157.0, 2026-09-28 |
| Pi | Same | unavailable (same reason) | Last evidence: 0.87.1, 2026-09-28 |

## Options (author decides)

| Option | What changes | Author-hours | Agent cost | Odds it settles the complaint | Undo | Seam tests | Three runtimes |
|--------|--------------|--------------|------------|-------------------------------|------|------------|----------------|
| **A. Accept, recorded (recommended)** | One paragraph in `skills/harness-doctor/references/checklist.md`: the seam code is necessary per body; the prose is convention | 0.25 | about USD 0.5 | 0.9 | revert one commit | untouched | untouched |
| B. Shorten the prose to one canonical sentence and fold in the F1 clause | 16 bodies, `adapters/README.md` | 0.5 | about USD 3-5, plus about USD 2 for a Codex and Pi re-smoke | 0.7 (saves about 40-60 tokens per load; the risk is a wording a runtime misreads) | revert | green if `SEAM_LINE` is kept (hoard and verify-gate prove it) | needs a yawn smoke on Codex and Pi; Claude Code checkable in session |
| C. Move the prose to a resident rule; keep only the code line in bodies | `rules/`, 16 bodies, the Codex and Pi adapters' rule loading | 0.5-1 | about USD 5 | 0.35: it trades about 80 tokens per load for about 65 tokens in *every* session on every runtime, so it is a net loss unless most sessions load 2 or more seam skills | revert | green | each adapter must load the rule; Pi and Codex unverified |
| D. Runtime-supplied root (env var or install-time field) | `bin/idh install`, three adapters, 16 bodies, tests, contract | 2 | about USD 15-30 | 0.3: it reopens the 0803 gate that found zero runtimes needed it | multi-file revert | rewrite the ratchet | new plumbing per runtime; unknown for Codex |
| E. Nothing | none | 0 | 0 | 0.5 (the complaint stays open, without a recorded reason) | n/a | n/a | n/a |

Recommendation: **A**, with F1 fixed alongside as its own small ticket if the
author wants it. That fix is 0.1 author-hour and about USD 1 for the clause,
plus the Codex and Pi re-smoke if it touches all 16 bodies. The duplication
holds 65 bytes of necessary code per body; the rest is about 80 tokens per
load, which is not worth a 16-file churn and a three-runtime re-smoke.

## Tickets filed

None (F1 is below the floor). Findings above the floor: 0.

## Revisit

- No earlier visit entry exists ("no prior visit"; the 2026-10-27 landing
  entry records the doctor's construction, not a visit).
- Revisit condition: rerun the seam substitution with the value Claude Code
  injects, and the recount (`grep -l 'For helper commands, set' skills/*/SKILL.md`),
  after any Claude Code upgrade, after any edit to the paragraph or to
  `adapters/README.md` § seam, or when the count of seam-bearing skills
  passes 20.
