"""Audit of the paper's short-term reversal factor (REVIEW_NOTES section 51).

The paper takes the market, SMB, HML and momentum factors from Ken French's library (their
printed standard deviations are his to the third or fourth decimal) but builds the reversal
factor itself; French's ST_Rev, the stand-in the check uses, was added to his library in 2006.
This script reproduces the three measurements the notes rest on and writes them to
``report/replication/REVERSAL_FACTOR_AUDIT.md``:

1. French's 2 x 3 recipe rebuilt from our CRSP monthly file reproduces his published ST_Rev and
   UMD, so the data and the recipe are not the gap.
2. Table 8 identifies the paper's own reversal factor. In-sample OLS satisfies
   R2 * var(y) = b' Sigma b exactly; with the four French factors' covariances known, the four
   portfolios' equations solve for the reversal factor's covariances with them. Only a factor
   standard deviation near the printed one gives a valid covariance matrix, so the printed value
   is not a misprint, and the implied correlations describe the factor.
3. Candidate series compared with that fingerprint, by data era.

Usage: ``python scripts/audit_reversal_factor.py [--out PATH]`` (needs the French files pulled
with ``git lfs pull`` and ``data/raw/wrds_api/monthly_stocks.parquet``).
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from project.factors import load_factors, load_losers_only
from project.paths import WRDS_API_DIR

_spec = importlib.util.spec_from_file_location("replicate", ROOT / "scripts" / "03_replicate.py")
rep = importlib.util.module_from_spec(_spec)
sys.modules["replicate"] = rep  # its dataclasses look their module up while it loads
_spec.loader.exec_module(rep)

KNOWN = ["market", "smb", "hml", "momentum"]
PORTFOLIOS = ["top5", "top20", "101-120", "all"]
WINDOWS = {"pre": ("1963-07", "1988-12"), "post": ("1989-01", "2002-12")}
ERAS = {"1963-07..1972-11": ("1963-07", "1972-11"), "1972-12..1982-12": ("1972-12", "1982-12"),
        "1983-01..1988-12": ("1983-01", "1988-12")}


def implied_covariances(known_cov: np.ndarray, loadings: np.ndarray, reversal_loading: np.ndarray,
                        r2: np.ndarray, sd_y: np.ndarray, reversal_sd: float) -> np.ndarray:
    """The reversal factor's covariances with the known factors that a set of regressions implies.

    For portfolio i, R2_i * sd_i**2 = b_i' S b_i + c_i**2 * s**2 + 2 c_i (b_i . k), where b_i are
    its loadings on the known factors (covariance ``known_cov``), c_i its reversal loading, s the
    reversal factor's standard deviation and k the unknown covariances. One equation per
    portfolio, linear in k; with as many portfolios as known factors the system is square.
    """
    A = 2 * reversal_loading[:, None] * loadings
    rhs = (r2 * sd_y**2 - np.einsum("ij,jk,ik->i", loadings, known_cov, loadings)
           - reversal_loading**2 * reversal_sd**2)
    return np.linalg.solve(A, rhs)


def is_valid_covariance(known_cov: np.ndarray, cross: np.ndarray, reversal_sd: float) -> bool:
    """True when the full matrix with the reversal factor appended is positive semidefinite."""
    k = len(cross)
    full = np.zeros((k + 1, k + 1))
    full[:k, :k], full[k, :k], full[:k, k], full[k, k] = known_cov, cross, cross, reversal_sd**2
    return bool(np.linalg.eigvalsh(full).min() >= -1e-12)


def paper_system(half: str) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Table 8's loadings, reversal loadings, R2 and portfolio SDs for one panel."""
    tab = rep.PAPER_TABLE8
    loadings = np.array([[tab[p][f"{half}_{f}"] for f in KNOWN] for p in PORTFOLIOS])
    rev = np.array([tab[p][f"{half}_reversal"] for p in PORTFOLIOS])
    r2 = np.array([tab[p][f"{half}_r2"] for p in PORTFOLIOS])
    sd = np.array([tab[p][f"{half}_std"] for p in PORTFOLIOS])
    return loadings, rev, r2, sd


def french_2x3(monthly: pd.DataFrame, signal: str) -> pd.Series:
    """French's six-portfolio factor from CRSP monthly rows.

    ``signal`` is "reversal" (prior month's return; low minus high) or "momentum" (months t-12
    to t-2; high minus low). Common shares of US firms on NYSE, Amex and Nasdaq; size is the prior
    month's capitalization split at the NYSE median, the signal at NYSE 30th and 70th
    percentiles; value weighted; half small plus half big.
    """
    m = monthly.copy()
    m["d"] = pd.to_datetime(m["mthcaldt"]) + pd.offsets.MonthEnd(0)
    m = m.drop_duplicates(["permno", "d"])
    common = ((m.securitytype == "EQTY") & (m.securitysubtype == "COM") & (m.sharetype == "NS")
              & (m.usincflg == "Y") & m.issuertype.isin(["ACOR", "CORP"])
              & m.primaryexch.isin(["N", "A", "Q"]))
    m["ok"], m["nyse"] = common.astype(float), (m.primaryexch == "N").astype(float)
    months = pd.date_range(m.d.min(), m.d.max(), freq="ME")
    wide = {c: m.pivot(index="d", columns="permno", values=c).reindex(months)
            for c in ("mthret", "mthcap", "mthprc", "ok", "nyse")}
    ret, cap = wide["mthret"], wide["mthcap"].where(wide["mthcap"] > 0)
    if signal == "reversal":
        sig, need = ret.shift(1), wide["mthprc"].shift(2).notna()
    else:
        logs = np.log1p(ret).shift(2).rolling(11, min_periods=1).sum()
        sig = np.expm1(logs).where(ret.shift(2).notna())
        need = wide["mthprc"].shift(13).notna()
    me, ok, nyse = cap.shift(1), wide["ok"].shift(1) == 1, wide["nyse"].shift(1) == 1
    out = {}
    for t in months[13:]:
        s, w, now = sig.loc[t], me.loc[t], ret.loc[t]
        use = ok.loc[t] & w.notna() & s.notna() & now.notna() & need.loc[t]
        if (use & nyse.loc[t]).sum() < 10:
            continue
        size = w[use & nyse.loc[t]].median()
        lo, hi = s[use & nyse.loc[t]].quantile(0.3), s[use & nyse.loc[t]].quantile(0.7)

        legs = {(sz, side): _vw(now, w, use & szm & sm)
                for sz, szm in (("S", w <= size), ("B", w > size))
                for side, sm in (("L", s <= lo), ("H", s >= hi))}
        low = (legs["S", "L"] + legs["B", "L"]) / 2
        high = (legs["S", "H"] + legs["B", "H"]) / 2
        out[t] = low - high if signal == "reversal" else high - low
    return pd.Series(out)


def _vw(ret: pd.Series, weight: pd.Series, mask: pd.Series) -> float:
    return float((ret[mask] * weight[mask]).sum() / weight[mask].sum())


def _sd(s: pd.Series, window: tuple[str, str]) -> float:
    return float(s.loc[window[0]:window[1]].std())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--out", type=Path,
                        default=ROOT / "report" / "replication" / "REVERSAL_FACTOR_AUDIT.md")
    args = parser.parse_args()
    factors = load_factors()
    losers = load_losers_only()
    lines = ["# Reversal factor audit", "",
             ("Generated by `scripts/audit_reversal_factor.py`; the reasoning is in REVIEW_NOTES "
              "section 51. Monthly standard deviations, July 1963 - December 1988 (pre) and "
              "January 1989 - December 2002 (post), as in Table 8."), ""]

    # 1. French's recipe on our data
    monthly = pd.read_parquet(WRDS_API_DIR / "monthly_stocks.parquet", columns=[
        "permno", "mthcaldt", "primaryexch", "securitytype", "securitysubtype", "sharetype",
        "usincflg", "issuertype", "mthret", "mthcap", "mthprc"])
    dates = pd.to_datetime(monthly["mthcaldt"])
    monthly = monthly[(dates >= "1962-05-01") & (dates <= "2002-12-31")]
    lines += ["## 1. French's 2 x 3 recipe rebuilt from our CRSP file", "",
              ("| factor | SD pre, rebuilt / French / paper | SD post, rebuilt / French / paper "
               "| correlation with French, pre / post |"), "|---|---|---|---|"]
    for name, col in (("reversal (ST_Rev)", "reversal"), ("momentum (UMD)", "momentum")):
        built = french_2x3(monthly, col)
        pub = factors[col].reindex(built.index)
        cells = [" / ".join(f"{v:.4f}" for v in (_sd(built, WINDOWS[h]), _sd(pub, WINDOWS[h]),
                                                  rep.PAPER_TABLE8_FACTOR_SD[h][col])) for h in WINDOWS]
        corr = " / ".join(f"{built.loc[a:b].corr(pub.loc[a:b]):.4f}" for a, b in WINDOWS.values())
        lines.append(f"| {name} | {cells[0]} | {cells[1]} | {corr} |")

    # 2. What Table 8 says about the paper's own factor
    lines += ["", "## 2. The reversal factor Table 8 implies", "",
              ("Correlations with the four French factors implied by each panel's regressions at "
               "an assumed reversal SD, and whether the implied covariance matrix is valid."), "",
              "| panel | assumed SD | implied correlation: market / SMB / HML / momentum | valid |",
              "|---|---|---|---|"]
    for half, (a, b) in WINDOWS.items():
        known = factors.loc[a:b, KNOWN]
        cov, sd4 = known.cov().to_numpy(), known.std().to_numpy()
        loadings, rev_b, r2, sd_y = paper_system(half)
        for s in (0.0259, 0.0327, 0.0400, 0.0445, 0.0550, 0.0723, 0.0900):
            cross = implied_covariances(cov, loadings, rev_b, r2, sd_y, s)
            corr = " / ".join(f"{x:+.2f}" for x in cross / (s * sd4))
            ok = "yes" if is_valid_covariance(cov, cross, s) else "no"
            mark = " (printed)" if abs(s - rep.PAPER_TABLE8_FACTOR_SD[half]["reversal"]) < 5e-4 else ""
            lines.append(f"| {half} | {s:.4f}{mark} | {corr} | {ok} |")

    # 3. Candidates against that fingerprint, by era
    lines += ["", "## 3. Candidate series: SD and correlation with the market", "",
              "| series | " + " | ".join(ERAS) + " | pre-1989 | post-1988 |",
              "|---|" + "---|" * (len(ERAS) + 2)]
    for name, s in (("French ST_Rev (long-short, the check's factor)", factors["reversal"]),
                    ("EW losers minus T-bill, no short leg (French deciles 1-3)", losers)):
        cells = []
        for a, b in [*ERAS.values(), *WINDOWS.values()]:
            part = s.loc[a:b]
            cells.append(f"{part.std():.4f}, {part.corr(factors['market'].loc[a:b]):+.2f}")
        lines.append(f"| {name} | " + " | ".join(cells) + " |")
    lines += [("| paper (Table 8; correlation implied at the printed SD) | | | | 0.0723, +0.81 "
               "| 0.0445, +0.79 |"), ""]
    args.out.write_text("\n".join(lines))
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
