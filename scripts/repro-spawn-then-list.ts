// Reproduction artifact for ticket 1021 — agent.spawn returns success for an
// agent that never runs (a seat vanished from agent.list with no error).
//
// This program is run by a TOP-LEVEL session in a runtime that exposes
// tools.agent (child executor sessions lack the agent connector). It is a
// committed method artifact, NOT wired into make check. Repository checkout
// expected at $IDH_ROOT (portable placeholder; never a literal home path).
//
// Recorded outcome (raid orchestrator, top-level session, 2026-10-03T12:10Z):
// NOT-REPRODUCED — 8/8 seats listed at every poll t+0..t+60s. Contrast in the
// same session: over-cap spawns returned loud errors ('subagent_concurrency_
// limit'), never silent success. Silent-success remains a known intermittent
// (PR #1143 rounds 1-2, 2026-10-02, five-seat parallel panel).
//
// RESULT lines: REPRODUCED only when a tracked spawn-success id never appears
// in agent.list; UNDETERMINED when a successful spawn returned no correlatable
// id (it cannot be diffed against the list, so it never counts either way).

declare namespace tools.agent {
  // Shape is defensive: the exact return schema varies across runtimes.
  function spawn(args: { prompt: string; [key: string]: unknown }): Promise<any>;
  function list(args?: { [key: string]: unknown }): Promise<any>;
}
declare namespace tools.self {
  function sleep(args: { seconds: number }): Promise<any>;
}

const SEATS = 8;
const POLL_INTERVAL_S = 7; // immediate poll, then every 5-10 s
const POLL_HORIZON_S = 60;
const CONDITIONS =
  "conditions: top-level session with agent connector, " +
  SEATS + "-seat parallel spawn, polls t+0s to t+" + POLL_HORIZON_S + "s";

async function main(): Promise<string> {
  // 1. Spawn SEATS agents in parallel with trivial prompts.
  const spawns = await Promise.allSettled(
    Array.from({ length: SEATS }, (_, i) =>
      tools.agent.spawn({
        prompt:
          "Repro 1021 seat " + i + ": reply with the word seat-" + i + " and exit.",
      })
    )
  );

  // 2. Collect spawn returns; keep only the ids the runtime reported success for.
  const spawnedIds: string[] = [];
  let idlessSuccesses = 0;
  spawns.forEach((r, i) => {
    const value = r.status === "fulfilled" ? r.value : null;
    const id = value && (value.id ?? value.agentId ?? value.agent_id);
    if (id !== undefined && id !== null) {
      spawnedIds.push(String(id));
    } else if (value) {
      idlessSuccesses++; // success with no id: cannot be correlated to the list
    }
    // A rejected or error-typed spawn is a loud failure, not the silent-success
    // defect under test; it is reported, not counted as a vanished seat.
  });

  // 3. Poll agent.list immediately (t+0) and every POLL_INTERVAL_S to the
  //    horizon. The t+0 poll matters: a seat that completes its trivial prompt
  //    may later leave the list legitimately; only a seat that never lists
  //    after a success spawn is the defect.
  const absent = new Set(spawnedIds);
  const polls = 1 + Math.floor(POLL_HORIZON_S / POLL_INTERVAL_S);
  for (let p = 0; p < polls && absent.size > 0; p++) {
    if (p > 0) await tools.self.sleep({ seconds: POLL_INTERVAL_S });
    const listing = await tools.agent.list();
    const entries = listing?.agents ?? listing ?? [];
    for (const entry of entries as any[]) {
      const entryId = entry?.id ?? entry?.agentId ?? entry?.agent_id;
      if (entryId !== undefined && entryId !== null) {
        absent.delete(String(entryId));
      }
    }
  }

  // 4. Exactly one RESULT line: diff spawn-success ids against list entries.
  const listed = spawnedIds.length - absent.size;
  if (spawnedIds.length === SEATS && absent.size === 0) {
    return (
      "RESULT: NOT-REPRODUCED — " + listed + "/" + SEATS + " listed; " + CONDITIONS
    );
  }
  if (absent.size === 0) {
    return (
      "RESULT: UNDETERMINED — " +
      idlessSuccesses +
      " spawn-success seats returned no correlatable id, " +
      listed +
      "/" +
      SEATS +
      " tracked seats listed; " +
      CONDITIONS
    );
  }
  return (
    "RESULT: REPRODUCED — " +
    absent.size +
    "/" +
    spawnedIds.length +
    " spawn-success seats absent from agent.list; " +
    CONDITIONS
  );
}
