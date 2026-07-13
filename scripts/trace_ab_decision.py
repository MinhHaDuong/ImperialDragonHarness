"""Phase-5 A/B decision rule — pure functions (ticket 0315).

Pre-registered in docs/trace-ab-2026-06.md. No argparse, no __main__: the sole
consumers are the unit tests now and the 0245 harvest step later, which imports
`decide` and `filter_window` directly. Zero LLM calls, no network, no I/O.

Decision rule (pre-registered before any B-arm data):
    adopt iff candidate cost is strictly below baseline
         AND each guardrail (reroll_per_pr, escalate_count) stays at or below
             baseline * (1 + guardrail_noise_pct).
A cost win with a breached guardrail is a REJECT — the guardrail is binding.

The metric keys match docs/trace-ab-2026-06.md exactly: the primary cost metric
is `cost_per_merged_pr` (measure A / default); measure B compares on
`cost_per_cycle` by passing `cost_key="cost_per_cycle"`. Keeping the code keys
identical to the pre-registration doc is the whole point of this ticket — the
0245 harvest reads the doc and must not hit a KeyError.
"""

# Pre-registered guardrail noise band (10%). Named so the doc and the harvest
# step share one source of truth; a caller may override for testing the band
# mechanics, but production harvest uses this pre-registered value.
PREREGISTERED_NOISE_PCT = 0.10

# Guardrail metrics: lower is better, capped at baseline*(1+noise).
_GUARDRAILS = ("reroll_per_pr", "escalate_count")


def filter_window(
    rows: list[dict], start: str, end: str, *, date_key: str = "date"
) -> list[dict]:
    """Keep rows whose ISO date lies within [start, end], inclusive both ends.

    Dates are compared on their `YYYY-MM-DD` prefix, which sorts
    lexicographically in chronological order, so no date parsing is needed and a
    full ISO timestamp (`2026-06-30T14:00Z`) still matches a bare-date window.
    `start` and `end` are bare `YYYY-MM-DD` strings.
    """
    return [r for r in rows if start <= r[date_key][:10] <= end]


def decide(
    baseline: dict,
    candidate: dict,
    *,
    cost_key: str = "cost_per_merged_pr",
    guardrail_noise_pct: float = PREREGISTERED_NOISE_PCT,
) -> dict:
    """Return {"verdict": "adopt"|"reject", "reasons": [...]} for candidate.

    `baseline` and `candidate` each carry the compared cost key (`cost_key`,
    default `cost_per_merged_pr`; pass `cost_per_cycle` for measure B) plus the
    guardrail keys reroll_per_pr and escalate_count. `guardrail_noise_pct` is
    the pre-registered tolerance band on the guardrails (default 10%).
    """
    reasons: list[str] = []

    if candidate[cost_key] < baseline[cost_key]:
        reasons.append(
            f"{cost_key} {candidate[cost_key]} < baseline "
            f"{baseline[cost_key]} (cost win)"
        )
        cost_win = True
    else:
        reasons.append(
            f"{cost_key} {candidate[cost_key]} not below baseline "
            f"{baseline[cost_key]} (no cost win)"
        )
        cost_win = False

    guardrails_hold = True
    for key in _GUARDRAILS:
        band = baseline[key] * (1 + guardrail_noise_pct)
        if candidate[key] <= band:
            reasons.append(f"{key} {candidate[key]} <= band {band} (holds)")
        else:
            reasons.append(f"{key} {candidate[key]} > band {band} (breach)")
            guardrails_hold = False

    verdict = "adopt" if cost_win and guardrails_hold else "reject"
    return {"verdict": verdict, "reasons": reasons}
