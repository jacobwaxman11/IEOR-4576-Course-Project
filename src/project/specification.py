"""Reconciled baseline and explicitly preserved historical sensitivities.

The baseline uses the volume screen and July-1963 start; screens and RMS are
disclosed conventions, not a claim to have recovered the authors’ code.
The legacy profile exists to measure changes on identical observations. Its inverse
short weights and daily-spread compounding are not buy-and-hold accounting.
The historical ``paper`` profile name is retained for cache reproducibility, but
its strict transaction-price screen is not a verified recovery of section 2.1:
historical Nasdaq bid-ask prices can coexist with actual trading. See
report/replication/WRDS_FOLLOWUP.md for explicit universe sensitivities.
"""

PROFILES = {
    "baseline": {
        "universe": "vol_common", "delayed_entry": "execute", "idle_policy": "opened",
        "same_issuer": "exclude", "max_stale_share": 0.95, "exclude_constant": True,
        "trigger_sigma": "rms", "short_weights": "value", "monthly_aggregation": "books",
        "sic_fallback": "formation_end",
    },
    "paper": {
        "universe": "traded_common", "delayed_entry": "execute", "idle_policy": "zero",
        "same_issuer": "allow", "max_stale_share": None, "exclude_constant": False,
        "trigger_sigma": "std", "short_weights": "value", "monthly_aggregation": "books", "sic_fallback": "formation_end",
    },
    "legacy": {
        "universe": "vol_common", "delayed_entry": "cancel", "idle_policy": "exclude",
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


def validate_paper_cache(meta: dict, *, size_deciles_top=None,
                         universe="traded_common", exclude_constant=False) -> None:
    """Claim experiments must not silently mix old selections or return conventions."""
    expected = {
        "format": 7, "normalization": "continued", "telephone_sic": "4811",
        "long_delisting_loss": None, "waste_sic": None,
        "universe": universe, "delayed_entry": "execute", "idle_policy": "zero",
        "size_deciles_top": size_deciles_top, "exclude_same_issuer": False, "max_stale_share": None,
        "exclude_constant": exclude_constant, "trigger_sigma": "std", "short_weights": "value",
        "monthly_aggregation": "books", "sic_fallback": "formation_end",
    }
    bad = {key: (meta.get(key), value) for key, value in expected.items()
           if meta.get(key) != value}
    if bad:
        raise ValueError(f"Claim experiment requires the corrected paper cache; mismatches: {bad}")



def validate_book_cache(meta: dict) -> None:
    """Table 7 reads cached books; selections may vary, but accounting must agree."""
    expected = {"format": 7, "monthly_aggregation": "books", "short_weights": "value"}
    bad = {key: (meta.get(key), value) for key, value in expected.items()
           if meta.get(key) != value}
    if bad:
        raise ValueError(f"Table 7 requires corrected book accounting; mismatches: {bad}")


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


def validate_cache_identity(meta: dict, *, expected_format: int, options=None) -> None:
    """A report must read the cache schema and explicit settings it supports."""
    expected = {"format": expected_format, **(options or {})}
    bad = {key: (meta.get(key), value) for key, value in expected.items()
           if meta.get(key) != value}
    if bad:
        raise ValueError(f"Incompatible report cache: {bad}")


def validate_claim_cache(meta: dict, *, specification="paper", size_deciles_top=None,
                         universe="traded_common", exclude_constant=False) -> None:
    """Require a declared complete profile before combining baseline claim reports."""
    if specification == "paper":
        return validate_paper_cache(meta, size_deciles_top=size_deciles_top,
                                    universe=universe, exclude_constant=exclude_constant)
    if specification != "baseline":
        raise ValueError("Claim reports support baseline or paper specifications")
    expected = dict(PROFILES[specification])
    expected["exclude_same_issuer"] = expected.pop("same_issuer") == "exclude"
    expected.update(format=7, normalization="continued", telephone_sic="4811",
                    long_delisting_loss=None, waste_sic=None, size_deciles_top=size_deciles_top)
    validate_cache_identity(meta, expected_format=7, options=expected)
