"""Tests for the replication driver: output folders, cache stamp and the replication check."""

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("replicate", ROOT / "scripts" / "03_replicate.py")
rep = importlib.util.module_from_spec(_spec)
sys.modules["replicate"] = rep
_spec.loader.exec_module(rep)


def test_primary_universe_writes_to_repo_result_folders():
    assert rep.tables_dir("vol_common") == ROOT / "results" / "replication" / "tables"
    assert rep.figures_dir("vol_common") == ROOT / "results" / "replication" / "figures"
    assert rep.tables_dir("vol_ns") == ROOT / "results" / "replication" / "tables" / "vol_ns"


def test_cache_stamp_and_verify(tmp_path, monkeypatch):
    monkeypatch.setattr(rep, "cohort_dir", lambda universe: tmp_path / universe / "cohorts")
    meta = tmp_path / "u" / "cohorts" / "cache_meta.json"
    with pytest.raises(SystemExit, match="no cache_meta.json"):
        rep.verify_cache("u", continued=True)
    assert not meta.exists()
    rep.stamp_cache("u", continued=True, force=False)
    assert json.loads(meta.read_text()) == {"normalization": "continued", "format": rep.CACHE_FORMAT}
    rep.verify_cache("u", continued=True)
    with pytest.raises(SystemExit, match="continued normalization"):
        rep.verify_cache("u", continued=False)
    with pytest.raises(SystemExit, match="--force"):
        rep.stamp_cache("u", continued=False, force=False)
    rep.stamp_cache("u", continued=False, force=True)
    rep.verify_cache("u", continued=False)


def test_cache_stamp_records_and_checks_formation_options(tmp_path, monkeypatch):
    monkeypatch.setattr(rep, "cohort_dir", lambda universe: tmp_path / universe / "cohorts")
    monkeypatch.setattr(rep, "FORMATION_OPTIONS", {"exclude_same_issuer": True, "max_stale_share": 0.95})
    meta = tmp_path / "u" / "cohorts" / "cache_meta.json"
    rep.stamp_cache("u", continued=True, force=False)
    assert json.loads(meta.read_text()) == {
        "normalization": "continued", "format": rep.CACHE_FORMAT,
        "exclude_same_issuer": True, "max_stale_share": 0.95,
    }
    rep.verify_cache("u", continued=True)
    monkeypatch.setattr(rep, "FORMATION_OPTIONS", {})
    with pytest.raises(SystemExit, match="exclude_same_issuer=True, this run uses no exclude"):
        rep.verify_cache("u", continued=True)
    with pytest.raises(SystemExit, match="--force"):
        rep.stamp_cache("u", continued=True, force=False)


def test_verify_names_an_unstamped_option(tmp_path, monkeypatch):
    monkeypatch.setattr(rep, "cohort_dir", lambda universe: tmp_path / universe / "cohorts")
    rep.stamp_cache("u", continued=True, force=False)
    monkeypatch.setattr(rep, "FORMATION_OPTIONS", {"max_stale_share": 0.95})
    with pytest.raises(SystemExit, match="no max_stale_share stamp"):
        rep.verify_cache("u", continued=True)
    monkeypatch.setattr(rep, "FORMATION_OPTIONS", {"telephone_sic": "4811"})
    with pytest.raises(SystemExit, match="no telephone_sic stamp"):
        rep.verify_cache("u", continued=True)
    monkeypatch.setattr(rep, "FORMATION_OPTIONS", {"trigger_sigma": "rms"})
    with pytest.raises(SystemExit, match="no trigger_sigma stamp"):
        rep.verify_cache("u", continued=True)


def test_share_argument_is_a_unit_interval_value():
    assert rep._share("0.95") == 0.95 and rep._share("0") == 0.0 and rep._share("1") == 1.0
    for bad in ("1.5", "-0.1"):
        with pytest.raises(argparse.ArgumentTypeError):
            rep._share(bad)


def test_verify_refuses_an_old_format_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(rep, "cohort_dir", lambda universe: tmp_path / universe / "cohorts")
    meta = tmp_path / "u" / "cohorts" / "cache_meta.json"
    meta.parent.mkdir(parents=True)
    meta.write_text(json.dumps({"normalization": "continued"}))
    with pytest.raises(SystemExit, match="format None"):
        rep.verify_cache("u", continued=True)
    assert json.loads(meta.read_text()) == {"normalization": "continued"}


def _synthetic_panel() -> pd.DataFrame:
    rng = np.random.default_rng(7)
    dates = pd.bdate_range("2019-07-01", "2020-12-31")
    common = rng.normal(0, 0.01, len(dates))
    rows = []
    sics = {1: 4911, 2: 4911, 3: 6020, 4: 6020, 5: 3711, 6: 3711}
    for permno, sic in sics.items():
        noise = rng.normal(0, 0.004 if permno in (1, 2) else 0.012, len(dates))
        ret = common + noise
        rows.append(pd.DataFrame({
            "permno": permno, "date": dates, "ret": ret, "terminal": False,
            "cap": 100.0 * permno, "exch": "N", "common": True, "siccd": sic,
        }))
    return pd.concat(rows, ignore_index=True)


def test_cohort_job_caches_everything_the_tables_need(tmp_path, monkeypatch):
    panel = _synthetic_panel()
    dates = pd.DatetimeIndex(sorted(panel["date"].unique()))

    def load_daily(start, end, columns=None):
        sel = panel[(panel["date"] >= pd.Timestamp(start)) & (panel["date"] <= pd.Timestamp(end))]
        return sel[list(columns)].reset_index(drop=True)

    monkeypatch.setattr(rep, "cohort_dir", lambda universe: tmp_path / universe / "cohorts")
    monkeypatch.setattr(rep, "load_daily", load_daily)
    monkeypatch.setattr(rep, "trading_calendar", lambda s, e: dates[(dates >= pd.Timestamp(s))
                                                                   & (dates <= pd.Timestamp(e))])
    monkeypatch.setattr(
        rep, "formation_universe", lambda s, e, universe, max_stale_share=None: [1, 2, 3, 4, 5, 6]
    )
    rep.init_worker((pd.Series(dtype="int64"), pd.Series(dtype="int64")))

    job = rep.Job(2020, 7, (2020, 12), (0, 1), "u", True)
    assert rep.build_cohort(job) == (2020, 7)
    assert rep.cohort_cache_complete(2020, 7, (0, 1), "u")
    monthly, summaries = rep.load_summaries([(2020, 7)], "u")
    summary = summaries[0]
    pairs = pd.read_parquet(tmp_path / "u" / "cohorts" / "2020-07" / "pairs.parquet")
    assert summary["stocks"] == 6 and summary["pairs"] == len(pairs) >= 3
    assert summary["sector_counts"]["Utilities"] == 2
    assert summary["sector_counts"]["pairs_Financials"] == 1
    legs = np.r_[pairs["permno_1"].to_numpy(), pairs["permno_2"].to_numpy()]
    utility_share = float(np.isin(legs, [1, 2]).mean())
    assert summary["composition"]["all"]["weight_utilities"] == pytest.approx(utility_share)
    assert set(summary["trading"]) == set(rep.PORTFOLIOS)

    t1 = monthly[monthly["table"] == "t1"]
    assert set(t1["wait"]) == {0, 1} and set(t1["capital"]) == set(rep.T1_CAPITALS)
    assert len(t1[(t1.wait == 1) & (t1.portfolio == "all") & (t1.capital == "committed")]) == 6
    t3 = monthly[monthly["table"] == "t3"]
    assert set(t3["sector"]) == {"Utilities", "Financials", "Industrials"}
    assert set(t3["portfolio"]) == {"all"}

    strategy, trading, composition, universe = rep.aggregate(monthly, summaries, (0, 1), (2020, 12))
    assert len(strategy[1]["all"]["employed"]) == 6
    assert strategy[1]["101-120"]["committed"].empty
    assert universe["mean_pairs_per_cohort"] == len(pairs)
    assert composition["all"]["weight_utilities"] == pytest.approx(utility_share)
    assert trading["all"]["avg_pairs_traded_per_period"] == summary["trading"]["all"]["n_opened"]
    table3, counts = rep.table3_from_cache(monthly, summaries, (2020, 12))
    assert set(table3["sector"]) == {"Utilities", "Financials", "Industrials"}
    assert counts["Utilities"].item() == 2
    trades = pd.read_parquet(tmp_path / "u" / "cohorts" / "2020-07" / "w0_trades.parquet")
    assert {"open_day", "close_day"} <= set(trades.columns)


@pytest.mark.parametrize(
    "ours, paper, mark",
    [(1.05, 1.0, "✓"), (0.91, 1.0, "✓"), (1.2, 1.0, "~"), (0.7, 1.0, "✗"), (-1.0, 1.0, "✗"),
     (float("nan"), 1.0, ""), (1.0, 0.0, "")],
)
def test_marks_use_relative_gap(ours, paper, mark):
    assert rep._mark(ours, paper) == mark


def _figure1_json(fig_dir: Path, trades, levels=(1.1006, 1.106), rank=4) -> None:
    fig_dir.mkdir(parents=True, exist_ok=True)
    info = {"rank": rank, "sigma": 0.02, "start_levels": list(levels), "trades": trades,
            "png": "results/replication/figures/figure1.png"}
    (fig_dir / "figure1.json").write_text(json.dumps(info))


def test_check_reports_figure1_reproduced_within_tolerance(tmp_path):
    trades = [[8, 35], [46, 56], [76, 83], [85, 99], [108, 125]]
    _figure1_json(tmp_path / "fig", trades)
    (tmp_path / "tab").mkdir()
    text = rep.write_replication_check(tmp_path / "tab", tmp_path / "fig", "vol_common").read_text()
    assert "Figure 1: reproduced" in text
    assert "| pair formed (rank) | 4 | top 5 | ✓ |" in text


def test_check_flags_figure1_with_a_missing_trade(tmp_path):
    _figure1_json(tmp_path / "fig", [[8, 35], [46, 56], [76, 83], [85, 99]])
    (tmp_path / "tab").mkdir()
    text = rep.write_replication_check(tmp_path / "tab", tmp_path / "fig", "vol_common").read_text()
    assert "Figure 1: not reproduced" in text


def test_check_scores_table1_cells_against_the_paper(tmp_path):
    out = tmp_path / "tab"
    out.mkdir()
    cols, data = [], {}
    for panel in ("A", "B"):
        for p in rep.PORTFOLIOS:
            cols.append((panel, p))
            data[(panel, p)] = dict(rep.PAPER_TABLE1[panel][p])
    table = pd.DataFrame(data)
    table.columns = pd.MultiIndex.from_tuples(cols, names=["panel", "portfolio"])
    table.loc["mean", ("A", "top5")] *= 2.0
    table.to_csv(out / "table1.csv")
    text = rep.write_replication_check(out, tmp_path / "fig", "vol_common").read_text()
    n = 2 * len(rep.PORTFOLIOS) * len(rep.PAPER_TABLE1["A"]["top5"])
    assert f"Table 1: Cells: {n}; ✓ {n - 1} (within 10%), ~ 0 (within 25%), ✗ 1." in text
    assert "Figure 1 (Kennecott vs Uniroyal" in text and "Not run" in text
    assert f"- Score: {n - 1:.1f} of {n} compared cells" in text
