"""Padmé direct seat bounds input and normalizes constrained responses."""

import importlib.util
import io
import json
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock


SOURCE = Path(__file__).resolve().parents[1] / "scripts/seat-runner/direct-client.py"
spec = importlib.util.spec_from_file_location("padme_direct_client", SOURCE)
client = importlib.util.module_from_spec(spec)
spec.loader.exec_module(client)


def test_large_diff_fails_before_endpoint_call():
    err = io.StringIO()
    with mock.patch.object(client.os.path, "getsize", return_value=32769), mock.patch.object(
        client.urllib.request, "urlopen"
    ) as endpoint, mock.patch.dict(client.os.environ, {"SEAT_MODEL": "openai/qwen3.8-27b"}), redirect_stderr(err):
        assert client.main() == 1
    endpoint.assert_not_called()
    assert "32768-byte local review limit" in err.getvalue()


def test_json_review_becomes_panel_contract():
    answer = {
        "choices": [
            {
                "finish_reason": "stop",
                "message": {
                    "content": json.dumps(
                        {
                            "findings": [
                                {
                                    "severity": "verifiable",
                                    "file": "src/demo.py",
                                    "line": 12,
                                    "rationale": "This branch drops the error.",
                                }
                            ],
                            "verdict": "approve",
                        }
                    )
                },
            }
        ]
    }
    out = io.StringIO()
    with mock.patch.object(client.os.path, "getsize", return_value=100), mock.patch(
        "builtins.open", return_value=io.StringIO("diff --git a/x b/x\n")
    ), mock.patch.object(client.urllib.request, "urlopen", return_value=io.BytesIO(json.dumps(answer).encode())) as endpoint, mock.patch.dict(
        client.os.environ,
        {"SEAT_MODEL": "openai/qwen3.8-27b", "SEAT_REASONING_EFFORT": "none", "OPENAI_API_BASE": "http://127.0.0.1:9/v1", "OPENAI_API_KEY": "fixture"},
    ), redirect_stdout(out):
        assert client.main() == 0
    assert out.getvalue().splitlines() == [
        "FINDING|severity=verifiable|file=src/demo.py:12|rationale=This branch drops the error.",
        "SUMMARY|findings=1|verdict=revise",
    ]
    request = endpoint.call_args.args[0]
    sent = json.loads(request.data)
    assert sent["model"] == "qwen3.8-27b"
    assert sent["response_format"]["type"] == "json_schema"
    assert sent["chat_template_kwargs"] == {"enable_thinking": False}
