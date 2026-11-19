"""Contract R12-B: re-rank the reversal constructions against the factor Table 8 implies (note 103).

Table 8 (p. 822) does not publish the reversal factor, but its four printed columns pin one: the
variance identity of each column is linear in the factor's four covariances with the market, SMB,
HML and momentum (`c`) given its variance, so the panel fixes `c` and leaves the standard deviation
`s_r` free in a band (REVIEW_NOTES 99, `claims/CLASS_A_AUDIT.md` sections 2 and 5). On that metric
the scored series `french_ew_d3_losers_only` has a cosine of +0.999 with the required vector and is
about 3.5 % short of its norm. Neither earlier ranking used this metric: note 73 ranked the
constructions against a point target (SD plus four correlations) and note 82 against Table 7's
loadings.

This script asks whether any construction closes the norm gap in **both** windows without losing
direction or the band. The targets, the 78 candidates, the metrics and the decision rule were
pre-registered before any candidate was scored (`.review/r12/B/PREREG.md`; the rule is also in
REVIEW_NOTES section 103). Nothing is re-run: the candidates are built by
`scripts/experiments/reversal_subperiods.py`'s own builders (imported, not copied) from the decile
panels and French's 2005 archives, and the targets and the variance identity are
`scripts/experiments/class_a_audit.py`'s own functions.

Per candidate and window it reports `s_r` and whether it is inside the band, the four covariances,
the cosine against `c_req`, the norm ratio, the premium, and the R2 the printed loadings would give
with that candidate's moments. A candidate beats the shipped series only if, in both windows, its
norm gap `|1 - |c|/|c_req||` is smaller, its cosine is no more than 0.002 below, and its `s_r` is in
the band; it must then also hold note 82's Table 7 test (`--table7`).

Usage
-----
    python scripts/experiments/panel_a_rerank.py --csv /tmp/panel_a_rerank.csv
    python scripts/experiments/panel_a_rerank.py --out summary.md --json summary.json
    python scripts/experiments/panel_a_rerank.py --table7      # only if one passes the rule
"""

from __future__ import annotations

import argparse
import contextlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

FF = ("market", "smb", "hml", "momentum")
WINDOWS = {"pre": ("1963-07-31", "1988-12-31"), "post": ("1989-01-31", "2002-12-31")}
SHIPPED = "french_ew_d3_losers_only"
#: The fourth width the grid lacks: prior-month deciles 1-4 / 7-10, the grid's own leg arithmetic.
EXTRA = {"d4": ((0, 1, 2, 3), (6, 7, 8, 9))}
COSINE_TOL = 0.002
MIN_MONTHS = 24


def load_module(name: str, path: Path):
    """A sibling experiment script as a module (the same loader `table7_rerank.py` uses)."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(name, module)
    spec.loader.exec_module(module)
    return module


def load_inputs() -> tuple:
    """The grid's builders, the audit's identities, and the driver's typed paper values."""
    pb = load_module("reversal_subperiods",
                     ROOT / "scripts" / "experiments" / "reversal_subperiods.py")
    audit = load_module("class_a_audit", ROOT / "scripts" / "experiments" / "class_a_audit.py")
    return pb, audit, audit._replicate_module()


@contextlib.contextmanager
def extra_decile_sets(extra: dict):
    """Extend `reversal_subperiods.DECILE_SETS` for one call, so the leg arithmetic is its own."""
    saved = {key: value for key, value in pb_module().DECILE_SETS.items()}
    pb_module().DECILE_SETS.update(extra)
    try:
        yield
    finally:
        pb_module().DECILE_SETS.clear()
        pb_module().DECILE_SETS.update(saved)


def pb_module():
    return sys.modules["reversal_subperiods"]


# --------------------------------------------------------------------------- targets

def targets(audit, rep) -> dict:
    """Panel A's and Panel B's `c_req`, band and premium, from the printed values alone.

    The same construction `claims/CLASS_A_AUDIT.md` section 5 compares the series we hold against,
    applied to both panels: `joint_test` at the printed `s_r`, with `Sigma` rescaled to Table 8's
    own factor SDs (section 2's second convention), and the mean identity's implied premium.
    """
    paper = audit.paper_regressions(rep)
    out = {}
    for half, window, pinned in (("pre", audit.PRE_WINDOW, audit.PRE_SD),
                                 ("post", audit.POST_WINDOW, audit.POST_SD)):
        coef = paper[half][0]
        sigma, _ = audit.sigma_from_factors(window, rescaled=True, rep=rep, panel=half)
        columns = {p: audit.column_identities(coef.loc[p], sigma.to_numpy(),
                                              rep.PAPER_TABLE8[p][f"{half}_std"],
                                              float(coef.loc[p, "r2"]), pinned)
                   for p in audit.PORTFOLIOS}
        joint = audit.joint_test(columns, coef, sigma.to_numpy(), pinned)
        out[half] = {
            "window": WINDOWS[half],
            "c_req": [float(x) for x in joint["covariances"]],
            "c_intercept": [float(x) for x in joint["covariance_intercept"]],
            "c_slope": [float(x) for x in joint["covariance_slope"]],
            "norm": float(np.linalg.norm(joint["covariances"])),
            "s_r_pinned": float(pinned),
            "band": [float(x) for x in joint["feasible_s_r_band"]],
            "joint_r2": float(joint["implied_r2_reversal_on_four"]),
            "feasible": bool(joint["feasible"]),
            "condition_number": float(joint["condition_number"]),
            "premium_pct": {p: float(100 * v) for p, v in
                            audit.mean_identity(coef, sigma, window, rep, panel=half).items()},
            "loadings": coef,
            "sigma": sigma,
            "sigma_y": {p: float(rep.PAPER_TABLE8[p][f"{half}_std"]) for p in audit.PORTFOLIOS},
            "printed_r2": {p: float(coef.loc[p, "r2"]) for p in audit.PORTFOLIOS},
            "portfolios": list(audit.PORTFOLIOS),
        }
    return out


# --------------------------------------------------------------------------- candidates

def sort_blocks(pb) -> dict[str, dict[str, pd.DataFrame]]:
    """The three sort sources' decile panels, built once by the grid's own builders."""
    return {"french": pb.french_deciles(pb.FRENCH_DIR),
            "crsp_all": pb.crsp_deciles(("N", "A", "Q")),
            "crsp_nyseamex": pb.crsp_deciles(("N", "A"))}


def candidates(pb, blocks: dict, rf: pd.Series) -> dict[str, pd.Series]:
    """The 72 pre-registered constructions plus the six bottom-four-decile losers-only builds."""
    out: dict[str, pd.Series] = {}
    for prefix, frame in blocks.items():
        out.update(pb.candidates(frame, rf, prefix))
    with extra_decile_sets(EXTRA):
        for prefix, frame in blocks.items():
            out.update({name: series for name, series in
                        pb.candidates(frame, rf, prefix).items()
                        if name.endswith("_d4_losers_only")})
    return out


# --------------------------------------------------------------------------- metrics

def direction(c, c_req) -> float:
    """The cosine of a candidate's covariance vector with the required one.

    +1 means the same direction (the factor the panel implies), 0 orthogonal, -1 the opposite.
    """
    c = np.asarray(c, dtype=float)
    req = np.asarray(c_req, dtype=float)
    return float(c @ req / (np.linalg.norm(c) * np.linalg.norm(req)))


def norm_ratio(c, c_req) -> float:
    """`|c| / |c_req|`: below one means the series under-moves with the factors."""
    return float(np.linalg.norm(np.asarray(c, dtype=float)) / np.linalg.norm(np.asarray(c_req, dtype=float)))


def norm_gap(c, c_req) -> float:
    """`|1 - |c|/|c_req||`, the pre-registered closeness metric."""
    return abs(1.0 - norm_ratio(c, c_req))


def printed_r2(c, s_r: float, sigma, loadings: pd.DataFrame, sigma_y) -> np.ndarray:
    """The R2 each printed column would carry with the candidate's `c` and `s_r`.

    Section 5's identity, `(b'Sigma b + 2 beta (b.c) + beta^2 s_r^2) / sigma_y^2`, evaluated with
    every loadings term printed and only the reversal factor's two moments taken from the
    candidate.
    """
    b = loadings[list(FF)].to_numpy(dtype=float)
    beta = loadings["reversal"].to_numpy(dtype=float)
    carried = np.einsum("ij,jk,ik->i", b, np.asarray(sigma, dtype=float), b)
    return (carried + 2 * beta * (b @ np.asarray(c, dtype=float)) + beta**2 * s_r**2) \
        / np.asarray(sigma_y, dtype=float)**2


def metrics(series: pd.Series, factors: pd.DataFrame, half: str, tgt: dict) -> dict | None:
    """One candidate against one panel's target: direction, norm, band, premium and the R2.

    The sample is the candidate joined to that vintage's factors and cut to the window, which is
    how `class_a_audit.factor_proximity` compares the series we hold (its section 5).
    """
    start, end = pd.Timestamp(tgt["window"][0]), pd.Timestamp(tgt["window"][1])
    data = factors.loc[start:end].join(series.rename("r"), how="inner").dropna()
    if len(data) < MIN_MONTHS:
        return None
    r = data["r"]
    sd = float(r.std(ddof=1))
    c = np.array([float(np.cov(data[f], r)[0, 1]) for f in FF])
    req = np.array(tgt["c_req"])
    own = np.array(tgt["c_intercept"]) + sd**2 * np.array(tgt["c_slope"])
    implied = printed_r2(c, sd, tgt["sigma"], tgt["loadings"],
                         [tgt["sigma_y"][p] for p in tgt["portfolios"]])
    printed = np.array([tgt["printed_r2"][p] for p in tgt["portfolios"]])
    low, high = tgt["band"]
    return {
        "window": half, "n": len(data), "s_r": sd, "in_band": bool(low <= sd <= high),
        **{f"c_{f}": float(v) for f, v in zip(FF, c)},
        "cosine": direction(c, req), "ratio": norm_ratio(c, req), "gap": norm_gap(c, req),
        # sensitivity: the same comparison against the target read at this candidate's own s_r
        "cosine_own": direction(c, own), "ratio_own": norm_ratio(c, own),
        "gap_own": norm_gap(c, own),
        "premium_pct": float(100 * r.mean()),
        "r2_on_four": float(c @ np.linalg.solve(tgt["sigma"].to_numpy(), c) / sd**2),
        **{f"r2_{p}": float(v) for p, v in zip(tgt["portfolios"], implied)},
        **{f"paper_r2_{p}": float(v) for p, v in zip(tgt["portfolios"], printed)},
        "r2_gap_sum": float(np.sum(np.abs(implied - printed))),
    }


def measure(cands: dict[str, pd.Series], factors: pd.DataFrame, tgts: dict) -> pd.DataFrame:
    """Every candidate x window x metric, one row per cell."""
    rows = []
    for name, series in cands.items():
        for half in ("pre", "post"):
            cell = metrics(series, factors, half, tgts[half])
            if cell is None:
                continue
            rows.append({"candidate": name, **cell})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- the rule

def judge(table: pd.DataFrame, shipped: str = SHIPPED, suffix: str = "") -> pd.DataFrame:
    """The pre-registered rule, per candidate: the three conditions, window by window, then both.

    ``suffix`` reads another target convention off the same table (``_own`` is the sensitivity in
    which the required vector is taken at the candidate's own dispersion); the rule itself is the
    unsuffixed call.
    """
    wide = table.pivot(index="candidate", columns="window")
    base = {half: {**{m: wide.loc[shipped, (f"{m}{suffix}", half)]
                      for m in ("gap", "cosine")},
                   "s_r_in_band": wide.loc[shipped, ("s_r_in_band", half)]}
            for half in ("pre", "post")}
    out = {}
    for name in wide.index:
        flags = {}
        for half in ("pre", "post"):
            gap = wide.loc[name, (f"gap{suffix}", half)]
            cosine = wide.loc[name, (f"cosine{suffix}", half)]
            in_band = wide.loc[name, ("s_r_in_band", half)]
            flags[f"norm_{half}"] = bool(gap < base[half]["gap"])
            flags[f"direction_{half}"] = bool(cosine >= base[half]["cosine"] - COSINE_TOL)
            flags[f"band_{half}"] = bool(in_band)
            flags[f"window_{half}"] = bool(flags[f"norm_{half}"] and flags[f"direction_{half}"]
                                           and flags[f"band_{half}"])
        flags["passes"] = bool(flags["window_pre"] and flags["window_post"])
        out[name] = flags
    return pd.DataFrame.from_dict(out, orient="index")


def add_band_column(table: pd.DataFrame) -> pd.DataFrame:
    """`s_r_in_band` as a column so `pivot` carries it."""
    table = table.copy()
    table["s_r_in_band"] = table["in_band"].astype(bool)
    return table


def rank_window(table: pd.DataFrame, half: str) -> pd.DataFrame:
    """One window's ranking: the pre-registered key, descriptive only."""
    part = table[table["window"] == half].set_index("candidate")
    ordered = part.sort_values(["gap", "cosine", "r2_gap_sum"], ascending=[True, False, True],
                               kind="mergesort")
    ordered["rank"] = np.arange(1, len(ordered) + 1)
    return ordered


def shortlist(judged: pd.DataFrame) -> list[str]:
    """The candidates the rule admits, in name order."""
    return sorted(judged.index[judged["passes"].to_numpy(dtype=bool)])


# --------------------------------------------------------------------------- Table 7 (note 82)

def table7_gaps(names: list[str], cands: dict[str, pd.Series]) -> pd.DataFrame:
    """Note 82's s, R and M for the named candidates, by that script's own code."""
    t7r = load_module("table7_rerank", ROOT / "scripts" / "experiments" / "table7_rerank.py")
    from project.factors import load_factors

    factors = load_factors(vintage="2005")
    books = t7r.book_series(t7r.resolve_cache(None))
    table = t7r.gaps({name: cands[name] for name in names}, factors, books)
    shipped = t7r.gaps({SHIPPED: cands[SHIPPED]}, factors, books).loc[SHIPPED]
    table["P"] = table["R"] / shipped["R"] + table["M"] / shipped["M"]
    table["worse_signs"] = table["wrong_sign"] >= shipped["wrong_sign"]
    table["worse_reversal"] = table["R"] >= shipped["R"]
    table["worse_market"] = table["M"] >= shipped["M"]
    table["table7_pass"] = ~(table["worse_signs"] | table["worse_reversal"] | table["worse_market"])
    return table


# --------------------------------------------------------------------------- report

def _row(rank: int, name: str, r: pd.Series) -> str:
    return (f"| {rank} | {name} | {r['gap']:.4f} | {r['ratio']:.4f} | {r['cosine']:.4f} | "
            f"{r['s_r']:.5f} | {'yes' if r['in_band'] else 'NO'} | {r['premium_pct']:.3f} | "
            f"{r['r2_gap_sum']:.3f} |")


def report(table: pd.DataFrame, judged: pd.DataFrame, tgts: dict, n_cands: int,
           judged_own: pd.DataFrame | None = None) -> str:
    """The summary the commit carries: targets, both rankings, the rule's outcome and the bind."""
    lines = ["# Re-ranking the reversal constructions against the factor Table 8 implies (R12-B)", ""]
    lines += ["## Targets, from the printed panels and French's 2005 archives", "",
              ("| panel | |c_req| | c_req (mkt, smb, hml, momo) | s_r pinned | band | joint R2 |"
               " premium %/month | feasible |"),
              "|---|---|---|---|---|---|---|---|"]
    for half in ("pre", "post"):
        t = tgts[half]
        prem = " / ".join(f"{v:.3f}" for v in t["premium_pct"].values())
        lines.append(f"| {half} | {t['norm']:.7f} | "
                     + ", ".join(f"{x:+.6f}" for x in t["c_req"])
                     + f" | {t['s_r_pinned']:.5f} | {t['band'][0]:.4f} to {t['band'][1]:.4f} | "
                     f"{t['joint_r2']:.3f} | {prem} | {'yes' if t['feasible'] else 'NO'} |")
    rows = table.groupby("candidate")["window"].nunique()
    lines += ["", (f"{n_cands} candidates, {int((rows == 2).sum())} with both windows "
                   "(the 72 of `claims/REVERSAL_SUBPERIODS.md` plus six `d4` losers-only builds)."),
              ""]
    for half, label in (("pre", "Panel A, 1963-07 to 1988-12"), ("post", "Panel B, 1989-01 to 2002-12")):
        ranked = rank_window(table, half)
        base = ranked.loc[SHIPPED]
        lines += [f"## {label}: the ten nearest on the norm gap", "",
                  ("| rank | candidate | gap | ratio | cosine | s_r | in band | premium % | "
                   "sum |R2 - printed| |"),
                  "|---|---|---|---|---|---|---|---|---|"]
        lines += [_row(int(r["rank"]), name, r) for name, r in ranked.head(10).iterrows()]
        lines += ["", (f"Shipped `{SHIPPED}`: rank {int(base['rank'])} of {len(ranked)} "
                       f"(gap {base['gap']:.4f}, ratio {base['ratio']:.4f}, cosine "
                       f"{base['cosine']:+.4f}, s_r {base['s_r']:.5f}, premium "
                       f"{base['premium_pct']:.3f} %, R2 gap sum {base['r2_gap_sum']:.3f})."), ""]
    if judged.loc[SHIPPED, "passes"]:
        lines += ["Note: the shipped series is compared with itself and cannot pass.", ""]
    passes = shortlist(judged)
    counts = {key: int(judged[key].to_numpy(dtype=bool).sum()) for key in
              ("norm_pre", "norm_post", "direction_pre", "direction_post", "band_pre", "band_post",
               "window_pre", "window_post", "passes")}
    both = judged.index[judged["norm_pre"] & judged["norm_post"]]
    lines += ["## The pre-registered rule", "",
              (f"Gap smaller than the shipped series' in the pre window: {counts['norm_pre']} of "
               f"{len(judged)}; in the post window: {counts['norm_post']}; in both: {len(both)}. "
               f"Cosine within {COSINE_TOL} of the shipped series' in pre / post: "
               f"{counts['direction_pre']} / {counts['direction_post']}. In band in pre / post: "
               f"{counts['band_pre']} / {counts['band_post']}. Windows passed: "
               f"{counts['window_pre']} / {counts['window_post']}. **Candidates passing both: "
               f"{len(passes)}**."), ""]
    if both.empty:
        lines += ["No candidate closes the norm gap in both windows.", ""]
    else:
        sub = judged.loc[both]
        for name in both[:12]:
            flags = ("direction pre/post "
                     + "/".join("yes" if sub.loc[name, k] else "NO"
                                for k in ("direction_pre", "direction_post"))
                     + ", band pre/post "
                     + "/".join("yes" if sub.loc[name, k] else "NO"
                                for k in ("band_pre", "band_post")))
            lines.append(f"- {name}: {flags}")
        lines.append("")
    # which constraint binds
    bind = []
    for key, why in (("band_pre", "the panel A band"), ("band_post", "the panel B band"),
                     ("direction_pre", "direction in panel A (cosine)"),
                     ("direction_post", "direction in panel B (cosine)")):
        fails = judged.index[~judged[key].to_numpy(dtype=bool)]
        bind.append(f"{why}: {len(fails)} candidates fail it")
    lines += ["Constraints, counted over all candidates: " + "; ".join(bind) + ".", ""]
    if len(both):
        pre_best = rank_window(table, "pre").head(3).index.tolist()
        post_best = rank_window(table, "post").head(3).index.tolist()
        lines += ["The three nearest in panel A: " + ", ".join(pre_best)
                  + "; in panel B: " + ", ".join(post_best)
                  + f". Same set: {sorted(pre_best) == sorted(post_best)}.", ""]
        gaps = table.pivot(index="candidate", columns="window")["gap"]
        rho = float(gaps["pre"].corr(gaps["post"], method="spearman"))
        lines += [(f"Spearman rank correlation of the norm gap across the two windows: "
                   f"{rho:+.3f} (n = {len(gaps)})."), ""]
    if judged_own is not None:
        own = shortlist(judged_own)
        c_own = {key: int(judged_own[key].to_numpy(dtype=bool).sum()) for key in
                 ("norm_pre", "norm_post", "window_pre", "window_post")}
        closes = judged_own.index[judged_own["norm_pre"] & judged_own["norm_post"]]
        lines += [("### Sensitivity, added after the rule was run: the target at the "
                   "candidate's own dispersion"), "",
                  ("The band says the panel is feasible for a range of reversal variances, and the "
                   "required vector `c` is affine in that variance, so a candidate with a smaller "
                   "s_r asks for a smaller `c`. The pre-registered metric compares every candidate "
                   "with `c` at the printed s_r; this reads it at the candidate's own. Conditions, "
                   f"comparison series and rule unchanged. Closer than the shipped series: "
                   f"{c_own['norm_pre']} of {len(judged_own)} in the pre window, "
                   f"{c_own['norm_post']} in the post window, {len(closes)} in both; windows passed "
                   f"{c_own['window_pre']} / {c_own['window_post']}; **candidates passing both: "
                   f"{len(own)}**"
                   + (": " + ", ".join(own) + "." if own else ".")), ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--csv", type=Path, default=None, help="every candidate x window x metric")
    ap.add_argument("--out", type=Path, default=None, help="the summary markdown")
    ap.add_argument("--json", type=Path, default=None, help="targets, rule flags and counts")
    ap.add_argument("--table7", action="store_true",
                    help="run note 82's Table 7 test on the candidates the rule admits")
    ap.add_argument("--limit", type=int, default=None,
                    help="score only the first N candidates of each sort source (a smoke run)")
    args = ap.parse_args(argv)

    pb, audit, rep = load_inputs()
    tgts = targets(audit, rep)
    from project.factors import load_factors
    factors = load_factors(vintage="2005")
    blocks = sort_blocks(pb)
    cands = candidates(pb, blocks, factors["rf"])
    if args.limit is not None:
        keep = sorted(cands)[: args.limit] + [SHIPPED]
        cands = {name: cands[name] for name in dict.fromkeys(keep)}
    table = add_band_column(measure(cands, factors, tgts))
    judged = judge(table)
    judged_own = judge(table, suffix="_own")
    text = report(table, judged, tgts, len(cands), judged_own)
    print(text)
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n")
    if args.csv is not None:
        args.csv.parent.mkdir(parents=True, exist_ok=True)
        merged = table.merge(judged.reset_index().rename(columns={"index": "candidate"}),
                            on="candidate", how="left")
        merged.to_csv(args.csv, index=False)
        print(f"wrote {args.csv} ({len(merged)} rows)")
    payload = {"targets": {h: {k: v for k, v in t.items()
                               if k not in ("loadings", "sigma")} for h, t in tgts.items()},
               "shipped": {m: {h: _num(table, SHIPPED, h, m) for h in ("pre", "post")}
                           for m in ("gap", "ratio", "cosine", "s_r", "premium_pct",
                                     "r2_gap_sum", "r2_on_four")},
               "counts": {k: int(judged[k].to_numpy(dtype=bool).sum()) for k in judged.columns},
               "passes": shortlist(judged)}
    if args.table7:
        # Note 82's test is the rule's second gate. The six `d4` builds are measured whether or
        # not they pass the first one: they are this contract's addition to the grid and note 82's
        # table covers only the 72. That row is supplementary, not a change to the rule.
        extra = [name for name in cands if name.endswith("_d4_losers_only")]
        t7 = table7_gaps(sorted(set(shortlist(judged)) | set(extra) | {SHIPPED}), cands)
        payload["table7"] = json.loads(t7[["wrong_sign", "R", "M", "P", "table7_pass"]]
                                       .to_json(orient="index"))
        print()
        print(f"note 82's Table 7 test, for the {len(t7) - 1} candidates this contract extends "
              "the grid with (the shipped series' row is the benchmark, so its P is 2):")
        print("| candidate | s | R | M | R2 gap | P | gate |")
        print("|---|---|---|---|---|---|---|")
        for name, row in t7.sort_values("P").iterrows():
            print(f"| {name} | {int(row['wrong_sign'])} | {row['R']:.4f} | {row['M']:.4f} | "
                  f"{row['r2_gap']:.4f} | {row['P']:.4f} | "
                  f"{'pass' if row['table7_pass'] else 'fail'} |")
    if args.json is not None:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(payload, indent=1, default=float) + "\n")
        print(f"wrote {args.json}")
    return 0


def _num(table: pd.DataFrame, name: str, half: str, metric: str) -> float | None:
    row = table[(table["candidate"] == name) & (table["window"] == half)]
    if not len(row):
        return None
    value = float(row[metric].iloc[0])
    return value if np.isfinite(value) else None


if __name__ == "__main__":
    raise SystemExit(main())