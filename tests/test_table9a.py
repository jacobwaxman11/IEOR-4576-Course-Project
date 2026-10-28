"""Tests for the Table 9 Panel A report script (scripts/claims/table9a.py)."""

import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "pairs-trading-performance-of-a-relative-value-arbitrage-rule_final.pdf"
_spec = importlib.util.spec_from_file_location("table9a", ROOT / "scripts" / "claims" / "table9a.py")
t9a = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(t9a)


@pytest.mark.skipif(shutil.which("pdftotext") is None or not PDF.exists(),
                    reason="needs pdftotext and the paper PDF")
def test_paper_targets_are_the_pdf_text():
    text = subprocess.run(["pdftotext", "-layout", str(PDF), "-"],
                          capture_output=True, text=True, check=True).stdout
    committed = json.loads((ROOT / "scripts" / "claims" / "table9a_paper.json").read_text())
    assert t9a.paper_json(text) == committed
    # spot values read off the printed page
    assert committed["panel_A"]["top20"]["mean"] == 0.00914
    assert committed["panel_A"]["top20"]["t_stat"] == 9.48
    assert committed["table1_panel_b"]["top20"]["mean"] == 0.00895


def _frame(values: dict) -> pd.DataFrame:
    return pd.DataFrame({key: values for key, _ in t9a.COLUMNS})


def test_panel_a_skewness_and_kurtosis_are_compared_swapped():
    printed = {metric: 1.0 for metric, _ in t9a.ROWS}
    printed.update(skew=7.0, kurtosis=0.5)  # as Table 9A prints them
    base = {metric: 1.0 for metric, _ in t9a.ROWS}
    paper = {"panel_A": {key: printed for key, _ in t9a.COLUMNS},
             "table1_panel_b": {key: base for key, _ in t9a.COLUMNS}}
    ours = {metric: 1.0 for metric, _ in t9a.ROWS}
    ours.update(skew=0.5, kurtosis=7.0)
    rows = t9a.comparison_rows(_frame(ours), _frame(ours), paper)
    by = {(r["portfolio"], r["metric"]): r for r in rows}
    assert by[("top20", "skew")]["paper"] == 0.5
    assert by[("top20", "skew")]["paper_as_printed"] == 7.0
    assert by[("top20", "skew")]["mark"] == "✓"
    assert by[("top20", "kurtosis")]["paper"] == 7.0
    assert by[("top20", "mean")]["our_change"] == 0.0


def test_marks_follow_the_ten_and_twenty_five_percent_bands():
    assert t9a.mark(1.09, 1.0) == "✓"
    assert t9a.mark(1.2, 1.0) == "~"
    assert t9a.mark(1.3, 1.0) == "✗"
    assert t9a.mark(float("nan"), 1.0) == ""
