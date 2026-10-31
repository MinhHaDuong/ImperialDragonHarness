/**
 * IDH wake reader for Pi (ticket 1316; writer side: scripts/runtime_wake.py, 1311).
 *
 * Pi has no way for another process to start a turn, so `runtime.py wake`
 * drops a job into an inbox directory and this extension is the reader. At
 * `session_start` (not in the factory: the factory runs for every load,
 * including ones that never become a session) it creates a per-session inbox
 * under $XDG_RUNTIME_DIR (else the OS temp dir), exports IDH_PI_SESSION_ID (the
 * session's id, for launch lines) and IDH_WAKE_INBOX into process.env so the bash tool's children, and so `runtime.py can wake`,
 * see it, and starts a timer. That export is the whole of "the extension is
 * loaded": without this file nothing sets the variable and wake answers NOOP.
 *
 * Delivery: every tick, when the agent is idle, the oldest non-dot `*.msg`
 * goes to `pi.sendUserMessage()` and is deleted only after that call returned
 * (a crash in between redelivers, never loses; an in-memory set stops a
 * failed delete from redelivering within one session). Dot-files are the
 * writer's half-written temporaries and are never read. One job per tick, so
 * the next one waits for the turn the first started.
 *
 * Fail-open like idh-guard: any error is swallowed and the next tick retries.
 * On shutdown the timer stops and the variable goes; the inbox is removed
 * unless a job is still pending.
 */

import { mkdirSync, mkdtempSync, readdirSync, readFileSync, rmSync, unlinkSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

const TICK_MS = 2000;

export default function (pi: ExtensionAPI): void {
	let timer: ReturnType<typeof setInterval> | undefined;
	let inbox: string | undefined;
	const delivered = new Set<string>();

	function stop(): void {
		delete process.env.IDH_PI_SESSION_ID;
		if (timer) clearInterval(timer);
		timer = undefined;
		if (!inbox) return;
		if (process.env.IDH_WAKE_INBOX === inbox) delete process.env.IDH_WAKE_INBOX;
		try {
			const pending = readdirSync(inbox).some((n) => n.endsWith(".msg") && !n.startsWith("."));
			if (!pending) rmSync(inbox, { recursive: true, force: true });
		} catch {
			/* fail-open */
		}
		inbox = undefined;
	}

	pi.on("session_start", async (_event, ctx) => {
		stop();
		try {
			// The session id for `runtime.py session id` (ticket 1384): launch lines name their parent by it.
			process.env.IDH_PI_SESSION_ID = ctx.sessionManager.getSessionId();
		} catch {
			/* fail-open: the launch line says `not exported` */
		}
		try {
			const base = join(process.env.XDG_RUNTIME_DIR || tmpdir(), "idh-wake");
			mkdirSync(base, { recursive: true, mode: 0o700 });
			const dir = mkdtempSync(join(base, "pi-"));
			inbox = dir;
			process.env.IDH_WAKE_INBOX = dir;
		} catch {
			return;
		}
		const dir = inbox;
		timer = setInterval(() => {
			try {
				if (!ctx.isIdle()) return;
				const next = readdirSync(dir)
					.filter((n) => n.endsWith(".msg") && !n.startsWith(".") && !delivered.has(n))
					.sort()[0];
				if (!next) return;
				const text = readFileSync(join(dir, next), "utf8").trim();
				delivered.add(next);
				if (text) pi.sendUserMessage(text);
				unlinkSync(join(dir, next));
			} catch {
				/* fail-open: the next tick retries */
			}
		}, TICK_MS);
		timer.unref?.();
	});

	pi.on("session_shutdown", async () => {
		stop();
	});
}
