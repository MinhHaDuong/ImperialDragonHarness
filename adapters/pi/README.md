# pi adapter — provider-assertion rule for `pi --print` drivers

Pi is a coding-agent runtime the harness can drive with
`pi --print --mode json`. Characterized on 0.87.1 (ticket 0979,
[docs/2026-10-02-pi-reroute-openrouter-0979.md](../../docs/2026-10-02-pi-reroute-openrouter-0979.md)),
on padme only, one machine configuration: with an empty or absent `--model`,
Pi silently discards the explicit `--provider` and serves the request through
the first provider with a valid key on the machine (huggingface in the
2026-10-02 reproduction). Exit 0, a normal-looking answer, no warning on
stderr or in the JSON stream. In the same tests an unknown provider name
errors visibly, and an unknown non-empty model id with an explicit provider
stays on that provider with a stderr warning. Upstream fixed the empty/absent
path in 1.0.0 (earendil-works/pi#10236).

Essai 0977 observed a silent reroute to openrouter with a **non-empty**
unresolvable id under `--provider ilaas`. That trigger is unreconciled with
the characterization above: ilaas was not tested (keys pending), and nothing
shows 0977's `--model` was empty. The rule below guards both cases, since it
checks the served provider whatever the trigger.

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
  <id>`; an empty `--model` is the reroute trigger characterized on 0.87.1
  (Pi 1.0.0 rejects the combination visibly).

## Rule: keep declared model ids resolvable

Model ids declared in the live Pi config (`~/.pi/agent/models.json`; note
`~/.pi/agent/models-store.json` is only a catalog cache) must stay resolvable:
verify the id against the backend's own model listing (e.g. `GET /v1/models`)
when declaring it, and re-verify when the backend changes its catalog. An
unresolvable id leaves the sovereign backend usable only through warnings.

## Scope today

The Pi adapter ships the bash guard extension
(`extensions/idh-guard.ts`, ticket 0809); it does not drive Pi. No
`pi --print` call sites exist in harness code today (grep-verified in the
raid log, 2026-10-02), so this rule is a documentation guard for the adapter
pilots (tickets 0923 and 0924): when a `pi --print` driver is wired, the
provider assertion above is part of its contract, not an optional check.

Relevant ticket: [0979](../../tickets/0979-pi-reroute-sans-avertissement-vers-openr.erg)
(silent reroute characterization, versions 0.87.1 and 1.0.0).
