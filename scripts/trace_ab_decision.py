"""Phase-5 A/B decision rule — pure functions (ticket 0315).

Pre-registered in docs/trace-ab-2026-06.md. No argparse, no __main__: the sole
consumers are the unit tests now and the 0245 harvest step later, which imports
`decide` and `filter_window` directly. Zero LLM calls, no network, no I/O.

Decision rule (pre-registered before any B-arm data):
    adopt iff candidate cost is strictly below baseline
         AND each guardrail (reroll_per_pr, escalate_count) stays at or below
             baseline * (1 + guardrail_noise_pct).
A cost win with a breached guardrail is a REJECT — the guardrail is binding.
"""

# Guardrail metrics: lower is better, capped at baseline*(1+noise).
_GUARDRAILS = ("reroll_per_pr", "escalate_count")


def filter_window(
    rows: list[dict], start: str, end: str, *, date_key: str = "date"
) -> list[dict]:
    """Keep rows whose ISO date lies within [start, end], inclusive both ends.

    Dates are compared as ISO-8601 strings (YYYY-MM-DD), which sort
    lexicographically in chronological order, so no date parsing is needed.
    """
    return [r for r in rows if start <= r[date_key] <= end]


def decide(
    baseline: dict, candidate: dict, *, guardrail_noise_pct: float = 0.10
) -> dict:
    """Return {"verdict": "adopt"|"reject", "reasons": [...]} for candidate.

    `baseline` and `candidate` each carry keys: cost_per_pr, reroll_per_pr,
    escalate_count. `guardrail_noise_pct` is the pre-registered tolerance band
    on the guardrails (default 0.10 = 10%).
    """
    reasons: list[str] = []

    if candidate["cost_per_pr"] < baseline["cost_per_pr"]:
        reasons.append(
            f"cost_per_pr {candidate['cost_per_pr']} < baseline "
            f"{baseline['cost_per_pr']} (cost win)"
        )
        cost_win = True
    else:
        reasons.append(
            f"cost_per_pr {candidate['cost_per_pr']} not below baseline "
            f"{baseline['cost_per_pr']} (no cost win)"
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
