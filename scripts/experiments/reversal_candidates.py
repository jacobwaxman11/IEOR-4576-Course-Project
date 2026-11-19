"""Table 4 + Table 8's 84 regression cells under candidate reversal factors.

REVIEW_NOTES section 53. The paper (p. 813) says the factor is "a short-term reversal
factor measured as the excess return of stocks in the top three deciles of prior-month
return minus the return on stocks in the bottom three deciles" and footnote 7 says the
construction is "similar to Carhart's (1997) momentum factor". This script keeps the four
French factors and swaps only the reversal column, scoring the same 84 cells the
replication check scores (Table 4's seven five-factor rows and Table 8's fourteen
pre/post rows, four portfolios each), so the comparison is like for like.

Candidates:
  st_rev        French's F-F_ST_Reversal_Factor (the shipped primary)
  losers_only   EW prior-month deciles 1-3 minus the bill (the recorded alternative)
  paper_vw      VW deciles 8-10 minus deciles 1-3, the paper's words, value weighted
  paper_ew      EW deciles 8-10 minus deciles 1-3
  paper_vw_rf   VW (deciles 8-10 - bill) - deciles 1-3, reading "excess return of
                stocks in the top three deciles ... minus the return on ... bottom"
                literally
  paper_vw_neg  VW deciles 1-3 minus deciles 8-10 (the words with the sign reversed)
  paper_ew_neg  EW deciles 1-3 minus deciles 8-10
  recipe        the paper's recipe built from CRSP: Carhart's (1997) PR1YR construction
                (equal-weight top 30% minus bottom 30% of NYSE/Amex/Nasdaq stocks,
                breakpoints over all stocks, re-formed monthly) at a one-month horizon,
                in the sign the paper's next sentence requires (losers minus winners)
  ff2x3_vw      French's 2 x 3 build as scripts/audit_reversal_factor.py has it, half small plus
                half big, low minus high prior-month return, value weighted
  ff2x3_ew      the same build, equal weighted inside the six portfolios

Reads ``results/replication/tables/monthly_returns.parquet`` (written by
``python scripts/03_replicate.py --aggregate-only``), French's files and, for the two
CRSP builds, ``data/raw/wrds_api/monthly_stocks.parquet``.

    python scripts/experiments/reversal_candidates.py
"""

import importlib.util
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from project.factors import (
    FRENCH_DIR,
    LOSERS_FILE,
    _french_text,
    _monthly_block,
    factor_regression,
    load_factors,
    load_losers_only,
)
from project.paths import WRDS_API_DIR


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


rep = _load("replicate", ROOT / "scripts" / "03_replicate.py")
audit = _load("audit_reversal_factor", ROOT / "scripts" / "audit_reversal_factor.py")

TABLES = ROOT / "results" / "replication" / "tables"
PORTFOLIOS = ["top5", "top20", "101-120", "all"]
ROWS = ["intercept", "market", "smb", "hml", "momentum", "reversal", "r2"]


def monthly() -> dict[str, pd.Series]:
    frame = pd.read_parquet(TABLES / "monthly_returns.parquet")
    frame = frame[(frame["wait"] == 1) & (frame["capital"] == "employed")]
    return {
        name: group.set_index("month_end")["monthly_return"].sort_index().dropna()
        for name, group in frame.groupby("portfolio")
    }


def decile_blocks() -> tuple[pd.DataFrame, pd.DataFrame]:
    """French's ten prior-month-return deciles, value weighted and equal weighted."""
    text = _french_text(FRENCH_DIR / LOSERS_FILE)
    vw = _monthly_block(text, "Value Weighted Returns -- Monthly")
    ew = _monthly_block(text, "Equal Weighted Returns -- Monthly")
    for frame in (vw, ew):
        frame.columns = [c.strip() for c in frame.columns]
    return vw, ew


def crsp_monthly() -> pd.DataFrame:
    crsp = pd.read_parquet(WRDS_API_DIR / "monthly_stocks.parquet", columns=[
        "permno", "mthcaldt", "primaryexch", "securitytype", "securitysubtype", "sharetype",
        "usincflg", "issuertype", "mthret", "mthcap", "mthprc"])
    dates = pd.to_datetime(crsp["mthcaldt"])
    return crsp[(dates >= "1962-05-01") & (dates <= "2002-12-31")]


def recipe(crsp: pd.DataFrame) -> pd.Series:
    """Equal-weight bottom 30% minus top 30% of prior-month return, all-stock breakpoints.

    The universe is the audit's (common shares of US firms on NYSE, Amex and Nasdaq, with a
    price two months back); only the sort and the weighting follow Carhart instead of French.
    """
    m = crsp.copy()
    m["d"] = pd.to_datetime(m["mthcaldt"]) + pd.offsets.MonthEnd(0)
    m = m.drop_duplicates(["permno", "d"])
    common = ((m.securitytype == "EQTY") & (m.securitysubtype == "COM") & (m.sharetype == "NS")
              & (m.usincflg == "Y") & m.issuertype.isin(["ACOR", "CORP"])
              & m.primaryexch.isin(["N", "A", "Q"]))
    m["ok"] = common.astype(float)
    months = pd.date_range(m.d.min(), m.d.max(), freq="ME")
    wide = {c: m.pivot(index="d", columns="permno", values=c).reindex(months)
            for c in ("mthret", "mthprc", "ok")}
    ret = wide["mthret"]
    sig, need, ok = ret.shift(1), wide["mthprc"].shift(2).notna(), wide["ok"].shift(1) == 1
    out = {}
    for t in months[13:]:
        s, now = sig.loc[t], ret.loc[t]
        use = ok.loc[t] & s.notna() & now.notna() & need.loc[t]
        if use.sum() < 10:
            continue
        lo, hi = s[use].quantile(0.3), s[use].quantile(0.7)
        out[t] = float(now[use & (s <= lo)].mean() - now[use & (s >= hi)].mean())
    return pd.Series(out)


def two_by_three(crsp: pd.DataFrame, weighted: bool) -> pd.Series:
    """The audit's 2 x 3 reversal factor, value weighted (French's recipe) or equal weighted."""
    if weighted:
        return audit.french_2x3(crsp, "reversal")
    value_weighted = audit._vw
    audit._vw = lambda ret, weight, mask: float(ret[mask].mean())
    try:
        return audit.french_2x3(crsp, "reversal")
    finally:
        audit._vw = value_weighted


def candidates() -> dict[str, pd.Series]:
    factors = load_factors()
    vw, ew = decile_blocks()
    top_vw, bot_vw = vw.iloc[:, 7:10].mean(axis=1), vw.iloc[:, 0:3].mean(axis=1)
    top_ew, bot_ew = ew.iloc[:, 7:10].mean(axis=1), ew.iloc[:, 0:3].mean(axis=1)
    rf = factors["rf"]
    crsp = crsp_monthly()
    return {
        "st_rev": factors["reversal"],
        "losers_only": load_losers_only(),
        "paper_vw": (top_vw - bot_vw).dropna(),
        "paper_ew": (top_ew - bot_ew).dropna(),
        "paper_vw_rf": (top_vw - rf - bot_vw).dropna(),
        "paper_vw_neg": (bot_vw - top_vw).dropna(),
        "paper_ew_neg": (bot_ew - top_ew).dropna(),
        "recipe": recipe(crsp),
        "ff2x3_vw": two_by_three(crsp, weighted=True),
        "ff2x3_ew": two_by_three(crsp, weighted=False),
    }


def score(series: dict[str, pd.Series], factors: pd.DataFrame,
          candidate: pd.Series) -> tuple[dict[str, tuple[str, float]], float]:
    """Marks for the 84 cells with ``candidate`` in the reversal column."""
    frame = factors.drop(columns=["reversal", "rf"]).join(candidate.rename("reversal"), how="inner")
    cells: dict[str, tuple[str, float]] = {}
    split = pd.Timestamp(1988, 12, 1) + pd.offsets.MonthEnd(0)
    for pname in PORTFOLIOS:
        s = series[pname]
        paper4 = rep.PAPER_TABLE4[pname]
        coef = factor_regression(s, frame)
        for row in ROWS:
            key = f"T4/{pname}/{row}"
            marks = rep._mark(float(coef[row]), paper4[row])
            cells[key] = (marks, float(coef[row]) / paper4[row] - 1)
        pre, post = s[s.index <= split], s[s.index > split]
        for half, part in (("pre", pre), ("post", post)):
            coef = factor_regression(part, frame)
            for row in ROWS:
                key = f"T8/{pname}/{half}_{row}"
                marks = rep._mark(float(coef[row]), rep.PAPER_TABLE8[pname][f"{half}_{row}"])
                cells[key] = (marks, float(coef[row]) / rep.PAPER_TABLE8[pname][f"{half}_{row}"] - 1)
    points = sum(1.0 if m == "✓" else 0.5 if m == "~" else 0.0 for m, _ in cells.values())
    return cells, points


def main() -> None:
    series = monthly()
    factors = load_factors()
    cands = candidates()
    print("candidate SDs: pre-1989 / post-1988 / corr with market (pre) / corr with ST_Rev")
    split = pd.Timestamp(1988, 12, 1) + pd.offsets.MonthEnd(0)
    window = series["top5"].index
    for name, s in cands.items():
        s = s.reindex(window).dropna()
        pre = s[s.index <= split]
        print(f"  {name:13s} {pre.std(ddof=1):.4f} "
              f"{s[s.index > split].std(ddof=1):.4f} "
              f"{pre.corr(factors['market'].reindex(pre.index)):+.2f} "
              f"{s.corr(factors['reversal'].reindex(s.index)):+.4f}")

    results = {}
    for name, s in cands.items():
        cells, points = score(series, factors, s)
        results[name] = (cells, points)
        tally = {m: sum(1 for v in cells.values() if v[0] == m) for m in ("✓", "~", "✗")}
        print(f"\n{name:13s} 84 cells: ✓ {tally['✓']}  ~ {tally['~']}  ✗ {tally['✗']}"
              f"  points {points:.1f}")

    base = results["st_rev"][0]
    print("\nper-cell wins against ST_Rev (closer to the paper, |relative gap|):")
    for name, (cells, _) in results.items():
        if name == "st_rev":
            continue
        better = sum(1 for k in base if abs(cells[k][1]) < abs(base[k][1]))
        worse = sum(1 for k in base if abs(cells[k][1]) > abs(base[k][1]))
        print(f"  {name:13s} closer in {better:2d} / 84 cells, further in {worse:2d}")
    print("\nreversal-row loadings (ours/paper) by candidate:")
    for name, (cells, _) in results.items():
        row = " ".join(f"{cells[f'T4/{p}/reversal'][1] + 1:.3f}" for p in PORTFOLIOS)
        pre = " ".join(f"{cells[f'T8/{p}/pre_reversal'][1] + 1:.3f}" for p in PORTFOLIOS)
        print(f"  {name:13s} T4 reversal ratio {row}   pre-1989 reversal ratio {pre}")


if __name__ == "__main__":
    main()