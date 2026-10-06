# Mistral Large 4 runtime and pricing evidence

Author handoff, 2026-10-06 around21:10 local. Direct API probes report
low rejected with HTTP400/code3051; supported reasoning_effort values
high and none. On one multiplication prompt capped at800 tokens, none
and omitted both returned123 completiontokens/275chars; high consumed800
tokens with2chars content. This small probe is not a high-arm tournament.

Pi1.0.4 has no ML4 catalogue/custom entry. Its transport sends
reasoning_effort only when model.reasoning is true. Sessions report off
and no thinking blocks. This supports the runtime identity, not a claim
that the underlying model performs no internal reasoning.

Correction to the handoff's cmd.txt inference: runner.py writes only
cmd[:6] to cmd.txt, then a prompt-length placeholder. --thinking and all
later flags are omitted from this diagnostic file even when present in
the launched command. Current runner configuration explicitly sets off;
cmd.txt cannot independently establish whether the flag was sent.

Measured Pi costobjects on0470-m sum to0.1549092USD: input0.06599,
output0.050724, cacheRead0.0381952. Thus cache was included, but at
0.4/2/0.04 perM instead of the registered preview0.68/2.09/0.07.
Repricing the recorded token components gives0.23203118USD, not a
supplier invoice. Preserve raw cost and report the derived estimate.
Regular announcement input/output1.36/4.18 differs from the preview rates.

Nine hosted cases were launched simultaneously, retaining0470. At this
checkpoint0338 is also complete and has three judge files; full-series
claims and high-effort comparisons remain pending.

Complete handoff pricing addition: author distinguishes official announcement
1.36/4.18 from OpenRouter promotion0.68/2.09. Actual runs use api.mistral.ai,
not OpenRouter. The official model card inspected in this session also
shows0.68/0.07/2.09 with crossed-out regular rates; this does not establish
an invoice. Retain the registered calculation scenario and mark native
billing reconciliation pending. Do not infer native pricing from OR alone.
