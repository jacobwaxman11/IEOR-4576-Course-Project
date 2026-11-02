"""Method disclosures and score arithmetic for reproducible replication reports."""

from __future__ import annotations

import re
from collections import Counter


def score_report(text: str) -> dict:
    """Count marked comparison cells; points are not a count of matching cells."""
    counts = Counter()
    for line in text.splitlines():
        if line.lstrip().startswith("|") and " / " in line:
            counts.update(re.findall(r"\s(✓|~|✗)\s*(?=\||$)", line))
    full, half, miss = (counts[m] for m in ("✓", "~", "✗"))
    n = full + half + miss
    return {"score": full + 0.5 * half, "valid": n > 0, "full": full, "half": half,
            "miss": miss, "total_cells": n, "within_10_percent": full,
            "within_25_percent": full + half,
            "within_10_fraction": full / n if n else None,
            "within_25_fraction": (full + half) / n if n else None}


def conventions(options: dict, short_weights: str) -> list[str]:
    """Describe the run's actual settings, never hard-coded historical defaults."""
    sigma = options.get("trigger_sigma", "std")
    aggregation = options.get("monthly_aggregation", "books")
    return [
        "## Specification and limitations", "",
        f"Entry scale: `{sigma}`. Standard deviation about the formation mean implements",
        "section 2.2 / Table 2A; RMS about zero is a separate legacy sensitivity.",
        f"Short weights: `{short_weights}`. `value` tracks the shorted stock's liability",
        "under section 2.3 equations (2)-(3); `position` is the superseded inverse-weight rule.",
        f"Monthly aggregation: `{aggregation}`. `books` compounds long and short books",
        "separately and subtracts, preserving Table 1B = Table 7 long minus short.",
        "`daily_difference` is a legacy sensitivity and does not preserve that identity.",
        f"Liquidity universe: `{options.get('universe', 'traded_common')}`; traded_common requires",
        "a CIZ trade-price flag, no recorded zero volume, and a finite return on every formation day.",
        "This conservative observable-trade screen is not a recovered historical CRSP vintage.",
        f"Idle cash policy: `{options.get('idle_policy', 'zero')}`; zero retains inactive cohorts in the desk average.",
        "Committed capital scales both daily books by the active fraction of selected pairs;",
        "the employed-capital denominator uses pairs open that day. This timing convention",
        "remains an interpretation of the paper's 'open during the trading period'.",
        f"Additional screens: same issuer excluded={options.get('exclude_same_issuer', False)};",
        f"constant path excluded={options.get('exclude_constant', False)}; "
        f"maximum stale share={options.get('max_stale_share')}.",
        "These extra screens are absent from the paper baseline. The old vol_common universe",
        "admits missing volume and quote-only days; it is retained as a sensitivity.",
        "Trading paths continue formation normalization.",
        f"SIC fallback: `{options.get('sic_fallback', 'formation_end')}`. The paper baseline uses",
        "dated formation-end codes only; unknowns map to Industrials. The legacy fallback",
        "can use future classifications and is excluded from the paper baseline.",
        "SIC group boundaries remain interpretations, not recovered S&P classifications.",
        f"Delayed entry: `{options.get('delayed_entry', 'execute')}`. Execute preserves the signal-day direction",
        "and exits the next day if a crossing occurred on the entry day. Cancel is legacy behavior.",
        "period_cash and selected_cash outputs audit fixed-dollar payoff/period denominators;",
        "they are explicit alternatives, not substitutes chosen to improve target fit.",
        "", "Factor results are proxy robustness checks: French ST_Rev is not the paper's",
        "unavailable custom reversal series, and rebuilt Ibbotson inputs have not been",
        "validated against its proprietary vintage. Significant proxy-factor alpha does not",
        "establish the original regression or a causal mispricing mechanism.",
        "", "The score reports weighted points and actual cell counts separately.",
        "A better score does not override the paper's rules or accounting identities.", "",
    ]
