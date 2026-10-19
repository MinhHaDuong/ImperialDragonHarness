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
 *
 * Session start (ticket 1122): the same extension also carries the session
 * context. Pi has a `session_start` event but no hook whose stdout becomes
 * context, so on a fresh session it runs `scripts/on-start.sh` itself and
 * queues the stdout as a custom message delivered with the next user turn
 * (`deliverAs: "nextTurn"`; measured on Pi 1.3.0 to reach the model). The
 * script's Claude-only lines stay silent because CLAUDE_PROJECT_DIR is
 * removed from its environment. Fail-open: nothing is injected on any failure.
 */

import { spawnSync } from "node:child_process";
import { existsSync, realpathSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

const GUARD_RELATIVE = join("scripts", "guard-destructive-bash.sh");
const GUARD_TIMEOUT_MS = 5000;
const ON_START_RELATIVE = join("scripts", "on-start.sh");
const ON_START_TIMEOUT_MS = 30000;

/** Walk up from this file until the harness root that carries the guard. */
function guardPath(relative: string = GUARD_RELATIVE): string | null {
	try {
		let dir = dirname(realpathSync(fileURLToPath(import.meta.url)));
		for (let i = 0; i < 6; i += 1) {
			const candidate = join(dir, relative);
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
	pi.on("session_start", async (event) => {
		// "reload", "resume" and "fork" keep the context the model already has.
		if (event.reason !== "startup" && event.reason !== "new") return;
		const script = guardPath(ON_START_RELATIVE);
		if (!script) return;
		try {
			const env = { ...process.env };
			delete env.CLAUDE_PROJECT_DIR;
			const result = spawnSync("bash", [script], {
				cwd: process.cwd(),
				env,
				timeout: ON_START_TIMEOUT_MS,
				encoding: "utf8" as const,
				stdio: ["ignore", "pipe", "ignore"],
			});
			const text = typeof result.stdout === "string" ? result.stdout.trim() : "";
			if (result.error || result.status !== 0 || !text) return;
			pi.sendMessage(
				{ customType: "idh-session-start", content: text, display: false },
				{ deliverAs: "nextTurn" },
			);
		} catch {
			/* fail-open */
		}
	});

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
