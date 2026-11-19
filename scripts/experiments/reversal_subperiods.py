"""Contract Pb: candidate reversal factors read in both Table 8 windows (REVIEW_NOTES 73).

Grid and metric pre-registered in report/replication/claims/REVERSAL_SUBPERIODS.md.
"""
import argparse
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from project.factors import FRENCH_DIR, LOSERS_FILE, _french_text, _monthly_block, load_factors
from project.paths import WRDS_API_DIR

KNOWN = ["market", "smb", "hml", "momentum"]
WINDOWS = {"pre": ("1963-07", "1988-12"), "post": ("1989-01", "2002-12")}
DECILE_SETS = {"d3": ((0, 1, 2), (7, 8, 9)), "d2": ((0, 1), (8, 9)), "d1": ((0,), (9,))}
LEGS = ("losers_only", "losers_minus_winners", "winners_minus_losers", "winners_only")
def load_audit():
    """The audit module: Table 8's system and the implied-covariance arithmetic."""
    path = ROOT / "scripts" / "audit_reversal_factor.py"
    spec = importlib.util.spec_from_file_location("audit_reversal_factor", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def french_deciles(french_dir: Path) -> dict[str, pd.DataFrame]:
    """French's ten prior-month deciles, value and equal weighted, columns 1..10."""
    text = _french_text(Path(french_dir) / LOSERS_FILE)
    out = {}
    for weighting, title in (("vw", "Value Weighted Returns -- Monthly"),
                             ("ew", "Equal Weighted Returns -- Monthly")):
        frame = _monthly_block(text, title)
        frame.columns = [c.strip() for c in frame.columns]
        out[weighting] = frame.iloc[:, :10].astype(float)
    return out


def crsp_deciles(exchanges: tuple[str, ...]) -> dict[str, pd.DataFrame]:
    """Ten prior-month deciles built from CRSP, equal and value weighted, columns 1..10.

    Common shares of US firms (the audit's filter) on ``exchanges``; the signal is the prior
    month's return, the breakpoints are that universe's own deciles of it, and the holdings are
    formed at the end of month t-1 and held through t. Value weights are month t-1 caps.
    """
    cols = ["permno", "mthcaldt", "primaryexch", "securitytype", "securitysubtype", "sharetype",
            "usincflg", "issuertype", "mthret", "mthcap", "mthprc"]
    m = pd.read_parquet(WRDS_API_DIR / "monthly_stocks.parquet", columns=cols)
    dates = pd.to_datetime(m["mthcaldt"])
    m = m[(dates >= "1962-05-01") & (dates <= "2002-12-31")]
    m = m.assign(d=pd.to_datetime(m["mthcaldt"]) + pd.offsets.MonthEnd(0))
    m = m.drop_duplicates(["permno", "d"])
    common = ((m.securitytype == "EQTY") & (m.securitysubtype == "COM") & (m.sharetype == "NS")
              & (m.usincflg == "Y") & m.issuertype.isin(["ACOR", "CORP"]))
    m = m[common & m.primaryexch.isin(list(exchanges))]
    months = pd.date_range(m.d.min(), m.d.max(), freq="ME")
    wide = {c: m.pivot(index="d", columns="permno", values=c).reindex(months)
            for c in ("mthret", "mthcap", "mthprc")}
    ret, cap = wide["mthret"], wide["mthcap"].where(wide["mthcap"] > 0)
    sig, need, me = ret.shift(1), wide["mthprc"].shift(2).notna(), cap.shift(1)
    rows_ew, rows_vw = {}, {}
    for t in months[13:]:
        s = sig.loc[t].to_numpy(dtype=float)
        r = ret.loc[t].to_numpy(dtype=float)
        w = me.loc[t].to_numpy(dtype=float)
        use = np.isfinite(s) & np.isfinite(r) & need.loc[t].to_numpy()
        if int(use.sum()) < 100:
            continue
        s, r, w = s[use], r[use], w[use]
        edges = np.quantile(s, np.linspace(0.1, 0.9, 9))
        grp = np.searchsorted(edges, s, side="right")
        ew = np.full(10, np.nan)
        vw = np.full(10, np.nan)
        for k in range(10):
            in_k = grp == k
            if not in_k.any():
                continue
            ew[k] = float(r[in_k].mean())
            wm = in_k & np.isfinite(w) & (w > 0)
            vw[k] = (float((r[wm] * w[wm]).sum() / w[wm].sum()) if wm.any()
                     else float(r[in_k].mean()))
        rows_ew[t], rows_vw[t] = ew, vw
    labels = list(range(1, 11))
    return {"ew": pd.DataFrame.from_dict(rows_ew, orient="index", columns=labels),
            "vw": pd.DataFrame.from_dict(rows_vw, orient="index", columns=labels)}


def candidates(blocks: dict[str, pd.DataFrame], rf: pd.Series,
               prefix: str) -> dict[str, pd.Series]:
    """The four legs of the pre-registered grid for one sort source, both weightings, three sets."""
    out = {}
    for weighting, frame in blocks.items():
        for set_name, (bottom_ix, top_ix) in DECILE_SETS.items():
            bottom = frame.iloc[:, list(bottom_ix)].mean(axis=1)
            top = frame.iloc[:, list(top_ix)].mean(axis=1)
            legs = {
                "losers_only": bottom - rf,
                "winners_only": top - rf,
                "losers_minus_winners": bottom - top,
                "winners_minus_losers": top - bottom,
            }
            for leg in LEGS:
                key = f"{prefix}_{weighting}_{set_name}_{leg}"
                out[key] = legs[leg].replace([np.inf, -np.inf], np.nan).dropna()
    return out


def targets(audit, factors: pd.DataFrame, label: str) -> dict:
    """Table 8's implied SD and correlations, at the printed SD, for one factor vintage."""
    out = {}
    for half, (a, b) in WINDOWS.items():
        known = factors.loc[a:b, KNOWN]
        cov, sd4 = known.cov().to_numpy(), known.std().to_numpy()
        loadings, rev_b, r2, sd_y = audit.paper_system(half)
        sd = float(audit.rep.PAPER_TABLE8_FACTOR_SD[half]["reversal"])
        cross = audit.implied_covariances(cov, loadings, rev_b, r2, sd_y, sd)
        out[half] = {
            "sd": sd,
            "corr": {f: float(c) for f, c in zip(KNOWN, cross / (sd * sd4))},
            "valid": bool(audit.is_valid_covariance(cov, cross, sd)),
            "vintage": label,
        }
    return out


def distance(series: pd.Series, factors: pd.DataFrame, tgt: dict) -> dict | None:
    """SD, the four correlations and the pre-registered distance, window by window."""
    out = {}
    for half, (a, b) in WINDOWS.items():
        s = series.loc[a:b].dropna()
        if len(s) < 24:
            return None
        sd = float(s.std())
        d = abs(float(np.log(sd / tgt[half]["sd"])))
        corr = {}
        for f in KNOWN:
            with np.errstate(invalid="ignore", divide="ignore"):
                c = float(s.corr(factors[f].loc[a:b].reindex(s.index)))
            corr[f] = c
            d += abs(c - tgt[half]["corr"][f])
        out[half] = {"sd": sd, "corr": corr, "d": d, "n": len(s)}
    out["total"] = out["pre"]["d"] + out["post"]["d"]
    return out


def fmt(p: dict) -> str:
    """One table row."""
    pre, post = p["pre"], p["post"]
    cells = [f"{pre['sd']:.4f}", *[f"{pre['corr'][f]:+.2f}" for f in KNOWN], f"{pre['d']:.3f}",
             f"{post['sd']:.4f}", *[f"{post['corr'][f]:+.2f}" for f in KNOWN], f"{post['d']:.3f}"]
    return " | ".join(cells)


def build(audit, vintage: str, label: str) -> tuple[dict, dict, pd.DataFrame]:
    """Every candidate of the grid for one factor vintage, its targets and its factors."""
    # the factors in the requested vintage; the prior-month deciles exist only today
    factors = load_factors(vintage=vintage)
    french_dir = FRENCH_DIR
    rf = factors["rf"]
    all_cands: dict[str, pd.Series] = {}
    all_cands.update(candidates(french_deciles(french_dir), rf, "french"))
    all_cands.update(candidates(crsp_deciles(("N", "A", "Q")), rf, "crsp_all"))
    all_cands.update(candidates(crsp_deciles(("N", "A")), rf, "crsp_nyseamex"))
    return all_cands, targets(audit, factors, label), factors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--dump-dir", type=Path, default=None,
                        help="directory to write the series of the --top nearest candidates")
    parser.add_argument("--top", type=int, default=3)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    audit = load_audit()
    vintages = {"today": "current", "2005": "2005"}
    built = {name: build(audit, vintage, name) for name, vintage in vintages.items()}
    lines = []
    for name, (_, tgt, _) in built.items():
        lines.append(f"targets, {name} factors:")
        for half in ("pre", "post"):
            corr = " ".join(f"{f} {tgt[half]['corr'][f]:+.2f}" for f in KNOWN)
            lines.append(f"  {half:4s} SD {tgt[half]['sd']:.4f}  {corr}"
                         f"  valid matrix: {tgt[half]['valid']}")
    table = {}
    for name, (cands, tgt, factors) in built.items():
        table[name] = {key: distance(s, factors, tgt) for key, s in cands.items()}
    header = ("| candidate | pre SD | pre mkt | pre SMB | pre HML | pre momo | pre d | "
              "post SD | post mkt | post SMB | post HML | post momo | post d | total |")
    for name, entries in table.items():
        rows = [(key, val) for key, val in entries.items() if val is not None]
        rows.sort(key=lambda kv: (round(kv[1]["total"], 3), kv[0]))
        lines += ["", f"candidates, {name} factors and targets ({len(rows)} with both windows):",
                  "", header, "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for key, val in rows:
            lines.append(f"| {key} | {fmt(val)} | {val['total']:.3f} |")
    text = "\n".join(lines)
    print(text)
    if args.out is not None:
        args.out.write_text(text + "\n")
    if args.dump_dir is not None:
        args.dump_dir.mkdir(parents=True, exist_ok=True)
        for name, entries in table.items():
            rows = [(k, v) for k, v in entries.items() if v is not None]
            rows.sort(key=lambda kv: (round(kv[1]["total"], 3), kv[0]))
            pick = [k for k, _ in rows[: args.top]]
            if "french_ew_d3_losers_only" not in pick:
                pick.append("french_ew_d3_losers_only")
            for key in pick:
                series = built[name][0][key]
                frame = pd.DataFrame({"month": series.index.strftime("%Y-%m-%d"),
                                      "reversal": series.to_numpy()})
                frame.to_csv(args.dump_dir / f"{key}__{name}.csv", index=False)
            print(f"dumped {len(pick)} series for {name} into {args.dump_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())