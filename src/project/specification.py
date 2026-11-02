"""Explicit paper baseline and a frozen, superseded comparison specification.

The legacy profile exists to measure changes on identical observations. Its inverse
short weights and daily-spread compounding are not buy-and-hold accounting.
"""

PROFILES = {
    "paper": {
        "same_issuer": "allow", "max_stale_share": None, "exclude_constant": False,
        "trigger_sigma": "std", "short_weights": "value", "monthly_aggregation": "books", "sic_fallback": "formation_end",
    },
    "legacy": {
        "same_issuer": "exclude", "max_stale_share": 0.95, "exclude_constant": True,
        "trigger_sigma": "rms", "short_weights": "position",
        "monthly_aggregation": "daily_difference", "sic_fallback": "legacy",
    },
}


def resolve_profile(args):
    """Fill absent command-line overrides; explicit overrides remain sensitivities."""
    for name, value in PROFILES[args.specification].items():
        if not hasattr(args, name):
            setattr(args, name, value)
    return args


def validate_paper_cache(meta: dict) -> None:
    """Claim experiments must not silently mix old selections or return conventions."""
    expected = {
        "format": 6, "normalization": "continued", "telephone_sic": "4811",
        "size_deciles_top": None, "exclude_same_issuer": False, "max_stale_share": None,
        "exclude_constant": False, "trigger_sigma": "std", "short_weights": "value",
        "monthly_aggregation": "books", "sic_fallback": "formation_end",
    }
    bad = {key: (meta.get(key), value) for key, value in expected.items()
           if meta.get(key) != value}
    if bad:
        raise ValueError(f"Claim experiment requires the corrected paper cache; mismatches: {bad}")


def stamp_experiment(output, source_meta: dict, parameters: dict, *, read_only=False):
    """Never reuse claim outputs produced by different accounting/settings."""
    import json
    from pathlib import Path

    output = Path(output)
    path = output / "accounting_meta.json"
    expected = {"accounting_version": 1, "source": source_meta, "parameters": parameters}
    existing = json.loads(path.read_text()) if path.exists() else None
    if existing == expected:
        return
    occupied = output.exists() and any(output.iterdir())
    if read_only or occupied:
        raise ValueError("Unstamped or incompatible claim output; use a new output directory for changed conventions")
    output.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(expected, sort_keys=True, indent=2) + "\n")
