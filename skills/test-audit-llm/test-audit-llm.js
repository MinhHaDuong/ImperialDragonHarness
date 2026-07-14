// test-audit-llm.js — read-and-judge test-quality audit (Workflow tool script).
//
// Sibling to maw-audit (ticket 0182/0219), DIFFERENT MECHANISM (ticket 0183):
// maw-audit MUTATES the source and RUNS the suite to mechanize three lenses
// (fang / handcuff / scope). A second family of test-quality lenses cannot be
// measured that way — they require READING the test and JUDGING intent, with NO
// execution. This skill is that judge. It runs NOTHING: no mutation, no test
// run, no worktrees. One judge agent per test file READS the file and returns a
// verdict on each of four lenses in a single pass.
//
// Four read-and-judge lenses (one judge, all four — NOT four passes):
//   - faithfulness   : does the test exercise prod-like paths, or a mocked
//                      fiction that stays green while production breaks?
//   - intent         : can a reader tell WHICH contract is asserted and WHY,
//                      without running it? (name lies / passes for wrong reason)
//   - negative-space : does it test error paths/boundaries/empty/huge inputs,
//                      or only the happy path?
//   - change-detector: does it assert HOW the code works (call sequences, mock
//                      interaction order) instead of WHAT it produces?
//
// Cost tier (ticket 0183): a BULK pass judges every file with the cheap model
// (haiku); only flagged / low-confidence FILES escalate to the strong model
// (sonnet), capped at the top K=8 by severity x churn so a large suite can never
// fan a second full wave. The sonnet re-judgement REPLACES the haiku verdict for
// those files (final say), mirroring maw-audit's skeptic.
//
// Composition (ticket 0183 exit criterion 4): findings are keyed on the
// repo-relative TEST-FILE path — the same identity maw-audit reports (its
// `file.test`). This skill reports at FILE granularity; 0184's per-function
// `<package>::<TestName>` and 0229's `<file>::<function>` are finer-grained, so
// composition with them is a FILE-LEVEL roll-up on the shared file key. The
// exit criterion offers "compose OR a clean standalone report"; this is the
// clean standalone with a shared file key.
//
// ADVISORY ONLY (ticket 0183 exit criterion 5): verdicts are SOFT judgment, not
// a passing/failing oracle. The report banner says so. Findings feed ticket
// creation (`tickets/erg new`), never a CI hard-gate and never a failing exit
// code. There is no canary/validity gate to fake — these are opinions, ranked.
//
// Just Work (tm): there is NO per-repo CONFIG block. A run-start DISCOVERY phase
// reads the launch repo and DERIVES the test-file list + framework conventions
// the judge needs for context. Because this skill EXECUTES NOTHING, discovery is
// far slimmer than maw-audit's: NO test command, NO test->source pairing table,
// NO mutation heuristics — just the files to judge. Explicit knobs survive only
// as OPTIONAL overrides (args), never as prerequisites.

export const meta = {
  name: 'test-audit-llm',
  description: 'Read-and-judge audit of test quality: one judge reads each test file and scores four lenses (faithfulness/test-reality gap, intent legibility, negative-space coverage, change-detector smell). Runs nothing — no mutation, no test run. Cheap-model bulk pass + strong-model escalation for the top flagged files. Advisory only: findings feed ticket creation, never a CI gate.',
  phases: [
    { title: 'Discovery', detail: 'an agent reads the launch repo and derives the test-file list + framework conventions (no per-repo CONFIG, no test command — nothing is executed)' },
    { title: 'Judge', detail: 'bulk pass — one cheap-model (haiku) judge per test file, four lenses in one read; no execution' },
    { title: 'Escalate', detail: 'strong-model (sonnet) re-judge of the top-K flagged/low-confidence files by severity x churn; sonnet replaces the bulk verdict for those files' },
    { title: 'Report', detail: 'deterministic no-LLM assembly: one row per finding {identity, lens, severity, rationale, suggestion}; markdown + JSON sidecar, keyed on the repo-relative test-file path' },
  ],
}

// ============================================================================
// OVERRIDES — there are NO required knobs. The DISCOVERY phase derives the
// test-file list from the launch repo at run start. The keys below are the
// OPTIONAL overrides an invoker may pass via the Workflow `args` input to pin a
// value discovery would otherwise derive. Anything the args do not pin,
// discovery fills. Merge order: FALLBACKS < discovery < args (an explicit
// override always wins).
//
// Optional override keys (all may be omitted):
//   PROJECT, LANGUAGE, FRAMEWORK  — orientation labels / judge context.
//   OUTPUT                        — report path (default below); JSON sidecar is
//                                   OUTPUT with the extension replaced by .json.
//   TEST_FILES                    — explicit list of repo-relative test files to
//                                   judge (skips/overrides discovery's list).
//   ESCALATE_K                    — top-K files to escalate to the strong model
//                                   (default 8 — caps the second wave).
//   RISK                          — per-file risk multiplier (human-owned).
//   HOME                          — for ~/ path expansion (sandbox has no process).
// ============================================================================

const ESCALATE_K_DEFAULT = 8

const FALLBACKS = {
  PROJECT: 'launch-repo',
  LANGUAGE: 'the launch repo',
  FRAMEWORK: '',
  OUTPUT: '~/TEST-AUDIT-LLM.md',
  TEST_FILES: [],
  ESCALATE_K: ESCALATE_K_DEFAULT,
  RISK: {},
}

// ============================================================================
// ENGINE — repo-agnostic below this line.
// ============================================================================

// Normalize args (the harness may deliver args as a JSON-encoded STRING; the
// Workflow sandbox has no Node `process`/`require`). Every override key is
// optional.
let _args = args
if (typeof _args === 'string') { try { _args = JSON.parse(_args) } catch { _args = null } }
if (!(_args && typeof _args === 'object')) _args = {}
const HOME = typeof _args.HOME === 'string' ? _args.HOME : ''
// The sandbox has no `process`, so a leading ~/ in a path is expanded only if
// the invoker passes HOME explicitly (mirrors maw-audit's expand guard).
const expand = p => (typeof p === 'string' && HOME) ? p.replace(/^~(?=\/)/, HOME) : p

// ---- Phase 0: DISCOVERY (read-only — derive the test-file list to judge) ----
// An agent reads the launch repo and DERIVES the list of test files plus the
// framework/conventions a judge needs for context. Read-only and NON-isolated:
// this skill executes nothing, so there is nothing to isolate. The derived
// object merges UNDER the args, so an explicit override always wins.
//
// Slimmer than maw-audit's discovery ON PURPOSE: no RUN_TEST, no test->source
// pairing table, no mutation heuristics — those exist in maw-audit only because
// it executes and mutates. A read-and-judge audit needs only the files.
const DISCOVERY_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  properties: {
    PROJECT: { type: 'string' },
    LANGUAGE: { type: 'string' },
    FRAMEWORK: { type: 'string', description: 'the test framework + conventions the judge should assume (e.g. "pytest, unittest.mock", "go testing + testify")' },
    TEST_FILES: {
      type: 'array',
      minItems: 1,
      items: { type: 'string', minLength: 1, description: 'a repo-root-relative test file path' },
      description: 'every test file to judge, as a repo-root-relative path',
    },
    evidence: { type: 'string', description: 'how the test tree + framework were identified (which build/config files and directories were read)' },
  },
  required: ['TEST_FILES'],
}

phase('Discovery')
const discovered = await agent(
  `You are the DISCOVERY phase of a READ-AND-JUDGE test-quality audit. You run in the LAUNCH repo (the repo this session is rooted in). This audit EXECUTES NOTHING — no test runs, no mutation. Your ONLY job is to enumerate the test files to judge and identify the framework, by READING the repo.

READ (as available — different repos use different ones):
  - Build/test config: pyproject.toml, pytest.ini/tox.ini, go.mod, package.json, Cargo.toml, Makefile — to learn the test framework + where tests live + any collection-exclusion rules (e.g. pytest norecursedirs).
  - The test tree: enumerate every test file (Python tests/test_*.py or *_test.py, Go *_test.go, JS *.test.js / *.spec.js, etc.).

DERIVE and return:
  - TEST_FILES: every test file to judge, each as a repo-ROOT-relative path (e.g. "tests/test_foo.py", not an absolute path and not a bare basename). EXCLUDE files the project deliberately does not collect (e.g. anything under a pytest norecursedirs directory such as skills/*/fixtures — those are audit anchors, not project tests). Each path must be a REAL file you saw in the tree.
  - FRAMEWORK: the test framework + mocking conventions the judge should assume.
  - PROJECT / LANGUAGE: orientation labels.
  - evidence: which config files + directories you read.

Do NOT run anything. Do NOT mutate anything. Return the structured object.`,
  { label: 'discovery:launch-repo', phase: 'Discovery', model: 'sonnet', effort: 'low', schema: DISCOVERY_SCHEMA }  // read-only file enumeration — sonnet is sufficient; effort:'low' (no synthesis)
).catch(e => { log(`discovery agent error: ${e}`); return null })

if (!discovered || !Array.isArray(discovered.TEST_FILES) || !discovered.TEST_FILES.length) {
  if (!_args.TEST_FILES || !_args.TEST_FILES.length) {
    const msg = 'ABORT: discovery did not derive a test-file list and no TEST_FILES override was supplied. There is nothing to judge. Re-run from the target repo root, or pass an explicit TEST_FILES override.'
    log(msg)
    return { aborted: true, reason: msg, discovered }
  }
  log('discovery returned no test-file list; falling back to the explicit TEST_FILES override supplied in args.')
}

// Merge order: FALLBACKS < discovery < args. An explicit override always wins.
const CONFIG = Object.assign({}, FALLBACKS, discovered || {}, _args)
CONFIG.TEST_FILES = (CONFIG.TEST_FILES || []).filter(Boolean)
CONFIG.RISK = CONFIG.RISK || {}
CONFIG.ESCALATE_K = Number(CONFIG.ESCALATE_K) > 0 ? Number(CONFIG.ESCALATE_K) : ESCALATE_K_DEFAULT
CONFIG.OUTPUT = expand(CONFIG.OUTPUT)
log(`discovery: ${CONFIG.TEST_FILES.length} test file(s) to judge, framework="${CONFIG.FRAMEWORK}", escalate top K=${CONFIG.ESCALATE_K}.`)

if (!CONFIG.TEST_FILES.length) {
  const msg = 'ABORT: TEST_FILES is empty after merge — nothing to judge.'
  log(msg)
  return { aborted: true, reason: msg, discovered }
}

const { TEST_FILES } = CONFIG

// ---- The four lenses, defined ONCE and carried in a single judge prompt ----
// ONE judge per file reads the file ONCE and returns a verdict per lens — NOT
// four passes (ticket 0183 "one judge per test file" + YAGNI).
const LENSES = `
THE FOUR LENSES (judge ALL FOUR from a single read — do NOT run anything):

1. faithfulness (test-reality gap): does the test exercise prod-like paths, or a
   MOCKED FICTION that can stay green while production breaks? Flag heavy mocking
   that stubs the very thing under test (mocking the subject-under-test itself,
   so its real logic never runs). A test that mocks away what it claims to verify
   is unfaithful.

2. intent (readability / intent legibility): can a reader tell WHICH contract is
   asserted and WHY, without running it? Flag a test whose NAME lies about what
   it checks, or that passes for the WRONG reason (a vacuous assertion, an
   assertion that cannot fail, a name promising X while the body checks Y).

3. negative-space (coverage of the un-happy path): does it test error paths,
   boundaries, malformed / empty / huge inputs — or ONLY the happy path? Flag a
   test that exercises one nominal case and never the guards, boundaries, or
   error branches the code clearly has.

4. change-detector (over-specification smell): does it assert HOW the code works
   (call sequences, mock interaction ORDER, internal call counts) instead of
   WHAT it produces (the observable return value / effect)? Flag assertions on
   internal call order or mock-interaction sequence — they break on harmless
   refactors and the structural cause of over-scoped tests.`

const JUDGE_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  properties: {
    testFile: { type: 'string' },
    findings: { type: 'array', items: {
      type: 'object', additionalProperties: false,
      properties: {
        // ONE finding per lens this file trips. A clean lens need not appear.
        lens: { type: 'string', enum: ['faithfulness', 'intent', 'negative-space', 'change-detector'] },
        severity: { type: 'string', enum: ['low', 'medium', 'high'], description: 'how badly this lens is violated' },
        confidence: { type: 'string', enum: ['low', 'medium', 'high'], description: 'the judge\'s confidence in this verdict; low confidence triggers strong-model escalation' },
        rationale: { type: 'string', minLength: 1, description: 'WHY — the concrete evidence in the test (the lie, the mock, the missing branch, the order assertion)' },
        suggestion: { type: 'string', description: 'a concrete fix (assert the outcome not the order, add an error-path case, mock the boundary not the subject, rename to match the contract)' },
      },
      required: ['lens', 'severity', 'confidence', 'rationale'],
    } },
    summary: { type: 'string' },
  },
  required: ['testFile', 'findings', 'summary'],
}

function judgePrompt(file) {
  return `You are a READ-AND-JUDGE auditor of ${CONFIG.LANGUAGE} test quality. Repo: ${CONFIG.PROJECT}. Framework: ${CONFIG.FRAMEWORK || '(infer from the file)'}.

Your job: READ the test file (and, if it helps you judge, the source it imports) and JUDGE it against four lenses. You RUN NOTHING — no test execution, no mutation. This is pure reading-and-judgement; the verdicts are SOFT advisory opinions, not a pass/fail oracle.

TEST FILE TO JUDGE: ${file}
${LENSES}

PROCEDURE:
1. Read ${file}. Read the source module(s) it imports if that clarifies the contract under test.
2. For EACH lens, decide whether the file VIOLATES it. Emit ONE finding per VIOLATED lens (a clean lens produces no finding — do not pad). One read, up to four findings.
3. For each finding set: severity (how bad), confidence (how sure — be honest; a borderline call is low/medium confidence and will be re-judged by a stronger model), rationale (the concrete evidence — quote or point to the lie/mock/missing-branch/order-assertion), and a concrete suggestion.
4. If the file is clean on all four lenses, return an empty findings array and say so in the summary.

Return the structured object. Do NOT run or mutate anything.`
}

// ---- Phase 1: BULK judge pass (cheap model, one agent per file) ----
// Pipeline over files: a cheap-model (haiku) judge reads each file once and
// returns four-lens findings. Non-isolated — this skill executes nothing, so
// there is nothing for a worktree to protect. Identity comes from the DISPATCH
// loop (file), never the agent's self-report (mirrors maw-audit's 0226 d1).
phase('Judge')
const bulk = await pipeline(
  TEST_FILES,
  file => agent(judgePrompt(file), { label: `judge:${file}`.slice(0, 60), phase: 'Judge', model: 'haiku', effort: 'low', schema: JUDGE_SCHEMA })  // bulk cheap-model pass; effort:'low'
            .then(a => { if (a) a.testFile = file; return a })
            .catch(e => { log(`judge ${file} error: ${e}`); return null }),
)

// Index the bulk verdicts by dispatch identity (the test-file path).
const byFile = {}
TEST_FILES.forEach((file, i) => { byFile[file] = bulk[i] || null })

// ---- Phase 2: ESCALATE — strong-model re-judge of the top-K flagged files ----
// Select FILES (not findings) that warrant a stronger look: any file with a
// low-confidence finding, OR a high-severity finding. Rank by severity x churn
// and re-judge only the top K with the strong model. The sonnet verdict
// REPLACES the haiku verdict for that file (final say, mirroring maw-audit's
// skeptic). This caps the second wave at <= K agents — a large suite can never
// fan a second full wave.
phase('Escalate')
const SEV = { low: 1, medium: 2, high: 3 }

// Churn = commit count per file (a sort weight, DECORATION). maw-audit's churn
// agent KILLED a 1.36M-token run by throwing on a serialization mismatch; here
// churn must NEVER throw — tolerant schema + try/catch, degrade to 0 (severity-
// only ordering), never a dead run.
const churnByFile = await (async () => {
  try {
    const res = await agent(
      `For ${CONFIG.PROJECT}, report the git churn (number of commits that touched the file) for each of these test files, using \`git log --follow --oneline -- <file> | wc -l\` from the repo root. Files: ${TEST_FILES.join(', ')}. Return a JSON object mapping each filename to its commit count (a plain number; a numeric string is also accepted).`,
      { label: 'churn:git-log', phase: 'Escalate', model: 'sonnet',
        schema: { type: 'object', additionalProperties: { type: ['integer', 'string'] } } }
    )
    return Object.fromEntries(Object.entries(res || {}).map(([k, v]) => [k, parseInt(v, 10) || 0]))
  } catch (e) {
    log(`churn agent failed (${e}); escalation ranking degrades to severity-only — audit otherwise valid`)
    return {}
  }
})()

const riskWeight = file => (CONFIG.RISK[file] || 1.0)
const churnWeight = file => (churnByFile[file] || 0)
// File-level severity score = max finding severity on the file (the worst lens).
const fileSeverity = a => (a && Array.isArray(a.findings) && a.findings.length)
  ? Math.max(...a.findings.map(f => SEV[f.severity] || 1)) : 0
const hasLowConfidence = a => !!(a && Array.isArray(a.findings) && a.findings.some(f => f.confidence === 'low'))
const hasHighSeverity = a => !!(a && Array.isArray(a.findings) && a.findings.some(f => f.severity === 'high'))

// Candidates: files whose bulk verdict is uncertain (low confidence) or alarming
// (high severity). A clean or confidently-mild file does not need the strong model.
const candidates = TEST_FILES
  .filter(file => hasLowConfidence(byFile[file]) || hasHighSeverity(byFile[file]))
// Rank by severity x risk x churn DESC; +1 on churn so a never-touched file
// still ranks by severity (a churn of 0 would zero out an otherwise total order).
const escalateScore = file => fileSeverity(byFile[file]) * riskWeight(file) * (churnWeight(file) + 1)
const escalateFiles = [...candidates]
  .sort((a, b) => escalateScore(b) - escalateScore(a))
  .slice(0, CONFIG.ESCALATE_K)

log(`escalate: ${candidates.length} candidate file(s); re-judging top ${escalateFiles.length} (cap K=${CONFIG.ESCALATE_K}) with the strong model.`)

const escalated = await parallel(escalateFiles.map(file => () =>
  agent(judgePrompt(file), { label: `escalate:${file}`.slice(0, 60), phase: 'Escalate', model: 'sonnet', schema: JUDGE_SCHEMA })
    .then(a => { if (a) { a.testFile = file; a._escalated = true } return a })
    .catch(e => { log(`escalate ${file} error: ${e}`); return null })
))
// Strong-model verdict REPLACES the bulk verdict for that file (final say).
escalateFiles.forEach((file, i) => { if (escalated[i]) byFile[file] = escalated[i] })

// ---- Phase 3: deterministic REPORT assembly (no LLM formatting of N objects) ----
phase('Report')
const esc = s => String(s == null ? '' : s).replace(/\n+/g, ' ').replace(/\|/g, '\\|').trim()

// Flatten to one row per finding, keyed on the repo-relative test-file path
// (= the composition key; same identity maw-audit reports as file.test).
const audits = TEST_FILES.map(f => byFile[f]).filter(Boolean)
const rows = audits.flatMap(a => (a.findings || []).map(f => ({
  identity: a.testFile,            // composition key — repo-relative test path
  lens: f.lens,
  severity: f.severity,
  confidence: f.confidence,
  rationale: f.rationale,
  suggestion: f.suggestion || '',
  escalated: !!a._escalated,
})))

const sevRank = r => (SEV[r.severity] || 1) * riskWeight(r.identity) * (churnWeight(r.identity) + 1)
const ranked = [...rows].sort((a, b) => sevRank(b) - sevRank(a))

const byLens = lens => ranked.filter(r => r.lens === lens)
const LENS_TITLES = {
  faithfulness: '🪞 Faithfulness / test-reality gap (mocks the subject — stays green while prod breaks)',
  intent: '🪧 Intent legibility (name lies, or passes for the wrong reason)',
  'negative-space': '🕳️ Negative-space coverage (only the happy path)',
  'change-detector': '🔁 Change-detector smell (asserts HOW, not WHAT)',
}

const L = []
L.push(`# Test-Audit (read-and-judge) — \`${CONFIG.PROJECT}\``)
L.push('')
L.push('> ⚠️ **ADVISORY ONLY — SOFT judgment, not a gate.** These verdicts are a reader\'s opinion from READING each test (no test was run, no code was mutated). They are NOT a pass/fail oracle and MUST NOT block a merge or fail CI. Use them to FEED ticket creation (`tickets/erg new`), spot-checking each row against the cited evidence before acting. A judge can be wrong; treat a finding as a prompt to look, not a verdict to enforce.')
L.push('')
L.push(`_Generated by the \`test-audit-llm\` read-and-judge workflow. One judge per test file scored four lenses in a single read; the top ${CONFIG.ESCALATE_K} flagged/low-confidence files were re-judged by a stronger model. Findings are keyed on the repo-relative test-file path so they compose (as a file-level roll-up) with maw-audit's file identity._`)
L.push('')

L.push('## Summary')
L.push('')
L.push('| Lens | Findings |')
L.push('|---|---|')
;['faithfulness', 'intent', 'negative-space', 'change-detector'].forEach(lens =>
  L.push(`| ${LENS_TITLES[lens]} | ${byLens(lens).length} |`))
L.push(`| **files judged** | ${audits.length} / ${TEST_FILES.length} |`)
L.push(`| **files escalated to the strong model** | ${escalateFiles.length} |`)
L.push('')

L.push('## All findings — sorted by severity × risk × churn')
L.push('')
if (!ranked.length) L.push('_None — every judged test file was clean on all four lenses (advisory; the judge runs nothing, so a clean verdict is the absence of a *legible* defect, not proof of correctness)._')
else {
  L.push('| Test file (identity) | Lens | Severity | Confidence | Rationale | Suggestion |')
  L.push('|---|---|---|---|---|---|')
  ranked.forEach(r => L.push(`| \`${esc(r.identity)}\` | ${esc(r.lens)} | ${esc(r.severity)}${r.escalated ? ' ⬆️' : ''} | ${esc(r.confidence)} | ${esc(r.rationale)} | ${esc(r.suggestion)} |`))
  L.push('')
  L.push('_⬆️ = re-judged by the stronger model (its verdict replaced the bulk verdict for that file). Sorted by severity × risk × churn so the highest-blast-radius × change-frequency findings surface first; risk is the human-supplied weight (default 1)._')
}
L.push('')

;['faithfulness', 'intent', 'negative-space', 'change-detector'].forEach(lens => {
  L.push(`## ${LENS_TITLES[lens]}`)
  L.push('')
  const rs = byLens(lens)
  if (!rs.length) L.push('_None flagged._')
  else {
    L.push('| Test file | Severity | Rationale | Suggestion |')
    L.push('|---|---|---|---|')
    rs.forEach(r => L.push(`| \`${esc(r.identity)}\` | ${esc(r.severity)} | ${esc(r.rationale)} | ${esc(r.suggestion)} |`))
  }
  L.push('')
})

L.push('## Per-file summaries')
L.push('')
audits.forEach(a => {
  const c = (a.findings || []).reduce((m, f) => { m[f.lens] = (m[f.lens] || 0) + 1; return m }, {})
  const tag = Object.entries(c).map(([k, v]) => `${v} ${k}`).join(', ') || 'clean'
  L.push(`- **\`${a.testFile}\`** (${tag})${a._escalated ? ' · _strong-model re-judged_' : ''} — ${esc(a.summary)}`)
})
L.push('')
L.push('## Next step (out of scope here)')
L.push('These are advisory findings, not changes. Triage them into tickets (`tickets/erg new`) — a stronger assertion for an unfaithful test, an error-path case for a negative-space gap, an outcome assertion to replace a change-detector. Spot-check each row against the cited rationale before filing.')

const report = L.join('\n')

// JSON sidecar — the machine-readable composition artifact. One object per
// finding with the canonical {identity, lens, severity, rationale} schema (the
// verify gate checks this shape on the committed sample). `suggestion`,
// `confidence`, `escalated` are carried too but are not part of the required key.
const sidecar = {
  project: CONFIG.PROJECT,
  granularity: 'file',                 // composition is a file-level roll-up
  filesJudged: audits.length,
  filesEscalated: escalateFiles.length,
  findings: rows,
}

return {
  report,
  sidecar,
  output: CONFIG.OUTPUT,
  sidecarOutput: CONFIG.OUTPUT.replace(/\.[^./]*$/, '.json'),
  counts: {
    faithfulness: byLens('faithfulness').length,
    intent: byLens('intent').length,
    negativeSpace: byLens('negative-space').length,
    changeDetector: byLens('change-detector').length,
    files: audits.length,
    escalated: escalateFiles.length,
  },
  churnByFile,
}
