"""Tests for the 1999-draft scorer on a small synthetic cohort cache."""

import json

import numpy as np
import pandas as pd
import pytest

from project import edition1999 as ed

COHORTS = ["1990-07", "1990-08", "1990-09"]


def _write_cohort(root, name, ret):
    d = root / name
    d.mkdir(parents=True)
    months = pd.date_range(name + "-01", periods=6, freq="ME")
    rows = []
    for wait in (0, 1):
        for p in ed.PORTFOLIOS:
            for cap in ("committed", "employed_literal"):
                for m in months:
                    rows.append(("t1", "", wait, p, cap, m, ret))
    pd.DataFrame(rows, columns=["table", "sector", "wait", "portfolio", "capital",
                                "month_end", "ret"]).to_parquet(d / "monthly.parquet")
    pd.DataFrame({"rank": [1, 2, 3, 101, 102], "permno_1": 1, "permno_2": 2,
                  "distance": 0.1, "sigma": [0.02, 0.02, 0.03, 0.05, 0.06]}
                 ).to_parquet(d / "pairs.parquet")
    pd.DataFrame({"rank": [1, 1, 2, 101], "open_day": [0, 40, 3, 5],
                  "close_day": [21, 63, 42, 26]}).to_parquet(d / "w0_trades.parquet")
    opened = pd.DataFrame({"opened": [True, True, False, True, False]},
                          index=pd.Index([1, 2, 3, 101, 102], name="rank"))
    opened.to_parquet(d / "w0_opened.parquet")
    comp = {p: {k: v[i] for k, v in ed.PAPER_T2B.items()} for i, p in enumerate(ed.PORTFOLIOS)}
    (d / "summary.json").write_text(json.dumps({"composition": comp}))


@pytest.fixture
def cache(tmp_path):
    for c in COHORTS:
        _write_cohort(tmp_path, c, 0.01)
    return tmp_path


def test_mark_thresholds():
    assert ed.mark(1.09, 1.0) == "✓"
    assert ed.mark(1.11, 1.0) == "~"
    assert ed.mark(0.75, 1.0) == "~"
    assert ed.mark(0.74, 1.0) == "✗"


def test_moments_match_known_values():
    skew, kurt = ed._moments(pd.Series([1.0, 2.0, 3.0, 4.0, 10.0]))
    assert skew == pytest.approx(1.13842, abs=1e-4)
    assert kurt == pytest.approx(-0.212, abs=1e-6)


def test_cohort_names_cover_the_draft_window():
    names = ed.cohort_names()
    assert (names[0], names[-1], len(names)) == ("1963-07", "1997-06", 408)


def test_table1_six_month_return_compounds_monthly_returns(cache):
    cells = ed.table1(cache, COHORTS)
    ours, paper, _ = cells[("Table I", "wait 0", "top5", "mean")]
    assert ours == pytest.approx(1.01**6 - 1)
    assert paper == 0.0598
    assert cells[("Table I", "wait 1", "all", "share negative")][0] == 0.0
    assert len([k for k in cells if k[0] == "Table I"]) == 72


def test_table2a_counts_pairs_trips_and_months_open(cache):
    cells = ed.table2a(cache, COHORTS)
    trigger = cells[("Table II A", "wait 0", "top5", "trigger")][0]
    assert trigger == pytest.approx(2 * (0.02 + 0.02 + 0.03) / 3)
    assert cells[("Table II A", "wait 0", "top5", "pairs traded")][0] == 2
    assert cells[("Table II A", "wait 0", "top5", "round trips")][0] == pytest.approx(1.5)
    assert cells[("Table II A", "wait 0", "top5", "months open")][0] == pytest.approx(
        (44 + 39) / 2 / 21)
    assert len([k for k in cells if k[0] == "Table II A"]) == 24


def test_table2b_reproduces_paper_when_cache_holds_paper_values(cache):
    cells = ed.table2b(cache, COHORTS)
    assert len(cells) == 40
    assert {v[2] for v in cells.values()} == {"✓"}


def test_summarize_and_report(cache):
    cells = ed.score_cohort_dir(cache, COHORTS)
    s = ed.summarize(cells)
    assert s["total"]["cells"] == 136
    assert s["total"]["score"] == s["total"]["full"] + 0.5 * s["total"]["half"]
    assert sum(s[t]["cells"] for t in ("Table I", "Table II A", "Table II B")) == 136
    text = ed.format_report(cells, len(COHORTS))
    assert "1999 NBER draft" in text and "| Table II B | 40 |" in text


def test_all_nan_composition_stat_fails_loudly(cache):
    for c in COHORTS:
        f = cache / c / "summary.json"
        d = json.loads(f.read_text())
        d["composition"]["top5"]["avg_size_decile"] = float("nan")
        f.write_text(json.dumps(d))
    with pytest.raises(ValueError, match="avg_size_decile in top5"):
        ed.table2b(cache, COHORTS)


def test_mark_agrees_with_the_rfs_check():
    import importlib.util
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("replicate", root / "scripts" / "03_replicate.py")
    rep = importlib.util.module_from_spec(spec)
    sys.modules["replicate"] = rep
    spec.loader.exec_module(rep)
    for ours in np.linspace(0.5, 1.5, 101):
        assert ed.mark(ours, 1.0) == rep._mark(ours, 1.0), ours
