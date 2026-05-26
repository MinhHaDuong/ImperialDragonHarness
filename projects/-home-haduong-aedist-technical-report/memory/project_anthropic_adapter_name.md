---
name: project_anthropic_adapter_name
description: "Anthropic adapter is query_anthropic.py, not adapter_anthropic.py — retry goes in dispatch()"
metadata: 
  node_type: memory
  type: project
  originSessionId: e63dac2c-61c4-4aeb-a18b-37ac8a268c54
---

The Anthropic provider adapter is `src/aedist/query_anthropic.py`. There is no `adapter_anthropic.py`.

**Why:** The file naming is inconsistent with the other adapters (`adapter_mistral.py`, `adapter_openai_responses.py`, `adapter_qwen_dashscope.py`). Ticket 0244 originally named the wrong file.

**How to apply:** When adding retry logic or modifying the Anthropic call site, the target is `query_anthropic.py`, specifically the `dispatch()` function (around line 385). The `retry_count=0` field in `_record_from_parsed()` (line 378) is a placeholder — actual retry logic is not implemented.
