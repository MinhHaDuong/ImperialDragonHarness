// fang-audit.js — fan-out mutation-testing workflow (Workflow tool script).
//
// EXTRACTED from the proven prototype that produced the validating 19-file
// git-erg run (~1.3M tokens, ~29 min, 90 caught / 8 toothless, canary PASS).
// See skills/fang-audit/SKILL.md for the prototype→skill correspondence and
// the EXPENSIVE-RUN warning.
//
// Three mutation modes, ONE workflow (ticket 0219):
//   - fang     (sensitivity): behavior-CHANGING mutation → test must go RED.
//   - handcuff (robustness):  behavior-PRESERVING refactor → test must stay GREEN.
//   - scope    (altitude):    a caught mutation's operator replayed across
//                             sibling sites → siblings survive = instance-pinned.
//
// Just Work (tm), ticket 0219 directive 1: there is NO per-repo CONFIG block to
// pre-author. A run-start DISCOVERY phase reads the LAUNCH repo (Makefile,
// pyproject.toml, go.mod, the test tree, imports + call sites) and DERIVES the
// test command, the test↔source pairing table, and language mutation
// heuristics. This is informed derivation by READING — allowed. The BANNED
// thing is the blind filename-glob heuristic (X_test→X.go, which broke on
// refs_git→refs.go). Explicit knobs survive ONLY as optional OVERRIDES (args),
// never as prerequisites. Precedent: the 0184 test-quality.py runner/adapter.

export const meta = {
  name: 'fang-audit',
  description: 'Mutation-test the launch repo: does each test FAIL on the defect it claims to catch (fang), STAY GREEN under refactors (handcuff), and guard the whole defect CLASS (scope)? Reports a unified three-axis per-test table. No source/test changes persist. Discovers its own config — no per-repo setup. EXPENSIVE on-demand audit (the validating fang-only run was ~1.3M tokens / ~29 min).',
  phases: [
    { title: 'Discovery', detail: 'an agent reads the launch repo and derives test command + pairing table + mutation heuristics (no per-repo CONFIG)' },
    { title: 'Precheck', detail: 'determinism gate (flakiness re-run); abort if the suite is flaky' },
    { title: 'Audit', detail: 'fang pass — behavioral test files, one Opus agent each, mutate→test→revert in isolated worktrees' },
    { title: 'Skeptic', detail: 'Sonnet adversarially re-checks every survived/equivalent verdict' },
    { title: 'Handcuff', detail: 'robustness pass — behavior-PRESERVING refactors, inverted oracle (red = over-scoped), own skeptic' },
    { title: 'Scope', detail: 'altitude pass — replay each caught operator at sibling sites; surviving siblings = instance-pinned contract' },
    { title: 'Guards', detail: 'designated canary guard tests, serialized (perf-sensitive); skipped openly if none discovered/designated' },
    { title: 'Cleanup', detail: 'reclaim any hand-rolled scratch worktrees the audit agents left on detached HEAD' },
  ],
}

// ============================================================================
// OVERRIDES — there are NO required knobs (ticket 0219 directive 1). The
// DISCOVERY phase derives everything from the launch repo at run start. The
// keys below are the OPTIONAL overrides an invoker may pass via the Workflow
// `args` input to pin a value discovery would otherwise derive — NOT a
// prerequisite the user must author. Anything the args do not pin, discovery
// fills. The merge order is: discovery result, then args on top (an explicit
// override always wins over a derived value).
//
// Optional override keys (all may be omitted — discovery supplies them):
//   PROJECT, LANGUAGE, PACKAGE_HINT, SRC_DIR  — labels / orientation.
//   OUTPUT                                    — report path (default below).
//   RUN_TEST, DEFAULT_TAGS, GUARD_TAGS        — test command + tag variants.
//   MUTATION_HEURISTICS                       — minimal compiling mutation hints.
//   HANDCUFF_HEURISTICS                       — behavior-PRESERVING refactor hints.
//   BEHAVIORAL                                — test↔source pairing table.
//   GUARDS                                    — designated canary files (opt-in).
//   UNTRACKED_SEED                            — uncommitted build inputs to copy.
//   PRECHECK_CMD                              — the 0184 flakiness gate command.
//   RISK                                      — per-file risk multiplier (human-owned).
//   HOME                                      — for ~/ path expansion (sandbox has no process).
// ============================================================================

// Engine fallbacks for the few knobs that are not safety-critical to derive.
// These are NOT a pairing table or a test command (those MUST come from
// discovery or an explicit override — never a name heuristic). They are the
// inert defaults the report uses when neither discovery nor args supply them.
const FALLBACKS = {
  PROJECT: 'launch-repo',
  LANGUAGE: 'the launch repo',
  PACKAGE_HINT: '',
  SRC_DIR: '.',
  OUTPUT: '~/FANG-AUDIT.md',
  DEFAULT_TAGS: '',
  GUARD_TAGS: '',
  MUTATION_HEURISTICS:
    'a MINIMAL, COMPILING, behavior-CHANGING edit to a mapped source target: ' +
    'flip a boundary < to <=, drop a resource Close()/cleanup, skip a validation ' +
    'branch, off-by-one an index, negate a predicate',
  HANDCUFF_HEURISTICS:
    'a behavior-PRESERVING refactor of a mapped source target: rename a local ' +
    'variable, reorder two independent statements, swap an equivalent construct ' +
    '(for↔while, if-else↔ternary), change an UNEXPORTED representation that the ' +
    "tests should not observe. Must NOT change any value, ordering, or effect the " +
    "test legitimately depends on — only the internal form.",
  BEHAVIORAL: [],
  GUARDS: [],
  UNTRACKED_SEED: [],
  PRECHECK_CMD: '',
  RISK: {},
}

// ============================================================================
// ENGINE — repo-agnostic below this line.
// ============================================================================

// Normalize args (ticket 0223: the harness may deliver args as a JSON-encoded
// STRING). These are the OPTIONAL overrides — every key may be absent.
let _args = args
if (typeof _args === 'string') { try { _args = JSON.parse(_args) } catch { _args = null } }
if (!(_args && typeof _args === 'object')) _args = {}
const HOME = typeof _args.HOME === 'string' ? _args.HOME : ''
const expand = p => (typeof p === 'string' && HOME) ? p.replace(/^~(?=\/)/, HOME) : p

// ---- Phase 0a: DISCOVERY (read-only — derive config from the launch repo) ----
// An agent reads the repo and DERIVES the test command, the test↔source
// pairing table, mutation + handcuff heuristics, and (optionally) guard
// candidates. Read-only: NON-isolated (no mutation, like the skeptic). The
// derived object merges UNDER the args, so an explicit override always wins.
const DISCOVERY_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  properties: {
    PROJECT: { type: 'string' },
    LANGUAGE: { type: 'string' },
    PACKAGE_HINT: { type: 'string' },
    SRC_DIR: { type: 'string', description: 'directory the test command runs in, relative to repo root' },
    RUN_TEST: { type: 'string', description: 'the cache-busting test command; <TAGS> placeholder for build-tag flags' },
    DEFAULT_TAGS: { type: 'string' },
    GUARD_TAGS: { type: 'string' },
    PRECHECK_CMD: { type: 'string', description: 'the 0184 test-quality.py flakiness gate invocation for this repo' },
    MUTATION_HEURISTICS: { type: 'string' },
    HANDCUFF_HEURISTICS: { type: 'string' },
    BEHAVIORAL: { type: 'array', items: {
      type: 'object', additionalProperties: false,
      properties: {
        test: { type: 'string' },
        src: { type: 'array', items: { type: 'string' } },
        rationale: { type: 'string', description: 'WHY this pairing — the import/call-site evidence, proving it is read-derived not glob-derived' },
      },
      required: ['test', 'src'],
    } },
    evidence: { type: 'string', description: 'what files were read (Makefile/pyproject/go.mod/test tree) and how the command + pairings were derived' },
  },
  required: ['RUN_TEST', 'BEHAVIORAL', 'SRC_DIR'],
}

phase('Discovery')
const discovered = await agent(
  `You are the DISCOVERY phase of a mutation-testing audit. You run in the LAUNCH repo (the repo this session is rooted in). Your job: by READING the repo, DERIVE the configuration the audit needs. Do NOT guess from filenames alone — derive from real evidence (build files, imports, call sites). The blind filename-glob heuristic (X_test → X.go) is BANNED: it returned a NONEXISTENT file for 5 of 19 git-erg tests, including both canaries.

READ (as available — different repos use different ones):
  - Build/test config: Makefile, pyproject.toml, go.mod, package.json, Cargo.toml, pytest.ini/tox.ini, justfile.
  - The test tree: every test file (Go *_test.go, Python tests/test_*.py / *_test.py, etc.).
  - For EACH test file, its imports and the symbols it calls — that is how you map it to the SOURCE file(s) it actually exercises. A test that imports and calls funcs from foo.go pairs to foo.go; a test exercising several modules pairs to all of them (non-1:1 is normal — encode it).

DERIVE and return:
  - RUN_TEST: the exact test command, WITH a cache-buster (go: -count=1; pytest: -p no:cacheprovider; cargo: cargo test) — a cached PASS would falsely exonerate a mutation. Put a <TAGS> placeholder where build-tag flags go (empty string if the language has no build tags). SRC_DIR = the directory the command runs in.
  - PRECHECK_CMD: the 0184 determinism gate for this repo, of the form 'python3 ~/.claude/scripts/test-quality.py flakiness --package-dir <DIR> --runs 3' (Go) or the documented adapter invocation for the language. If the 0184 utility has no adapter for this language, return PRECHECK_CMD as an empty string (the precheck will then warn-and-proceed, not hard-gate).
  - MUTATION_HEURISTICS: language-specific examples of a MINIMAL, COMPILING, behavior-CHANGING mutation.
  - HANDCUFF_HEURISTICS: language-specific examples of a behavior-PRESERVING refactor (rename local, reorder independent statements, equivalent-construct swap, unexported-representation change).
  - BEHAVIORAL: the explicit test↔source pairing table — one {test, src:[...], rationale} per behavioral test file. The rationale MUST cite the import/call-site evidence, so it is provably read-derived, not name-derived.
  - PROJECT / LANGUAGE / PACKAGE_HINT: orientation labels.
  - evidence: which files you read and how you derived the command + pairings.

Do NOT designate guard/canary files — that is an explicit human opt-in (passed as an override), never auto-discovered. Do NOT mutate anything. Return the structured object.`,
  { label: 'discovery:launch-repo', phase: 'Discovery', schema: DISCOVERY_SCHEMA }
).catch(e => { log(`discovery agent error: ${e}`); return null })

if (!discovered || !Array.isArray(discovered.BEHAVIORAL) || !discovered.BEHAVIORAL.length) {
  if (!_args.BEHAVIORAL || !_args.BEHAVIORAL.length) {
    const msg = 'ABORT: discovery did not derive a test↔source pairing table and no BEHAVIORAL override was supplied. Cannot audit without knowing which source each test exercises (the banned filename-glob heuristic is the only alternative — refused). Re-run from the target repo root, or pass an explicit BEHAVIORAL override.'
    log(msg)
    return { aborted: true, reason: msg, discovered }
  }
  log('discovery returned no pairing table; falling back to the explicit BEHAVIORAL override supplied in args.')
}

// Merge order (ticket 0219 directive 1): FALLBACKS < discovery < args.
// An explicit override always wins over a derived value; a derived value
// always wins over the inert engine fallback. No required per-repo CONFIG.
const CONFIG = Object.assign({}, FALLBACKS, discovered || {}, _args)
// Normalize the derived/overridden BEHAVIORAL to the engine's {test, src} shape
// (discovery adds a `rationale` the engine ignores).
CONFIG.BEHAVIORAL = (CONFIG.BEHAVIORAL || []).map(p => ({ test: p.test, src: p.src }))
CONFIG.GUARDS = CONFIG.GUARDS || []
CONFIG.RISK = CONFIG.RISK || {}
CONFIG.OUTPUT = expand(CONFIG.OUTPUT)
CONFIG.UNTRACKED_SEED = (CONFIG.UNTRACKED_SEED || []).map(s => ({ ...s, from: expand(s.from) }))
log(`discovery: ${CONFIG.BEHAVIORAL.length} test↔source pairings, RUN_TEST="${CONFIG.RUN_TEST}", ${CONFIG.GUARDS.length} designated guard(s).`)

const { BEHAVIORAL, GUARDS } = CONFIG

const AUDIT_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  properties: {
    testFile: { type: 'string' },
    sourceFiles: { type: 'array', items: { type: 'string' } },
    testFuncs: { type: 'array', items: { type: 'string' }, description: 'Test* funcs defined in this test file' },
    baselineGreen: { type: 'boolean', description: 'did the suite pass before any mutation' },
    hasNegativeControl: { type: 'boolean' },
    findings: { type: 'array', items: {
      type: 'object',
      additionalProperties: false,
      properties: {
        behavior: { type: 'string' },
        testFunc: { type: 'string' },
        mutation: { type: 'string' },
        result: { type: 'string', enum: ['caught', 'survived', 'equivalent', 'compile-error', 'skipped'] },
        failingTests: { type: 'array', items: { type: 'string' } },
        sameFileCaught: { type: 'boolean' },
        isCanary: { type: 'boolean' },
        survivedJustification: { type: 'string' },
        evidence: { type: 'string' },
        suggestion: { type: 'string' },
      },
      required: ['behavior', 'testFunc', 'mutation', 'result'],
    } },
    summary: { type: 'string' },
  },
  required: ['testFile', 'findings', 'summary'],
}

const SKEPTIC_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  properties: {
    finalVerdict: { type: 'string', enum: ['survived', 'equivalent'] },
    reasoning: { type: 'string' },
    distinguishingInput: { type: 'string' },
  },
  required: ['finalVerdict', 'reasoning'],
}

// Δ5 — determinism precheck schema (new; not in prototype).
const PRECHECK_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  properties: {
    exitCode: { type: 'integer', description: 'exit code of the flakiness gate (0 = stable, 2 = new flakiness)' },
    gate: { type: 'string', description: 'the "gate" field from the JSON report: "pass" or "fail"' },
    flakyTests: { type: 'array', items: { type: 'string' }, description: 'identities flagged flaky, if any' },
    evidence: { type: 'string', description: 'the raw command + a short excerpt of its JSON stdout' },
  },
  required: ['exitCode', 'gate'],
}

const RULES = `
PROCEDURE (do exactly this):
1. Read <SRC_DIR>/<TESTFILE> and the source target(s). List every Test* function defined IN THE TEST FILE — call this OWN_FUNCS (needed for step 5).
2. Confirm baseline is green: <RUN_TEST>  must PASS. Set baselineGreen. If it does NOT pass at baseline, STOP: return one finding result="compile-error" with evidence, and baselineGreen=false.
3. Identify the distinct behaviors / invariants / defect-classes the tests claim to enforce — ONE per test func or meaningful assertion cluster. Choose between 1 and 8, proportional to the number of test funcs (tiny files get 1-2; large files get more).
4. For EACH behavior, in sequence:
   a. Apply ONE minimal, COMPILING, behavior-changing mutation to a mapped source target that represents the REAL defect class the test exists to catch (<MUTATION_HEURISTICS>). Not a strawman, not a no-op.
   b. Run: <RUN_TEST>   — capture output.
   c. Record the names of all FAILED tests into failingTests.
   d. ALWAYS restore pristine before the next mutation: git checkout -- <the source file you edited>. Never hand-revert.
   If a mutation does not COMPILE, set result="compile-error" and try a different compiling mutation for that behavior.
5. CLASSIFY each finding (precision is everything):
   - "caught": failingTests intersects OWN_FUNCS (a test defined in THIS file went red). Set sameFileCaught=true. This file has a real fang.
   - If tests failed but NONE are in OWN_FUNCS (only sibling files caught it): sameFileCaught=false, and this file gets NO fang credit -> result="survived"; in evidence name which sibling caught it.
   - "survived" (TOOTHLESS — an accusation): no OWN_FUNC failed, AND you can exhibit a concrete input within this test's domain where the mutated code is observably WRONG. Put that input + expected-vs-actual in survivedJustification.
   - "equivalent" (NOT an accusation): no test failed and you CANNOT construct a distinguishing input. Put a POSITIVE argument for why the mutation is behavior-neutral on the test's domain in survivedJustification (not merely "didn't find one").
6. For every "survived" finding, put a concrete fix in suggestion: a stronger assertion, or a negative-control test (deliberately break the invariant and assert the guard trips).
You are in an isolated throwaway git worktree at the repo root — all your edits are discarded; mutate freely. Return the structured object.`

function applyRules(tags) {
  return RULES
    .replaceAll('<RUN_TEST>', CONFIG.RUN_TEST.replaceAll('<TAGS>', tags))
    .replaceAll('<TAGS>', tags)
    .replaceAll('<MUTATION_HEURISTICS>', CONFIG.MUTATION_HEURISTICS)
    .replaceAll('<SRC_DIR>', CONFIG.SRC_DIR)
}

function auditPrompt(file) {
  return `You are mutation-testing whether a ${CONFIG.LANGUAGE} test has "fangs": does it actually FAIL when the code it covers is broken? Repo: ${CONFIG.PROJECT}, ${CONFIG.PACKAGE_HINT}.

ASSIGNMENT
- Test file: ${file.test}
- Source target(s) you may mutate: ${file.src.join(', ')}
- <TAGS> = (none — this is a default-suite test; run with no build tags)
${applyRules(CONFIG.DEFAULT_TAGS).replaceAll('<TESTFILE>', file.test)}`
}

// Untracked inputs the guard build needs but that are absent from a fresh
// worktree (only the committed tree propagates). The guard agent copies these
// in before the baseline check — Δ from the prototype only in that the source
// path is a CONFIG knob, not hardcoded. Empty list => no copy line.
const SEED_INSTRUCTIONS = (CONFIG.UNTRACKED_SEED || [])
  .map(s => `    test -f ${s.dest} || cp ${s.from} ${s.dest}`)
  .join('\n')

function guardPrompt(file) {
  const seed = SEED_INSTRUCTIONS
    ? `\n- Some test inputs the guard build needs are UNTRACKED and may be ABSENT from this worktree. Copy each in if missing, FIRST:\n${SEED_INSTRUCTIONS}`
    : ''
  return `You are mutation-testing a designated GUARD/canary test for ${CONFIG.PROJECT}, ${CONFIG.PACKAGE_HINT}. These guard tests already ship "negative controls"; your job is to confirm the guard's PRIMARY invariant actually trips under a real defect, then audit its other assertions.

ASSIGNMENT
- Test file: ${file.test}
- Source target(s): ${file.src.join(', ')}
- <TAGS> = ${CONFIG.GUARD_TAGS}   (REQUIRED — these files only compile under the guard build tag)

SETUP (do FIRST):${seed}
- Then confirm the guard build compiles AND passes at baseline with the guard tags. If it does not, STOP and return one finding result="compile-error" describing the baseline failure.

CANARY (your FIRST mutation — set isCanary=true on this finding):
${file.canary}
The canary MUST classify as "caught" (a guard test in this file goes red). If it does NOT, that is a critical signal the harness is miswired — still report it truthfully.

After the canary, audit the file's OTHER assertions per the standard procedure.
${applyRules(CONFIG.GUARD_TAGS).replaceAll('<TESTFILE>', file.test)}`
}

function skepticPrompt(file, f) {
  const dir = f.result === 'survived'
    ? `This is a "survived" verdict — an ACCUSATION that the test is toothless. Your job is to REFUTE it. Try hard to prove EITHER (a) the mutation is actually EQUIVALENT — behavior-neutral on every input the test legitimately exercises — OR (b) a sibling test elsewhere does catch it so the accusation is mis-scoped. If you find a real input where the mutated code is observably wrong AND it is in this test's domain, the accusation stands. Default to finalVerdict="equivalent" (accusation withdrawn) if you are uncertain.`
    : `This is an "equivalent" verdict — the audit agent claimed it could NOT distinguish the mutation. Your job is the INVERSE: try hard to CONSTRUCT a concrete input, within this test's legitimate domain, where the mutated code produces observably WRONG output. If you succeed, finalVerdict="survived" (this is a real fang gap the audit missed) and put the input in distinguishingInput. If the mutation truly is behavior-neutral, finalVerdict="equivalent".`
  return `Cross-model adversarial check of a mutation-testing verdict on ${CONFIG.PROJECT} test ${file.test} (source: ${(f.sourceFiles||file.src).join(', ')}).

BEHAVIOR: ${f.behavior}
MUTATION APPLIED: ${f.mutation}
TEST THAT SHOULD CATCH IT: ${f.testFunc}
AUDIT AGENT'S JUSTIFICATION: ${f.survivedJustification || '(none given)'}
FAILING TESTS OBSERVED: ${(f.failingTests||[]).join(', ') || '(none)'}

${dir}

You may read the files (${file.test} and the source) to reason precisely, but you do NOT need to run the test suite. Return finalVerdict + reasoning (+ distinguishingInput if relevant).`
}

async function skepticize(audit, file) {
  if (!audit || !Array.isArray(audit.findings)) return audit
  const targets = audit.findings
    .map((f, i) => ({ f, i }))
    .filter(x => x.f.result === 'survived' || x.f.result === 'equivalent')
  if (!targets.length) return audit
  const verdicts = await parallel(targets.map(x => () =>
    agent(skepticPrompt(file, x.f), {
      label: `skeptic:${file.test}:${x.f.testFunc}`.slice(0, 60),
      phase: 'Skeptic', model: 'sonnet', schema: SKEPTIC_SCHEMA,
    })
  ))
  verdicts.forEach((v, k) => {
    if (!v) return
    const i = targets[k].i
    audit.findings[i].skepticVerdict = v.finalVerdict
    audit.findings[i].skepticReasoning = v.reasoning
    if (v.distinguishingInput) audit.findings[i].skepticDistinguishingInput = v.distinguishingInput
    audit.findings[i].result = v.finalVerdict // skeptic has final say on survived<->equivalent
  })
  return audit
}

// ---- Δ5: Phase 0 — determinism precheck GATE (blocks the fan-out) ----
phase('Precheck')
// Δ0219: discovery may report no PRECHECK_CMD when the 0184 utility has no
// adapter for the launch repo's language. The gate then degrades to
// warn-and-proceed (an OPEN skip, never a faked PASS) rather than aborting a
// language it simply cannot pre-vet. The report records the un-vetted state.
let precheckSkipped = false
if (!CONFIG.PRECHECK_CMD) {
  precheckSkipped = true
  log('precheck SKIPPED openly — discovery found no 0184 flakiness adapter for this language; verdicts are NOT determinism-vetted. Stabilize manually before trusting toothless rows.')
}
const precheck = precheckSkipped ? { exitCode: 0, gate: 'skipped' } : await agent(
  `Run the determinism precheck for ${CONFIG.PROJECT} and report the result. You cannot mutation-test a flaky suite, so this gate runs BEFORE any mutation.

Run EXACTLY this command from the repo root and capture its exit code and stdout:
    ${CONFIG.PRECHECK_CMD}

This is the 0184 test-quality utility's flakiness gate. Exit-code contract:
  - exit 0 = suite is stable (or all flakiness is baselined) -> gate "pass"
  - exit 2 = NEW flakiness found -> gate "fail"
The JSON report on stdout carries a "gate" field ("pass"/"fail"); read it to confirm. Report exitCode, gate, any flaky test identities, and a short evidence excerpt. Do NOT mutate anything.`,
  { label: 'precheck:flakiness', phase: 'Precheck', schema: PRECHECK_SCHEMA }
).catch(() => null)  // Δ10: a precheck agent error falls into the abort path below, not an opaque crash

if (!precheck || precheck.exitCode !== 0 || precheck.gate === 'fail') {
  const detail = precheck
    ? `exit ${precheck.exitCode}, gate=${precheck.gate}${precheck.flakyTests && precheck.flakyTests.length ? ', flaky: ' + precheck.flakyTests.join(', ') : ''}`
    : 'precheck agent returned nothing'
  // Distinguish a real flaky verdict (exit 2 AND gate=="fail") from a
  // mis-invocation (argparse usage error also exits 2) before declaring flaky.
  const flaky = precheck && precheck.exitCode === 2 && precheck.gate === 'fail'
  const msg = flaky
    ? `ABORT: suite is flaky, verdicts untrustworthy — ${detail}. Stabilize the suite (see the flakiness report) before running the fang audit.`
    : `ABORT: determinism precheck did not pass cleanly — ${detail}. Cannot trust mutation verdicts on an un-vetted suite.`
  log(msg)
  return { aborted: true, reason: msg, precheck }
}
if (!precheckSkipped) log(`precheck PASS — suite stable (exit ${precheck.exitCode}, gate=${precheck.gate}); proceeding to mutation audit.`)

// ---- Phase 1+2: behavioral audit -> skeptic (pipeline, no barrier) ----
phase('Audit')
// Δ8: isolation:'worktree' — Workflow agents run in the SESSION checkout by
// default (probe-verified 2026-06-05, ticket 0221); without per-agent
// worktrees the concurrent mutate→test→revert loops corrupt each other.
// This also binds the run to the session's repo: invoke from a session
// rooted in the TARGET repo (see SKILL.md). Skeptics stay non-isolated —
// read-and-judge, no execution.
const behavioral = await pipeline(
  BEHAVIORAL,
  file => agent(auditPrompt(file), { label: `audit:${file.test}`, phase: 'Audit', schema: AUDIT_SCHEMA, isolation: 'worktree' })
            .then(a => { if (a) a.testFile = a.testFile || file.test; return a }),
  (audit, file) => skepticize(audit, file),
)

// ---- Phase 3: guards, SERIALIZED (M3 — perf-sensitive, no concurrent load) ----
phase('Guards')
const guards = []
for (const file of GUARDS) {
  // Δ10: a single guard-agent failure must not discard the behavioral results
  // already collected — degrade to null (the canary gate then reports SUSPECT,
  // which is the honest verdict when a guard agent dies).
  let a = await agent(guardPrompt(file), { label: `audit:${file.test}`, phase: 'Guards', schema: AUDIT_SCHEMA, isolation: 'worktree' })  // Δ8
    .catch(e => { log(`guard ${file.test} agent error: ${e}`); return null })
  // Δ7: tag findings from this run STRUCTURALLY as canary-guard findings.
  // Canary designation comes from CONFIG.GUARDS (the workflow knows which
  // agent it dispatched), NEVER from a read-back of the agent's isCanary flag.
  if (a) { a.testFile = a.testFile || file.test; a._isGuardFile = true; a = await skepticize(a, file) }
  guards.push(a)
  log(`guard ${file.test}: ${a ? (a.findings.filter(f => f.isCanary).map(f => f.result).join(',') || a.findings[0]?.result) : 'null'}`)
}

const all = [...behavioral, ...guards].filter(Boolean)

// ---- Deterministic report assembly (no LLM formatting of N objects) ----
const esc = s => String(s == null ? '' : s).replace(/\n+/g, ' ').replace(/\|/g, '\\|').trim()
const base = p => String(p || '').split('/').pop()
// Δ7: carry _isGuardFile down onto each finding so canary scoping is by
// CONFIG-dispatched role, not by a self-asserted flag.
const flat = all.flatMap(a => (a.findings || []).map(f => ({ ...f, _file: base(a.testFile), _isGuardFile: !!a._isGuardFile })))
const survived = flat.filter(f => f.result === 'survived')
const equivalent = flat.filter(f => f.result === 'equivalent')
const caught = flat.filter(f => f.result === 'caught')
const compileErr = flat.filter(f => f.result === 'compile-error')
const gaps = survived.filter(f => !(f.failingTests && f.failingTests.length))      // nothing anywhere caught it
const siblingOnly = survived.filter(f => f.failingTests && f.failingTests.length)   // a sibling file caught it, this file didn't

// Δ7: Canary = the designated guard files' primary canary mutations ONLY.
// Scope by the structural _isGuardFile tag (set from CONFIG.GUARDS dispatch),
// NOT by the agent-supplied isCanary flag — behavioral agents sometimes
// mis-set isCanary on their own findings and pollute this gate (the prototype
// patched this ad hoc with a filename regex; the principle is now baked in:
// canary designation is a workflow input, never an agent claim).
const canaryFindings = flat.filter(f => f._isGuardFile && f.isCanary)
const canaryOK = canaryFindings.length >= GUARDS.length && canaryFindings.every(f => f.result === 'caught')

// ---- Δ4: FREE-RIDER metrics (oracle-strength + diagnosticity) ----
// Both derived from the mutation data already collected — NO extra runs.
//  - diagnosticity: on a caught mutant, how FEW tests fired? Fewer red tests
//    => the failure bisects sharply to the cause. Per caught finding.
//  - oracle-strength: per test func, how MANY mutants did it kill? A weak
//    assertion (!= nil) kills few; a strong one (== expected) kills many.
const diagnosticity = caught
  .map(f => ({ file: f._file, testFunc: f.testFunc, mutation: f.mutation, testsFired: (f.failingTests || []).length }))
  .sort((a, b) => a.testsFired - b.testsFired)
const oracleByFunc = {}
caught.forEach(f => {
  const key = `${f._file}::${f.testFunc}`
  oracleByFunc[key] = (oracleByFunc[key] || 0) + 1
})
const oracleStrength = Object.entries(oracleByFunc)
  .map(([k, kills]) => ({ key: k, mutantsKilled: kills }))
  .sort((a, b) => b.mutantsKilled - a.mutantsKilled)

// ---- Δ6: risk × churn weighting for the per-test report sort ----
// Churn = commit count per file from git log (the workflow asks an agent for
// it once, cheaply); risk = the human-supplied CONFIG.RISK multiplier
// (default 1.0). The toothless rows are sorted by risk × churn DESC so the
// highest-blast-radius × change-frequency gaps surface first. Risk is NEVER
// inferred — per the ticket, the human owns that judgment.
// `churnByFile` is populated by the churn agent below; default 0 keeps the
// sort total even if churn is unavailable.
// Δ10: churn is DECORATION (a sort weight) — it must never kill the run. The
// 2026-06-05 run died HERE at the finish line: the tool layer serialized the
// agent's integer values as strings, the integer-typed schema rejected them,
// and the uncaught throw discarded 1.36M tokens of completed audit work.
// Tolerant schema (string|integer) + parseInt + try/catch => worst case is a
// flat churn of 0 and a degraded sort, never a dead run.
const churnByFile = await (async () => {
  const files = [...new Set(flat.map(f => f._file))]
  try {
    const res = await agent(
      `For ${CONFIG.PROJECT}, report the git churn (number of commits that touched the file) for each of these test files, using \`git log --follow --oneline -- <file> | wc -l\` from the repo root. Files: ${files.join(', ')}. Return a JSON object mapping each filename to its commit count (a plain number; a numeric string is also accepted).`,
      { label: 'churn:git-log', phase: 'Guards',
        schema: { type: 'object', additionalProperties: { type: ['integer', 'string'] } } }
    )
    return Object.fromEntries(Object.entries(res || {}).map(([k, v]) => [k, parseInt(v, 10) || 0]))
  } catch (e) {
    log(`churn agent failed (${e}); risk×churn sort degrades to churn=0 — report otherwise valid`)
    return {}
  }
})()

const riskWeight = f => (CONFIG.RISK[f._file] || 1.0)
const churnWeight = f => (churnByFile[f._file] || 0)
const rxc = f => riskWeight(f) * churnWeight(f)
const survivedRanked = [...survived].sort((a, b) => rxc(b) - rxc(a))

const L = []
L.push(`# Fang Audit — \`${CONFIG.PROJECT}\` ${CONFIG.LANGUAGE} test harness`)
L.push('')
L.push('_Mutation-testing audit: each test was probed by breaking the code it covers and checking whether the test goes red. Generated by the `fang-audit` fan-out workflow. No source or test files were changed in the repo — all mutations lived and died in throwaway worktrees._')
L.push('')
L.push('## Canary (validity gate)')
L.push('')
if (canaryOK) {
  L.push('✅ **PASS** — every designated guard test caught its primary canary mutation, so the mutation harness itself works and the findings below are trustworthy:')
  canaryFindings.forEach(f => L.push(`- \`${f._file}\` → **${f.result}** — ${esc(f.mutation)}`))
} else {
  L.push('🛑 **FAIL / SUSPECT** — a guard canary did not classify as `caught`. The harness may be miswired (or the guard-tag / untracked-input setup failed). **Treat the toothless list with caution.** Canary results:')
  canaryFindings.forEach(f => L.push(`- \`${f._file}\` → **${f.result}** — ${esc(f.mutation)}`))
  if (canaryFindings.length < GUARDS.length) L.push(`- (only ${canaryFindings.length} canary finding(s) reported; expected ${GUARDS.length})`)
}
L.push('')
L.push('## Summary')
L.push('')
L.push('| Verdict | Count |')
L.push('|---|---|')
L.push(`| 🦷 **toothless** (\`survived\` — mutation went undetected by the file's own tests) | **${survived.length}** |`)
L.push(`| &nbsp;&nbsp;↳ of which ⚠️ **true coverage gap** (no test *anywhere* caught it) | ${gaps.length} |`)
L.push(`| &nbsp;&nbsp;↳ of which caught only by a *sibling* file (this file lacks the fang) | ${siblingOnly.length} |`)
L.push(`| ✅ fang confirmed (\`caught\` by a same-file test) | ${caught.length} |`)
L.push(`| 🔵 inconclusive (\`equivalent\` — no distinguishing input exists) | ${equivalent.length} |`)
L.push(`| 🔧 compile-error (mutation skipped) | ${compileErr.length} |`)
L.push(`| **files audited** | ${all.length} / ${BEHAVIORAL.length + GUARDS.length} |`)
L.push('')
L.push('_Counts are mutations probed, not tests. The 🦷 toothless rows are the actionable headline; the two sub-rows partition them. `caught` is the healthy majority._')
L.push('')

L.push('## 🦷 Toothless tests (survived a real, distinguishing mutation) — sorted by risk × churn')
L.push('')
if (!survived.length) L.push('_None — every probed behavior was caught by a same-file test, or was inconclusive._')
else {
  L.push('| Test file | Test func | risk×churn | Mutation | Distinguishing input (why it\'s wrong) | Suggested fang |')
  L.push('|---|---|---|---|---|---|')
  survivedRanked.forEach(f => L.push(`| \`${esc(f._file)}\` | \`${esc(f.testFunc)}\` | ${rxc(f).toFixed(1)} (r${riskWeight(f)}×c${churnWeight(f)}) | ${esc(f.mutation)} | ${esc(f.survivedJustification)} | ${esc(f.suggestion)} |`))
  L.push('')
  L.push('_Each row survived both the Opus audit and the Sonnet adversarial skeptic. "Distinguishing input" is a concrete case where the mutated code is observably wrong yet no same-file test failed. Sorted by risk × churn so the highest-blast-radius × change-frequency gaps surface first; risk is the human-supplied weight (default 1)._')
}
L.push('')

if (gaps.length) {
  L.push('### ⚠️ Coverage gaps (no test anywhere caught the mutation)')
  L.push('')
  gaps.forEach(f => L.push(`- \`${esc(f._file)}\` / \`${esc(f.testFunc)}\` — ${esc(f.behavior)}: ${esc(f.mutation)}`))
  L.push('')
}

L.push('## 🔵 Inconclusive (equivalent mutants — NOT accusations)')
L.push('')
if (!equivalent.length) L.push('_None._')
else {
  L.push('| Test file | Test func | Mutation | Why behavior-neutral |')
  L.push('|---|---|---|---|')
  equivalent.forEach(f => L.push(`| \`${esc(f._file)}\` | \`${esc(f.testFunc)}\` | ${esc(f.mutation)} | ${esc(f.survivedJustification || f.skepticReasoning)} |`))
}
L.push('')

L.push('## ✅ Confirmed fangs (caught by a same-file test)')
L.push('')
L.push('<details><summary>' + caught.length + ' confirmed — expand</summary>')
L.push('')
L.push('| Test file | Test func | Mutation | Caught by |')
L.push('|---|---|---|---|')
caught.forEach(f => L.push(`| \`${esc(f._file)}\` | \`${esc(f.testFunc)}\` | ${esc(f.mutation)} | ${esc((f.failingTests||[]).join(', '))} |`))
L.push('')
L.push('</details>')
L.push('')

// Δ4: free-rider sections (oracle-strength + diagnosticity) from existing data.
L.push('## 🧬 Oracle strength (free rider — mutants killed per test func)')
L.push('')
L.push('_A strong oracle (e.g. `== expected`) kills many mutants; a weak one (`!= nil`) kills few. Derived from the mutation data already collected — no extra runs._')
L.push('')
if (!oracleStrength.length) L.push('_No caught mutants to rank._')
else {
  L.push('| Test func | Mutants killed |')
  L.push('|---|---|')
  oracleStrength.forEach(o => L.push(`| \`${esc(o.key)}\` | ${o.mutantsKilled} |`))
}
L.push('')

L.push('## 🎯 Diagnosticity (free rider — tests fired per killed mutant)')
L.push('')
L.push('_On red, does the suite bisect to the cause? FEWER tests firing per killed mutant = sharper diagnosis. Derived from the same data — no extra runs._')
L.push('')
if (!diagnosticity.length) L.push('_No caught mutants to rank._')
else {
  L.push('| Test file | Test func | Mutation | Tests fired |')
  L.push('|---|---|---|---|')
  diagnosticity.forEach(d => L.push(`| \`${esc(d.file)}\` | \`${esc(d.testFunc)}\` | ${esc(d.mutation)} | ${d.testsFired} |`))
}
L.push('')

L.push('## Per-file summaries')
L.push('')
all.forEach(a => {
  const c = (a.findings||[]).reduce((m, f) => { m[f.result] = (m[f.result]||0)+1; return m }, {})
  const tag = Object.entries(c).map(([k,v]) => `${v} ${k}`).join(', ')
  L.push(`- **\`${a.testFile}\`** (${tag})${a.hasNegativeControl ? ' · _has negative control_' : ''} — ${esc(a.summary)}`)
})
L.push('')
L.push('## Next step (out of scope here)')
L.push('Applying the suggested fangs is a follow-up ticket — this audit changes no test code. Spot-check 2–3 toothless rows against their distinguishing input before acting.')

return { report: L.join('\n'), output: CONFIG.OUTPUT, canaryOK,
  counts: { survived: survived.length, gaps: gaps.length, caught: caught.length, equivalent: equivalent.length, compileErr: compileErr.length, files: all.length },
  freeRiders: { oracleStrength, diagnosticity }, churnByFile, raw: all }
