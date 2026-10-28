"""Tests for the opt-in size screen of the formation universe (Table 9 Panel A).

The screen is the paper's "pairs that are formed using only stocks in the top
three size deciles" (Section 3.9). Two things can go wrong and both are tested
here: the decile assignment itself, and the wiring that makes a cohort use it
only when the option is set.
"""

import argparse
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from project.evaluation import restrict_to_size_deciles, size_deciles

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("replicate", ROOT / "scripts" / "03_replicate.py")
rep = importlib.util.module_from_spec(_spec)
sys.modules["replicate"] = rep
_spec.loader.exec_module(rep)


def _cross_section(n=1000, exchange="N", common=True):
    """``n`` NYSE common names with caps 1..n; one row per PERMNO."""
    permnos = pd.Index(np.arange(1000, 1000 + n), name="permno")
    caps = pd.Series(np.arange(1, n + 1, dtype=float), index=permnos)
    exch = pd.Series(exchange, index=permnos)
    flag = pd.Series(common, index=permnos)
    return permnos, caps, exch, flag


def test_the_screen_keeps_exactly_deciles_one_to_three():
    """On an even cross-section the top three deciles are the 300 largest names."""
    permnos, caps, exch, flag = _cross_section()
    deciles = size_deciles(caps, caps[exch.isin(("N", "A")) & flag.eq(True)])
    kept = restrict_to_size_deciles(permnos, caps, exch, flag, 3)
    assert len(kept) == 300
    assert kept.equals(permnos[deciles.le(3).to_numpy()])
    assert caps[kept].min() == 701 and caps[kept].max() == 1000
    assert set(deciles[kept].unique()) == {1.0, 2.0, 3.0}
    # a larger N keeps a superset, and 10 keeps every name that has a cap
    assert restrict_to_size_deciles(permnos, caps, exch, flag, 1).equals(permnos[900:])
    assert restrict_to_size_deciles(permnos, caps, exch, flag, 5).equals(permnos[500:])
    assert len(restrict_to_size_deciles(permnos, caps, exch, flag, 10)) == 1000


def test_breakpoints_are_nyse_and_amex_common_only():
    """An outsider never moves a breakpoint, but is still classified against them."""
    permnos, caps, exch, flag = _cross_section()
    outsiders = pd.Index([9001, 9002, 9003], name="permno")
    all_permnos = permnos.append(outsiders)
    extra_caps = pd.Series([1e9, 5e8, 2e5], index=outsiders)
    caps = pd.concat([caps, extra_caps])
    exch = pd.concat([exch, pd.Series(["Q", "Q", "N"], index=outsiders)])
    flag = pd.concat([flag, pd.Series([True, True, False], index=outsiders)])
    kept = restrict_to_size_deciles(all_permnos, caps, exch, flag, 3)
    # the cut is unchanged at 701, so the screen keeps the same 300 NYSE names
    # plus the two Nasdaq names and the one non-common name, which are all huge
    assert set(kept) - set(permnos) == {9001, 9002, 9003}
    assert len(kept[kept.isin(permnos)]) == 300
    assert caps[kept[kept.isin(permnos)]].min() == 701
    # drop the outsiders from the breakpoint set and the 300-name cut is identical
    nyse_only = restrict_to_size_deciles(permnos, caps, exch, flag, 3)
    assert nyse_only.equals(permnos[700:])


def test_a_name_without_a_cap_is_dropped():
    """No formation-end cap means no decile, so the screen cannot keep the name."""
    permnos, caps, exch, flag = _cross_section(n=100)
    caps = caps.copy()
    caps.iloc[95] = np.nan
    deciles = size_deciles(caps, caps[exch.isin(("N", "A")) & flag.eq(True)])
    assert np.isnan(deciles.iloc[95]) and deciles.notna().sum() == 99
    kept = restrict_to_size_deciles(permnos, caps, exch, flag, 1)
    assert permnos[95] not in kept
    assert kept.equals(permnos[deciles.le(1).to_numpy()])
    assert len(kept) > 0
    # N = 10 keeps every name that has a cap, and only those
    kept10 = restrict_to_size_deciles(permnos, caps, exch, flag, 10)
    assert len(kept10) == 99 and permnos[95] not in kept10


def test_the_option_is_an_optional_cache_stamp():
    """Off, the screen leaves no trace in the stamp; on, it is recorded and checked."""
    defaults = argparse.Namespace(same_issuer="exclude", max_stale_share=None,
                                  telephone_sic="4811", trigger_sigma="rms",
                                  short_weights="position", size_deciles_top=None)
    assert "size_deciles_top" not in rep.formation_options(defaults)
    screened = argparse.Namespace(**{**vars(defaults), "size_deciles_top": 3})
    assert rep.formation_options(screened)["size_deciles_top"] == 3


def test_decile_count_argument_is_one_to_ten():
    assert rep._decile_count("3") == 3 and rep._decile_count("10") == 10
    for bad in ("0", "11", "three"):
        with pytest.raises(argparse.ArgumentTypeError):
            rep._decile_count(bad)


def test_a_shard_file_carries_the_screen_to_its_children():
    job = rep.Job(2020, 7, (2020, 12), (0, 1), "vol_common", True,
                  size_deciles_top=3)
    assert rep.job_from_shard(rep.job_to_shard(job)) == job
    plain = rep.Job(2020, 7, (2020, 12), (0, 1), "vol_common", True)
    assert rep.job_from_shard(rep.job_to_shard(plain)).size_deciles_top is None


def _synthetic_panel() -> pd.DataFrame:
    """Six stocks, caps 100..600 on the label day, so deciles are 1..10 spread."""
    rng = np.random.default_rng(7)
    dates = pd.bdate_range("2019-07-01", "2020-12-31")
    common = rng.normal(0, 0.01, len(dates))
    rows = []
    sics = {1: 4911, 2: 4911, 3: 6020, 4: 6020, 5: 3711, 6: 3711}
    for permno, sic in sics.items():
        noise = rng.normal(0, 0.004 if permno in (1, 2) else 0.012, len(dates))
        rows.append(pd.DataFrame({
            "permno": permno, "date": dates, "ret": common + noise, "terminal": False,
            "cap": 100.0 * permno, "exch": "N", "common": True, "siccd": sic,
            "prc_ok": True, "vol_zero": False, "vol_pos": True,
        }))
    return pd.concat(rows, ignore_index=True)


def _build(tmp_path, monkeypatch, month, size_deciles_top):
    panel = _synthetic_panel()
    dates = pd.DatetimeIndex(sorted(panel["date"].unique()))

    def load_daily(start, end, columns=None, permnos=None):
        sel = panel[(panel["date"] >= pd.Timestamp(start)) & (panel["date"] <= pd.Timestamp(end))]
        if permnos is not None:
            sel = sel[sel["permno"].isin(list(permnos))]
        return sel[list(columns)].reset_index(drop=True)

    monkeypatch.setattr(rep, "cohort_dir", lambda universe: tmp_path / universe / "cohorts")
    monkeypatch.setattr(rep, "load_daily", load_daily)
    monkeypatch.setattr(
        rep, "trading_calendar",
        lambda s, e: dates[(dates >= pd.Timestamp(s)) & (dates <= pd.Timestamp(e))],
    )
    monkeypatch.setattr(
        rep, "formation_universe",
        lambda s, e, universe, max_stale_share=None, panel=None: [1, 2, 3, 4, 5, 6],
    )
    rep.init_worker((pd.Series(dtype="int64"), pd.Series(dtype="int64")))
    job = rep.Job(2020, month, (2020, 12), (0, 1), "vol_common", True,
                  size_deciles_top=size_deciles_top)
    assert rep.build_cohort(job) == (2020, month)
    coh = tmp_path / "vol_common" / "cohorts" / f"2020-{month:02d}"
    pairs = pd.read_parquet(coh / "pairs.parquet")
    summary = rep.load_summaries([(2020, month)], "vol_common")[1][0]
    return pairs, summary


def test_screened_cohort_forms_pairs_only_in_the_top_three_deciles(tmp_path, monkeypatch):
    """Caps 100..600 put stocks 5 and 6 in deciles 2 and 1; the screen keeps those."""
    pairs, summary = _build(tmp_path, monkeypatch, 8, 3)
    legs = set(pairs["permno_1"]) | set(pairs["permno_2"])
    assert legs == {5, 6}
    assert summary["stocks"] == 2 and summary["pairs"] == len(pairs) == 1
    assert summary["size_deciles_top"] == 3


def test_unscreened_cohort_is_the_shipped_one(tmp_path, monkeypatch):
    pairs, summary = _build(tmp_path, monkeypatch, 7, None)
    assert "size_deciles_top" not in summary
    assert summary["stocks"] == 6 and summary["pairs"] == len(pairs)
    assert {5, 6} < (set(pairs["permno_1"]) | set(pairs["permno_2"]))
