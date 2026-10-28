"""Replication driver for Gatev, Goetzmann and Rouwenhorst (2006).

Loops over monthly cohorts (12-month formation, 6-month trading, first trading
month 1963-07, last cohort 2002-12). Each cohort job loads its data once, forms
unrestricted and within-sector pairs, simulates the 2-sigma rule (wait 0 and 1)
and caches its monthly returns, Table 2 inputs, Panel B composition and sector
counts. The tables are then aggregated from those small cohort summaries.

Usage:
    .venv/bin/python scripts/03_replicate.py [--steps tables,table3,figure1,check]
        [--start 1963-07] [--end 2002-12] [--wait 0,1] [--workers N]
        [--limit-cohorts K] [--force] [--universe vol_common]
        [--normalization continued|rebased] [--aggregate-only]
        [--same-issuer exclude|allow] [--max-stale-share SHARE|none]
        [--telephone-sic 4811|481x] [--trigger-sigma rms|std]
        [--size-deciles-top N]

Cohorts are cached under data/processed/replication/{NAME}/cohorts/, stamped
with their trading normalization, cache format and formation options in
cache_meta.json. Outputs
go to results/replication/tables/ and results/replication/figures/ for the
primary universe and to a {NAME} subfolder for other variants. Reruns are
incremental; --force rebuilds every cohort; --aggregate-only only reads a
complete, matching cache.
"""

from __future__ import annotations

import argparse
import calendar
import json
import os

# One BLAS/OpenMP thread per process. A cohort's linear algebra is small (the
# Gram matrix of a 3,000 x 252 window takes ~8 ms single-threaded), so the
# thread pools buy nothing and cost plenty: with N worker processes on a busy
# host they spin-wait against each other, and a cohort that needs 0.8 s of CPU
# took 1-4 s of wall time. Pinning them also keeps every worker's memory small.
for _var in (
    "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS", "NUMBA_NUM_THREADS", "VECLIB_MAXIMUM_THREADS",
):
    os.environ.setdefault(_var, "1")

import shutil
import subprocess
import sys
import tempfile
import time
import traceback
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

# Anchor this checkout's package: an editable install pins its .pth to one
# absolute path, so a copy of this repository must not silently import the
# original checkout's code. The package sits at the repository root in some
# checkouts and under src/ in others, so anchor whichever exists.
_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src") if (_ROOT / "src" / "project").exists() else str(_ROOT))

from project.data import (
    formation_columns,
    formation_universe,
    issuer_map,
    load_daily,
    pin_arrow_threads,
    trading_calendar,
)
from project.evaluation import (
    PORTFOLIOS,
    cohort_monthly,
    composition_stats,
    overlap_average,
    portfolio_daily,
    portfolio_legs,
    restrict_to_size_deciles,
    summary_stats,
    trading_components,
    trading_stats_from_components,
)
from project.factors import (
    FACTORS,
    IBBOTSON_FACTORS,
    factor_regression,
    factor_residuals,
    factor_tstats,
    load_factors,
    load_ibbotson_factors,
    load_losers_only,
)
from project.features import normalized_prices, select_pairs, select_pairs_within_groups
from project.models import simulate_cohort
from project.paths import ROOT
from project.plotting import plot_pair_trading_period, position_indicator
from project.sectors import (
    SECTORS,
    default_cache_path,
    earliest_known_sic,
    header_sic,
    sectors_for,
)

PAPER_TABLE1: dict[str, dict[str, dict[str, float]]] = {
    "A": {
        "top5": {
            "mean": 0.01308, "nw_se": 0.00148, "t_stat": 8.84, "median": 0.01194,
            "std": 0.02280, "skew": 0.62, "kurtosis": 7.81, "min": -0.10573,
            "max": 0.14716, "share_negative": 0.26, "committed_mean": 0.00784,
        },
        "top20": {
            "mean": 0.01436, "nw_se": 0.00124, "t_stat": 11.56, "median": 0.01235,
            "std": 0.01688, "skew": 1.39, "kurtosis": 10.54, "min": -0.06629,
            "max": 0.13295, "share_negative": 0.15, "committed_mean": 0.00805,
        },
        "101-120": {
            "mean": 0.01081, "nw_se": 0.00094, "t_stat": 11.54, "median": 0.00955,
            "std": 0.01540, "skew": 1.34, "kurtosis": 10.30, "min": -0.03857,
            "max": 0.12684, "share_negative": 0.21, "committed_mean": 0.00679,
        },
        "all": {
            "mean": 0.01104, "nw_se": 0.00099, "t_stat": 11.16, "median": 0.00728,
            "std": 0.01670, "skew": 3.42, "kurtosis": 25.25, "min": -0.02721,
            "max": 0.17178, "share_negative": 0.17, "committed_mean": 0.00614,
        },
    },
    "B": {
        "top5": {
            "mean": 0.00745, "nw_se": 0.00119, "t_stat": 6.26, "median": 0.00699,
            "std": 0.02101, "skew": 0.34, "kurtosis": 10.64, "min": -0.12628,
            "max": 0.14350, "share_negative": 0.35, "committed_mean": 0.00463,
        },
        "top20": {
            "mean": 0.00895, "nw_se": 0.00096, "t_stat": 9.29, "median": 0.00690,
            "std": 0.01527, "skew": 1.45, "kurtosis": 16.13, "min": -0.08218,
            "max": 0.13490, "share_negative": 0.23, "committed_mean": 0.00520,
        },
        "101-120": {
            "mean": 0.00795, "nw_se": 0.00085, "t_stat": 9.40, "median": 0.00694,
            "std": 0.01438, "skew": 0.98, "kurtosis": 7.78, "min": -0.04266,
            "max": 0.10464, "share_negative": 0.28, "committed_mean": 0.00503,
        },
        "all": {
            "mean": 0.00715, "nw_se": 0.00090, "t_stat": 7.92, "median": 0.00411,
            "std": 0.01577, "skew": 3.32, "kurtosis": 25.66, "min": -0.02951,
            "max": 0.16325, "share_negative": 0.32, "committed_mean": 0.00396,
        },
    },
}

PAPER_TABLE2A: dict[str, dict[str, float]] = {
    "top5": {
        "avg_price_deviation_trigger": 0.04758,
        "avg_pairs_traded_per_period": 4.81,
        "avg_round_trips_per_pair": 2.02,
        "std_round_trips_per_pair": 0.62,
        "avg_time_open_months": 3.75,
        "std_time_open_months": 0.80,
    },
    "top20": {
        "avg_price_deviation_trigger": 0.05284,
        "avg_pairs_traded_per_period": 19.30,
        "avg_round_trips_per_pair": 1.96,
        "std_round_trips_per_pair": 0.40,
        "avg_time_open_months": 3.76,
        "std_time_open_months": 0.45,
    },
    "101-120": {
        "avg_price_deviation_trigger": 0.07560,
        "avg_pairs_traded_per_period": 19.41,
        "avg_round_trips_per_pair": 1.78,
        "std_round_trips_per_pair": 0.27,
        "avg_time_open_months": 3.98,
        "std_time_open_months": 0.38,
    },
    "all": {
        "avg_price_deviation_trigger": 0.16888,
        "avg_pairs_traded_per_period": 1944.22,
        "avg_round_trips_per_pair": 1.62,
        "std_round_trips_per_pair": 0.16,
        "avg_time_open_months": 3.97,
        "std_time_open_months": 0.17,
    },
}

PAPER_TABLE2B: dict[str, dict[str, float]] = {
    "top5": {
        "avg_size_decile": 2.54,
        "weight_top3_deciles": 0.78,
        "weight_top5_deciles": 0.91,
        "share_mixed_decile_pairs": 0.66,
        "avg_decile_diff_mixed_pairs": 0.97,
        "weight_utilities": 0.72,
        "weight_transportation": 0.02,
        "weight_financials": 0.11,
        "weight_industrials": 0.15,
        "share_mixed_sector_pairs": 0.20,
    },
    "top20": {
        "avg_size_decile": 2.71,
        "weight_top3_deciles": 0.74,
        "weight_top5_deciles": 0.91,
        "share_mixed_decile_pairs": 0.69,
        "avg_decile_diff_mixed_pairs": 0.97,
        "weight_utilities": 0.71,
        "weight_transportation": 0.02,
        "weight_financials": 0.13,
        "weight_industrials": 0.14,
        "share_mixed_sector_pairs": 0.22,
    },
    "101-120": {
        "avg_size_decile": 3.41,
        "weight_top3_deciles": 0.58,
        "weight_top5_deciles": 0.79,
        "share_mixed_decile_pairs": 0.75,
        "avg_decile_diff_mixed_pairs": 0.97,
        "weight_utilities": 0.32,
        "weight_transportation": 0.02,
        "weight_financials": 0.26,
        "weight_industrials": 0.40,
        "share_mixed_sector_pairs": 0.44,
    },
    "all": {
        "avg_size_decile": 4.57,
        "weight_top3_deciles": 0.40,
        "weight_top5_deciles": 0.62,
        "share_mixed_decile_pairs": 0.82,
        "avg_decile_diff_mixed_pairs": 0.98,
        "weight_utilities": 0.08,
        "weight_transportation": 0.03,
        "weight_financials": 0.16,
        "weight_industrials": 0.73,
        "share_mixed_sector_pairs": 0.33,
    },
}

PAPER_UNIVERSE = {
    "mean_stocks_per_cohort": 2317.0,
    "mean_pairs_per_cohort": 2057.0,
    "mean_pairs_opened_wait1": 1944.22,
}

PANEL_OF_WAIT = {0: "A", 1: "B"}

PAPER_TABLE3: dict[str, dict[str, list[float]]] = {
    "Utilities": {
        "top5": [0.00905, 7.37, 0.00829, 0.02154, 0.44, 13.67, -0.12347, 0.16563, 0.28],
        "top20": [0.01084, 10.26, 0.00938, 0.01645, 0.76, 12.38, -0.08750, 0.12730, 0.19],
        "101-120": [0.009256, 6.11, 0.00665, 0.02640, 0.66, 5.52, -0.07868, 0.12133, 0.35],
        "all": [0.01036, 10.51, 0.00969, 0.01472, 1.39, 12.74, -0.03519, 0.12878, 0.18],
    },
    "Transportation": {
        "top5": [0.00497, 2.98, 0.00594, 0.03892, -0.50, 4.98, -0.19570, 0.10961, 0.44],
        "top20": [0.00577, 4.26, 0.00547, 0.02942, -0.11, 5.00, -0.12467, 0.11099, 0.42],
        "all": [0.00440, 3.07, 0.00339, 0.02871, 0.53, 5.89, -0.12526, 0.13560, 0.44],
    },
    "Financials": {
        "top5": [0.00678, 4.79, 0.00557, 0.02598, 0.81, 6.37, -0.081988, 0.149291, 0.40],
        "top20": [0.00775, 7.60, 0.00615, 0.01792, 0.61, 6.48, -0.07810, 0.10638, 0.33],
        "101-120": [0.00854, 7.12, 0.00660, 0.02358, 1.98, 18.27, -0.100477, 0.195797, 0.32],
        "all": [0.00726, 7.62, 0.00511, 0.01808, 2.64, 21.21, -0.04452, 0.17211, 0.34],
    },
    "Industrials": {
        "top5": [0.00490, 4.11, 0.00292, 0.02361, 0.40, 4.94, -0.10016, 0.10546, 0.42],
        "top20": [0.00607, 6.93, 0.00547, 0.01601, 0.43, 4.75, -0.04786, 0.08022, 0.36],
        "101-120": [0.00664, 6.80, 0.00550, 0.01825, 0.94, 7.65, -0.05412, 0.11619, 0.35],
        "all": [0.00715, 7.52, 0.00397, 0.01672, 2.97, 20.95, -0.03431, 0.16072, 0.34],
    },
}
PAPER_TABLE3_ROWS = [
    "mean", "t_stat", "median", "std", "skew", "kurtosis", "min", "max", "share_negative",
]
# Paper Table 5 Panel A (monthly value at risk, "wait one day") and Table 8 (the
# same series split at 1988-12, with a five-factor regression in each half). Both are
# scored since SCORE_LOG row 15. Table 5's mean and standard deviation rows repeat
# Table 1 Panel B, and its probability of a loss and minimum repeat Table 1 Panel B's
# share negative and minimum, so they are left out. Table 8's factor standard
# deviations describe the factor data, not the replication, and its t-statistics
# derive from the coefficients, so neither is scored.
PAPER_TABLE5: dict[str, dict[str, float]] = {
    "top5": {"serial_correlation": 0.14, "var_1": -0.04320, "var_5": -0.02142,
             "var_10": -0.01516, "var_25": -0.00460},
    "top20": {"serial_correlation": 0.24, "var_1": -0.01943, "var_5": -0.01002,
              "var_10": -0.00577, "var_25": 0.00054},
    "101-120": {"serial_correlation": 0.19, "var_1": -0.02236, "var_5": -0.01293,
                "var_10": -0.00756, "var_25": -0.00145},
    "all": {"serial_correlation": 0.12, "var_1": -0.01994, "var_5": -0.00877,
            "var_10": -0.00614, "var_25": -0.00146},
}
PAPER_TABLE8: dict[str, dict[str, float]] = {
    "top5": {"pre_mean": 0.01034, "pre_std": 0.02259, "post_mean": 0.00217,
             "post_std": 0.01660},
    "top20": {"pre_mean": 0.01181, "pre_std": 0.01689, "post_mean": 0.00375,
              "post_std": 0.00987},
    "101-120": {"pre_mean": 0.01052, "pre_std": 0.01527, "post_mean": 0.00327,
                "post_std": 0.01121},
    "all": {"pre_mean": 0.00992, "pre_std": 0.01651, "post_mean": 0.00212,
            "post_std": 0.01295},
}
FACTOR_ROWS = ["intercept", *FACTORS, "r2"]
_TABLE8_REGRESSIONS = {
    #          intercept   market     SMB       HML      momentum  reversal   R2
    "pre": {"top5": (0.00353, -0.43395, -0.44181, 0.03568, 0.01291, 0.43575, 0.19),
            "top20": (0.00670, -0.31200, -0.33193, 0.03162, -0.01630, 0.33274, 0.23),
            "101-120": (0.00710, -0.28946, -0.27508, -0.06840, -0.07689, 0.28765, 0.26),
            "all": (0.00446, -0.43429, -0.40184, -0.06983, -0.15848, 0.45222, 0.70)},
    "post": {"top5": (0.00337, 0.07339, -0.00400, 0.03441, -0.00424, -0.06259, 0.02),
             "top20": (0.00417, 0.04804, 0.02888, 0.01412, -0.02266, -0.01727, 0.04),
             "101-120": (0.00363, 0.00241, 0.02332, 0.01830, -0.08840, 0.02404, 0.19),
             "all": (-0.00065, -0.06958, -0.06063, -0.08202, -0.12670, 0.18808, 0.64)},
}
for _half, _ports in _TABLE8_REGRESSIONS.items():
    for _p, _vals in _ports.items():
        PAPER_TABLE8[_p].update({f"{_half}_{row}": v for row, v in zip(FACTOR_ROWS, _vals)})
TABLE8_PCT = {f"{h}_{r}" for h in ("pre", "post") for r in ("mean", "std", "intercept")}
# Table 8's last column, each factor's standard deviation in the panel. Not scored: it is how
# the factors are identified (French's market, SMB, HML and momentum match it; the reversal
# factor does not, REVIEW_NOTES sections 49-50), so it is verified against the PDF.
PAPER_TABLE8_FACTOR_SD = {
    "pre": {"market": 0.04580, "smb": 0.02923, "hml": 0.02597, "momentum": 0.03506,
            "reversal": 0.07228},
    "post": {"market": 0.04390, "smb": 0.03856, "hml": 0.03641, "momentum": 0.04926,
             "reversal": 0.04448},
}

# Table 4 ("Systematic risk of pairs trading strategies", wait one day). Its mean and
# standard deviation repeat Table 1 Panel B and its serial correlation repeats Table 5
# Panel A, so the scored rows are the Sharpe ratio and the Fama-French + momentum +
# reversal regression (coefficients and R2; t-statistics not scored), then the regression on
# Ibbotson's four factors (``ibbotson_*`` rows, see ``project.factors``). The paper's last
# column, the equity premium over the same months, is scored on its own. It is French's
# Mkt-RF, the regressions' market factor: Table 8 calls that factor the "U.S. equity
# risk-premium" and its printed SDs are Mkt-RF's, and Mkt-RF reproduces all four printed
# statistics where the S&P 500 less bills misses the serial correlation (0.0002 against 0.05;
# REVIEW_NOTES section 50). The note's "S&P 500 returns are calculated in excess of Treasury
# bill returns" describes the Ibbotson model's market factor, which keeps the S&P.
PAPER_TABLE4: dict[str, dict[str, float]] = {
    "top5": {"sharpe": 0.35, **dict(zip(FACTOR_ROWS, (0.00545, -0.06661, -0.04233, 0.05740,
                                                      -0.02804, 0.10192, 0.05)))},
    "top20": {"sharpe": 0.59, **dict(zip(FACTOR_ROWS, (0.00764, -0.03155, 0.00111, 0.04514,
                                                       -0.04817, 0.07237, 0.09)))},
    "101-120": {"sharpe": 0.55, **dict(zip(FACTOR_ROWS, (0.00714, -0.07697, -0.02333, -0.01724,
                                                         -0.10312, 0.09459, 0.18)))},
    "all": {"sharpe": 0.45, **dict(zip(FACTOR_ROWS, (0.00512, -0.14520, -0.07079, -0.05403,
                                                     -0.18077, 0.20077, 0.54)))},
}
IBBOTSON_ROWS = [f"ibbotson_{r}" for r in ("intercept", *IBBOTSON_FACTORS, "r2")]
_TABLE4_IBBOTSON = {
    #           intercept   market    small     default   horizon    R2
    "top5": (0.00716, -0.00182, 0.04120, 0.14593, 0.07997, 0.02),
    "top20": (0.00857, 0.01377, 0.05227, 0.15989, 0.06818, 0.05),
    "101-120": (0.00766, 0.01642, 0.03646, 0.16811, 0.04034, 0.04),
    "all": (0.00651, 0.06466, 0.07608, 0.30571, 0.03422, 0.15),
}
for _p, _vals in _TABLE4_IBBOTSON.items():
    PAPER_TABLE4[_p].update(dict(zip(IBBOTSON_ROWS, _vals)))
TABLE4_PCT = {"intercept", "ibbotson_intercept"}
PAPER_EQUITY_PREMIUM = {"mean": 0.00410, "std": 0.04509, "sharpe": 0.09,
                        "serial_correlation": 0.05}
# The intercepts' Newey-West t-statistics (six lags), printed in parentheses in Table 4 and on
# the "t-Statistic" rows of Table 8. Reported beside ours, not scored: they answer the paper's
# question (is the excess return explained by the factors?) rather than measure the match.
PAPER_ALPHA_T = {
    "full": {"top5": 3.81, "top20": 7.08, "101-120": 8.66, "all": 5.30},
    "pre": {"top5": 1.72, "top20": 4.41, "101-120": 6.54, "all": 4.19},
    "post": {"top5": 2.12, "top20": 3.77, "101-120": 3.01, "all": -0.56},
}

# Figure 4: the correlations of the top 20 and 101-120 one-day-wait series printed in
# the text, raw and on five-factor residuals ("0.48 ... 0.51 ... 0.18", "0.41 ... 0.42
# and 0.20"); the subperiods split at 1988-12 as Table 8 does.
PAPER_FIGURE4 = {
    "correlation, full sample": {"raw": 0.48, "residual": 0.41},
    "correlation, before 1989": {"raw": 0.51, "residual": 0.42},
    "correlation, after 1988": {"raw": 0.18, "residual": 0.20},
}
# Table 7 ("Returns to long and short components of pairs", wait one day): the
# two books Table 1's fully-invested return is the difference of. Scored since
# 2026-10-25 (SCORE_LOG row 14); the rows below are the four printed for each
# book. The paper's regression block needs Fama-French, momentum and reversal
# factors and is not reproduced by the driver.
LEG_CAPITALS = ("long_book", "short_book")
TABLE7_ROWS = [
    "long: mean monthly return",
    "long: standard error (Newey-West)",
    "long: standard deviation",
    "long: monthly serial correlation",
    "short: mean monthly return",
    "short: standard error (Newey-West)",
    "short: standard deviation",
    "short: monthly serial correlation",
]
TABLE7_PCT = {r for r in TABLE7_ROWS if not r.endswith("serial correlation")}
PAPER_TABLE7: dict[str, dict[str, float]] = {
    "top5": {
        "long: mean monthly return": 0.01245,
        "long: standard error (Newey-West)": 0.00183,
        "long: standard deviation": 0.03875,
        "long: monthly serial correlation": 0.06,
        "short: mean monthly return": 0.00501,
        "short: standard error (Newey-West)": 0.00177,
        "short: standard deviation": 0.03259,
        "short: monthly serial correlation": 0.11,
    },
    "top20": {
        "long: mean monthly return": 0.0133,
        "long: standard error (Newey-West)": 0.00179,
        "long: standard deviation": 0.03653,
        "long: monthly serial correlation": 0.09,
        "short: mean monthly return": 0.00435,
        "short: standard error (Newey-West)": 0.00174,
        "short: standard deviation": 0.03161,
        "short: monthly serial correlation": 0.12,
    },
    "101-120": {
        "long: mean monthly return": 0.01458,
        "long: standard error (Newey-West)": 0.0017,
        "long: standard deviation": 0.03437,
        "long: monthly serial correlation": 0.13,
        "short: mean monthly return": 0.00663,
        "short: standard error (Newey-West)": 0.00165,
        "short: standard deviation": 0.03146,
        "short: monthly serial correlation": 0.12,
    },
    "all": {
        "long: mean monthly return": 0.01623,
        "long: standard error (Newey-West)": 0.00254,
        "long: standard deviation": 0.05157,
        "long: monthly serial correlation": 0.17,
        "short: mean monthly return": 0.00908,
        "short: standard error (Newey-West)": 0.00231,
        "short: standard deviation": 0.04601,
        "short: monthly serial correlation": 0.16,
    },
}
SUBPERIOD_SPLIT = (1988, 12)
DIAGNOSTIC_FILES = ("table5_var.csv", "table8_subperiod.csv")
RISK_FILES = ("table4.csv", "table4_equity_premium.csv", "figure4.csv",
              "reversal_alternative.csv")
#: Digitised from the embedded rasters by ``scripts/digitize_figures.py``: Figure 2's
#: monthly bars (``up`` / ``down`` / ``signed``, calibrated so the tallest bar is Table 1
#: Panel A's top-20 maximum) and Figure 3's two pairs curves (``fully_invested`` /
#: ``committed``, cumulative levels read off its log scale).
FIGURE_FIXTURES = ("figure2_bars.csv", "figure3_curves.csv")

PAPER_SECTOR_COUNTS = {"Utilities": 156, "Transportation": 61, "Financials": 371, "Industrials": 1729}
TABLE3_PORTFOLIOS = {
    "top5": range(1, 6), "top20": range(1, 21), "101-120": range(101, 121), "all": None,
}
TABLE3_CAPITALS = ("employed", "committed", "employed_count")

FIGURE1 = {
    "cohort": (1963, 8),
    "permnos": (12706, 14912),
    "labels": {12706: "Kennecott", 14912: "Uniroyal (U.S. Rubber)"},
    "paper_trades": [(7, 35), (46, 55), (74, 82), (86, 99), (108, 126)],
    "paper_start_level": 1.10,
    "day_tolerance": 3,
}

PRIMARY_UNIVERSE = "vol_common"
STEPS = ("tables", "table3", "figure1", "check")
_SIC_FALLBACKS: tuple[pd.Series, ...] | None = None

CACHE_ROOT_OVERRIDE: Path | None = None
OUT_ROOT_OVERRIDE: Path | None = None
FORMATION_OPTIONS: dict = {}
_ISSUERS: pd.Series | None = None


def cohort_dir(universe: str) -> Path:
    if CACHE_ROOT_OVERRIDE is not None:
        return CACHE_ROOT_OVERRIDE / "cohorts"
    return ROOT / "data" / "processed" / "replication" / universe / "cohorts"


def tables_dir(universe: str) -> Path:
    if OUT_ROOT_OVERRIDE is not None:
        return OUT_ROOT_OVERRIDE / "tables"
    base = ROOT / "results" / "replication" / "tables"
    return base if universe == PRIMARY_UNIVERSE else base / universe


def figures_dir(universe: str) -> Path:
    if OUT_ROOT_OVERRIDE is not None:
        return OUT_ROOT_OVERRIDE / "figures"
    base = ROOT / "results" / "replication" / "figures"
    return base if universe == PRIMARY_UNIVERSE else base / universe


CACHE_FORMAT = 5
T1_CAPITALS = ("committed", "employed", "committed_count", "employed_count", "employed_literal")


def read_cache_meta(universe: str) -> dict | None:
    meta = cohort_dir(universe) / "cache_meta.json"
    return json.loads(meta.read_text()) if meta.exists() else None


def _expected_meta(continued: bool) -> dict:
    return {
        "normalization": "continued" if continued else "rebased",
        "format": CACHE_FORMAT,
        **FORMATION_OPTIONS,
    }


def verify_cache(universe: str, continued: bool) -> None:
    """Refuse to read a cache that is unstamped, of an older format or built
    under the other trading normalization. Reading never writes the stamp."""
    meta = read_cache_meta(universe)
    want = _expected_meta(continued)
    if meta is None:
        raise SystemExit(
            f"{universe} cache has no cache_meta.json; rebuild it with --force"
        )
    if meta.get("format") != CACHE_FORMAT:
        raise SystemExit(
            f"{universe} cache has format {meta.get('format')}, expected {CACHE_FORMAT}; "
            "rebuild it with --force"
        )
    if meta.get("normalization") != want["normalization"]:
        raise SystemExit(
            f"{universe} cache was built with {meta.get('normalization')} normalization; "
            f"pass --normalization {meta.get('normalization')} or rebuild with --force"
        )
    for key in ("exclude_same_issuer", "max_stale_share", "telephone_sic", "trigger_sigma",
                "short_weights", "size_deciles_top"):
        if meta.get(key) != want.get(key):
            built = f"{key}={meta[key]}" if key in meta else f"no {key} stamp"
            now = f"{key}={want[key]}" if key in want else f"no {key}"
            raise SystemExit(
                f"{universe} cache was built with {built}, this run uses {now}; "
                "match the formation flags or rebuild with --force"
            )


def stamp_cache(universe: str, continued: bool, force: bool) -> None:
    """Stamp the cache before building into it; refuse to mix builds unless forced."""
    meta = read_cache_meta(universe)
    want = _expected_meta(continued)
    if meta is not None and meta != want and not force:
        raise SystemExit(
            f"{universe} cache is stamped {meta}; this run would build {want}. "
            "Rebuild it with --force"
        )
    path = cohort_dir(universe) / "cache_meta.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(want) + "\n")


def shift_month(year: int, month: int, k: int) -> tuple[int, int]:
    """Shift (year, month) by k months."""
    idx = year * 12 + (month - 1) + k
    return idx // 12, idx % 12 + 1


def month_start(year: int, month: int) -> date:
    return date(year, month, 1)


def month_end(year: int, month: int) -> date:
    return date(year, month, calendar.monthrange(year, month)[1])


def cohort_months(start: tuple[int, int], end: tuple[int, int]) -> list[tuple[int, int]]:
    """All cohort first-trading months in [start, end] inclusive."""
    out = []
    y, m = start
    while (y, m) <= end:
        out.append((y, m))
        y, m = shift_month(y, m, 1)
    return out


@dataclass(frozen=True)
class Job:
    year: int
    month: int
    end: tuple[int, int]
    waits: tuple[int, ...]
    universe: str
    continued: bool = True
    cohorts_root: str | None = None
    exclude_same_issuer: bool = False
    max_stale_share: float | None = None
    telephone_sic: str = "4811"
    trigger_sigma: str = "rms"
    short_weights: str = "position"
    #: Largest CRSP size decile a formation-end stock may sit in (``None``: no
    #: screen). ``3`` forms pairs only inside the top three deciles, the universe
    #: of the paper's Table 9 Panel A. Judge eligibility first, then the screen.
    size_deciles_top: int | None = None


def init_worker(fallbacks: tuple[pd.Series, ...] | None = None) -> None:
    """Seed this process's SIC fallbacks; ``None`` means "compute them on first use"."""
    global _SIC_FALLBACKS
    _SIC_FALLBACKS = fallbacks


def sic_cache_path(cohorts_root: str | None) -> Path | None:
    """Where this run may cache the panel SIC scan, if somewhere other than default.

    A run that redirects its cohort cache (``--cache-root``) redirects this too:
    a private or sandboxed rebuild must not rewrite the shared
    ``sic_fallback.parquet`` that sits beside the cache it compares itself to.
    ``None`` leaves ``earliest_known_sic`` its own default.
    """
    # The same file name the default uses, so every cache holds one format.
    return Path(cohorts_root).parent / default_cache_path().name if cohorts_root else None


def _sic_fallbacks(cohorts_root: str | None = None) -> tuple[pd.Series, ...]:
    """This process's SIC fallbacks, computed on first use.

    Unknown (0) dated codes fill from the CRSP security-header SIC first (a
    stock's own header classification), then from the earliest known dated SIC;
    SCORE_LOG.md row 10 records the move and the cell shifts.

    A shard child calls this on its first cohort. ``run_jobs`` has already
    scanned the panel in the parent, so the child normally just reads the small
    cache file; if that file is missing or stale it scans the panel itself,
    which is slower but never wrong. The header SIC comes with it because the
    two are always used together (``sectors_for``).
    """
    global _SIC_FALLBACKS
    if _SIC_FALLBACKS is None:
        try:
            header = header_sic()
        except (FileNotFoundError, OSError) as err:
            print(f"warning: security-header SIC fallback unavailable ({err}); "
                  "sector labels may shift", file=sys.stderr)
            header = pd.Series(dtype="float64", name="siccd")
        _SIC_FALLBACKS = (header, earliest_known_sic(cache_path=sic_cache_path(cohorts_root)))
    return _SIC_FALLBACKS


def _issuer_series() -> pd.Series:
    global _ISSUERS
    if _ISSUERS is None:
        _ISSUERS = issuer_map()
    return _ISSUERS


def _monthly_rows(table: str, sector: str, wait: int, pname: str, capital: str,
                  monthly: pd.Series) -> list[dict]:
    return [
        {"table": table, "sector": sector, "wait": wait, "portfolio": pname,
         "capital": capital, "month_end": ts, "ret": float(v)}
        for ts, v in monthly.items()
    ]


def build_cohort(job: Job) -> tuple[int, int]:
    """Build one cohort and cache everything the tables need.

    Loads the formation and trading data once, forms unrestricted and
    within-sector pairs, simulates them and writes under
    ``cohort_dir(universe)/YYYY-MM/``: ``pairs.parquet``, per wait
    ``w{wait}_trades.parquet`` and ``w{wait}_opened.parquet``, ``monthly.parquet``
    (each cohort's monthly returns for Tables 1 and 3) and ``summary.json``
    (Table 2 inputs, Panel B, universe and sector counts), written last.
    The trading period is loaded from the full panel regardless of the
    formation share filter, so a share-type change inside the trading period
    does not cut a stock off early.

    ``job.size_deciles_top`` (default ``None``: off) screens the eligible
    formation set to the largest size deciles before any pair is formed, so it
    changes which pairs exist, not just which are reported: the paper's
    Table 9 Panel A universe. Absent, the cohort is the shipped one byte for
    byte.
    """
    form_start = month_start(*shift_month(job.year, job.month, -12))
    form_end = month_end(*shift_month(job.year, job.month, -1))
    trade_start = month_start(job.year, job.month)
    trade_end = min(month_end(*shift_month(job.year, job.month, 5)), month_end(*job.end))
    # Three narrow reads instead of one wide one. The formation window needs
    # only what the eligibility rule reads plus the date and the returns (7
    # instead of 13); the label day and the trading window are separate small
    # reads, the latter restricted to the pair legs. Peak memory per cohort is
    # what limits how many can run at once on a loaded host, and the wide
    # 18-month frame was 300 MB of it.
    form_cal = trading_calendar(form_start, form_end)
    if len(form_cal) == 0:
        raise ValueError(f"No formation days for cohort {job.year}-{job.month:02d}")
    end_day = form_cal[-1]
    # The label day: sectors, the Table 2 Panel B caps and -- with
    # ``size_deciles_top`` -- the size deciles of the formation universe.
    row = load_daily(end_day, end_day, ["permno", "cap", "exch", "common", "siccd"])
    row = row.set_index("permno")
    formation_cols = [*formation_columns(job.universe, job.max_stale_share), "date"]
    form_panel = load_daily(form_start, form_end, formation_cols)
    universe = formation_universe(
        form_start, form_end, universe=job.universe, max_stale_share=job.max_stale_share,
        panel=form_panel,
    )
    if job.size_deciles_top is not None:
        # Table 9 Panel A's size screen: pairs form only inside the top deciles.
        # It reads the label day, which is also read below for the sectors and
        # Table 2 Panel B inputs, so that day is loaded once, before the screen.
        universe = restrict_to_size_deciles(
            universe, row["cap"], row["exch"], row["common"], job.size_deciles_top
        )
    form = form_panel.loc[form_panel["permno"].isin(set(universe)), ["permno", "date", "ret"]]
    del form_panel
    prices = normalized_prices(form.pivot(index="date", columns="permno", values="ret").sort_index())
    del form
    issuers = _issuer_series() if job.exclude_same_issuer else None
    pairs = select_pairs(prices, issuers, job.trigger_sigma)

    labels = sectors_for(row["siccd"].reindex(universe).fillna(0),
                         *_sic_fallbacks(job.cohorts_root), telephone=job.telephone_sic)
    sector_pairs = select_pairs_within_groups(prices, labels, issuers, job.trigger_sigma)
    levels = prices.iloc[-1] if job.continued else None
    del prices

    cal = trading_calendar(trade_start, trade_end)
    if len(cal) == 0:
        raise ValueError(f"No trading days for cohort {job.year}-{job.month:02d}")
    permnos = sorted(
        set(pairs["permno_1"]) | set(pairs["permno_2"])
        | set(sector_pairs["permno_1"]) | set(sector_pairs["permno_2"])
    )
    # Only the pair legs are read, and only for the trading window: a cohort
    # needs ~1,500 permnos x 126 days, not the whole panel of the window.
    trd = load_daily(cal[0], cal[-1], ["permno", "date", "ret", "terminal"], permnos=permnos)
    rets = trd.pivot(index="date", columns="permno", values="ret").reindex(index=cal, columns=permnos)
    term = (
        trd.pivot(index="date", columns="permno", values="terminal")
        .reindex(index=cal, columns=permnos)
        .eq(True)
    )
    del trd

    coh_dir = cohort_path(job)
    coh_dir.mkdir(parents=True, exist_ok=True)
    (coh_dir / "summary.json").unlink(missing_ok=True)
    pairs.to_parquet(coh_dir / "pairs.parquet")
    sigma = pairs.set_index("rank")["sigma"]
    rows: list[dict] = []
    summary: dict = {
        "waits": list(job.waits),
        "stocks": int(pd.concat([pairs["permno_1"], pairs["permno_2"]]).nunique()),
        "pairs": len(pairs),
        "trading": {},
        "composition": {},
        "sector_counts": {s: int(labels.eq(s).sum()) for s in SECTORS},
    }
    if job.size_deciles_top is not None:
        # Recorded only when the screen is on, so a default cohort's summary
        # stays byte-identical to the shipped cache.
        summary["size_deciles_top"] = job.size_deciles_top
    for wait in job.waits:
        result = simulate_cohort(pairs, rets, term, wait=wait, start_levels=levels)
        result.trades.to_parquet(coh_dir / f"w{wait}_trades.parquet")
        result.opened.rename("opened").to_frame().to_parquet(coh_dir / f"w{wait}_opened.parquet")
        for pname, ranks in PORTFOLIOS.items():
            for capital in T1_CAPITALS:
                monthly = cohort_monthly(portfolio_daily(result, ranks, capital, job.short_weights))
                rows += _monthly_rows("t1", "", wait, pname, capital, monthly)
            long_daily, short_daily = portfolio_legs(result, ranks, job.short_weights)
            for name, daily in zip(LEG_CAPITALS, (long_daily, short_daily)):
                rows += _monthly_rows("t1", "", wait, pname, name, cohort_monthly(daily))
            if wait == 1:
                summary["trading"][pname] = trading_components(result, sigma, ranks)
        if wait == 1:
            summary["opened_w1"] = int(result.opened.sum())

    caps = row["cap"].astype(float)
    info = {
        "pairs": pairs,
        "caps": caps,
        "breakpoint_caps": caps[row["exch"].isin(("N", "A")) & row["common"].eq(True)],
        "all_caps": caps,
        "siccd": row["siccd"],
        "sectors": labels,
    }
    for pname, ranks in PORTFOLIOS.items():
        summary["composition"][pname] = composition_stats(info, ranks).to_dict()

    for sector in SECTORS:
        sp = sector_pairs[sector_pairs["group"] == sector].drop(columns="group")
        summary["sector_counts"][f"pairs_{sector}"] = len(sp)
        if sp.empty:
            continue
        result = simulate_cohort(sp, rets, term, wait=1, start_levels=levels)
        for pname, ranks in TABLE3_PORTFOLIOS.items():
            if ranks is not None and len(sp) < max(ranks):
                continue
            for capital in TABLE3_CAPITALS:
                monthly = cohort_monthly(portfolio_daily(result, ranks, capital, job.short_weights))
                rows += _monthly_rows("t3", sector, 1, pname, capital, monthly)

    pd.DataFrame(rows, columns=["table", "sector", "wait", "portfolio", "capital",
                                "month_end", "ret"]).to_parquet(coh_dir / "monthly.parquet")
    (coh_dir / "summary.json").write_text(json.dumps(summary, default=float) + "\n")
    return job.year, job.month


def cohort_cache_complete(year: int, month: int, waits: tuple[int, ...], universe: str) -> bool:
    path = cohort_dir(universe) / f"{year:04d}-{month:02d}" / "summary.json"
    if not path.exists():
        return False
    return set(waits) <= set(json.loads(path.read_text()).get("waits", []))


def load_summaries(cohorts: list[tuple[int, int]], universe: str) -> tuple[pd.DataFrame, list[dict]]:
    """All cached monthly rows (with a ``cohort`` column) and the per-cohort summaries."""
    frames, summaries = [], []
    for year, month in cohorts:
        coh = cohort_dir(universe) / f"{year:04d}-{month:02d}"
        frame = pd.read_parquet(coh / "monthly.parquet")
        frame["cohort"] = pd.Timestamp(year, month, 1) + pd.offsets.MonthEnd(0)
        frames.append(frame)
        summaries.append(json.loads((coh / "summary.json").read_text()))
    return pd.concat(frames, ignore_index=True), summaries


def _strategy_series(frame: pd.DataFrame, end_ts: pd.Timestamp) -> pd.Series:
    """Overlap-average one key's cohort monthly returns to the strategy series."""
    months = {
        cohort: pd.Series(g["ret"].to_numpy(), index=pd.DatetimeIndex(g["month_end"]))
        for cohort, g in frame.groupby("cohort", sort=True)
    }
    strat = overlap_average(months)
    return strat[strat.index <= end_ts]


def aggregate(
    monthly: pd.DataFrame, summaries: list[dict], waits: tuple[int, ...], end: tuple[int, int],
    cohorts: list[tuple[int, int]] | None = None,
) -> tuple[dict, dict, dict, pd.Series]:
    """Tables 1 and 2 from cached cohort summaries.

    Returns (strategy, trading, composition, universe): ``strategy[wait][portfolio]
    [capital]`` is the strategy's monthly return Series, ``trading[portfolio]``
    the Table 2 Panel A Series (wait 1), ``composition[portfolio]`` the Panel B
    Series and ``universe`` the stocks / pairs / pairs-opened means.
    """
    end_ts = pd.Timestamp(month_end(*end))
    t1 = monthly[monthly["table"] == "t1"]
    groups = dict(tuple(t1.groupby(["wait", "portfolio", "capital"], sort=False)))
    empty = pd.Series(dtype=float, index=pd.DatetimeIndex([]))
    strategy = {
        w: {
            p: {
                c: _strategy_series(groups[(w, p, c)], end_ts) if (w, p, c) in groups else empty
                for c in (*T1_CAPITALS, *LEG_CAPITALS)
            }
            for p in PORTFOLIOS
        }
        for w in waits
    }
    trading = {}
    if 1 in waits:
        labels = [f"{year:04d}-{month:02d}" for year, month in cohorts] if cohorts else None
        trading = {
            p: trading_stats_from_components([s["trading"][p] for s in summaries], labels)
            for p in PORTFOLIOS
        }
    composition = {
        p: pd.DataFrame([s["composition"][p] for s in summaries]).mean() for p in PORTFOLIOS
    }
    universe = pd.Series(
        {
            "mean_stocks_per_cohort": float(np.mean([s["stocks"] for s in summaries])),
            "mean_pairs_per_cohort": float(np.mean([s["pairs"] for s in summaries])),
            "mean_pairs_opened_wait1": (
                float(np.mean([s["opened_w1"] for s in summaries])) if 1 in waits else np.nan
            ),
        }
    )
    return strategy, trading, composition, universe


def table3_from_cache(
    monthly: pd.DataFrame, summaries: list[dict], end: tuple[int, int],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Table 3 statistics (one row per sector, portfolio and capital) and sector counts."""
    end_ts = pd.Timestamp(month_end(*end))
    t3 = monthly[monthly["table"] == "t3"]
    rows = []
    for (sector, pname, capital), frame in t3.groupby(["sector", "portfolio", "capital"]):
        strat = _strategy_series(frame, end_ts)
        stats = summary_stats(strat)
        stats["n_months"] = int(strat.notna().sum())
        stats["n_cohorts"] = int(frame["cohort"].nunique())
        rows.append({"sector": sector, "portfolio": pname, "capital": capital, **stats.to_dict()})
    counts = pd.DataFrame([s["sector_counts"] for s in summaries]).fillna(0)
    return pd.DataFrame(rows), counts



def _monthly_autocorr(series: pd.Series) -> float:
    """Lag-1 autocorrelation over calendar-adjacent months.

    Missing months are reindexed in rather than dropped, so a strided sample
    (or any gap) never pairs two months that are not one month apart.
    """
    s = series.dropna()
    if len(s) <= 2:
        return float("nan")
    months = s.reindex(pd.date_range(s.index.min(), s.index.max(), freq="ME"))
    return float(months.autocorr(lag=1))

def _factors_or_none() -> pd.DataFrame | None:
    """French's five factors, or None (with a warning) while the LFS files are not pulled."""
    try:
        return load_factors()[FACTORS]
    except (FileNotFoundError, ValueError) as err:
        print(f"warning: factor files unavailable ({err}); the regression rows of Tables 4 "
              "and 8 and Figure 4's residual correlations are not computed", file=sys.stderr)
        return None


def _losers_only_or_none() -> pd.Series | None:
    """The losers-only reversal series for the unscored alternative, or None while unavailable."""
    try:
        return load_losers_only()
    except (FileNotFoundError, ValueError) as err:
        print(f"warning: prior-return deciles unavailable ({err}); the reversal-factor "
              "alternative is not computed", file=sys.stderr)
        return None


def write_reversal_alternative(series: dict[str, pd.Series], factors: pd.DataFrame,
                               reversal: pd.Series, out_dir: Path) -> None:
    """Tables 4 and 8's five-factor regressions again, with ``reversal`` as the reversal factor.

    ``reversal`` is the series Table 8's own regressions imply for the paper's factor (see
    ``load_losers_only`` and REVIEW_NOTES section 51). Written to ``reversal_alternative.csv``
    as ``{full,pre,post}_{row}`` and reported unscored beside the scored rows, which keep
    French's ST_Rev.
    """
    alt = factors.assign(reversal=reversal.reindex(factors.index)).dropna()
    split = pd.Timestamp(*SUBPERIOD_SPLIT, 1) + pd.offsets.MonthEnd(0)
    rows = {}
    for pname, s in series.items():
        out = {}
        for half, part in (("full", s), ("pre", s[s.index <= split]), ("post", s[s.index > split])):
            coef = factor_regression(part, alt)
            out.update({f"{half}_{r}": float(coef[r]) for r in FACTOR_ROWS})
        rows[pname] = pd.Series(out)
    frame = pd.DataFrame(rows)
    frame.index.name = "statistic"
    frame.to_csv(out_dir / "reversal_alternative.csv")


def _reversal_alternative_section(out_dir: Path, total: list) -> list[str]:
    """The unscored comparison of the alternative regressions, with what they would score.

    Cells read "ours vs paper mark", without the scored cells' " / ", so the scorer skips them.
    The scored figure they are set against is recomputed from the scored rows' own tables.
    """
    path = out_dir / "reversal_alternative.csv"
    if not (path.exists() and (out_dir / "table4.csv").exists()
            and (out_dir / "table8_subperiod.csv").exists()):
        return []
    alt = pd.read_csv(path, index_col=0)
    t4 = pd.read_csv(out_dir / "table4.csv", index_col=0)
    t8 = pd.read_csv(out_dir / "table8_subperiod.csv", index_col=0)
    lines = ["## Reversal factor: the paper's own, as Table 8 implies it (unscored)", "",
             "The scored regressions above use French's ST_Rev, the long-short factor the paper",
             "describes. The paper built its own reversal factor, and its Table 8 regressions are",
             "consistent only with a factor whose standard deviation is near the printed 0.072",
             "before 1989 and whose correlation with the market is about +0.8: the profile of a",
             "long-only portfolio of prior-month losers, not of a long-short factor (REVIEW_NOTES",
             "section 51, `scripts/audit_reversal_factor.py`). The rows below repeat the regressions",
             "with that series, French's equal-weighted bottom three prior-month deciles less the",
             "T-bill, in place of ST_Rev. They are not scored.", ""]
    alt_marks, scored_marks = [], []
    for half, label, paper_of, ours_of in (
            ("full", "Table 4, full sample", lambda p, r: PAPER_TABLE4[p][r],
             lambda p, r: t4.loc[r, p]),
            ("pre", "Table 8, before 1989", lambda p, r: PAPER_TABLE8[p][f"pre_{r}"],
             lambda p, r: t8.loc[f"pre_{r}", p]),
            ("post", "Table 8, after 1988", lambda p, r: PAPER_TABLE8[p][f"post_{r}"],
             lambda p, r: t8.loc[f"post_{r}", p])):
        lines += [f"| {label}: ours vs paper | " + " | ".join(PORTFOLIOS) + " |",
                  "|---|" + "---|" * len(PORTFOLIOS)]
        for r in FACTOR_ROWS:
            cells = []
            for p in PORTFOLIOS:
                ours, paper = float(alt.loc[f"{half}_{r}", p]), paper_of(p, r)
                mark = _mark(ours, paper)
                alt_marks.append(mark)
                scored_marks.append(_mark(float(ours_of(p, r)), paper))
                fmt = (lambda v: f"{100 * v:.2f}%") if r == "intercept" else (lambda v: f"{v:.3g}")
                cells.append(f"{fmt(ours)} vs {fmt(paper)} {mark}")
            lines.append(f"| {r} | " + " | ".join(cells) + " |")
        lines.append("")
    def points(m):
        return m.count("✓") + 0.5 * m.count("~")
    scored_total = points(total)
    lines += [(f"With this series the {len(alt_marks)} regression cells would score "
               f"{points(alt_marks):.1f}, against {points(scored_marks):.1f} with ST_Rev, and the "
               f"total {scored_total - points(scored_marks) + points(alt_marks):.1f} instead of "
               f"{scored_total:.1f}."), ""]
    return lines


def _ibbotson_or_none() -> pd.DataFrame | None:
    """Ibbotson's four factors, or None (with a warning) while an input is unavailable."""
    try:
        return load_ibbotson_factors()[IBBOTSON_FACTORS]
    except (FileNotFoundError, ImportError, ValueError, KeyError) as err:
        print(f"warning: Ibbotson factors unavailable ({err}); Table 4's Ibbotson rows are "
              "not computed", file=sys.stderr)
        return None


def write_risk_tables(series: dict[str, pd.Series], factors: pd.DataFrame | None,
                      out_dir: Path, ibbotson: pd.DataFrame | None = None) -> None:
    """Table 4 (Sharpe ratio, both factor regressions, equity premium) and Figure 4.

    ``series`` maps each portfolio to its one-day-wait fully-invested monthly returns.
    Without ``factors`` the five-factor rows and the residual correlations are left out;
    without ``ibbotson`` the Ibbotson rows are.
    """
    t4 = {}
    for pname, s in series.items():
        row = {"sharpe": float(s.mean() / s.std(ddof=1))}
        if factors is not None:
            coef = factor_regression(s, factors)
            row.update({r: float(coef[r]) for r in FACTOR_ROWS})
            row.update({f"t_{r}": float(v) for r, v in factor_tstats(s, factors).items()})
        if ibbotson is not None:
            coef = factor_regression(s, ibbotson)
            row.update({f"ibbotson_{r}": float(coef[r])
                        for r in ("intercept", *IBBOTSON_FACTORS, "r2")})
        t4[pname] = pd.Series(row)
    frame = pd.DataFrame(t4)
    frame.index.name = "statistic"
    frame.to_csv(out_dir / "table4.csv")

    if factors is not None:
        ep = factors["market"].reindex(series["top5"].index).dropna()
        pd.Series({"mean": float(ep.mean()), "std": float(ep.std(ddof=1)),
                   "sharpe": float(ep.mean() / ep.std(ddof=1)),
                   "serial_correlation": _monthly_autocorr(ep)},
                  name="equity_premium").rename_axis("statistic").to_csv(
            out_dir / "table4_equity_premium.csv")

    both = pd.concat([series["top20"].rename("a"), series["101-120"].rename("b")], axis=1).dropna()
    split = pd.Timestamp(*SUBPERIOD_SPLIT, 1) + pd.offsets.MonthEnd(0)
    resid = None
    if factors is not None:
        resid = pd.concat([factor_residuals(both["a"], factors).rename("a"),
                           factor_residuals(both["b"], factors).rename("b")], axis=1).dropna()
    rows = {}
    for label, pick in (("correlation, full sample", lambda x: x),
                        ("correlation, before 1989", lambda x: x[x.index <= split]),
                        ("correlation, after 1988", lambda x: x[x.index > split])):
        part = pick(both)
        rows[label] = {"raw": float(part["a"].corr(part["b"]))}
        if resid is not None:
            rpart = pick(resid)
            rows[label]["residual"] = float(rpart["a"].corr(rpart["b"]))
    fig4 = pd.DataFrame(rows).T
    fig4.index.name = "statistic"
    fig4.to_csv(out_dir / "figure4.csv")


def write_outputs(
    strategy: dict,
    trading: dict,
    waits: tuple[int, ...],
    n_cohorts: int,
    out_dir: Path,
    composition: dict[str, pd.Series] | None = None,
    uni_summary: pd.Series | None = None,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    frames = []
    for wait in waits:
        for pname in PORTFOLIOS:
            for capital in T1_CAPITALS:
                s = strategy[wait][pname][capital]
                frames.append(
                    pd.DataFrame(
                        {
                            "wait": wait,
                            "portfolio": pname,
                            "capital": capital,
                            "month_end": s.index,
                            "monthly_return": s.to_numpy(),
                        }
                    )
                )
    pd.concat(frames, ignore_index=True).to_parquet(out_dir / "monthly_returns.parquet")

    if 0 in waits or 1 in waits:
        cols: dict[tuple[str, str], pd.Series] = {}
        for wait, panel in PANEL_OF_WAIT.items():
            if wait not in waits:
                continue
            for pname in PORTFOLIOS:
                employed = summary_stats(strategy[wait][pname]["employed"])
                committed = summary_stats(strategy[wait][pname]["committed"])
                row = employed.copy()
                row["committed_mean"] = committed["mean"]
                row["mean_employed_literal"] = summary_stats(
                    strategy[wait][pname]["employed_literal"]
                )["mean"]
                cols[(panel, pname)] = row
        table1 = pd.DataFrame(cols)
        table1.columns = pd.MultiIndex.from_tuples(table1.columns, names=["panel", "portfolio"])
        table1.index.name = "metric"
        table1.to_csv(out_dir / "table1.csv")

        # Table 7 (scored since 2026-10-25): the two books the fully-invested
        # return is the difference of, summarised the way the paper prints them.
        if 1 in waits:
            t7 = {}
            for pname in PORTFOLIOS:
                legs = {"long": strategy[1][pname]["long_book"],
                        "short": strategy[1][pname]["short_book"]}
                rows = {}
                for side, series in legs.items():
                    st = summary_stats(series)
                    rows[f"{side}: mean monthly return"] = st["mean"]
                    rows[f"{side}: standard error (Newey-West)"] = st["nw_se"]
                    rows[f"{side}: standard deviation"] = st["std"]
                    rows[f"{side}: monthly serial correlation"] = _monthly_autocorr(series)
                t7[pname] = pd.Series(rows)
            table7 = pd.DataFrame(t7)
            table7.index.name = "metric"
            table7.to_csv(out_dir / "table7.csv")
        else:
            (out_dir / "table7.csv").unlink(missing_ok=True)

        # Table 5 Panel A's serial correlation and percentiles, Table 8's split at
        # 1988-12 and Table 4 and Figure 4, all of the one-day-wait series. An earlier
        # run's files go first, so a run without wait 1 prints "Not run".
        for fname in DIAGNOSTIC_FILES + RISK_FILES:
            (out_dir / fname).unlink(missing_ok=True)
        if 1 in waits:
            factors = _factors_or_none()
            var_rows, sub_rows = {}, {}
            split = pd.Timestamp(*SUBPERIOD_SPLIT, 1) + pd.offsets.MonthEnd(0)
            for pname in PORTFOLIOS:
                s = strategy[1][pname]["employed"].dropna()
                var_rows[pname] = pd.Series({
                    "serial_correlation": _monthly_autocorr(s),
                    **{f"var_{q}": float(s.quantile(q / 100)) for q in (1, 5, 10, 25)},
                })
                pre, post = s[s.index <= split], s[s.index > split]
                halves = {
                    "pre_mean": float(pre.mean()), "pre_std": float(pre.std(ddof=1)),
                    "post_mean": float(post.mean()), "post_std": float(post.std(ddof=1)),
                }
                if factors is not None:
                    for half, part in (("pre", pre), ("post", post)):
                        coef = factor_regression(part, factors)
                        halves.update({f"{half}_{row}": float(coef[row]) for row in FACTOR_ROWS})
                        halves.update({f"{half}_t_{r}": float(v)
                                       for r, v in factor_tstats(part, factors).items()})
                sub_rows[pname] = pd.Series(halves)
            for fname, rows in zip(DIAGNOSTIC_FILES, (var_rows, sub_rows)):
                frame = pd.DataFrame(rows)
                frame.index.name = "statistic"
                frame.to_csv(out_dir / fname)
            employed = {p: strategy[1][p]["employed"].dropna() for p in PORTFOLIOS}
            write_risk_tables(employed, factors, out_dir, _ibbotson_or_none())
            losers = _losers_only_or_none() if factors is not None else None
            if losers is not None:
                write_reversal_alternative(employed, factors, losers, out_dir)

    if trading:
        t2 = pd.DataFrame(trading)
        t2.index.name = "statistic"
        t2.to_csv(out_dir / "table2_panelA.csv")

    if composition:
        t2b = pd.DataFrame(composition)
        t2b.index.name = "statistic"
        t2b.to_csv(out_dir / "table2_panelB.csv")

    if uni_summary is not None:
        uni = uni_summary.rename("value").to_frame()
        uni.index.name = "statistic"
        uni.to_csv(out_dir / "universe_summary.csv")

    write_comparison(strategy, trading, waits, n_cohorts, out_dir, composition, uni_summary)


def _fmt(value: float, paper: float) -> str:
    return f"{value:.5f} / {paper:.5f}" if pd.notna(value) else "NA"


def write_comparison(
    strategy: dict,
    trading: dict,
    waits: tuple[int, ...],
    n_cohorts: int,
    out_dir: Path,
    composition: dict[str, pd.Series] | None = None,
    uni_summary: pd.Series | None = None,
) -> None:
    lines = [
        "# Table 1 / Table 2: replication vs. paper",
        "",
        f"Cohorts: {n_cohorts} monthly cohorts, overlapping-averaged as in the paper.",
        "Replication values are rounded to 5 decimals (paper reports 5); the",
        "distribution rows use employed capital ('fully invested').",
        "",
    ]
    for wait, panel in PANEL_OF_WAIT.items():
        if wait not in waits:
            continue
        lines += [f"## Table 1 Panel {panel} ({'no waiting' if wait == 0 else '1-day waiting'})", ""]
        metrics = list(next(iter(PAPER_TABLE1[panel].values())).keys())
        header = "| metric | " + " | ".join(
            f"{p} (ours / paper)" for p in PORTFOLIOS
        ) + " |"
        lines += [header, "|" + "---|" * (len(PORTFOLIOS) + 1)]
        for metric in metrics:
            cells = []
            for pname in PORTFOLIOS:
                paper = PAPER_TABLE1[panel][pname][metric]
                if metric == "committed_mean":
                    ours = summary_stats(strategy[wait][pname]["committed"])["mean"]
                else:
                    ours = summary_stats(strategy[wait][pname]["employed"])[metric]
                cells.append(_fmt(ours, paper))
            lines.append(f"| {metric} | " + " | ".join(cells) + " |")
        lines.append("")
    if 0 in waits or 1 in waits:
        lines += [
            (
                "'Fully invested' = value-weighted return of the open long positions minus"
                " that of the open short positions (eq. 2); 'committed capital' scales it by"
                " the share of selected pairs holding a position."
                " `mean_employed_literal` (table1.csv only) uses INTERFACES.md's literal"
                " denominator for comparison."
            ),
            "",
        ]
    if trading:
        lines += ["## Table 2 Panel A (1-day waiting)", ""]
        stats = list(next(iter(PAPER_TABLE2A.values())).keys())
        lines.append("| statistic | " + " | ".join(f"{p} (ours / paper)" for p in trading) + " |")
        lines.append("|" + "---|" * (len(trading) + 1))
        for stat in stats:
            cells = [_fmt(trading[pname][stat], PAPER_TABLE2A[pname][stat]) for pname in trading]
            lines.append(f"| {stat} | " + " | ".join(cells) + " |")
        lines.append("")
    if composition:
        lines += [
            "## Table 2 Panel B (composition; wait-independent)",
            "",
            "Size deciles use CRSP breakpoints (NYSE + AMEX common securities, per",
            "the paper's 'using CRSP breakpoints')",
            "on the last trading day of the formation window, 1 = largest. The",
            "`_allpanel` rows (table2_panelB.csv only) use breakpoints from every",
            "panel row on that date. The paper's 'average decile difference for",
            "mixed pairs' (0.97) is below 1, the least a mean of integer gaps",
            "between mixed pairs can be, so its row here is the average over all",
            "pairs, same-decile pairs counting 0 (SCORE_LOG.md row 6); the mean",
            "over mixed pairs only is `avg_decile_diff_mixed_only`",
            "(table2_panelB.csv only), 1.67 for the top 5 (REVIEW_NOTES section 34).",
            "",
        ]
        stats = list(next(iter(PAPER_TABLE2B.values())).keys())
        header = "| statistic | " + " | ".join(f"{p} (ours / paper)" for p in composition) + " |"
        lines += [header, "|" + "---|" * (len(composition) + 1)]
        for stat in stats:
            cells = [
                _fmt(composition[pname][stat], PAPER_TABLE2B[pname][stat])
                for pname in composition
            ]
            lines.append(f"| {stat} | " + " | ".join(cells) + " |")
        lines.append("")
    if uni_summary is not None:
        lines += ["## Universe summary", ""]
        lines.append("| statistic | ours / paper |")
        lines.append("|---|---|")
        paper_notes = {
            "mean_stocks_per_cohort": "2,317 (Table 3 caption)",
            "mean_pairs_per_cohort": "2,057 (Table 9 note)",
            "mean_pairs_opened_wait1": "1,944.22 (Table 2 Panel A, all)",
        }
        for stat, paper in PAPER_UNIVERSE.items():
            ours = uni_summary[stat]
            cells = f"{ours:.2f} / {paper:.2f} ({paper_notes[stat]})" if pd.notna(ours) else (
                f"NA / {paper:.2f} ({paper_notes[stat]})"
            )
            lines.append(f"| {stat} | {cells} |")
        lines.append("")
    (out_dir / "table1_vs_paper.md").write_text("\n".join(lines))


def write_table3(table: pd.DataFrame, counts: pd.DataFrame, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    table.to_csv(out_dir / "table3.csv", index=False)
    counts.mean().to_csv(out_dir / "table3_counts.csv", header=["mean_per_cohort"])


def figure1(universe: str, out_dir: Path) -> dict:
    """GGR Figure 1 from the cached wait-0 cohort: Kennecott vs Uniroyal, Aug 1963 - Jan 1964.

    Trades are reported as 1-based (open day, close day). The position opens at
    the close of the open day and closes at the close of the close day, so the
    indicator is up from the open day to the close day.
    """
    year, month = FIGURE1["cohort"]
    a, b = FIGURE1["permnos"]
    coh = cohort_dir(universe) / f"{year:04d}-{month:02d}"
    pairs = pd.read_parquet(coh / "pairs.parquet")
    hit = pairs[(pairs["permno_1"] == a) & (pairs["permno_2"] == b)]
    if hit.empty:
        raise SystemExit(f"Figure 1 pair {a}/{b} is not formed in the {universe} {year}-{month:02d} cohort")
    rank = int(hit["rank"].iloc[0])
    trades = pd.read_parquet(coh / "w0_trades.parquet")
    trades = trades[trades["rank"] == rank].sort_values("open_day")

    form_start = month_start(*shift_month(year, month, -12))
    form_end = month_end(*shift_month(year, month, -1))
    cal = trading_calendar(month_start(year, month), month_end(*shift_month(year, month, 5)))
    panel = load_daily(form_start, cal[-1].date(), ["permno", "date", "ret"])
    panel["date"] = pd.to_datetime(panel["date"])
    rets = panel[panel["permno"].isin([a, b])].pivot(index="date", columns="permno", values="ret")
    form_prices = normalized_prices(rets.loc[: pd.Timestamp(form_end), [a, b]])
    path = (1.0 + rets.reindex(cal)[[a, b]].fillna(0.0)).cumprod() * form_prices.iloc[-1]

    spans = [(int(o) + 1, int(c) + 1) for o, c in zip(trades["open_day"], trades["close_day"])]
    is_open = pd.Series(position_indicator(len(cal), spans), index=cal)
    png = plot_pair_trading_period(
        path, is_open, FIGURE1["labels"], out_dir / "figure1.png",
        f"Figure 1 replication: pair rank {rank}, {len(spans)} trades, "
        f"day-0 levels {form_prices.iloc[-1, 0]:.3f} / {form_prices.iloc[-1, 1]:.3f}",
    )
    info = {
        "rank": rank,
        "sigma": float(hit["sigma"].iloc[0]),
        "start_levels": [round(float(v), 4) for v in form_prices.iloc[-1]],
        "trades": spans,
        "png": str(png.relative_to(ROOT)),
    }
    (out_dir / "figure1.json").write_text(json.dumps(info, indent=2) + "\n")
    return info


def _mark(ours: float, paper: float) -> str:
    if not np.isfinite(ours) or paper == 0:
        return ""
    gap = abs(ours / paper - 1)
    return "✓" if gap <= 0.10 else ("~" if gap <= 0.25 else "✗")


def _cell(ours: float, paper: float, pct: bool, tally: list, show_mark: bool = True,
          digits: int = 2) -> str:
    fmt = (lambda v: f"{100 * v:.{digits}f}%") if pct else (lambda v: f"{v:.3g}")
    mark = _mark(ours, paper)
    tally.append(mark)
    if not np.isfinite(ours):
        return f"NA / {fmt(paper)}"
    return f"{fmt(ours)} / {fmt(paper)} {mark}" if show_mark else f"{fmt(ours)} / {fmt(paper)}"


def _portfolio_table(frame: pd.DataFrame, paper_tab: dict, title: str, pct: set,
                     tally: list, show_mark: bool = True, digits: int = 2) -> list[str]:
    """A check block with one row per paper statistic and one column per portfolio."""
    lines = [f"## {title}", "", "| statistic | " + " | ".join(PORTFOLIOS) + " |",
             "|---|" + "---|" * len(PORTFOLIOS)]
    for stat in paper_tab["top5"]:
        cells = [_cell(float(frame.loc[stat, p]), paper_tab[p][stat], stat in pct, tally,
                       show_mark, digits) for p in PORTFOLIOS]
        lines.append(f"| {stat} | " + " | ".join(cells) + " |")
    return lines


def _alpha_t_rows(frame: pd.DataFrame, title: str) -> list[str]:
    """Unscored rows: the intercepts' Newey-West t-statistics, ours against the paper's.

    Written "ours vs paper", without the scored cells' " / ", so the scorer skips them.
    """
    halves = {"Table 4": [("full", "t_intercept", "full sample")],
              "Table 8": [("pre", "pre_t_intercept", "before 1989"),
                          ("post", "post_t_intercept", "after 1988")]}.get(title.split(" (")[0], [])
    rows = []
    for half, key, label in halves:
        if key not in frame.index:
            continue
        cells = [f"{float(frame.loc[key, p]):.2f} vs {PAPER_ALPHA_T[half][p]:.2f}"
                 for p in PORTFOLIOS]
        rows.append(f"| alpha t-statistic, {label} (Newey-West, 6 lags; unscored) | "
                    + " | ".join(cells) + " |")
    return rows


def _tally_line(tally: list) -> str:
    n = sum(m != "" for m in tally)
    return (f"Cells: {n}; ✓ {tally.count('✓')} (within 10%), ~ {tally.count('~')} "
            f"(within 25%), ✗ {tally.count('✗')}.")


def _score_line(marks: list) -> str:
    """The weighted total the scorer, the conformance test and SCORE_LOG.md all use."""
    n = sum(m != "" for m in marks)
    return (f"Score: {marks.count('✓') + 0.5 * marks.count('~'):.1f} of {n} compared cells "
            "(✓ = 1, ~ = ½, ✗ = 0); history in SCORE_LOG.md.")


PCT_STATS = {"mean", "nw_se", "median", "std", "min", "max", "committed_mean"}


def _short_weight_header(short_weights: str) -> tuple[list[str], list[str]]:
    """The check header's description of the eq. (3) short weight, matching the run's setting."""
    if short_weights == "position":
        portfolio = [
            "positions minus that of the short positions, each position weighted by eq. (3)",
            "applied to its own return (a long by its value, a short by prod(1 - r), which",
            "shrinks as the shorted stock rises), and committed returns scale it by the",
            "share of selected pairs holding a position (fully-invested/committed ratios",
            "1.61-2.02 against the paper's 1.58-1.81, the \"all\" column furthest off);",
        ]
        disclosure = [
            "The short-position weight is also our reading: weighting a short by the",
            "shorted stock's value instead (--short-weights value) gives SCORE_LOG.md row",
            "12. The weight is floored at zero; 780 of the 2,968,816 Table 1 positions",
            "carry zero weight after their shorted stock doubles in a day, none of them in",
            "the top 5, top 20 or 101-120 portfolios, so the floor acts on the \"all\"",
            "columns. REVIEW_NOTES section 29 gives the evidence and the objections (Table",
            "8 before 1989 and the 1999 draft).",
        ]
    else:
        portfolio = [
            "positions minus that of the short positions, each position weighted by its",
            "value since it opened (a short by the shorted stock's value), and committed",
            "returns scale it by the share of selected pairs holding a position",
            "(fully-invested/committed ratios 1.60-1.90 against the paper's 1.58-1.81);",
        ]
        disclosure = [
            "The short-position weight is also our reading: this run uses --short-weights",
            "value, SCORE_LOG.md row 12's convention; the default since row 13 weights a",
            "short by prod(1 - r), and REVIEW_NOTES section 29 compares the two.",
        ]
    return portfolio, disclosure


def _monthly_series(frame: pd.DataFrame, wait: int, portfolio: str, capital: str) -> pd.Series:
    sel = frame[(frame["wait"] == wait) & (frame["portfolio"] == portfolio)
                & (frame["capital"] == capital)]
    return pd.Series(sel["monthly_return"].to_numpy(),
                     index=pd.DatetimeIndex(sel["month_end"])).sort_index()


def _figure_comparison(out_dir: Path) -> list[str]:
    """Figures 2 and 3 against the paper, through readings of their images.

    Figures 2 and 3 are images in the published PDF, so their comparison goes through a
    reading of those images; ``scripts/digitize_figures.py`` writes the two files this
    reads. Figure 2's scale is set by its tallest bar equal to Table 1 Panel A's top-20
    maximum, and the month alignment is checked rather than assumed (the offset scan
    prints the best lag). Figure 3's log scale is read off its four decade rules, so its
    curves are levels. Figure 2 is compared on the no-wait series because its bars match
    the paper's own Table 1 Panel A row, not Panel B's (the test is printed); the one-day-
    wait series is shown beside it. Figure 4 prints its correlations in the text and is
    scored with the tables.

    No marks: a value read off an image is evidence about which periods disagree, not a
    number the paper prints. Every number in the prose is computed here, so the text
    cannot drift from the tables beside it.
    """
    ref = ROOT / "report" / "replication" / "reference"
    monthly = out_dir / "monthly_returns.parquet"
    bars_path = ref / FIGURE_FIXTURES[0]
    if not monthly.exists() or not bars_path.exists():
        return []
    frame = pd.read_parquet(monthly)
    ours = _monthly_series(frame, 0, "top20", "employed")
    if ours.empty:
        return []
    bars = pd.read_csv(bars_path)
    bars.index = pd.DatetimeIndex(pd.to_datetime(bars["month"]) + pd.offsets.MonthEnd(0))
    joined = pd.concat([ours.rename("ours"), bars[["up", "down", "signed"]]], axis=1).dropna()
    if len(joined) < 100:
        return []
    offset = _best_offset(joined)
    wait1 = _monthly_series(frame, 1, "top20", "employed").reindex(joined.index)
    digit = joined["signed"]
    vote = {"A": 0, "B": 0}
    for stat, value in (("mean", digit.mean()), ("median", digit.median()), ("std", digit.std()),
                        ("kurtosis", digit.kurt() + 3), ("min", digit.min()),
                        ("share_negative", float((digit < 0).mean()))):
        gaps = {k: abs(value / PAPER_TABLE1[k]["top20"][stat] - 1) for k in vote}
        vote[min(gaps, key=gaps.get)] += 1
    lines = [
        "## Figures 2 and 3 (read back from the paper's images, not scored)",
        "",
        ("Figures 2 and 3 are 150-dpi rasters inside the PDF. `scripts/digitize_figures.py` "
         "reads them once and"),
        ("writes `report/replication/reference/`; the numbers below are those readings "
         "against the cached"),
        ("top-20 series. Figure 2's scale is fixed so its tallest bar equals Table 1 "
         "Panel A's top-20"),
        (f"maximum ({PAPER_TABLE1['A']['top20']['max']:.3%}), and the month offset scan "
         f"below peaks at {offset:+d}. The raster carries 1.19 columns per month"),
        ("and draws each bar about three columns wide, so a bar is placed to within a "
         "month either side and"),
        ("the annual sums (one signed reading per month) are the finest comparison it "
         "supports. Figure 3"),
        "is a log scale whose decades are drawn as rules, so its curves are read as levels.",
        "",
        ("Which series Figure 2 plots: the text says \"the next-day trading rule\", but "
         "the bars themselves"),
        (f"match the paper's own no-wait top-20 row (Table 1 Panel A) on {vote['A']} of 6 "
         f"statistics and the one-day-wait row"),
        (f"(Panel B) on {vote['B']}: their mean is {digit.mean():.2%} a month against "
         f"Panel A's {PAPER_TABLE1['A']['top20']['mean']:.2%} and Panel B's "
         f"{PAPER_TABLE1['B']['top20']['mean']:.2%}."),
        ("That test uses only the paper's numbers, so the comparison below is on our no-wait "
         "series, with the"),
        "one-day-wait series beside it for reference.",
        "",
    ]
    pos, neg = joined[joined["ours"] > 0], joined[joined["ours"] < 0]
    big = joined[joined["up"] > 0.034]
    same = ((big["ours"] - big["up"]).abs() / big["up"] <= 0.15).sum()
    annual = joined.groupby(joined.index.year)[["ours", "signed"]].sum()
    annual1 = wait1.groupby(wait1.index.year).sum()
    lines += [
        "| Figure 2, monthly bars | ours, no wait | ours, one-day wait | paper, digitised |",
        "|---|---|---|---|",
        (f"| correlation of the positive bars | {pos['ours'].corr(pos['up']):.2f} "
         f"| {wait1[pos.index].corr(pos['up']):.2f} | 1 by definition ({len(pos)} months) |"),
        (f"| correlation of the negative bars | {neg['ours'].abs().corr(neg['down']):.2f} "
         f"| {wait1[neg.index].abs().corr(neg['down']):.2f} "
         f"| 1 by definition ({len(neg)} months) |"),
        (f"| **correlation of the annual sums** | **{annual['ours'].corr(annual['signed']):.2f}** "
         f"| {annual1.corr(annual['signed']):.2f} | 1 by definition ({len(annual)} years) |"),
        (f"| mean annual sum | {annual['ours'].mean():.2%} | {annual1.mean():.2%} "
         f"| {annual['signed'].mean():.2%} |"),
        (f"| best month offset, -3..+3 | {offset:+d} months | - "
         f"| the alignment that maximises the two correlations |"),
        (f"| bars above 3.4% matched within 15% in the same month | {same} of {len(big)} | - | - |"),
        (f"| tallest month | {joined['ours'].idxmax():%Y-%m} ({joined['ours'].max():.2%}) "
         f"| {wait1.idxmax():%Y-%m} ({wait1.max():.2%}) "
         f"| {joined['signed'].idxmax():%Y-%m} ({joined['signed'].max():.2%}) |"),
        (f"| deepest month | {joined['ours'].idxmin():%Y-%m} ({joined['ours'].min():.2%}) "
         f"| {wait1.idxmin():%Y-%m} ({wait1.min():.2%}) "
         f"| {joined['signed'].idxmin():%Y-%m} ({joined['signed'].min():.2%}) |"),
        "",
    ]
    lines += _figure3_comparison(frame, ref / FIGURE_FIXTURES[1])
    lines += _single_month_attribution(joined)
    lines += [("Not scored: a value recovered from a 640-pixel image is evidence about which "
               "periods disagree, not a"), "value the paper prints.", ""]
    return lines


def _figure3_comparison(frame: pd.DataFrame, curves_path: Path) -> list[str]:
    """Figure 3's two pairs curves, as levels, against our compounded top-20 series.

    The paper's text says the figure is "the top 20 one-day-waiting strategy", so the
    comparison is with Table 1 Panel B's series. A third column per curve compounds the
    paper's own Panel B mean over the same months, which tests the figure against its table.
    """
    if not curves_path.exists():
        return []
    curves = pd.read_csv(curves_path)
    curves.index = pd.DatetimeIndex(pd.to_datetime(curves["month"]) + pd.offsets.MonthEnd(0))
    split = pd.Timestamp("1987-12-31")
    table = PAPER_TABLE1["B"]["top20"]
    rows = {"end level, 2002-12": [], "level at 1987-12": [], "peak (month)": [],
            "share of the log rise made after 1987": [], "correlation of the log paths": []}
    for name, capital, mean in (("fully_invested", "employed", table["mean"]),
                                ("committed", "committed", table["committed_mean"])):
        r = _monthly_series(frame, 1, "top20", capital)
        paper = curves[name].dropna()
        if r.empty or paper.empty:
            return []
        # ours is set to the paper's level at its first read month, so the two paths
        # start together and only what happens after that month is compared
        level = (1.0 + r.fillna(0.0)).cumprod()
        level = level / level.asof(paper.index[0]) * paper.iloc[0]
        level = level[level.index >= paper.index[0]]
        logs = pd.concat([np.log(level), np.log(paper)], axis=1).dropna()
        for s in (level, paper):
            rise = np.log(s.iloc[-1] / s.iloc[0])
            rows["end level, 2002-12"].append(f"{s.iloc[-1]:.1f}")
            rows["level at 1987-12"].append(f"{s.asof(split):.1f}")
            rows["peak (month)"].append(f"{s.max():.1f} ({s.idxmax():%Y-%m})")
            rows["share of the log rise made after 1987"].append(
                f"{np.log(s.iloc[-1] / s.asof(split)) / rise:.0%}")
        # a full-sample mean says where the path ends, not how it gets there
        rows["end level, 2002-12"].append(f"{paper.iloc[0] * (1.0 + mean) ** (len(paper) - 1):.1f}")
        for label in ("level at 1987-12", "peak (month)", "share of the log rise made after 1987"):
            rows[label].append("-")
        rows["correlation of the log paths"] += [
            f"{logs.iloc[:, 0].corr(logs.iloc[:, 1]):.3f}", "1 by definition", "-"]
    start = curves["fully_invested"].first_valid_index()
    lines = [("| Figure 3, cumulative top 20, one-day wait | fully invested, ours | paper's figure "
              "| paper's Table 1 B mean, compounded | committed, ours | paper's figure "
              "| paper's Table 1 B mean, compounded |"), "|---|---|---|---|---|---|---|"]
    lines += [f"| {label} | " + " | ".join(cells) + " |" for label, cells in rows.items()]
    lines += ["", (f"The curves are read from {start:%Y-%m}, where the tracker first "
                   "separates them; ours and the compounded"),
              ("means start at the paper's level in that month. The compounded means ignore "
               "volatility drag, which"),
              ("is under a basis point a month at these standard deviations. The S&P 500, the "
               "figure's third curve,"),
              "is not read.", ""]
    return lines


def _single_month_attribution(joined: pd.DataFrame) -> list[str]:
    """How much of Table 1's top-20 shape gap one month at the paper's maximum accounts for.

    The skew, kurtosis and maximum cells of the top-20 portfolio miss together. Figure 2's
    tallest bar places the paper's maximum month to within the months its columns cover;
    this sets the month of that window where our own return is highest to the printed
    maximum, everything else left alone. A control places the same height on our own
    tallest month instead: if the control moves the cells as much, the table says how big
    the gap is, not where it sits.
    """
    if "up" not in joined or len(joined) < 100:
        return []
    ours = joined["ours"]
    top = float(joined["up"].max())
    window = joined.index[joined["up"] >= top - 1e-12]
    month = ours[window].idxmax()
    paper = PAPER_TABLE1["A"]["top20"]

    def patched(at: pd.Timestamp) -> pd.Series:
        s = ours.copy()
        s[at] = paper["max"]
        return summary_stats(s)

    base, fixed, control = summary_stats(ours), patched(month), patched(ours.idxmax())
    lines = [
        ("| Table 1 Panel A, top 20: one month at the printed maximum | ours "
         f"| {month:%Y-%m} set | control: {ours.idxmax():%Y-%m} set | paper |"),
        "|---|---|---|---|---|",
    ]
    for key, label, fmt in (("skew", "skewness", "{:.2f}"), ("kurtosis", "kurtosis", "{:.2f}"),
                            ("max", "maximum", "{:.2%}")):
        lines.append(f"| {label} | " + " | ".join(
            fmt.format(x[key]) for x in (base, fixed, control, paper)) + " |")
    lines += [
        "",
        (f"Figure 2's tallest bar covers {window[0]:%Y-%m} to {window[-1]:%Y-%m}; the raster "
         f"cannot split it further, so the"),
        (f"month set is the one of those where our return is highest ({month:%Y-%m}, "
         f"{ours[month]:.2%}). Raising it to the printed"),
        (f"maximum moves skewness from {base['skew']:.2f} to {fixed['skew']:.2f} and kurtosis "
         f"from {base['kurtosis']:.2f} to {fixed['kurtosis']:.2f} (paper"),
        (f"{paper['skew']:.2f} and {paper['kurtosis']:.2f}); the control moves them to "
         f"{control['skew']:.2f} and {control['kurtosis']:.2f}. The table measures the"),
        ("size of the top-20 shape gap - about one month at the paper's maximum - and the "
         "window says where"),
        "the paper puts that month; it does not by itself show which month ours is missing.",
        "",
    ]
    return lines


def _best_offset(joined: pd.DataFrame) -> int:
    """The month shift of the bars that maximises the two bar correlations."""
    best, best_score = 0, -np.inf
    for offset in range(-3, 4):
        shifted = joined.copy()
        shifted["up"] = joined["up"].shift(offset)
        shifted["down"] = joined["down"].shift(offset)
        pos = shifted[shifted["ours"] > 0]
        neg = shifted[shifted["ours"] < 0]
        score = pos["ours"].corr(pos["up"]) + neg["ours"].abs().corr(neg["down"])
        if np.isfinite(score) and score > best_score:
            best, best_score = offset, score
    return best


def write_replication_check(out_dir: Path, fig_dir: Path, universe: str,
                            short_weights: str) -> Path:
    """Compare Figures 1 and 4 and Tables 1-4, 5A, 7 and 8 with the paper; writes the check."""
    portfolio, disclosure = _short_weight_header(short_weights)
    lines = [
        f"# Replication check: GGR (2006) Figures 1 and 4, Tables 1-4, 5 Panel A, 7 and 8 ({universe})",
        "",
        "Cells show ours / paper. ✓ within 10% of the paper, ~ within 25%, ✗ further.",
        "",
        "Conventions that are our reading of the paper, not its words: fully invested",
        "returns are eq. (2) across the portfolio, the value-weighted return of the long",
        *portfolio,
        "trading prices continue the",
        "formation normalization (GGR Figure 1); a no-trade day is a day with recorded",
        "zero volume, a stock whose price never moves in the formation window is",
        "excluded, and so is a stock with no recorded volume and an unchanged price on",
        "more than 95% of the formation days (near-frozen quotes); a stock is never",
        "matched with another security of its own issuer (same CRSP permco, e.g. two",
        "share classes). The paper states none of these three exclusions beyond",
        "screening out stocks with a no-trade day; REVIEW_NOTES section 18 gives the",
        "evidence, and SCORE_LOG.md the score without them. Telephone utilities are",
        "SIC 4811, the 1972 telephone code that CRSP carries before 1987 (4810 and the",
        "1987 codes 4812-4819 are Industrials); the paper gives no SIC ranges, and",
        "REVIEW_NOTES section 20 gives the evidence. Waste management (SIC",
        "4950-4959) is Industrials, following GICS; S&P's contemporaneous scheme is",
        "unverified and the 1999 draft is neutral on it, so this is a classification",
        "choice worth five cells in the Utilities 101-120 band (REVIEW_NOTES section",
        "24). The trigger's sigma is the",
        "formation spread's root mean square about zero, sqrt(SSD/N), not its standard",
        "deviation about its mean; the paper says \"historical standard deviations\",",
        "and REVIEW_NOTES section 21 gives the evidence. The one-day wait skips a",
        "signal whose prices cross back on the intervening day; the paper states no",
        "such condition, and dropping it changes no mark (REVIEW_NOTES section 47).",
        "Table 1 compounds the daily difference of the long and the short book,",
        "while the paper's Table 1 = Table 7 identity implies compounding each book",
        "first; that reading scores 184.0 of 291 (REVIEW_NOTES section 33).",
        *disclosure,
        "",
        "The paper's five-factor block rests on a reversal factor it does not name: its",
        "printed statistics pin a 2.19%/month premium at 7.23% monthly volatility, and the",
        "Table 8 Panel A loadings need a reversal factor whose variance Mkt-RF/SMB/HML/UMD",
        "already explain 95% of, where French ST_Rev is 26% explained. That is implausible",
        "rather than contradictory -- PAPER_CONSISTENCY.md reports the arithmetic, the",
        "joint test and its rounding sensitivity, and `scripts/paper_consistency.py`",
        "reproduces them -- so a ✗ in those rows is a gap here as much as in the source.",
        "",
        "The score total, its history and how it is counted live in SCORE_LOG.md. The",
        "open gaps are in OPEN_QUESTIONS.md; the 1999 NBER draft is scored separately",
        "in EDITION_1999.md.",
        "",
    ]
    header_len = len(lines)
    summary = []
    marks: list = []

    fig_file = fig_dir / "figure1.json"
    lines += ["## Figure 1 (Kennecott vs Uniroyal, trading Aug 1963 - Jan 1964, no wait)", ""]
    if fig_file.exists():
        fig = json.loads(fig_file.read_text())
        ours = [tuple(t) for t in fig["trades"]]
        paper = FIGURE1["paper_trades"]
        tol = FIGURE1["day_tolerance"]
        same = len(ours) == len(paper) and all(
            abs(o[0] - p[0]) <= tol and abs(o[1] - p[1]) <= tol for o, p in zip(ours, paper)
        )
        level_ok = all(abs(v / FIGURE1["paper_start_level"] - 1) <= 0.02 for v in fig["start_levels"])
        lines += [
            "| check | ours | paper | match |",
            "|---|---|---|---|",
            f"| pair formed (rank) | {fig['rank']} | top 5 | {'✓' if fig['rank'] <= 5 else '✗'} |",
            (f"| trades (open day, close day) | {ours} | {paper} (read off the chart) "
            f"| {'✓' if same else '✗'} (±{tol} days) |"),
            (f"| day-0 levels (formation end) | {fig['start_levels']} | about "
            f"{FIGURE1['paper_start_level']:.2f} | {'✓' if level_ok else '✗'} |"),
            "",
            f"Plot: `{fig['png']}`.",
            "",
        ]
        summary.append(f"Figure 1: {'reproduced' if same and level_ok else 'not reproduced'}")
    else:
        lines += ["Not run (`--steps figure1`).", ""]

    if (out_dir / "table1.csv").exists():
        t1 = pd.read_csv(out_dir / "table1.csv", header=[0, 1], index_col=0)
        tally: list = []
        for (wait, panel), title in zip(PANEL_OF_WAIT.items(), ("no wait", "one-day wait")):
            if panel not in t1.columns.get_level_values(0):
                lines += [f"## Table 1 Panel {panel} ({title})", "",
                          f"Not run (needs `--wait {wait}`).", ""]
                continue
            lines += [f"## Table 1 Panel {panel} ({title})", "",
                      "| statistic | " + " | ".join(PORTFOLIOS) + " |",
                      "|---|" + "---|" * len(PORTFOLIOS)]
            for stat in PAPER_TABLE1[panel]["top5"]:
                cells = [_cell(float(t1[(panel, p)][stat]), PAPER_TABLE1[panel][p][stat],
                               stat in PCT_STATS, tally) for p in PORTFOLIOS]
                label = {"mean": "mean (fully invested)", "committed_mean": "mean (committed)"}
                lines.append(f"| {label.get(stat, stat)} | " + " | ".join(cells) + " |")
            lines.append("")
        lines += [_tally_line(tally), ""]
        summary.append("Table 1: " + _tally_line(tally))
        marks += tally

    for fname, paper_tab, title in (
        ("table2_panelA.csv", PAPER_TABLE2A, "Table 2 Panel A (one-day wait)"),
        ("table2_panelB.csv", PAPER_TABLE2B, "Table 2 Panel B (composition)"),
    ):
        if not (out_dir / fname).exists():
            continue
        t2 = pd.read_csv(out_dir / fname, index_col=0)
        tally = []
        lines += _portfolio_table(t2, paper_tab, title, set(), tally)
        lines += ["", _tally_line(tally), ""]
        summary.append(f"{title.split(' (')[0]}: " + _tally_line(tally))
        marks += tally

    if (out_dir / "table3.csv").exists():
        t3 = pd.read_csv(out_dir / "table3.csv").set_index(["sector", "portfolio", "capital"])
        counts = pd.read_csv(out_dir / "table3_counts.csv", index_col=0)["mean_per_cohort"]
        tally = []
        lines += ["## Table 3 stocks per cohort", "", "| sector | ours / paper |", "|---|---|"]
        for sector in SECTORS:
            lines.append(f"| {sector} | {_cell(float(counts.get(sector, np.nan)), PAPER_SECTOR_COUNTS[sector], False, tally)} |")
        lines.append("")
        for sector, ports in PAPER_TABLE3.items():
            lines += [f"## Table 3: {sector} (fully invested, one-day wait)", "",
                      "| statistic | " + " | ".join(ports) + " |", "|---|" + "---|" * len(ports)]
            for i, stat in enumerate(PAPER_TABLE3_ROWS):
                cells = []
                for p in ports:
                    key = (sector, p, "employed")
                    ours = float(t3.loc[key, stat]) if key in t3.index else np.nan
                    cells.append(_cell(ours, ports[p][i], stat in PCT_STATS, tally))
                lines.append(f"| {stat} | " + " | ".join(cells) + " |")
            lines.append("")
        lines += [_tally_line(tally), ""]
        summary.append("Table 3: " + _tally_line(tally))
        marks += tally

    base291 = list(marks)
    if (out_dir / "table7.csv").exists():
        t7 = pd.read_csv(out_dir / "table7.csv", index_col=0)
        tally = []
        title = "Table 7 (long and short books, one-day wait)"
        lines += _portfolio_table(t7, PAPER_TABLE7, title, TABLE7_PCT, tally)
        lines += ["", _tally_line(tally), ""]
        summary.append("Table 7: " + _tally_line(tally))
        marks += tally
    base323 = list(marks)

    risk_note = [
        "## Tables 4, 5 Panel A and 8 and Figure 4: conventions",
        "",
        "Tables 4, 5 Panel A and 8 and Figure 4 describe the one-day-wait series of Table 1",
        "Panel B; rows that repeat a scored row (means, standard deviations, Table 4's serial",
        "correlation, Table 5's loss probability and minimum) are left out. Percentiles are",
        "linearly interpolated (pandas' default) and serial correlation is the lag-1",
        "correlation of calendar-adjacent months; the paper states neither estimator. The",
        "regressions are OLS on French's market, SMB, HML, momentum and short-term reversal",
        "factors, and on Ibbotson's market, small-stock, default and horizon premia (Ibbotson's",
        "bond returns from Goyal and Welch's data, the small-stock series rebuilt from CRSP by",
        "its recipe; coefficients and R2 are scored, the paper's Newey-West t-statistics and factor",
        "standard deviations are not; the intercepts' t-statistics, six lags, are printed beside",
        "the paper's). Table 4's equity-premium column is French's Mkt-RF, the regressions' market",
        "factor, which Table 8 names the \"U.S. equity risk-premium\" (REVIEW_NOTES section 50).",
        "French's reversal factor is losers minus winners, the sign",
        "of the paper's printed loadings. The paper built its own reversal factor (French's",
        "dates from 2006), and Table 8 identifies it as no long-short factor: its regressions",
        "need a standard deviation near 0.072 before 1989, against ST_Rev's 0.026, and a +0.8",
        "correlation with the market. Its loadings are therefore not expected to match; the",
        "regressions with the series it resembles, prior-month losers less the bill, are",
        "reported unscored at the end (REVIEW_NOTES section 51). Marks are ratios, so they read",
        "harshly where the paper's value is near zero (a 25th percentile of +0.054%, an SMB",
        "loading of 0.001).",
        "",
    ]
    lines += risk_note
    for fname, paper_tab, title, pct, digits in (
        ("table4.csv", PAPER_TABLE4, "Table 4 (systematic risk, one-day wait)", TABLE4_PCT, 3),
        ("table5_var.csv", PAPER_TABLE5, "Table 5 Panel A (monthly value at risk)",
         {"var_1", "var_5", "var_10", "var_25"}, 3),
        ("table8_subperiod.csv", PAPER_TABLE8, "Table 8 (subperiod analysis)", TABLE8_PCT, 3),
    ):
        if not (out_dir / fname).exists():
            lines += [f"## {title}", "", "Not run (needs the one-day-wait series from the",
                      "`tables` step with `--wait 1`).", ""]
            continue
        raw = pd.read_csv(out_dir / fname, index_col=0)
        frame = raw.reindex(list(paper_tab["top5"]))
        tally = []
        lines += _portfolio_table(frame, paper_tab, title, pct, tally, digits=digits)
        lines += _alpha_t_rows(raw, title)
        if title.startswith("Table 4") and (out_dir / "table4_equity_premium.csv").exists():
            ep = pd.read_csv(out_dir / "table4_equity_premium.csv", index_col=0).iloc[:, 0]
            lines += ["", "| statistic | French's Mkt-RF (ours / paper) |", "|---|---|"]
            for stat, paper in PAPER_EQUITY_PREMIUM.items():
                lines.append(f"| equity premium: {stat} | "
                             + _cell(float(ep.get(stat, np.nan)), paper,
                                     stat in {"mean", "std"}, tally, digits=digits) + " |")
        lines += ["", _tally_line(tally), ""]
        summary.append(f"{title.split(' (')[0]}: " + _tally_line(tally))
        marks += tally
    if (out_dir / "figure4.csv").exists():
        f4 = pd.read_csv(out_dir / "figure4.csv", index_col=0)
        tally = []
        lines += ["## Figure 4 (top 20 against 101-120, correlations printed in the text)", "",
                  "| statistic | raw | five-factor residuals |", "|---|---|---|"]
        for stat, paper in PAPER_FIGURE4.items():
            cells = [_cell(float(f4.loc[stat, col]) if col in f4.columns else np.nan,
                           paper[col], False, tally) for col in ("raw", "residual")]
            lines.append(f"| {stat} | " + " | ".join(cells) + " |")
        lines += ["", _tally_line(tally), ""]
        summary.append("Figure 4: " + _tally_line(tally))
        marks += tally

    lines += _reversal_alternative_section(out_dir, marks)

    if any(marks):
        summary.append(_score_line(marks))
        for label, part, rows in (("Tables 1-3", base291, "rows 1-13"),
                                  ("Tables 1-3 and 7", base323, "row 14")):
            n = sum(m != "" for m in part)
            summary.append(f"{label} alone: {part.count('✓') + 0.5 * part.count('~'):.1f} "
                           f"of {n}, the cell set of SCORE_LOG.md {rows}.")

    fig_lines = _figure_comparison(out_dir)
    if fig_lines:
        lines += fig_lines

    lines[header_len:header_len] = ["## Summary", ""] + [f"- {s}" for s in summary] + [""]
    path = out_dir / "replication_check.md"
    path.write_text("\n".join(lines))
    return path


# --------------------------------------------------------------------------
# Building cohorts in parallel: one shard per child interpreter
# --------------------------------------------------------------------------
#
# Every parallel build -- one worker or twenty -- runs the same way: the parent
# writes each shard's jobs to a JSON file, launches it as a fresh
# ``sys.executable`` running this script with ``--build-shard``, and supervises
# the children. There is one primitive in that sentence (``subprocess``) and no
# shared state between parent and child beyond the filesystem.
#
# The alternatives this replaced are worth recording, because both looked
# simpler and both were wrong for this program:
#
# * The standard library's process pools create a POSIX semaphore in /dev/shm
#   when the pool is built, and a sandbox that mounts /dev/shm read-only refuses
#   that with ``PermissionError: [Errno 13]`` -- under fork, spawn *and*
#   forkserver alike. It is not something the process can configure away, so a
#   pool there silently degraded to the hand-rolled fallback below.
# * A hand-rolled fork does work there, but it forks a parent that already holds
#   pyarrow's thread pools (the SIC panel scan starts them) -- the deadlock
#   CPython 3.12 warns about -- needs concurrent draining of the status pipes,
#   and lets anything a child does before its ``_exit`` escape into the parent's
#   scheduling loop.
#
# A shard child cannot corrupt the parent: it is a separate process from its
# first instruction, single-threaded until it pins its own pools, and it prints
# to a log *file* rather than a pipe, so no cohort report can block on a full
# buffer. Its progress is a ``status-<cohort>.json`` written atomically after
# each cohort, so a child killed by the OOM killer is distinguishable from one
# that built its cohorts. Ctrl-C terminates the children instead of leaving them
# building behind the user's back.
#
# The status files live under the shard directory, not inside
# ``<cohort>/status.json``: the cohort cache has to stay byte-identical to what
# earlier builds produced (the reproduction check compares it file by file), so
# a build may not add a file to all 474 cohort directories.


def cohort_path(job: Job) -> Path:
    """The directory one job's cohort is cached in."""
    base = Path(job.cohorts_root) if job.cohorts_root else cohort_dir(job.universe)
    return base / f"{job.year:04d}-{job.month:02d}"


def job_to_shard(job: Job) -> dict:
    """One job as JSON-safe data (its tuples become lists for the shard file)."""
    data = asdict(job)
    data["end"] = list(data["end"])
    data["waits"] = list(data["waits"])
    return data


def job_from_shard(data: dict) -> Job:
    """The inverse of :func:`job_to_shard`."""
    return Job(**{**data, "end": tuple(data["end"]), "waits": tuple(data["waits"])})


def cohort_status_file(shard_dir: Path, job: Job) -> Path:
    """Where a shard records that it has finished one cohort."""
    return Path(shard_dir) / f"status-{job.year:04d}-{job.month:02d}.json"


def _write_json_atomically(path: Path, payload) -> Path:
    """Replace ``path`` with ``payload`` in one rename: readers see old or new."""
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, name = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
    os.close(handle)
    staged = Path(name)
    try:
        staged.write_text(json.dumps(payload) + "\n")
        os.replace(staged, path)
    except BaseException:
        staged.unlink(missing_ok=True)
        raise
    return path


def build_shard(shard_path: Path) -> int:
    """Build one shard's cohorts; exit 0 only if every one of them was built.

    This is the child half of :func:`run_jobs`, in its own interpreter: it pins
    pyarrow's thread pools for itself (the parent's settings do not cross the
    process boundary), reads its jobs from ``shard_path``, and writes a status
    file after each cohort, so the parent can tell a built cohort from one this
    process never reached.
    """
    shard_path = Path(shard_path)
    shard_dir = shard_path.parent
    pin_arrow_threads()
    jobs = [job_from_shard(data) for data in json.loads(shard_path.read_text())]
    failed = 0
    for job in jobs:
        name = f"{job.year:04d}-{job.month:02d}"
        try:
            build_cohort(job)
        except Exception:  # noqa: BLE001 - reported to the parent through the file
            failed += 1
            _write_json_atomically(cohort_status_file(shard_dir, job),
                                   {"ok": False, "cohort": name,
                                    "error": traceback.format_exc()[-4000:]})
            print(f"[{shard_path.stem}] {name} failed", flush=True)
            return 1  # stop this shard: the parent stops the others
        else:
            _write_json_atomically(cohort_status_file(shard_dir, job),
                                   {"ok": True, "cohort": name})
            print(f"[{shard_path.stem}] {name} built", flush=True)
    return 0 if failed == 0 else 1


#: Cohorts per shard file. Small shards keep the workers busy to the very end --
#: the 1963-1975 years are several times heavier than the 1990s ones -- let a
#: failure surface within a few cohorts instead of a quarter of the sample, and
#: give the parent room to stop launching new work after the first one.
SHARD_COHORTS = 12


def _shard_size(n_jobs: int, workers: int) -> int:
    """Cohorts per shard: small, and at least ~4 shards for every worker."""
    return max(1, min(SHARD_COHORTS, -(-n_jobs // (workers * 4))))


def _write_shards(shard_dir: Path, jobs: list[Job],
                  shard_size: int) -> list[tuple[Path, list[Job]]]:
    """Deal ``jobs`` into small shards, round-robin, so each spans the sample.

    Dealing them out (job 0 to shard 0, job 1 to shard 1, ...) rather than
    slicing contiguous blocks matters twice: every shard then holds every n-th
    month, so no single shard inherits all of the heavy early years, and each
    shard's cohorts are spread over the whole sample, so a failure shows up
    early instead of after half a year of work.
    """
    count = max(1, -(-len(jobs) // max(1, shard_size)))
    batches: list[list[Job]] = [[] for _ in range(count)]
    for index, job in enumerate(jobs):
        batches[index % count].append(job)
    written = []
    for index, batch in enumerate(batches):
        path = Path(shard_dir) / f"shard-{index:02d}.json"
        path.write_text(json.dumps([job_to_shard(job) for job in batch]))
        written.append((path, batch))
    return written


@dataclass
class _Shard:
    """A launched shard child, with what the parent must check when it exits."""

    path: Path
    jobs: list[Job]
    proc: subprocess.Popen
    log: Path


def _shard_command(shard_path: Path) -> list[str]:
    """The child command line: this interpreter, in shard mode, with the run's flags.

    ``subprocess._args_from_interpreter_flags()`` repeats what this process was
    started with (``-I``, ``-E``, ``-s``, ``-X utf8``, ``-W``...), so a child
    runs the parent's interpreter configuration instead of a bare one; only the
    cohort cache flag is ours to forward, because it is the one global a child
    still consults (``cohort_dir``).
    """
    command = [sys.executable, *subprocess._args_from_interpreter_flags(),
               str(Path(__file__).resolve()), "--build-shard", str(shard_path)]
    if CACHE_ROOT_OVERRIDE is not None:
        command += ["--cache-root", str(CACHE_ROOT_OVERRIDE)]
    return command


def _launch(shard_path: Path, jobs: list[Job], running: list[_Shard]) -> None:
    """Start one shard child and register it before anything else can interrupt.

    Its output goes to a log file beside the shard; the thread caps are only
    *defaults*, so an OMP_NUM_THREADS the user exported for memory reasons is
    left alone.
    """
    log = Path(shard_path).with_suffix(".log")
    env = dict(os.environ)
    for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
                "NUMEXPR_NUM_THREADS", "NUMBA_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        env.setdefault(var, "1")
    with open(log, "wb") as handle:
        proc = subprocess.Popen(_shard_command(shard_path), stdout=handle,
                                stderr=subprocess.STDOUT, env=env, cwd=str(ROOT))
    shard = _Shard(path=Path(shard_path), jobs=list(jobs), proc=proc, log=log)
    try:
        running.append(shard)
    except BaseException:  # a Ctrl-C landing between the spawn and the registration
        _stop([shard])
        raise


def _kill_hard(shard: _Shard) -> None:
    """SIGKILL a child that outlived its grace period (best effort, never raises)."""
    if shard.proc.poll() is not None:
        return
    try:
        shard.proc.kill()
    except OSError:  # it exited between poll() and kill()
        return
    try:
        shard.proc.wait(timeout=5)
    except BaseException:  # noqa: BLE001 - a second Ctrl-C during cleanup
        return


def _stop(shards: list[_Shard]) -> None:
    """Terminate the children, then kill any survivor -- even after a second Ctrl-C.

    Cleanup must not be interrupted again: the grace wait swallows a second
    KeyboardInterrupt and anything still alive is killed, so the first
    KeyboardInterrupt is the one that reaches the caller.
    """
    for shard in shards:
        if shard.proc.poll() is None:
            try:
                shard.proc.terminate()
            except OSError:  # it exited between poll() and terminate()
                continue
    for shard in shards:
        try:
            shard.proc.wait(timeout=5)
        except BaseException:  # noqa: BLE001 - the grace period, or a second Ctrl-C
            _kill_hard(shard)


def _shard_result(shard: _Shard) -> tuple[int, list[str]]:
    """How many cohorts this shard built, and one message per one it did not."""
    code = shard.proc.wait()
    rows = []
    for job in shard.jobs:
        status = cohort_status_file(shard.path.parent, job)
        try:
            rows.append((job, json.loads(status.read_text())))
        except (OSError, ValueError):
            rows.append((job, None))
    stopped_early = any(payload is not None and not payload.get("ok") for _, payload in rows)
    built = 0
    problems: list[str] = []
    for job, payload in rows:
        name = f"cohort {job.year}-{job.month:02d}"
        if payload is None:
            if stopped_early:
                problems.append(f"{name} failed: not attempted, its shard stopped at an "
                                "earlier failed cohort")
            else:
                problems.append(f"{name} failed: no status file (its shard exited "
                                f"{code}); see {shard.log}")
        elif payload.get("ok"):
            built += 1
        else:
            problems.append(f"{name} failed:\n{payload.get('error') or 'no error recorded'}")
    if not problems and code != 0:
        problems.append(f"shard {shard.path.name} exited {code} after reporting every "
                        f"cohort as built; see {shard.log}")
    return built, problems


def _shard_warnings(shard: _Shard) -> list[str]:
    """The child's own "warning:" lines, which would otherwise die with its log."""
    try:
        lines = shard.log.read_text(errors="replace").splitlines()
    except OSError:
        return []
    return [line.strip() for line in lines if line.strip().startswith("warning:")]


def run_jobs(jobs: list[Job], workers: int) -> None:
    """Build ``jobs`` in up to ``workers`` child interpreters, small shards each.

    The parent scans the processed panel for SIC fallbacks once -- the children
    then read the cache file it wrote instead of each re-reading ~8 GB -- deals
    the jobs into many small shards, and supervises: at most ``workers``
    children at a time, each printing to its own log file, and no new child
    after the first failure (a shard stops at its own first failed cohort). A
    cohort counts as built only when its status file says so and its shard
    finished: a child killed by the OOM killer, a segfault or a Ctrl-C leaves no
    status file, which is exactly the "a dead worker counts as a success" bug
    this replaces. Ctrl-C terminates the children and re-raises.
    """
    if not jobs:
        return
    workers = max(1, min(workers, len(jobs)))
    started = time.perf_counter()
    # Before the temporary dir exists: a cold scan takes a minute and no child can
    # start without the cache file it writes.
    sic_cache = sic_cache_path(jobs[0].cohorts_root)
    earliest_known_sic(cache_path=sic_cache)
    expected_cache = sic_cache if sic_cache is not None else default_cache_path()
    if not expected_cache.exists():
        print(f"warning: could not write the SIC fallback cache {expected_cache}; "
              "every shard will rescan the panel", file=sys.stderr)
    shard_dir = Path(tempfile.mkdtemp(prefix="ggr-build-"))
    pending = _write_shards(shard_dir, jobs, _shard_size(len(jobs), workers))
    total_shards = len(pending)
    running: list[_Shard] = []
    errors: list[str] = []
    warnings_seen: dict[str, int] = {}
    built = 0
    next_mark = 25
    try:
        while pending or running:
            while pending and len(running) < workers and not errors:
                path, batch = pending.pop(0)
                _launch(path, batch, running)
            if not running:
                break
            time.sleep(0.05)
            for shard in list(running):
                if shard.proc.poll() is None:
                    continue
                running.remove(shard)
                built_now, problems = _shard_result(shard)
                built += built_now
                errors.extend(problems)
                for text in _shard_warnings(shard):
                    warnings_seen[text] = warnings_seen.get(text, 0) + 1
                if built >= next_mark:
                    print(f"  built {built}/{len(jobs)} cohorts "
                          f"({time.perf_counter() - started:.0f}s)", flush=True)
                    next_mark = (built // 25 + 1) * 25
    except BaseException:
        _stop(running)
        print(f"shard logs kept in {shard_dir}", file=sys.stderr)
        raise
    for text, times in warnings_seen.items():
        suffix = f" ({times} shards)" if times > 1 else ""
        print(f"{text}{suffix}", file=sys.stderr, flush=True)
    if errors:
        print(f"shard logs kept in {shard_dir}", file=sys.stderr)
        raise RuntimeError(f"{len(errors)} cohort(s) failed; first:\n{errors[0]}")
    shutil.rmtree(shard_dir, ignore_errors=True)
    print(f"  built {built}/{len(jobs)} cohorts in "
          f"{time.perf_counter() - started:.0f}s ({total_shards} shards, "
          f"{workers} at a time)", flush=True)

def _share(text: str) -> float:
    value = float(text)
    if not 0.0 <= value <= 1.0:
        raise argparse.ArgumentTypeError(f"{text} is not a share between 0 and 1")
    return value


def _stale_share(text: str) -> float | None:
    return None if text.lower() == "none" else _share(text)


def _decile_count(text: str) -> int:
    """A size-decile count 1..10 (``evaluation.size_deciles``: 1 = largest)."""
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{text} is not a whole number of deciles") from None
    if not 1 <= value <= 10:
        raise argparse.ArgumentTypeError(f"{text} is not between 1 and 10 deciles")
    return value


def parse_month(text: str) -> tuple[int, int]:
    y, m = text.split("-")
    return int(y), int(m)


def formation_options(args: argparse.Namespace) -> dict:
    """The cache stamp's formation and engine options, each recorded with its value
    so that two builds differing in any setting never share a stamp."""
    options: dict = {"exclude_same_issuer": args.same_issuer == "exclude"}
    if args.max_stale_share is not None:
        options["max_stale_share"] = args.max_stale_share
    if args.size_deciles_top is not None:
        options["size_deciles_top"] = args.size_deciles_top
    options["telephone_sic"] = args.telephone_sic
    options["trigger_sigma"] = args.trigger_sigma
    options["short_weights"] = args.short_weights
    return options


def main_shard(args) -> int:
    """The ``--build-shard`` entry point: one child's half of :func:`run_jobs`.

    Only ``--cache-root`` is forwarded, because ``cohort_dir`` is the one global
    a child still consults (a job's own ``cohorts_root`` covers the rest); the
    other build flags describe a driver run that this child is not doing.
    """
    global CACHE_ROOT_OVERRIDE
    if args.cache_root:
        CACHE_ROOT_OVERRIDE = Path(args.cache_root).resolve()
    return build_shard(Path(args.build_shard))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", default="1963-07", help="first cohort month YYYY-MM")
    parser.add_argument("--end", default="2002-12", help="last cohort month YYYY-MM")
    parser.add_argument("--wait", default="0,1", help="comma-separated waits, e.g. 0,1")
    parser.add_argument(
        "--workers", type=int, default=None,
        help="cohorts built in parallel (default 8, capped at the CPU count); each worker "
             "holds one shard's cohorts in memory, so lower it on a host with little free "
             "memory; the cohort build is independent per cohort, so this is the main speed "
             "knob",
    )
    parser.add_argument("--limit-cohorts", type=int, default=None, help="smoke test: first K cohorts")
    parser.add_argument("--force", action="store_true", help="rebuild cached cohorts")
    parser.add_argument(
        "--universe", default=PRIMARY_UNIVERSE,
        help="formation universe variant; non-primary variants write to a subfolder",
    )
    parser.add_argument(
        "--normalization", choices=("continued", "rebased"), default="continued",
        help="trading prices continue the formation normalization (default, as in GGR "
             "Figure 1) or are rebased to 1 on the first trading day",
    )
    parser.add_argument(
        "--same-issuer", choices=("allow", "exclude"), default="exclude",
        help="exclude pairs of two securities of one issuer (same CRSP permco); default exclude",
    )
    parser.add_argument(
        "--max-stale-share", type=_stale_share, default=0.95,
        help="drop stocks with no recorded volume and an unchanged price on more than "
             "this share of the formation days; 'none' keeps them (default 0.95)",
    )
    parser.add_argument(
        "--telephone-sic", choices=("4811", "481x"), default="4811",
        help="SIC codes of telephone utilities: 4811, the 1972 code CRSP carries before "
             "1987 (default), or the older 4810-4819 map",
    )
    parser.add_argument(
        "--trigger-sigma", choices=("rms", "std"), default="rms",
        help="sigma of the 2-sigma rule: the formation spread's root mean square about "
             "zero, sqrt(SSD/N) (default), or its standard deviation about its mean",
    )
    parser.add_argument(
        "--short-weights", choices=("value", "position"), default="position",
        help="eq. (3) weight of a short position in the value-weighted books: the position's "
             "own compounded return, prod(1 - r), floored at zero (default), or the shorted "
             "stock's value since the trade opened",
    )
    parser.add_argument(
        "--size-deciles-top", type=_decile_count, default=None,
        help="form pairs only among stocks in the largest N CRSP size deciles at the "
             "formation end (Table 9 Panel A uses 3); default off (no size screen)",
    )
    parser.add_argument(
        "--aggregate-only", action="store_true",
        help="regenerate Tables 1 and 2 from the cohort cache; error if any cohort is missing",
    )
    parser.add_argument(
        "--steps", default=",".join(STEPS),
        help=f"comma-separated subset of {','.join(STEPS)}",
    )
    parser.add_argument(
        "--stride", type=int, default=1,
        help="build/aggregate every Nth cohort (deterministic samples for benchmarks)",
    )
    parser.add_argument(
        "--cache-root", default=None,
        help="redirect the cohort cache (and its stamp) to this directory",
    )
    parser.add_argument(
        "--out-root", default=None,
        help="redirect tables/figures output to this directory",
    )
    parser.add_argument(
        "--build-shard", default=None, metavar="SHARD_JSON",
        help="internal: build the cohorts of one shard file and exit (see run_jobs)",
    )
    args = parser.parse_args()
    if args.build_shard is not None:
        raise SystemExit(main_shard(args))
    if args.workers is None:
        # Eight concurrent cohorts by default, capped at the CPU count. Each
        # worker holds one shard's cohorts in memory, so a host short of free
        # memory should ask for fewer with --workers.
        args.workers = max(1, min(8, os.cpu_count() or 1))

    steps = [x.strip() for x in args.steps.split(",") if x.strip()]
    unknown = sorted(set(steps) - set(STEPS))
    if unknown:
        raise SystemExit(f"unknown steps: {unknown}; choose from {STEPS}")
    start = parse_month(args.start)
    end = parse_month(args.end)
    waits = tuple(int(w) for w in args.wait.split(","))
    continued = args.normalization == "continued"
    global CACHE_ROOT_OVERRIDE, OUT_ROOT_OVERRIDE, FORMATION_OPTIONS
    exclude_same_issuer = args.same_issuer == "exclude"
    FORMATION_OPTIONS = formation_options(args)
    cohorts_root = None
    if args.cache_root:
        CACHE_ROOT_OVERRIDE = Path(args.cache_root).resolve()
        cohorts_root = str(CACHE_ROOT_OVERRIDE / "cohorts")
    if args.out_root:
        OUT_ROOT_OVERRIDE = Path(args.out_root).resolve()
    args.cohorts_root = cohorts_root
    cohorts = cohort_months(start, end)
    if args.stride > 1:
        cohorts = cohorts[:: args.stride]
    if args.limit_cohorts is not None:
        cohorts = cohorts[: args.limit_cohorts]
    out_dir = tables_dir(args.universe)
    fig_dir = figures_dir(args.universe)

    if "tables" in steps or "table3" in steps:
        if args.aggregate_only:
            verify_cache(args.universe, continued)
            missing = [
                (y, m) for y, m in cohorts
                if not cohort_cache_complete(y, m, waits, args.universe)
            ]
            if missing:
                sample = ", ".join(f"{y}-{m:02d}" for y, m in missing[:10])
                raise SystemExit(
                    f"--aggregate-only: {len(missing)} cohorts missing from the "
                    f"{args.universe} cache (e.g. {sample}); build them first."
                )
            jobs = []
        else:
            stamp_cache(args.universe, continued, args.force)
            jobs = [
                Job(y, m, end, waits, args.universe, continued, args.cohorts_root,
                    exclude_same_issuer, args.max_stale_share, args.telephone_sic,
                    args.trigger_sigma, args.short_weights,
                    size_deciles_top=args.size_deciles_top)
                for y, m in cohorts
                if args.force or not cohort_cache_complete(y, m, waits, args.universe)
            ]
        print(
            f"universe={args.universe}: {len(cohorts)} cohorts, {len(jobs)} to build, "
            f"waits={waits}, workers={args.workers}",
            flush=True,
        )
        if jobs:
            run_jobs(jobs, args.workers)
        monthly, summaries = load_summaries(cohorts, args.universe)
        if "tables" in steps:
            strategy, trading, composition, uni_summary = aggregate(
                monthly, summaries, waits, end, cohorts)
            write_outputs(strategy, trading, waits, len(cohorts), out_dir, composition, uni_summary)
            print(f"Tables 1 and 2 written to {out_dir}", flush=True)
        if "table3" in steps:
            write_table3(*table3_from_cache(monthly, summaries, end), out_dir)
            print(f"Table 3 written to {out_dir}", flush=True)

    if "figure1" in steps:
        verify_cache(args.universe, continued)
        info = figure1(args.universe, fig_dir)
        print(f"Figure 1: rank {info['rank']}, trades {info['trades']}, saved {info['png']}")

    if "check" in steps:
        path = write_replication_check(out_dir, fig_dir, args.universe, args.short_weights)
        print(f"Replication check written to {path}")


if __name__ == "__main__":
    main()
