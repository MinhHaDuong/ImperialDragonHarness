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
 * Session start: the same extension also carries the session
 * context. Pi has a `session_start` event but no hook whose stdout becomes
 * context, so on a fresh session it runs `scripts/on-start-context.sh` itself and
 * queues the stdout as a custom message delivered with the next user turn
 * (`deliverAs: "nextTurn"`; measured on Pi 1.3.0 to reach the model). The
 * script's Claude-only lines stay silent because CLAUDE_PROJECT_DIR is
 * removed from its environment. Fail-open: nothing is injected on any failure.
 *
 * Skill case notes (ticket 1405, pilot 1394): Pi has no Skill tool, a skill
 * loads when the model reads `skills/<name>/SKILL.md`. A `tool_result`
 * handler on `read` feeds `scripts/skill-case-notes.sh` the payload the
 * Claude PostToolUse hook gets (`tool_input.skill`, session id, cwd) and
 * appends its additionalContext to the read result. The script owns the
 * once-per-session marker, the project lookup and the log. Fail-open.
 *
 * Conditional rules (ticket 1424): Claude Code loads a rule whose `paths:`
 * globs match a file the session touches; Pi does not. The same
 * `tool_result` handler, on read, write, edit and bash (their inputs carry
 * `path` or `command`, probe 2026-11-01 on Pi 1.4.0), feeds
 * `scripts/conditional_rules.py` the Codex-shaped payload and appends the rule
 * bodies it returns. The script owns matching, the marker and the log. Fail-open.
 */

import { spawnSync } from "node:child_process";
import { existsSync, realpathSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

const GUARD_RELATIVE = join("scripts", "guard-destructive-bash.sh");
const GUARD_TIMEOUT_MS = 5000;
const ON_START_RELATIVE = join("scripts", "on-start-context.sh");
const ON_START_TIMEOUT_MS = 30000;
const CASE_NOTES_RELATIVE = join("scripts", "skill-case-notes.sh");
const CASE_NOTES_TIMEOUT_MS = 10000;
const RULES_RELATIVE = join("scripts", "conditional_rules.py");
const RULES_TIMEOUT_MS = 10000;
const RULES_TOOLS = new Set(["read", "write", "edit", "bash"]);
const SKILL_FILE = /(?:^|[\\/])skills[\\/]([a-z0-9][a-z0-9_-]*)[\\/]SKILL\.md$/;

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

	/** Run a context hook script on a payload; its additionalContext, or "" on any failure. */
	function hookContext(command: string, args: string[], payload: object, timeout: number): string {
		try {
			const result = spawnSync(command, args, {
				input: JSON.stringify(payload),
				timeout,
				encoding: "utf8" as const,
				stdio: ["pipe", "pipe", "ignore"],
			});
			if (result.error || result.status !== 0 || !result.stdout) return "";
			const text = JSON.parse(result.stdout)?.hookSpecificOutput?.additionalContext;
			return typeof text === "string" ? text : "";
		} catch {
			return ""; /* fail-open */
		}
	}

	pi.on("tool_result", async (event, ctx) => {
		if (event.isError) return undefined;
		try {
			const notes: string[] = [];
			const session_id = ctx.sessionManager.getSessionId();
			const cwd = ctx.sessionManager.getCwd();
			const path = (event.input as { path?: unknown }).path;
			const match = event.toolName === "read" && typeof path === "string" ? SKILL_FILE.exec(path) : null;
			const caseNotes = match ? guardPath(CASE_NOTES_RELATIVE) : null;
			if (match && caseNotes) {
				notes.push(hookContext("bash", [caseNotes], {
					hook_event_name: "PostToolUse",
					session_id,
					cwd,
					tool_name: "Skill",
					tool_input: { skill: match[1] },
				}, CASE_NOTES_TIMEOUT_MS));
			}
			const rules = RULES_TOOLS.has(event.toolName) ? guardPath(RULES_RELATIVE) : null;
			if (rules) {
				notes.push(hookContext("python3", [rules], {
					hook_event_name: "PostToolUse",
					session_id,
					cwd,
					tool_name: event.toolName,
					tool_input: event.input,
				}, RULES_TIMEOUT_MS));
			}
			const extra = notes.filter((n) => n);
			if (!extra.length) return undefined;
			return {
				content: [...event.content, ...extra.map((text) => ({ type: "text" as const, text: "\n\n" + text }))],
			};
		} catch {
			return undefined; /* fail-open */
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
