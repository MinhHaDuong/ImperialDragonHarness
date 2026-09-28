/**
 * IDH dirty-reset guard adapter for Pi (ticket 0809).
 *
 * The guard owns the decision; this extension only normalizes input and
 * carries the decision. It registers a `tool_call` handler for the bash
 * tool, feeds the canonical `scripts/guard-destructive-bash.sh` the same
 * JSON payload the Claude Code and Codex PreToolUse hooks feed it
 * (`tool_input.command` plus the session cwd), and translates its exit
 * code: 0 allows, 2 blocks with the guard's own stderr reason.
 *
 * The guard is fail-open by design (a broken guard must not brick every
 * bash call), so infra failures here allow too: a missing script, a
 * failed spawn or a timeout returns undefined rather than blocking.
 * Pi's own fail-safe (a throwing handler blocks the tool) is therefore
 * narrowed by catching everything: this adapter carries the guard's
 * decision, including its fail-open doctrine, and never invents one.
 *
 * The guard is located through the same seam as the skills: this file is
 * reached through a projected symlink (~/.pi/agent/extensions/idh-guard.ts
 * -> the harness checkout), so realpath of the self module resolves to the
 * canonical tree and scripts/guard-destructive-bash.sh is found under it.
 */

import { spawnSync } from "node:child_process";
import { existsSync, realpathSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

const GUARD_RELATIVE = join("scripts", "guard-destructive-bash.sh");
const GUARD_TIMEOUT_MS = 5000;

/** Walk up from this file until the harness root that carries the guard. */
function guardPath(): string | null {
	try {
		let dir = dirname(realpathSync(fileURLToPath(import.meta.url)));
		for (let i = 0; i < 6; i += 1) {
			const candidate = join(dir, GUARD_RELATIVE);
			if (existsSync(candidate)) return candidate;
			const parent = dirname(dir);
			if (parent === dir) break;
			dir = parent;
		}
	} catch {
		/* fall through to fail-open */
	}
	return null;
}

export default function (pi: ExtensionAPI): void {
	pi.on("tool_call", async (event) => {
		if (event.toolName !== "bash") return undefined;
		const command = (event.input as { command?: unknown }).command;
		if (typeof command !== "string" || !command.includes("--hard")) {
			return undefined;
		}

		const guard = guardPath();
		if (!guard) return undefined;

		let result: ReturnType<typeof spawnSync>;
		try {
			result = spawnSync("bash", [guard], {
				input: JSON.stringify({
					tool_input: { command },
					cwd: process.cwd(),
				}),
				timeout: GUARD_TIMEOUT_MS,
				encoding: "utf8" as const,
				stdio: ["pipe", "pipe", "pipe"],
			});
		} catch {
			return undefined; // fail-open, like the guard
		}
		if (result.error || result.signal || result.status === null) {
			return undefined; // infra failure: the guard never decided
		}
		if (result.status === 2) {
			return {
				block: true,
				reason: (result.stderr ?? "").trim() ||
					"BLOCKED: git reset --hard would discard uncommitted changes to tracked files.",
			};
		}
		return undefined; // 0 (allow) and any other status: the guard allows
	});
}
