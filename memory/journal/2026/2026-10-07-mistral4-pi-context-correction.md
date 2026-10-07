Date: 2026-10-07

Context: Native ML4 arena ticket 0874 ended with length, no submitted solution.
Correction linked to docs/2026-10-07-mistral4-0874-postmortem.md and
2026-10-06 Mistral handoff: Pi's unknown-model fallback copied Devstral 2 settings,
including contextWindow262144, maxTokens262144, reasoningfalse and inherited cost.
Pi clamps max_tokens to configured context minus estimated history minus4096.

Official native GET /v1/models reports mistral-large-4 max_context_length524288,
reasoning and vision enabled, billing model mistral-large-4-0-launch-discount.
An explicit model declaration was added to ~/.pi/agent/models.json, preserving
other providers and backing up the previous file: context524288, output262144,
reasoningtrue, text/image input, native mistral-conversations API. Registered
preview USD/M rates .68 input,2.09 output,.07 cached input replace fallback costs;
graph costs remain allocated from the author's invoice, not Pi estimates.

Validation via fresh Pi process: captured max_tokens262144, HTTP200. First smoke
returned401 because literal apiKey MISTRAL_API_KEY in the custom provider did
not resolve as intended; removing that override restored native environment-key
resolution. No credential persisted in committed diagnostics.

Thinking off still omits reasoning_effort in the captured HTTP payload. This
change corrects context/model metadata; it does not prove native reasoning none.
Existing processes retain old settings. Author requested 0874 retry with breaker5
and HTTP capture; launched as native arm mb, with old mr failure preserved.
Raw captures remain private in ~/arena; no prompts or keys committed.
