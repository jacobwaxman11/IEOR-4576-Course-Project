"""Pin the two defects R12 fixed in `scripts/paper_consistency.py` (REVIEW_NOTES 102).

`REVIEW_NOTES` 99's audit (`claims/CLASS_A_AUDIT.md` section 4) found two reasons the
script's Panel A figure disagreed with an independent re-derivation, and the script now
shares both inputs with the scored checks:

1. **Vintage.** It read French's factors at the module default (``current``); every scored
   check runs the 2005 archives, the files the paper had. It now reads 2005 and prints it.
2. **Precision.** It read Table 8's loadings from `scripts/paper_cells.json` at three
   significant figures (``-0.434`` for the printed ``-0.43395``), which put the Panel A
   joint R^2 at 0.9502 against the printed precision's 0.9434. It now reads
   `scripts/03_replicate.py`'s five-decimal ``PAPER_TABLE8``.

The tests below hold the two fixes together: the script's own joint R^2 and
`scripts/experiments/class_a_audit.py`'s must agree to 1e-3, and the script must report the
2005 vintage. They are data-light: they skip, with a reason, when the factor archives are
still Git LFS pointers.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src") if (ROOT / "src" / "project").exists() else str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "experiments"))

import paper_consistency as pc

SCRIPT = ROOT / "scripts" / "paper_consistency.py"


@pytest.fixture(scope="module")
def factors():
    """The scored vintage's factor panel, or a skip when the files are LFS pointers."""
    try:
        return pc.load_check_factors()
    except FileNotFoundError as exc:  # LFS pointer or missing file
        pytest.skip(f"public factor files unavailable: {exc}")


def _script_joint_r2(factors) -> float:
    """`paper_consistency.py`'s Panel A joint R^2, through its own functions and inputs."""
    table8 = pc.typed_table8()
    pre = (factors.index >= pc.START) & (factors.index <= pc.SPLIT)
    betas = [[pc.cell(table8, f"pre_{c}", i) for c in pc.FF] for i in range(1, 5)]
    joint = pc.joint_reversal_r2(
        betas,
        [pc.cell(table8, "pre_reversal", i) for i in range(1, 5)],
        [pc.cell(table8, "pre_r2", i) for i in range(1, 5)],
        [pc.cell(table8, "pre_std", i) / 100.0 for i in range(1, 5)],
        pc.PAPER_FACTOR_SD["pre"], pc.four_factor_corr(factors, pre))
    return joint["r2_of_reversal_on_four"]


def _audit_joint_r2() -> float:
    """`class_a_audit.py`'s Panel A joint R^2, through that script's own functions."""
    import class_a_audit as audit

    rep = audit._replicate_module()
    coef, _tstats = audit.paper_regressions(rep)["pre"]
    sigma, _corr = audit.sigma_from_factors(audit.PRE_WINDOW, rescaled=True, rep=rep,
                                           panel="pre")
    portfolios = list(audit.PORTFOLIOS)
    columns = {p: audit.column_identities(coef.loc[p], sigma.to_numpy(),
                                         rep.PAPER_TABLE8[p]["pre_std"],
                                         float(coef.loc[p, "r2"]), audit.PRE_SD)
               for p in portfolios}
    joint = audit.joint_test(columns, coef.loc[portfolios], sigma.to_numpy(), audit.PRE_SD)
    return float(joint["implied_r2_reversal_on_four"])


def test_panel_a_joint_r2_agrees_with_the_class_a_audit(factors):
    """The two scripts must read Table 8 at the same precision and land on 0.9434.

    At `paper_cells.json`'s three significant figures the same kernel returns 0.9502, which
    is the 0.007 this test exists to keep out of the page.
    """
    audit_r2 = _audit_joint_r2()
    assert audit_r2 == pytest.approx(0.9434, abs=1e-3), audit_r2
    script_r2 = _script_joint_r2(factors)
    assert script_r2 == pytest.approx(audit_r2, abs=1e-3), (script_r2, audit_r2)
    # and the five-decimal transcription is what makes the difference, not the vintage
    three_figure = pc.load_paper()["Table 8 (subperiod analysis)"]
    pre = (factors.index >= pc.START) & (factors.index <= pc.SPLIT)
    legacy = pc.joint_reversal_r2(
        [[pc.cell(three_figure, f"pre_{c}", i) for c in pc.FF] for i in range(1, 5)],
        [pc.cell(three_figure, "pre_reversal", i) for i in range(1, 5)],
        [pc.cell(three_figure, "pre_r2", i) for i in range(1, 5)],
        [pc.cell(three_figure, "pre_std", i) / 100.0 for i in range(1, 5)],
        pc.PAPER_FACTOR_SD["pre"], pc.four_factor_corr(factors, pre))
    assert abs(legacy["r2_of_reversal_on_four"] - audit_r2) > 5e-3


def test_script_reports_the_2005_vintage(tmp_path):
    """The scored checks run French's 2005 archives, so this script must say it does."""
    out_json = tmp_path / "findings.json"
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--json", str(out_json)],
        capture_output=True, text=True, cwd=str(ROOT), check=False,
        env={"PATH": "/usr/bin:/bin", "HOME": str(Path.home())},
    )
    if proc.returncode != 0 and "public factor files" in proc.stderr:
        pytest.skip(f"public factor files unavailable: {proc.stderr[-500:]}")
    assert proc.returncode == 0, proc.stderr[-2000:]
    assert "French's 2005 archives" in proc.stdout, proc.stdout[:2000]
    assert json.loads(out_json.read_text())["factor_vintage"] == "2005"