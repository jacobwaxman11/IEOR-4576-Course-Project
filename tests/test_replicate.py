"""Tests for the replication driver: output folders, cache stamp and the replication check."""

import argparse
import importlib.util
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from project import sectors

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


def test_formation_options_stamp_every_value():
    defaults = argparse.Namespace(same_issuer="exclude", max_stale_share=None, telephone_sic="4811",
                                  trigger_sigma="rms", short_weights="position",
                                  size_deciles_top=None)
    assert rep.formation_options(defaults) == {
        "exclude_same_issuer": True, "telephone_sic": "4811", "trigger_sigma": "rms",
        "short_weights": "position",
    }
    other = argparse.Namespace(same_issuer="allow", max_stale_share=0.9, telephone_sic="481x",
                               trigger_sigma="std", short_weights="value",
                               size_deciles_top=3)
    assert rep.formation_options(other) == {
        "exclude_same_issuer": False, "max_stale_share": 0.9, "telephone_sic": "481x",
        "trigger_sigma": "std", "short_weights": "value", "size_deciles_top": 3,
    }


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
    monkeypatch.setattr(rep, "FORMATION_OPTIONS", {"short_weights": "position"})
    with pytest.raises(SystemExit, match="no short_weights stamp"):
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
            # the vol_common universe's row flags: every row trades and is priced
            "prc_ok": True, "vol_zero": False, "vol_pos": True,
        }))
    return pd.concat(rows, ignore_index=True)


def test_cohort_job_caches_everything_the_tables_need(tmp_path, monkeypatch):
    panel = _synthetic_panel()
    dates = pd.DatetimeIndex(sorted(panel["date"].unique()))

    def load_daily(start, end, columns=None, permnos=None):
        sel = panel[(panel["date"] >= pd.Timestamp(start)) & (panel["date"] <= pd.Timestamp(end))]
        if permnos is not None:
            sel = sel[sel["permno"].isin(list(permnos))]
        return sel[list(columns)].reset_index(drop=True)

    monkeypatch.setattr(rep, "cohort_dir", lambda universe: tmp_path / universe / "cohorts")
    monkeypatch.setattr(rep, "load_daily", load_daily)
    monkeypatch.setattr(rep, "trading_calendar", lambda s, e: dates[(dates >= pd.Timestamp(s))
                                                                   & (dates <= pd.Timestamp(e))])
    monkeypatch.setattr(
        rep, "formation_universe",
        lambda s, e, universe, max_stale_share=None, panel=None: [1, 2, 3, 4, 5, 6],
    )
    rep.init_worker((pd.Series(dtype="int64"), pd.Series(dtype="int64")))

    job = rep.Job(2020, 7, (2020, 12), (0, 1), "vol_common", True)
    assert rep.build_cohort(job) == (2020, 7)
    assert rep.cohort_cache_complete(2020, 7, (0, 1), "vol_common")
    monthly, summaries = rep.load_summaries([(2020, 7)], "vol_common")
    summary = summaries[0]
    pairs = pd.read_parquet(tmp_path / "vol_common" / "cohorts" / "2020-07" / "pairs.parquet")
    assert summary["stocks"] == 6 and summary["pairs"] == len(pairs) >= 3
    assert summary["sector_counts"]["Utilities"] == 2
    assert summary["sector_counts"]["pairs_Financials"] == 1
    legs = np.r_[pairs["permno_1"].to_numpy(), pairs["permno_2"].to_numpy()]
    utility_share = float(np.isin(legs, [1, 2]).mean())
    assert summary["composition"]["all"]["weight_utilities"] == pytest.approx(utility_share)
    assert set(summary["trading"]) == set(rep.PORTFOLIOS)

    t1 = monthly[monthly["table"] == "t1"]
    assert set(t1["wait"]) == {0, 1} and set(t1["capital"]) == {
        *rep.T1_CAPITALS, *rep.LEG_CAPITALS}
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
    trades = pd.read_parquet(tmp_path / "vol_common" / "cohorts" / "2020-07" / "w0_trades.parquet")
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
    text = rep.write_replication_check(tmp_path / "tab", tmp_path / "fig", "vol_common", "position").read_text()
    assert "Figure 1: reproduced" in text
    assert "| pair formed (rank) | 4 | top 5 | ✓ |" in text


def test_check_flags_figure1_with_a_missing_trade(tmp_path):
    _figure1_json(tmp_path / "fig", [[8, 35], [46, 56], [76, 83], [85, 99]])
    (tmp_path / "tab").mkdir()
    text = rep.write_replication_check(tmp_path / "tab", tmp_path / "fig", "vol_common", "position").read_text()
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
    text = rep.write_replication_check(out, tmp_path / "fig", "vol_common", "position").read_text()
    n = 2 * len(rep.PORTFOLIOS) * len(rep.PAPER_TABLE1["A"]["top5"])
    assert f"Table 1: Cells: {n}; ✓ {n - 1} (within 10%), ~ 0 (within 25%), ✗ 1." in text
    assert "Figure 1 (Kennecott vs Uniroyal" in text and "Not run" in text
    assert f"- Score: {n - 1:.1f} of {n} compared cells" in text


def test_check_header_describes_the_short_weight_it_was_run_with(tmp_path):
    (tmp_path / "tab").mkdir()
    pos = rep.write_replication_check(tmp_path / "tab", tmp_path / "fig", "vol_common",
                                      "position").read_text()
    val = rep.write_replication_check(tmp_path / "tab", tmp_path / "fig", "vol_common",
                                      "value").read_text()
    assert "a short by prod(1 - r)" in pos and "1.61-2.02" in pos and "floored at zero" in pos
    assert "a short by the shorted stock's value" in val and "1.60-1.90" in val
    assert "this run uses --short-weights\nvalue" in val
    assert "1.61-2.02" not in val and "floored at zero" not in val


def _paper_table1(out: Path, panels=("A", "B")) -> None:
    cols, data = [], {}
    for panel in panels:
        for p in rep.PORTFOLIOS:
            cols.append((panel, p))
            data[(panel, p)] = dict(rep.PAPER_TABLE1[panel][p])
    table = pd.DataFrame(data)
    table.columns = pd.MultiIndex.from_tuples(cols, names=["panel", "portfolio"])
    table.to_csv(out / "table1.csv")


def test_check_scores_tables_5_and_8(tmp_path):
    out = tmp_path / "tab"
    out.mkdir()
    _paper_table1(out)
    for fname, paper in zip(rep.DIAGNOSTIC_FILES, (rep.PAPER_TABLE5, rep.PAPER_TABLE8)):
        frame = pd.DataFrame(paper) * 3.0
        frame.index.name = "statistic"
        frame.to_csv(out / fname)
    text = rep.write_replication_check(out, tmp_path / "fig", "vol_common", "position").read_text()
    n = 2 * len(rep.PORTFOLIOS) * len(rep.PAPER_TABLE1["A"]["top5"])
    extra = sum(len(rep.PAPER_TABLE5[p]) + len(rep.PAPER_TABLE8[p]) for p in rep.PORTFOLIOS)
    assert f"- Score: {n:.1f} of {n + extra} compared cells" in text
    assert "Diagnostics" not in text
    block = text.split("## Table 5 Panel A")[1]
    assert "| var_5 | -6.426% / -2.142% ✗ |" in block
    assert "- Table 5 Panel A: Cells: 20; ✓ 0 (within 10%), ~ 0 (within 25%), ✗ 20." in text
    assert "## Table 4 (systematic risk, one-day wait)\n\nNot run" in text


def test_check_reports_a_missing_table1_panel_as_not_run(tmp_path):
    out = tmp_path / "tab"
    out.mkdir()
    _paper_table1(out, panels=("A",))
    text = rep.write_replication_check(out, tmp_path / "fig", "vol_common", "position").read_text()
    n = len(rep.PORTFOLIOS) * len(rep.PAPER_TABLE1["A"]["top5"])
    assert "Not run (needs `--wait 1`)." in text
    assert f"- Score: {n:.1f} of {n} compared cells" in text
    assert text.count("Not run (needs the one-day-wait series") == 3


def test_risk_tables_without_factors_write_sharpe_and_raw_correlations(tmp_path):
    idx = pd.date_range("1963-07-31", periods=60, freq="ME")
    rng = np.random.default_rng(3)
    base = rng.normal(0.008, 0.015, 60)
    series = {p: pd.Series(base + rng.normal(0, 0.01, 60), index=idx) for p in rep.PORTFOLIOS}
    rep.write_risk_tables(series, None, tmp_path)
    t4 = pd.read_csv(tmp_path / "table4.csv", index_col=0)
    assert list(t4.index) == ["sharpe"]
    # the equity premium is the factors' market column, so it needs the factors too
    assert not (tmp_path / "table4_equity_premium.csv").exists()
    s = series["top5"]
    assert t4.loc["sharpe", "top5"] == pytest.approx(s.mean() / s.std(ddof=1))
    f4 = pd.read_csv(tmp_path / "figure4.csv", index_col=0)
    assert list(f4.columns) == ["raw"]
    assert f4.loc["correlation, full sample", "raw"] == pytest.approx(
        series["top20"].corr(series["101-120"]))


def test_risk_tables_take_the_equity_premium_from_mkt_rf_and_print_alpha_t(tmp_path):
    idx = pd.date_range("1963-07-31", periods=120, freq="ME")
    rng = np.random.default_rng(5)
    factors = pd.DataFrame(rng.normal(0.005, 0.04, (130, len(rep.FACTORS))),
                           index=pd.date_range("1963-01-31", periods=130, freq="ME"),
                           columns=rep.FACTORS)
    series = {p: pd.Series(0.008 + 0.1 * factors["market"].loc[idx].to_numpy()
                           + rng.normal(0, 0.01, 120), index=idx) for p in rep.PORTFOLIOS}
    rep.write_risk_tables(series, factors, tmp_path)
    ep = pd.read_csv(tmp_path / "table4_equity_premium.csv", index_col=0).iloc[:, 0]
    mkt = factors["market"].loc[idx]  # the portfolio months only, not the factor file's
    assert ep["mean"] == pytest.approx(mkt.mean())
    assert ep["std"] == pytest.approx(mkt.std(ddof=1))
    t4 = pd.read_csv(tmp_path / "table4.csv", index_col=0)
    want = rep.factor_tstats(series["top20"], factors)
    assert t4.loc["t_intercept", "top20"] == pytest.approx(want["intercept"])
    rows = rep._alpha_t_rows(t4, "Table 4 (systematic risk, one-day wait)")
    assert len(rows) == 1 and " / " not in rows[0]  # unscored: the scorer skips rows without " / "
    assert f"{t4.loc['t_intercept', 'top5']:.2f} vs 3.81" in rows[0]


def test_reversal_alternative_is_reported_but_not_scored(tmp_path):
    idx = pd.date_range("1963-07-31", periods=474, freq="ME")
    rng = np.random.default_rng(6)
    factors = pd.DataFrame(rng.normal(0.005, 0.04, (474, len(rep.FACTORS))), index=idx,
                           columns=rep.FACTORS)
    series = {p: pd.Series(0.008 + 0.2 * factors["reversal"].to_numpy()
                           + rng.normal(0, 0.01, 474), index=idx) for p in rep.PORTFOLIOS}
    losers = pd.Series(rng.normal(0.01, 0.07, 474), index=idx)
    rep.write_risk_tables(series, factors, tmp_path)
    rep.write_reversal_alternative(series, factors, losers, tmp_path)
    alt = pd.read_csv(tmp_path / "reversal_alternative.csv", index_col=0)
    assert {f"{h}_{r}" for h in ("full", "pre", "post") for r in rep.FACTOR_ROWS} == set(alt.index)
    want = rep.factor_regression(series["top5"], factors.assign(reversal=losers))
    assert alt.loc["full_reversal", "top5"] == pytest.approx(want["reversal"])
    frame = pd.DataFrame(rep.PAPER_TABLE8)
    frame.index.name = "statistic"
    frame.to_csv(tmp_path / "table8_subperiod.csv")
    lines = rep._reversal_alternative_section(tmp_path, ["✓", "~"])
    assert lines[0].startswith("## Reversal factor")
    # the scorer only reads rows with " / ": none of these may carry one
    assert not [line for line in lines if line.startswith("|") and " / " in line]
    # the closing line sets the alternative's total against the scored total passed in
    tail = lines[-2]
    assert tail.startswith("With this series the 84 regression cells would score")
    assert "instead of 1.5." in tail


def _jobs(months=(1, 2, 3), tmp_path=None):
    """Job fixtures; ``tmp_path`` keeps a real build's cohort writes in the test."""
    root = str(Path(tmp_path) / "cohorts") if tmp_path is not None else None
    return [rep.Job(2020, month, (2020, 12), (0,), "vol_common", True, root)
            for month in months]


def _raise(exc):
    def build(job):
        raise exc

    return build


def _venv_python() -> str:
    candidate = ROOT / ".venv" / "bin" / "python"
    return str(candidate if candidate.exists() else Path(sys.executable))


class TestShardFiles:
    """The shard file is the whole contract between the parent and a child."""

    def test_a_job_survives_the_json_round_trip(self):
        job = rep.Job(1994, 7, (2002, 12), (0, 1), "vol_ns", False, "/tmp/some/cache",
                      True, 0.9, "481x", "std", "value")
        assert rep.job_from_shard(rep.job_to_shard(job)) == job

    def test_the_jobs_are_dealt_round_robin_across_small_shards(self, tmp_path):
        jobs = [rep.Job(2020, month, (2020, 12), (0,), "vol_common", True)
                for month in range(1, 13)]
        shards = rep._write_shards(tmp_path, jobs, 4)
        assert [len(batch) for _, batch in shards] == [4, 4, 4]
        assert sorted(job.month for _, batch in shards for job in batch) == list(range(1, 13))
        # Dealt out, not sliced: shard 0 holds every third month, so it spans the
        # sample instead of owning one contiguous (and much heavier) stretch of it.
        assert [job.month for job in shards[0][1]] == [1, 4, 7, 10]
        assert [job.month for job in shards[1][1]] == [2, 5, 8, 11]
        for path, batch in shards:
            reread = [rep.job_from_shard(data) for data in json.loads(path.read_text())]
            assert reread == batch

    def test_small_shards_but_always_a_few_per_worker(self):
        assert rep._shard_size(474, 4) == rep.SHARD_COHORTS
        assert rep._shard_size(8, 4) == 1              # 8 cohorts, 4 workers: one each
        assert rep._shard_size(1, 4) == 1


class TestShardChild:
    """The child half: one status file per cohort, and a thread pin of its own."""

    def test_a_built_cohort_and_a_failed_one_get_their_status_files(self, tmp_path,
                                                                   monkeypatch):
        pinned = []
        monkeypatch.setattr(rep, "pin_arrow_threads", lambda: pinned.append(True))
        good, bad = _jobs((1, 2), tmp_path)

        def build(job):
            if job.month == 2:
                raise ValueError("no formation days")

        monkeypatch.setattr(rep, "build_cohort", build)
        shard = tmp_path / "shard-00.json"
        shard.write_text(json.dumps([rep.job_to_shard(good), rep.job_to_shard(bad)]))
        assert rep.build_shard(shard) == 1                    # one cohort failed
        assert pinned                                          # it pinned its own pools
        ok_status = json.loads((tmp_path / "status-2020-01.json").read_text())
        bad_status = json.loads((tmp_path / "status-2020-02.json").read_text())
        assert ok_status == {"ok": True, "cohort": "2020-01"}
        assert bad_status["ok"] is False
        assert "no formation days" in bad_status["error"]
        leftovers = [p.name for p in tmp_path.iterdir() if p.name.endswith(".tmp")]
        assert leftovers == []

    def test_a_status_file_is_replaced_in_one_rename(self, tmp_path):
        target = tmp_path / "status-2020-01.json"
        rep._write_json_atomically(target, {"ok": True})
        rep._write_json_atomically(target, {"ok": False, "error": "later"})
        assert json.loads(target.read_text()) == {"ok": False, "error": "later"}
        assert sorted(path.name for path in tmp_path.iterdir()) == ["status-2020-01.json"]

class TestShardSupervision:
    """The parent's half: launch, supervise, stop on the first failure."""

    @staticmethod
    def _stub(tmp_path, monkeypatch, body: str, extra_argv=()):
        """Run ``body`` as the shard child, with the shards kept in the test."""
        shard_dir = tmp_path / "shards"
        shard_dir.mkdir()
        monkeypatch.setattr(rep.tempfile, "mkdtemp", lambda prefix="": str(shard_dir))
        monkeypatch.setattr(rep, "earliest_known_sic",
                            lambda **kwargs: pd.Series(dtype="int64"))
        stub = tmp_path / "stub_child.py"
        stub.write_text(body)
        monkeypatch.setattr(
            rep, "_shard_command",
            lambda shard_path: [_venv_python(), str(stub), str(shard_path), *extra_argv])
        return shard_dir

    def test_a_killed_child_leaves_a_failed_cohort_and_a_log(self, tmp_path, monkeypatch):
        shard_dir = self._stub(tmp_path, monkeypatch, "import sys\nsys.exit(137)\n")
        with pytest.raises(RuntimeError, match="no status file"):
            rep.run_jobs(_jobs((1,), tmp_path), 1)
        assert [path.suffix for path in shard_dir.iterdir() if path.suffix == ".log"]
        assert not (shard_dir / "status-2020-01.json").exists()

    def test_a_status_file_that_is_not_ok_names_the_cohort(self, tmp_path, monkeypatch):
        body = """
import json, sys
from pathlib import Path
shard = Path(sys.argv[1])
for data in json.loads(shard.read_text()):
    status = shard.parent / f"status-{data['year']:04d}-{data['month']:02d}.json"
    status.write_text(json.dumps({"ok": False, "error": "ValueError: no formation days"}))
sys.exit(1)
"""
        self._stub(tmp_path, monkeypatch, body)
        with pytest.raises(RuntimeError, match="no formation days"):
            rep.run_jobs(_jobs((1,), tmp_path), 1)

    def test_the_first_failure_stops_new_shards(self, tmp_path, monkeypatch):
        body = """
import sys
from pathlib import Path
shard = Path(sys.argv[1])
with open(shard.parent / "launched.txt", "a") as handle:
    handle.write(shard.name + "\\n")
sys.exit(1)
"""
        shard_dir = self._stub(tmp_path, monkeypatch, body)
        # 8 cohorts over the default shard size for 2 workers is 8 shards, so
        # there is real work left to cancel when the first one fails.
        with pytest.raises(RuntimeError):
            rep.run_jobs(_jobs(tuple(range(1, 9)), tmp_path), 2)
        launched = (shard_dir / "launched.txt").read_text().split()
        assert 0 < len(launched) < 8, "every shard was launched despite the failure"

    def test_ctrl_c_terminates_the_children(self, tmp_path, monkeypatch):
        pid_file = tmp_path / "child.pid"
        body = """
import os, sys, time
from pathlib import Path
Path(sys.argv[2]).write_text(str(os.getpid()))
time.sleep(60)
"""
        self._stub(tmp_path, monkeypatch, body, extra_argv=(str(pid_file),))
        real_sleep = time.sleep
        raised = []

        def interrupt_once_the_child_is_up(seconds):
            if raised:                       # the parent's own cleanup may sleep too
                real_sleep(seconds)
                return
            raised.append(True)
            deadline = time.perf_counter() + 30
            while not pid_file.exists() and time.perf_counter() < deadline:
                real_sleep(0.01)
            raise KeyboardInterrupt

        monkeypatch.setattr(rep.time, "sleep", interrupt_once_the_child_is_up)
        with pytest.raises(KeyboardInterrupt):
            rep.run_jobs(_jobs((1,), tmp_path), 1)
        pid = int(pid_file.read_text())
        deadline = time.perf_counter() + 10
        alive = True
        while alive and time.perf_counter() < deadline:
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                alive = False
            else:
                real_sleep(0.05)
        assert not alive, "the shard child survived Ctrl-C"


class TestOneRealCohortInAShard:
    """The whole path end to end, in a real child interpreter."""

    def test_a_cohort_is_built_by_the_child_and_reported(self, tmp_path):
        panel_dir_value = sectors.default_panel_dir()
        if not panel_dir_value.exists():
            pytest.skip("needs the processed CRSP daily panel")
        cache = tmp_path / sectors.default_cache_path().name
        sectors._write_cache(cache, pd.DataFrame({"permno": [1], "siccd": [4911]}),
                             sectors._panel_signature(panel_dir_value))
        job = rep.Job(1963, 7, (1963, 12), (0,), "vol_common", True,
                      str(tmp_path / "cohorts"))
        rep.run_jobs([job], 1)
        built = tmp_path / "cohorts" / "1963-07"
        assert {"summary.json", "monthly.parquet", "pairs.parquet"} <= {
            path.name for path in built.iterdir()}


class TestShardWarningsAndLaunch:
    """The parent must not lose a child's warnings, nor its settings."""

    def test_the_child_inherits_the_parents_interpreter_flags(self):
        cmd = rep._shard_command(Path("/tmp/s.json"))
        flags = rep.subprocess._args_from_interpreter_flags()
        assert cmd[0] == sys.executable
        assert cmd[1:1 + len(flags)] == flags
        assert cmd[-2:] == ["--build-shard", "/tmp/s.json"]
        assert cmd[1 + len(flags)].endswith("03_replicate.py")

    def test_a_childs_warning_is_echoed_once(self, tmp_path, monkeypatch, capsys):
        body = (
            "import json, sys\n"
            "from pathlib import Path\n"
            "shard = Path(sys.argv[1])\n"
            "for data in json.loads(shard.read_text()):\n"
            "    name = 'status-%04d-%02d.json' % (data['year'], data['month'])\n"
            "    (shard.parent / name).write_text(json.dumps({'ok': True}))\n"
            "print('warning: X', file=sys.stderr)\n"
        )
        TestShardSupervision._stub(tmp_path, monkeypatch, body)
        rep.run_jobs(_jobs((1, 2), tmp_path), 2)
        err = capsys.readouterr().err
        assert err.count("warning: X") == 1
        assert "(2 shards)" in err

    def test_a_user_thread_cap_is_not_overridden(self, tmp_path, monkeypatch):
        class Proc:
            returncode = None
            poll = staticmethod(lambda: None)
            wait = staticmethod(lambda timeout=None: 0)
            terminate = staticmethod(lambda: None)
            kill = staticmethod(lambda: None)

        seen = {}

        def fake(cmd, **kwargs):
            seen.update(kwargs)
            return Proc()

        shard = tmp_path / "s.json"
        shard.write_text("[]")
        monkeypatch.setenv("OMP_NUM_THREADS", "2")
        monkeypatch.setattr(rep.subprocess, "Popen", fake)
        running = []
        rep._launch(shard, [], running)
        assert seen["env"]["OMP_NUM_THREADS"] == "2"
        assert seen["env"]["MKL_NUM_THREADS"] == "1"
        assert len(running) == 1
