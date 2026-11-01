import { appendFileSync } from "node:fs";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
export default function (pi: ExtensionAPI): void {
	pi.on("tool_result", async (event) => {
		appendFileSync("<probe-dir>/events.jsonl", JSON.stringify({ tool: event.toolName, input: event.input, isError: event.isError }) + "\n");
		const tag = "CODEWORD-" + event.toolName.toUpperCase() + "-5521";
		return { content: [...event.content, { type: "text" as const, text: "\n\n" + tag }] };
	});
}
