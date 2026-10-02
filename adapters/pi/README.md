# pi adapter — provider-assertion rule

Pi is a coding-agent runtime the harness can drive with
`pi --print --mode json`. Characterized on 0.87.1 (ticket 0979,
[docs/2026-10-02-pi-reroute-openrouter-0979.md](../../docs/2026-10-02-pi-reroute-openrouter-0979.md)):
when model resolution comes up empty — an empty or absent `--model` — Pi
silently discards the explicit `--provider` and serves the request through
the first provider with a valid key on the machine (huggingface in the
2026-10-02 reproduction, openrouter in essai 0977). Exit 0, a normal-looking
answer, no warning on stderr or in the JSON stream. An unknown provider name
errors visibly, and an unknown model id with an explicit provider stays on
that provider with a stderr warning — the cross-provider reroute is the
empty/absent-model path.

## Rule: assert the served provider, never the requested one

Every Pi run targeting a sovereign backend (padme, Albert, ILaaS, or any
backend declared in the live Pi config) must verify that `"provider"` in the
`--mode json` output equals the requested provider **before trusting the
answer**. Concretely:

- Run with `--mode json` and read the served provider from the `turn_end`
  event's message (`turn_end.message.provider`) — the requested provider and
  the exit code prove nothing.
- If the served provider differs from the requested one, treat the run as
  failed and assume the prompt content has egressed to the fallback provider —
  potentially uncleared material leaving the sovereign perimeter.
- Always pass both flags together, non-empty: `--provider <sovereign> --model
  <id>`; an empty `--model` is the characterized reroute trigger on 0.87.1
  (Pi 1.0.0 rejects the combination visibly).

## Rule: keep declared model ids resolvable

Model ids declared in the live Pi config (`~/.pi/agent/models.json`; note
`~/.pi/agent/models-store.json` is only a catalog cache) must stay resolvable:
verify the id against the backend's own model listing (e.g. `GET /v1/models`)
when declaring it, and re-verify when the backend changes its catalog. An
unresolvable id leaves the sovereign backend usable only through warnings.

## Scope today

No `pi --print` call sites exist in harness code today (grep-verified in the
raid log, 2026-10-02), so this file is a documentation guard for the adapter
pilots (tickets 0923 and 0924): when a runtime adapter for Pi is wired, the
provider assertion above is part of its contract, not an optional check.

Relevant ticket: [0979](../../tickets/0979-pi-reroute-sans-avertissement-vers-openr.erg)
(silent reroute characterization, versions 0.87.1 and 1.0.0).
