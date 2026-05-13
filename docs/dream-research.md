# /dream Research Note — 2026-05-13

## Verdict

The initial survey (2026-04-30) remains **broadly valid**, but five critical shifts have emerged: (1) Anthropic released "dreaming" as a managed-agent primitive (May 2026), providing a reference implementation architecture and real-world performance data (6x Harvey completion rate lift). (2) Mem0 advanced to v2.0.2 with no breaking schema changes; the four-operation classifier (ADD/UPDATE/DELETE/NOOP) is confirmed production-ready. (3) TiMem (January 2026) introduces temporal-hierarchical consolidation (five-level tree) as a SOTA alternative to flat reflection; critical for long-horizon agents. (4) Importance-sum triggers remain optional but are now validated by SCM (sleep-consolidated memory, 2026) as a scalable replacement for time-based scheduling. (5) Letta sleep-time agents remain experimental; client-side subagent consolidation is replacing server-side sleep, shifting the /dream design toward local-first consolidation.

**Recommendation**: Implement `/dream` using the four-operation mem0 classifier (confirmed production-grade) with optional importance-weighted trigger support. Adopt Anthropic's dreaming architecture as a reference: isolated background execution, separate model (haiku 4.5 for cost), explicit memory snapshot before mutation, and rollback capability. Optionally add temporal-hierarchical organization (TiMem pattern) for multi-session reasoning paths. Importance-sum triggers should be a v2 feature, not v1.

---

## Pattern status

### mem0 (ADD/UPDATE/DELETE/NOOP tool-call classifier) — VALID with production certification

**Status**: VALID (2504.19413, April 2025)

**Evidence**: 
- Four operations confirmed in arxiv preprint: ADD (new fact, no semantic equivalent), UPDATE (augment existing fact), DELETE (contradiction), NOOP (already present or irrelevant).
- K-neighborhood retrieval uses **semantic similarity** (vector embeddings, top-s=10), not graph k-hop. Presented to LLM via function-calling.
- Mem0 released v2.0.2 (May 7, 2026) with no breaking schema changes.
- No mention of deprecated API; v2.x is current production.
- Apache Cassandra (v1.0.1, Nov 2025) and Valkey (v0.1.118, Sept 2025) storage backends added for distributed deployments.

**For /dream**: Use as-is. Sem0's classifier is battle-tested. Consider making embedding model configurable (haiku 4.5 for cost; accept user override).

---

### Generative Agents recursive reflection (Park 2023, 2304.03442) — VALID baseline, superseded for long-horizon

**Status**: VALID as baseline reflection; SUPERSEDED for multi-day horizons by TiMem.

**Evidence**:
- Park's reflection mechanism (2023) remains standard: extract high-level insights from raw memories, rewrite at higher abstraction, use LLM scoring for importance.
- A-MEM (NeurIPS 2025, 2502.12110) **validates** Park's reflection as a core pattern, adding Zettelkasten-style link updates. Link graph updates during consolidation are now confirmed best-practice.
- TiMem (January 2026, 2601.02845) shows temporal-hierarchical consolidation (five levels: segments → utterance clusters → persona slices → interaction arcs → persona profiles) achieves 75.30% accuracy and 52.20% memory-length reduction vs. flat reflection.

**For /dream**: Use Park's reflection for v1 (proven, simple). Reserve TiMem five-level pattern for v2 (if Claude Code tracks session boundaries and multi-day interactions).

---

### Zep / Graphiti bi-temporal invalidation (2501.13956) — VALID, mature

**Status**: VALID (January 2025)

**Evidence**:
- Graphiti's bi-temporal modeling tracks four timestamps: `t'created`/`t'expired` (system lifecycle), `t_valid`/`t_invalid` (domain facts).
- When new facts conflict with existing facts, Graphiti invalidates but does not delete. Old facts remain in audit log; timestamps preserve "when it was true."
- This is **the reference implementation** for non-destructive memory mutation.
- Zep ships knowledge graph memory as production service; Graphiti is OSS engine underneath.

**For /dream**: Git history already provides bi-temporal audit for free (tickets/0070 Action 3.c: "leave a tombstone line if needed; git is the audit log"). Explicit `t_valid`/`t_invalid` metadata in MEMORY.md files is **optional** v2 feature. v1 can rely on git.

---

### Letta sleep-time agents — PARTIALLY UPDATED (April 2025 baseline; May 2026 shift to client-side)

**Status**: UPDATED. April 2025 documentation describes server-side sleep-time agents; May 2026 announcement signals shift to **client-side subagent consolidation**.

**Evidence**:
- Letta docs (April 2025) describe sleep-time agents as secondary agents sharing memory, running in background, modifying memory asynchronously.
- Letta's May 2026 roadmap indicates server-side sleep will be replaced by client-side subagent system running the same compute/tools/context.
- Implication: `/dream` should be designed to **run on client, not depend on server-side triggers**.

**For /dream**: Design as local-first (already true per 0070 Action 7). No server-side dependency. Subprocess or manual cron scheduling. This aligns with Letta's direction.

---

### A-MEM / Zettelkasten link updates (2502.12110) — VALID, now confirmed best-practice

**Status**: VALID (February 2025, NeurIPS 2025 poster)

**Evidence**:
- A-MEM proposes dynamic indexing and linking: as new memories are integrated, they trigger updates to contextual representations and attributes of **historical** memories. Link graph evolves.
- Empirical results on six foundation models show SOTA improvement vs. baselines.
- This **validates** the importance of link updates during consolidation, beyond mere dedup.

**For /dream**: v1 can skip explicit link updates (complexity budget). v2 should add: after UPDATE/DELETE steps, rescan MEMORY.md index for stale backlinks and update them. This is the A-MEM pattern.

---

### Importance-sum trigger (Park) — VALID, now formally validated as scalable alternative

**Status**: VALID as optional v2. Now validated by SCM (2604.20943, April 2026) as scalable replacement for time-based scheduling.

**Evidence**:
- Park's importance scoring (2023) is standard: LLM assigns importance to each fact based on perceived long-term value.
- **SCM** (Sleep-Consolidated Memory, April 2026) implements importance-based thresholding: facts with multi-dimensional importance scores > threshold are retained; others decay.
- TF-IDF ranking adopted for importance-weighted batching, though more sophisticated scoring functions possible.
- Result: importance-weighted consolidation reduces memory size while preserving signal.

**For /dream**: v1 uses time-based trigger (0070: "plain time-based"). v2 can add optional importance-weighted trigger (`--importance-threshold`). Default: time-based (simpler, predictable).

---

## New findings

### 1. Anthropic "Dreaming" (May 2026) — Reference implementation, public roadmap

**Finding**: Anthropic released "dreaming" for Claude Managed Agents in research preview (May 6, 2026, Code with Claude SF). This is the closest published equivalent to `/dream`.

**Details**:
- Scheduled process runs between agent sessions.
- Reviews prior sessions and memory stores; merges duplicates; removes outdated entries; highlights recurring patterns (mistakes, team preferences, converged workflows).
- Developers can set automatic update or review-before-land workflow.
- **Real-world impact**: Harvey reported ~6x task completion rate lift after dreaming activation (internal testing).
- Architecture: runs on Anthropic's managed-agent platform; agents can't inspect or modify dreaming behavior directly.

**Implication for /dream**: 
- Anthropic's design validates the concept: background memory consolidation produces measurable agent improvement.
- However, Anthropic's approach is cloud-native (runs on their servers). `/dream` must be local-first and work across multi-project directories (not a single agent).
- Core pattern to adopt: **snapshot-before-mutation** (read full memory state, propose edits, write results, allow rollback).

---

### 2. Temporal-Hierarchical Consolidation (TiMem, January 2026) — SOTA for long-horizon agents

**Finding**: TiMem (2601.02845) introduces **five-level temporal memory tree** for long-horizon agents, achieving SOTA accuracy (75.30% LoCoMo, 76.88% LongMemEval-S) with 52% memory-length reduction.

**Details**:
- Level 1: Raw utterances / factual segments.
- Level 2: Utterance clusters (semantic grouping over minutes/hours).
- Level 3: Persona slices (extracted behaviors from a session).
- Level 4: Interaction arcs (longer-term behavioral trajectories).
- Level 5: Persona profiles (stable long-term knowledge about user/agent preferences).
- Consolidation proceeds bottom-up with semantic-guided merging (no fine-tuning needed).
- Adaptive recall balances precision vs. latency by returning memories at appropriate abstraction level for query complexity.

**Implication for /dream**: 
- Flat reflection (Park 2023) works for daily consolidation; TiMem is overkill for single-day horizons.
- If Claude Code's projects span multi-session or multi-week horizons, TiMem's hierarchy will improve long-term personalization.
- v1 action: Implement flat reflection; document TiMem as v2 extension if project tracks session timestamps and multi-week arcs.

---

### 3. Claude API Memory Tool (May 2026) — Native primitives now public

**Finding**: Anthropic published the memory tool as a first-class Claude API primitive (available in current SDK). Managed Agents ship with persistent memory as headline feature.

**Details**:
- Memory tool exposes `/memories` directory filesystem interface.
- Commands: `view`, `create`, `str_replace`, `insert`, `delete`, `rename` (same operations as text editor).
- Client-side implementation: Claude makes tool calls; application executes locally.
- Comes with example implementations (Python `BetaAbstractMemoryTool`, TypeScript `betaMemoryTool`).
- Security: must validate paths to prevent traversal attacks (`../`, URL-encoded sequences, etc.).

**Implication for /dream**: 
- `/dream` shares design DNA with Anthropic's memory tool: CRUD operations on memory files, validation, path safety.
- Can study their example implementations (GitHub) for error handling patterns and security guards.
- No new operation types; memory tool is isomorphic to filesystem ops.

---

### 4. Cognee Memify (2026) — Post-processing pipeline for enrichment

**Finding**: Cognee released Memify as a modular post-processing pipeline (extraction + enrichment stages). Distinct from raw graph construction.

**Details**:
- Requires pre-built knowledge graph (Cognify output).
- Extraction: selects triplets, document chunks, or cached sessions.
- Enrichment: LLM-driven processing (index vectors, derive rules, consolidate descriptions), write updates back to graph.
- Memify runs without disrupting core workflows (asynchronous).
- Practical operations: prune stale nodes, strengthen frequent connections, reweight edges, add derived facts.

**Implication for /dream**: 
- Memify's two-stage architecture (extract, then enrich) is a good mental model for `/dream`: (1) read memories, retrieve neighbors, (2) apply LLM classification (mem0 four-op), (3) write updates.
- Cognee is graph-native; `/dream` is markdown/file-native. But the pipeline concept transfers well.

---

### 5. ICLR 2026 Workshop on MemAgents — Emerging standardization on retrieval + consolidation

**Finding**: ICLR 2026 is running a dedicated workshop ("MemAgents: Memory for LLM-Based Agentic Systems") covering data structures, retrieval, consolidation, and benchmarks.

**Details**:
- Focus areas: systems/evaluation (data structures, benchmarks for non-i.i.d. long-horizon competence), retrieval/consolidation pipelines, neuroscience-inspired approaches (hippocampal–cortical consolidation).
- Signals ecosystem convergence on consolidation as first-class problem, not afterthought.

**Implication for /dream**: 
- Evidence that consolidation is becoming standard infrastructure (like memory tools, retrieval). `/dream` is well-aligned with the field direction.
- Watch ICLR 2026 proceedings for new algorithms (post May 13, 2026 today).

---

## Recommended design

### For /dream v1 (MVP, production-ready by Q2 2026)

1. **Trigger**: Time-based only (configurable cron; default `0 2 * * *`, 2 AM nightly). No importance-weighted logic yet.

2. **Classifier**: Use mem0 four-operation pipeline (ADD/UPDATE/DELETE/NOOP).
   - For each memory candidate in all projects' MEMORY.md files:
     - Retrieve top-10 semantic neighbors (vector embedding similarity).
     - Prompt LLM: `Given candidate fact X and these neighbors [list], decide: ADD (new), UPDATE (augment), DELETE (contradicts), NOOP (already present).`
     - Apply edits in place (no `rm`; use git as audit log; optional tombstone comments like `# DELETED: <original line> — conflict with <new fact>`).

3. **Reflection**: Park 2023 recursive reflection (flat, single-level).
   - After dedup/merge pass, extract N=5 high-level insights from survivor set.
   - Rewrite MEMORY.md index from insights + survivors. Keep index under 200 lines.

4. **Scope**: Cross-project (iterate `~/.claude/projects/*/memory/`).
   - Per-project safeguard: skip if no mtime change since last consolidation marker.
   - Consolidation marker: one-line log in git commit body or `.dream.log` file.

5. **Model**: Haiku 4.5 (cost-optimized; allow user override).

6. **Idempotence + safety**:
   - `--dry-run` flag shows proposed edits without writing.
   - `--rollback <commit-hash>` reverts last consolidation.
   - Git isolates all writes to IDH (never touch project repos).

7. **Exit criteria** (from 0070):
   - Implements mem0 four-op classifier ✓
   - Flat Park reflection ✓
   - Cross-project scope ✓
   - Time-based trigger (no importance yet) ✓
   - Dry-run + dry-rollback ✓

### For /dream v2 (post-MVP, 2026-Q3+)

1. **Importance-weighted trigger**: Add optional `--importance-threshold` (replaces time-based for that run). Requires per-fact importance metadata in MEMORY.md.

2. **Temporal-hierarchical reflection**: Adopt TiMem five-level pattern **if** project tracks session boundaries (timestamps on memory entries). Otherwise, keep flat.

3. **Link updates** (A-MEM): After UPDATE/DELETE passes, rescan MEMORY.md backlinks and update stale references.

4. **Bi-temporal metadata**: Explicit `t_valid`/`t_invalid` timestamps in memory entries (complement git audit log). Facilitates recovery to "state on date X."

5. **Consolidation benchmarking**: Use LoCoMo / LongMemEval-S metrics to measure memory recall accuracy and length reduction.

---

## Bibliography

- [Mem0 v2.0.2 (May 2026)](https://github.com/mem0ai/mem0/releases) — Memory layer production release; v2.x has no breaking schema changes from v1.
- [Chhikara et al. (2025). Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory. arXiv:2504.19413](https://arxiv.org/abs/2504.19413) — Four-operation ADD/UPDATE/DELETE/NOOP classifier with vector-based k-neighborhood retrieval.
- [Park et al. (2023). Generative Agents: Interactive Simulacra of Human Behavior. UIST 2023. arXiv:2304.03442](https://arxiv.org/abs/2304.03442) — Baseline for recursive reflection and importance scoring.
- [Rasmussen et al. (January 2025). Zep: A Temporal Knowledge Graph Architecture for Agent Memory. arXiv:2501.13956](https://arxiv.org/abs/2501.13956) — Bi-temporal invalidation (t'_created, t'_expired, t_valid, t_invalid); non-destructive memory mutation.
- [Letta Docs (April 2025). Sleep-time agents](https://docs.letta.com/guides/agents/architectures/sleeptime/) — Background memory consolidation agents; May 2026 roadmap signals shift to client-side subagent model.
- [Xu et al. (February 2025). A-MEM: Agentic Memory for LLM Agents. NeurIPS 2025. arXiv:2502.12110](https://arxiv.org/abs/2502.12110) — Zettelkasten-style link generation and dynamic link updates during consolidation.
- [Cognee. Memify Post-Processing Pipeline (2026)](https://docs.cognee.ai/core-concepts/main-operations/memify) — Two-stage extraction + enrichment architecture for knowledge graph consolidation.
- [Anthropic. Dreaming for Claude Managed Agents (May 6, 2026)](https://letsdatascience.com/blog/anthropic-dreaming-claude-managed-agents-self-improving-may-6) — Cloud-native reference implementation; 6x Harvey completion rate lift reported; snapshot-before-mutation pattern.
- [Anthropic. Memory tool (May 2026). Claude API Docs](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool) — Native memory tool (view/create/str_replace/insert/delete/rename); client-side implementation; path validation required.
- [Zhao et al. (January 2026). TiMem: Temporal-Hierarchical Memory Consolidation for Long-Horizon Conversational Agents. arXiv:2601.02845](https://arxiv.org/abs/2601.02845) — Five-level temporal memory tree (segments → clusters → slices → arcs → profiles); SOTA long-horizon consolidation; 75.30% accuracy, 52% memory reduction.
- [Li et al. (April 2026). SCM: Sleep-Consolidated Memory with Algorithmic Forgetting for Large Language Models. arXiv:2604.20943](https://arxiv.org/html/2604.20943) — Importance-based thresholding for memory retention; validates importance-sum trigger pattern as scalable alternative to time-based scheduling.
- [ICLR 2026 Workshop. MemAgents: Memory for LLM-Based Agentic Systems](https://openreview.net/forum?id=U51WxL382H) — Emerging standardization on memory data structures, retrieval, consolidation, and benchmarks.
- [Mem0 Changelog (2025-2026)](https://docs.mem0.ai/changelog) — Apache Cassandra support (v1.0.1, Nov 2025), Valkey support (v0.1.118, Sept 2025), v2.0.x releases April-May 2026.

---

**Note**: All URLs and arxiv IDs verified as of 2026-05-13. This research note is companion to ticket 0070 and should be read before implementation begins.
