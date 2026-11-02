"""The recall report must never turn a failing control or partial run into a claim."""
from types import SimpleNamespace

import pandas as pd
import pytest

from project.recall_report import PORTFOLIOS, RUNS, render_recall_report, validate_recall_sample


def fixture():
    table = pd.DataFrame({p: {"mean": -.01, "t_stat": -2.5, "committed_mean": -.005}
                          for p in PORTFOLIOS})
    tables = {r: table for r in (*RUNS, "off")}
    target = {p: {"mean": .01, "t_stat": 3., "committed_mean": .005} for p in PORTFOLIOS}
    paper = {"table9_panel_b": target, "table1_panel_b": target}
    summary = {"control": {"trades_identical": True, "month_missing": 0, "month_gap": 0.},
               "trades": {r: {"trades": 10, "n_recalled": 3,
                              "trades_short_without_volume": 1} for r in RUNS}}
    cfg = SimpleNamespace(cache_root="cache", out_root="out", raw_dir="volume", end=(2002, 12))
    return cfg, [(1963, 7)], tables, [summary], paper, 1., 1, "report"


def test_negative_results_and_partial_sample_have_honest_labels():
    text = render_recall_report(*fixture())
    assert "PARTIAL diagnostic only" in text
    assert "Positive means: 0/4" in text
    assert "Newey-West t > 2: 0/4" in text
    assert "Paper no recall (%)" in text and "Paper recall (%)" in text
    assert "retrospective" in text and "future trading-period volumes" in text
    assert "--cache-root cache" in text and "--stop 1963-07" in text
    assert "Replicated" not in text


@pytest.mark.parametrize("bad", [{"trades_identical": False}, {"month_missing": 1},
                                 {"month_gap": .001}])
def test_failed_control_cannot_generate_report(bad):
    args = fixture()
    args[3][0]["control"].update(bad)
    with pytest.raises(ValueError, match="failed no-recall control"):
        render_recall_report(*args)


def recall_months():
    return pd.DataFrame([
        {"cohort": "2002-11-30", "month_end": month, "run": run, "portfolio": p,
         "capital": capital, "ret": .01}
        for month in ("2002-11-30", "2002-12-31") for run in ("off", *RUNS)
        for p in PORTFOLIOS for capital in ("employed", "committed")])


def test_sample_validator_counts_censored_thresholds():
    result = validate_recall_sample(recall_months(), [(2002, 11)], (2002, 12))
    assert result == {"cohorts": 1, "rows": 80, "series": 40,
                      "sample_end_censored_thresholds": 1}


@pytest.mark.parametrize("defect", ["missing", "duplicate", "nonfinite", "wrong_month"])
def test_sample_validator_rejects_incomplete_or_invalid_results(defect):
    frame = recall_months()
    if defect == "missing":
        frame = frame.iloc[1:]
    elif defect == "duplicate":
        frame = pd.concat([frame, frame.iloc[:1]])
    elif defect == "nonfinite":
        frame.loc[0, "ret"] = float("nan")
    else:
        frame.loc[0, "month_end"] = "2003-01-31"
    with pytest.raises(ValueError, match="recall"):
        validate_recall_sample(frame, [(2002, 11)], (2002, 12))


def test_sample_end_threshold_limitation_is_reported():
    args = list(fixture())
    args[1] = [(2002, 11)]
    assert "truncates 1 cohort windows" in render_recall_report(*args)


def test_recall_report_preserves_explicit_source_sensitivity():
    args = fixture()
    args[0].source_universe = 'vol_common'
    args[0].source_exclude_constant = True
    text = render_recall_report(*args)
    assert 'Source universe: `vol_common`' in text
    assert '--source-universe vol_common --source-exclude-constant' in text
