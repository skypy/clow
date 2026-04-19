"""Approximate per-million-token rates (USD) for cost estimation.

These rates drift over time. Treat the estimate as approximate only; this
matches FR-014 and Principle V's posture on staleness. Update the table
when Anthropic publishes new pricing.
"""

from __future__ import annotations

from .aggregator import ModelMix, Totals


# (input, output, cache_write, cache_read) per 1M tokens in USD.
RATES: dict[str, tuple[float, float, float, float]] = {
    "opus": (15.0, 75.0, 18.75, 1.50),
    "sonnet": (3.0, 15.0, 3.75, 0.30),
    "haiku": (0.80, 4.0, 1.00, 0.08),
}


def estimate_cost(totals: Totals, models: ModelMix) -> float:
    """Blend family rates by the model mix percentages and apply to totals.

    Returned as a USD float rounded to two decimal places. The blend is
    deliberately coarse: we do not track per-family token counts, so this
    is a best-effort single number rather than a per-model breakdown.
    """
    mix = {
        "opus": models.opus_pct / 100.0,
        "sonnet": models.sonnet_pct / 100.0,
        "haiku": models.haiku_pct / 100.0,
    }
    # Renormalise if "other" models shaved some percentage off — otherwise
    # cost silently under-reports for users running non-standard models.
    total_known = sum(mix.values()) or 1.0
    mix = {k: v / total_known for k, v in mix.items()}

    def blend(idx: int) -> float:
        return sum(mix[fam] * RATES[fam][idx] for fam in mix)

    per_m = (
        totals.tokens_input * blend(0)
        + totals.tokens_output * blend(1)
        + totals.tokens_cache_create * blend(2)
        + totals.tokens_cache_read * blend(3)
    )
    return round(per_m / 1_000_000, 2)
