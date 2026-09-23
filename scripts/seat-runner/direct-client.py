#!/usr/bin/env python3
"""Single request, read-only reviewer client for OpenAI-compatible endpoints.

Runs inside seat-runner's network-denied container; OPENAI_API_BASE reaches only
the configured endpoint through its Unix-socket relay.
"""

import json
import os
import re
import sys
import urllib.error
import urllib.request


def main() -> int:
    model = os.environ["SEAT_MODEL"]
    if model.startswith("openai/"):
        model = model[len("openai/") :]
    with open("/review.diff", encoding="utf-8") as f:
        diff = f.read()
    instructions = (
        "Review this code diff. Report only real defects you can prove from "
        "the diff. You have no tools. Return JSON only. Each finding needs a "
        "severity, changed-file path, changed line number, and one-sentence rationale."
    )
    schema = {
        "type": "object",
        "properties": {
            "findings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "severity": {"type": "string", "enum": ["verifiable", "consider"]},
                        "file": {"type": "string"},
                        "line": {"type": "integer", "minimum": 1},
                        "rationale": {"type": "string"},
                    },
                    "required": ["severity", "file", "line", "rationale"],
                },
            },
            "verdict": {"type": "string", "enum": ["approve", "revise"]},
        },
        "required": ["findings", "verdict"],
    }
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": instructions},
            {"role": "user", "content": "Review this unified diff:\n\n" + diff},
        ],
        "temperature": 0,
        "max_tokens": int(os.environ.get("SEAT_MAX_OUTPUT_TOKENS", "512")),
        "stream": False,
        "response_format": {"type": "json_schema", "json_schema": {"name": "review", "schema": schema}},
    }
    if os.environ.get("SEAT_REASONING_EFFORT"):
        body["reasoning_effort"] = os.environ["SEAT_REASONING_EFFORT"]
        if body["reasoning_effort"] == "none":
            body["chat_template_kwargs"] = {"enable_thinking": False}
    base = os.environ["OPENAI_API_BASE"].rstrip("/")
    request = urllib.request.Request(
        base + "/chat/completions",
        data=json.dumps(body).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + os.environ["OPENAI_API_KEY"],
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            result = json.load(response)
    except (urllib.error.URLError, ValueError) as exc:
        print(f"direct-client: endpoint request failed: {type(exc).__name__}", file=sys.stderr)
        return 1
    try:
        choice = result["choices"][0]
        content = choice["message"]["content"]
        finish = choice["finish_reason"]
    except (KeyError, IndexError, TypeError):
        print("direct-client: response has no usable completion", file=sys.stderr)
        return 1
    if finish != "stop" or not isinstance(content, str) or not content.strip():
        print(f"direct-client: incomplete or empty completion (finish={finish})", file=sys.stderr)
        return 1
    try:
        result = json.loads(content)
        findings = result["findings"]
        if not isinstance(findings, list) or len(findings) > 10:
            raise ValueError("bad findings list")
        lines = []
        for item in findings:
            severity, path, line, rationale = item["severity"], item["file"], item["line"], item["rationale"]
            if severity not in ("verifiable", "consider") or not isinstance(path, str):
                raise ValueError("bad finding")
            if not re.fullmatch(r"[^\s|]+", path) or not isinstance(line, int) or line < 1:
                raise ValueError("finding lacks file and line")
            if not isinstance(rationale, str) or not rationale.strip():
                raise ValueError("finding lacks rationale")
            rationale = " ".join(rationale.split()).replace("|", "/")
            lines.append(f"FINDING|severity={severity}|file={path}:{line}|rationale={rationale}")
    except (KeyError, TypeError, ValueError) as exc:
        print(f"direct-client: malformed review JSON ({exc})", file=sys.stderr)
        return 1
    for line in lines:
        print(line)
    print(f"SUMMARY|findings={len(lines)}|verdict={'revise' if lines else 'approve'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
