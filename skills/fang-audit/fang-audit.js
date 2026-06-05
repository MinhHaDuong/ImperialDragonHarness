// fang-audit.js — fan-out mutation-testing workflow (Workflow tool script).
//
// EXTRACTED from the proven prototype that produced the validating 19-file
// git-erg run (~1.3M tokens, ~29 min, 90 caught / 8 toothless, canary PASS).
// See skills/fang-audit/SKILL.md for the prototype→skill correspondence and
// the EXPENSIVE-RUN warning. This is fang-only v1 (ticket 0182); handcuff,
// scope/altitude, and the three-axis report live in ticket 0219.

export const meta = {
  name: 'fang-audit',
  description: 'Mutation-test the configured test harness: does each test FAIL on the defect it claims to catch? Reports toothless tests. No source/test changes persist. EXPENSIVE on-demand audit (the validating run was ~1.3M tokens / ~29 min).',
  phases: [
    { title: 'Precheck', detail: 'determinism gate (flakiness re-run); abort if the suite is flaky' },
    { title: 'Audit', detail: 'behavioral test files, one Opus agent each, mutate→test→revert in isolated worktrees' },
    { title: 'Skeptic', detail: 'Sonnet adversarially re-checks every survived/equivalent verdict' },
    { title: 'Guards', detail: 'designated canary guard tests, serialized (perf-sensitive)' },
  ],
}

// ============================================================================
// DEFAULTS — the validated git-erg reference configuration, kept as living
// documentation of every knob. Δ9: NEVER edit this file per repo — the target
// repo owns its config in `.fang-audit.json` at its root, which the SKILL.md
// invocation reads and passes as the Workflow `args` input; args override
// these defaults key-by-key. Everything below the merge is the repo-agnostic
// engine (verbatim from the prototype except the marked deltas).
// ============================================================================

const DEFAULTS = {
  // Human-readable name of the project under audit (report title only).
  PROJECT: 'YOUR-PROJECT',

  // Where the workflow writes the final report. Throwaway worktrees die with
  // the run, so this MUST be an absolute path in the MAIN repo (untracked is
  // fine). NO hardcoded /home — use an absolute path you control, e.g.
  // `${process.env.HOME}/your-repo/FANG-AUDIT.md`.
  OUTPUT: `${process.env.HOME}/YOUR-REPO/FANG-AUDIT.md`,

  // <TAGS> = build-tag flags for the DEFAULT suite (usually empty string).
  DEFAULT_TAGS: '',
  // <TAGS> for the guard (perf-sensitive) suite, e.g. '-tags scaling'.
  GUARD_TAGS: '-tags scaling',

  // RUN_TEST — the language-specific test command each agent runs, as prose
  // embedded in the procedure. The engine substitutes <TAGS>. Keep <COUNT>
  // (the cache-busting flag) explicit: a cached PASS would falsely exonerate a
  // mutation. Go example below; for other languages give the equivalent
  // (e.g. `pytest -p no:cacheprovider`, `cargo test`).
  RUN_TEST: 'cd src/go && go test <TAGS> -count=1 ./...',

  // Language label + the package/working directory the test command runs in,
  // surfaced in prompts so the agent orients. SRC_DIR is the directory holding
  // the test + source files, relative to the repo root (used in the procedure
  // text the agent follows).
  LANGUAGE: 'Go',
  PACKAGE_HINT: 'package main, in src/go/',
  SRC_DIR: 'src/go',

  // UNTRACKED_SEED (M4) — inputs the test build needs that are NOT committed,
  // so a fresh worktree (which only has the committed tree) lacks them. The
  // guard agent copies each from `from` into `dest` if missing, BEFORE the
  // baseline check. Empty list = no seeding (fully generic). Keep `from` paths
  // out of the /home/[a-z] form — use ${process.env.HOME}.
  // (The git-erg guard build references an untracked resource_test.go that
  // shares the //go:build scaling compile unit with scaling_test.go; without
  // it the scaling build fails to compile and the canary falsely FAILs.)
  UNTRACKED_SEED: [
    { dest: 'src/go/resource_test.go', from: `${process.env.HOME}/git-erg/src/go/resource_test.go` },
  ],

  // Mutation heuristics — language-specific examples of a MINIMAL, COMPILING,
  // behavior-CHANGING mutation. These steer the agent away from strawmen.
  MUTATION_HEURISTICS:
    'flip a boundary < to <=, drop a Close(), skip a validation branch, ' +
    'off-by-one an index, negate a predicate',

  // TEST↔SOURCE pairing table (M1). NOT a name heuristic — an explicit map.
  // Non-1:1 repos always need this; even 1:1 repos benefit from the audit
  // trail. `test` is the test file, `src` the source target(s) it may mutate.
  BEHAVIORAL: [
    { test: 'atomicwrite_test.go', src: ['atomicwrite.go'] },
    { test: 'check_test.go',       src: ['check.go'] },
    { test: 'close_test.go',       src: ['close.go'] },
    { test: 'config_test.go',      src: ['config.go'] },
    { test: 'contract_test.go',    src: ['check.go', 'list.go', 'validate.go'] },
    { test: 'erg_test.go',         src: ['erg.go'] },
    { test: 'identity_test.go',    src: ['identity.go'] },
    { test: 'list_test.go',        src: ['list.go'] },
    { test: 'migrate_test.go',     src: ['migrate.go'] },
    { test: 'new_test.go',         src: ['new.go'] },
    { test: 'nextid_test.go',      src: ['nextid.go'] },
    { test: 'ref_test.go',         src: ['ref.go'] },
    { test: 'refs_test.go',        src: ['refs.go'] },
    { test: 'refs_git_test.go',    src: ['refs.go'] },
    { test: 'resolve_test.go',     src: ['main.go'] },
    { test: 'tag_test.go',         src: ['tag.go'] },
    { test: 'validate_test.go',    src: ['validate.go'] },
  ],

  // GUARDS — DESIGNATED canary files (perf-sensitive guard tests with a known
  // primary invariant). `canary` is the explicit, workflow-author-written
  // mutation that MUST trip the guard. Canary designation is a CONFIG input —
  // NEVER an agent claim (this is the isCanary-pollution fix, crit 7).
  GUARDS: [
    { test: 'scaling_test.go', src: ['erg.go'],
      canary: 'In erg.go make loadErgs (line ~664) re-parse each ticket more than once — e.g. wrap the per-file parse in a nested loop over the corpus so total work is O(N^2). This reintroduces the quadratic re-parse the scaling guard exists to catch; TestScalingLinear* must go red.' },
    { test: 'resource_test.go', src: ['check.go', 'list.go', 'close.go', 'rm.go', 'ready.go', 'erg.go'],
      canary: 'Introduce a file-descriptor leak in a corpus read/command path exercised by TestScalingFDHygiene (the cmdCheck/cmdList/cmdReady/cmdClose/cmdRm read path). E.g. os.Open a file (or open a git pipe) without closing it, or delete a Close()/defer f.Close() on the ticket-read path. TestScalingFDHygiene must report a leaked fd.' },
  ],

  // DETERMINISM PRECHECK (crit 5) — the cheap, zero-token gate run BEFORE any
  // mutation. Delegated to the 0184 utility's flakiness subcommand (exit 0 =
  // stable, exit 2 = new flakiness). You cannot mutation-test a flaky suite.
  // The precheck agent runs this verbatim and reports the exit code + JSON.
  PRECHECK_CMD:
    'python3 ~/.claude/scripts/test-quality.py flakiness --package-dir src/go --runs 3',

  // RISK weights (crit 6) — OPTIONAL per-file risk multiplier for the report
  // sort. The ticket is explicit: do NOT automate the risk judgment — risk is
  // a human-supplied input. Default 1.0 for any file not listed. Example: a
  // security invariant (header-injection sanitize) outranks a cosmetic check.
  RISK: {
    // 'identity_test.go': 3.0,
  },
}

// ============================================================================
// ENGINE — repo-agnostic below this line. Verbatim from the prototype except
// where marked Δ.
// ============================================================================

// Δ9: per-repo config arrives via the Workflow `args` input (read from the
// target repo's `.fang-audit.json` by the SKILL.md invocation) and overrides
// DEFAULTS key-by-key. Tilde-expand the two path-bearing knobs script-side —
// JSON cannot carry `${process.env.HOME}`.
const expand = p => typeof p === 'string' ? p.replace(/^~(?=\/)/, process.env.HOME) : p
const CONFIG = Object.assign({}, DEFAULTS, (args && typeof args === 'object') ? args : {})
CONFIG.OUTPUT = expand(CONFIG.OUTPUT)
CONFIG.UNTRACKED_SEED = (CONFIG.UNTRACKED_SEED || []).map(s => ({ ...s, from: expand(s.from) }))

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
const precheck = await agent(
  `Run the determinism precheck for ${CONFIG.PROJECT} and report the result. You cannot mutation-test a flaky suite, so this gate runs BEFORE any mutation.

Run EXACTLY this command from the repo root and capture its exit code and stdout:
    ${CONFIG.PRECHECK_CMD}

This is the 0184 test-quality utility's flakiness gate. Exit-code contract:
  - exit 0 = suite is stable (or all flakiness is baselined) -> gate "pass"
  - exit 2 = NEW flakiness found -> gate "fail"
The JSON report on stdout carries a "gate" field ("pass"/"fail"); read it to confirm. Report exitCode, gate, any flaky test identities, and a short evidence excerpt. Do NOT mutate anything.`,
  { label: 'precheck:flakiness', phase: 'Precheck', schema: PRECHECK_SCHEMA }
)

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
log(`precheck PASS — suite stable (exit ${precheck.exitCode}, gate=${precheck.gate}); proceeding to mutation audit.`)

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
  let a = await agent(guardPrompt(file), { label: `audit:${file.test}`, phase: 'Guards', schema: AUDIT_SCHEMA, isolation: 'worktree' })  // Δ8
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
const churnByFile = await (async () => {
  const files = [...new Set(flat.map(f => f._file))]
  const res = await agent(
    `For ${CONFIG.PROJECT}, report the git churn (number of commits that touched the file) for each of these test files, using \`git log --follow --oneline -- <file> | wc -l\` from the repo root. Files: ${files.join(', ')}. Return a JSON object mapping each filename to its commit count.`,
    { label: 'churn:git-log', phase: 'Guards',
      schema: { type: 'object', additionalProperties: { type: 'integer' } } }
  )
  return res || {}
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
