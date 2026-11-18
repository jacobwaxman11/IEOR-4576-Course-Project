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
        [--telephone-sic 4811|481x] [--waste-sic industrials|utilities]
        [--trigger-sigma rms|std] [--size-deciles-top N] [--long-delisting-loss]

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
import hashlib
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
    processed_source_identity,
    trading_calendar,
    universe_flags,
)
from project.evaluation import (
    PORTFOLIOS,
    QUANTILE_METHODS,
    cohort_monthly,
    composition_stats,
    overlap_average,
    portfolio_daily,
    portfolio_legs,
    portfolio_monthly,
    quantile,
    restrict_to_size_deciles,
    set_moments,
    set_nw_correction,
    set_quantile_method,
    set_sign_zero,
    share_negative,
    summary_stats,
    trading_components,
    trading_stats_from_components,
)
from project.factors import (
    FACTORS,
    IBBOTSON_FACTORS,
    factor_problem_files,
    factor_regression,
    factor_residuals,
    factor_tstats,
    load_factors,
    load_ibbotson_factors,
    load_losers_only,
    set_ibbotson_market,
    set_vintage,
    vintage,
)
from project.features import (
    demote_frozen_pairs,
    normalized_prices,
    select_pairs,
    select_pairs_within_groups,
)
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
from project.table7 import excess, monthly_autocorr, regression_rows, strategy_series

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

#: The hold-out sentence, section 1.2 (p. 800): "Using the original model, but the
#: post-1988 data, we found that over the 1999-2002 period, the excess return of the
#: fully invested portfolio of the top 20 pairs averaged 10.4% per annum, with an
#: annual standard deviation of 3.8% and a large and significant Newey-West-adjusted
#: t-statistic of 4.82." Scored on the no-wait rule, the reading REVIEW_NOTES section
#: 17 recorded before any of these cells existed; the one-day-wait reading prints
#: beside it, unscored.
PAPER_HOLDOUT = {"mean_annual": 0.104, "sd_annual": 0.038, "t_stat": 4.82}

#: Footnote 4 (p. 804): under the assumption that only a long stock returns -100% on
#: delisting, "the average monthly return on the top 20 pairs portfolio is 1.32% with
#: a standard deviation of 1.9%" (no wait). Scored from the cache built with
#: --long-delisting-loss (--delist-cache, make delist100).
PAPER_FOOTNOTE4 = {"mean": 0.0132, "std": 0.019}

#: Table 9 Panel A (p. 824), as printed: pairs formed only from stocks in the top
#: three size deciles, the one-day wait. The paper prints its skewness and kurtosis
#: rows the wrong way round against Table 1's (COVERAGE.md, "where the published
#: version contradicts itself" 1): the row labelled "Kurtosis" reads 0.02-1.77 and
#: the one labelled "Skewness" 7.01-11.67, where Table 1 prints skewness 0.3-3.3 and
#: an absolute kurtosis 7.8-25.7. These are the printed rows, and the block is scored
#: as printed; the swapped reading is printed below it as an unscored diagnostic.
PAPER_TABLE9A: dict[str, dict[str, float]] = {
    "top5": {"mean": 0.00835, "nw_se": 0.00112, "t_stat": 7.47, "median": 0.008,
             "std": 0.01904, "kurtosis": 0.02, "skew": 7.01, "min": -0.10894,
             "max": 0.10144, "share_negative": 0.32, "committed_mean": 0.00493},
    "top20": {"mean": 0.00914, "nw_se": 0.00096, "t_stat": 9.48, "median": 0.00793,
              "std": 0.01464, "kurtosis": 0.98, "skew": 8.2, "min": -0.05646,
              "max": 0.10003, "share_negative": 0.26, "committed_mean": 0.00514},
    "101-120": {"mean": 0.00728, "nw_se": 0.00075, "t_stat": 9.66, "median": 0.00614,
                "std": 0.01579, "kurtosis": 0.8, "skew": 6.46, "min": -0.03803,
                "max": 0.10642, "share_negative": 0.33, "committed_mean": 0.00462},
    "all": {"mean": 0.0069, "nw_se": 0.00064, "t_stat": 10.85, "median": 0.00508,
            "std": 0.01294, "kurtosis": 1.77, "skew": 11.67, "min": -0.0268,
            "max": 0.10478, "share_negative": 0.27, "committed_mean": 0.00401},
}

#: The row labels the paper prints for the two rows Panel A transposes.
TABLE9A_SWAP_LABELS = {"skew": "Kurtosis", "kurtosis": "Skewness"}

#: Table 9 Panel B (p. 825), as printed: the one-day-wait rule with recalls on the
#: short positions on high-volume days (volume more than one standard deviation
#: above its 18-month mean, both split-adjusted). Panel B prints its shape rows
#: the right way round -- skewness 0.15-2.82, absolute kurtosis 5.39-18.98 -- so
#: this block needs no transposition; ``share_negative`` is the printed 39% as 0.39.
PAPER_TABLE9B: dict[str, dict[str, float]] = {
    "top5": {"mean": 0.00619, "nw_se": 0.00115, "t_stat": 5.39, "median": 0.00592,
             "std": 0.02210, "skew": 0.15, "kurtosis": 5.39, "min": -0.09611,
             "max": 0.10504, "share_negative": 0.39, "committed_mean": 0.00304},
    "top20": {"mean": 0.00854, "nw_se": 0.00094, "t_stat": 9.07, "median": 0.00703,
              "std": 0.01488, "skew": 0.48, "kurtosis": 6.0, "min": -0.06594,
              "max": 0.07255, "share_negative": 0.26, "committed_mean": 0.00347},
    "101-120": {"mean": 0.00665, "nw_se": 0.00085, "t_stat": 7.81, "median": 0.00531,
                "std": 0.01505, "skew": 1.03, "kurtosis": 7.39, "min": -0.04408,
                "max": 0.10084, "share_negative": 0.34, "committed_mean": 0.00296},
    "all": {"mean": 0.00585, "nw_se": 0.00098, "t_stat": 5.95, "median": 0.00312,
            "std": 0.01555, "skew": 2.82, "kurtosis": 18.98, "min": -0.03465,
            "max": 0.14173, "share_negative": 0.37, "committed_mean": 0.00202},
}

#: The run of ``scripts/claims/table9b_recalls.py`` the section scores: the primary
#: reading, ``rearm`` -- a recalled short ends the pair and it is re-entered only
#: once a new divergence fires (the script's ``RUN_REARM``).
TABLE9B_RUN = "rearm"
#: Table 6 (pp. 818-819), as printed: the random-pair bootstrap, two panels (no
#: waiting, wait one day) x two capital measures x three statistics x four
#: portfolios, each cell the average over the 200 replications. The text layer typesets
#: this table's minus sign as the glyph "7" ("70.00137" is -0.00137), as it does
#: elsewhere; REVIEW_NOTES section 65 records that ours are our own draws.
PAPER_TABLE6: dict[str, dict[str, float]] = {
    "A|employed|mean": {"top5": -0.00137, "top20": -0.00111, "101-120": -0.00105,
                        "top120": -0.00113},
    "A|employed|std": {"top5": 0.05521, "top20": 0.02295, "101-120": 0.02264,
                       "top120": 0.012},
    "A|employed|median": {"top5": -0.00192, "top20": -0.00153, "101-120": -0.00156,
                          "top120": -0.00162},
    "A|committed|mean": {"top5": -0.00083, "top20": -0.00077, "101-120": -0.00089,
                         "top120": -0.00091},
    "A|committed|std": {"top5": 0.02635, "top20": 0.01358, "101-120": 0.01443,
                        "top120": 0.0076},
    "A|committed|median": {"top5": -0.00123, "top20": -0.001, "101-120": -0.00123,
                           "top120": -0.00122},
    "B|employed|mean": {"top5": -0.00177, "top20": -4e-05, "101-120": -0.00154,
                        "top120": -0.00156},
    "B|employed|std": {"top5": 0.05966, "top20": 0.0531, "101-120": 0.02404,
                       "top120": 0.01213},
    "B|employed|median": {"top5": -0.00241, "top20": -0.00172, "101-120": -0.00206,
                          "top120": -0.00201},
    "B|committed|mean": {"top5": -0.00103, "top20": -0.00094, "101-120": -0.00112,
                         "top120": -0.00112},
    "B|committed|std": {"top5": 0.02811, "top20": 0.01363, "101-120": 0.01449,
                        "top120": 0.00761},
    "B|committed|median": {"top5": -0.00152, "top20": -0.00118, "101-120": -0.00148,
                           "top120": -0.00139},
}

#: Table 6's four printed columns: ranks 1-5, 1-20, 101-120 and all 120 top pairs.
TABLE6_PORTS = ("top5", "top20", "101-120", "top120")
#: The printed row groups, and the one row label per scored row: the paper's panel,
#: capital block and statistic, so every row of the check keys one paper cell.
TABLE6_PANELS = {"A": "A. No waiting", "B": "B. Wait one day"}
TABLE6_BLOCKS = {"employed": "fully invested", "committed": "committed capital"}
TABLE6_STATS = {"mean": "Mean excess return", "std": "Standard deviation",
                "median": "Median"}
TABLE6_HEADER = ("| statistic | Top 5 | Top 20 | Top 100-120 | All 120 |\n"
                 "|---|---|---|---|---|")

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
# Table 5 Panel B (p. 816): the same nine statistics on the DAILY returns of the
# one-day-wait fully-invested portfolios. Its note says the rows are "Monthly and
# daily VAR percentiles of pairs trading strategies between July 1963 and December
# 2002 (474 months)" under "the rule that opens a position in a pair on the day
# following the day on which the prices of the stocks in the pair diverge by two
# historical standard deviations", and the text prints the top-five worst day
# (10.08%) and the 1% quantiles (1.24% and 0.65%). Scored since SCORE_LOG row 18;
# the cache stores the daily series since format 7.
PAPER_TABLE5B: dict[str, dict[str, float]] = {
    "top5": {"mean": 0.00033, "std": 0.00492, "serial_correlation": -0.12,
             "var_1": -0.01236, "var_5": -0.00710, "var_10": -0.00504, "var_25": -0.00239,
             "share_negative": 0.47, "min": -0.10079},
    "top20": {"mean": 0.00040, "std": 0.00296, "serial_correlation": -0.06,
              "var_1": -0.00647, "var_5": -0.00398, "var_10": -0.00293, "var_25": -0.00133,
              "share_negative": 0.44, "min": -0.06723},
    "101-120": {"mean": 0.00035, "std": 0.00277, "serial_correlation": 0.00,
                "var_1": -0.00653, "var_5": -0.00400, "var_10": -0.00288, "var_25": -0.00130,
                "share_negative": 0.45, "min": -0.01987},
    "all": {"mean": 0.00027, "std": 0.00169, "serial_correlation": 0.35,
            "var_1": -0.00327, "var_5": -0.00202, "var_10": -0.00149, "var_25": -0.00071,
            "share_negative": 0.46, "min": -0.01069},
}
TABLE5B_PCT = {"mean", "std", "var_1", "var_5", "var_10", "var_25", "min"}
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
#: The Newey-West t-statistics Table 8 prints on a row under each coefficient (p. 822),
#: per panel and coefficient, in the table's column order. Scored since SCORE_LOG row 25.
PAPER_TABLE8_T: dict[str, list[float]] = {
    "pre_intercept": [1.72, 4.41, 6.54, 4.19],
    "pre_market": [-4.29, -3.57, -3.80, -7.26],
    "pre_smb": [-3.75, -2.86, -2.86, -5.76],
    "pre_hml": [0.64, 0.73, -1.84, -1.97],
    "pre_momentum": [0.29, -0.50, -2.92, -5.01],
    "pre_reversal": [4.44, 3.62, 4.05, 7.98],
    "post_intercept": [2.12, 3.77, 3.01, -0.56],
    "post_market": [1.68, 1.81, 0.06, -2.43],
    "post_smb": [-0.10, 1.32, 0.69, -2.83],
    "post_hml": [0.61, 0.45, 0.50, -2.65],
    "post_momentum": [-0.13, -1.29, -4.17, -7.59],
    "post_reversal": [-1.76, -0.67, 0.54, 5.56],
}
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
#: The Newey-West t-statistics Table 4 prints in parentheses beside each coefficient
#: (p. 814, six lags), in the table's column order. Scored since SCORE_LOG row 25.
PAPER_TABLE4_T: dict[str, list[float]] = {
    "intercept": [3.81, 7.08, 8.66, 5.30],
    "market": [-1.03, -0.64, -1.77, -3.10],
    "smb": [-0.71, 0.02, -0.50, -1.66],
    "hml": [1.37, 1.45, -0.59, -1.82],
    "momentum": [-0.94, -2.45, -5.83, -8.50],
    "reversal": [1.50, 1.27, 2.24, 4.34],
    "ibbotson_intercept": [6.32, 9.25, 9.39, 7.77],
    "ibbotson_market": [-0.07, 0.74, 0.90, 1.98],
    "ibbotson_small_premium": [1.32, 2.22, 1.66, 1.93],
    "ibbotson_default_premium": [1.11, 1.38, 1.81, 2.82],
    "ibbotson_horizon_premium": [1.55, 1.64, 1.04, 0.77],
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
# 2026-10-25 (SCORE_LOG row 14) for the four rows the paper prints for each book, and
# since row 18 for the regression block below them: the book's own monthly return less
# the 30-day bill (the note, p. 821) on French's five factors, coefficients and R2
# scored, Newey-West t-statistics printed unscored as in Tables 4 and 8. The paper's
# own reversal factor is unidentified (REVIEW_NOTES section 51), so the reversal column
# is whichever series the driver's factor frame carries (``--reversal-factor``).
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
        # The regression block (p. 821): each book less the 30-day bill on
        # the five factors, coefficients and R2 only (the t rows follow).
        "long: intercept": 0.00103,
        "long: market": 0.37415,
        "long: smb": -0.16764,
        "long: hml": 0.48401,
        "long: momentum": -0.0543,
        "long: reversal": 0.15854,
        "long: r2": 0.39,
        "short: intercept": -0.00442,
        "short: market": 0.44075,
        "short: smb": -0.12532,
        "short: hml": 0.42661,
        "short: momentum": -0.02625,
        "short: reversal": 0.05662,
        "short: r2": 0.41,
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
        # The regression block (p. 821): each book less the 30-day bill on
        # the five factors, coefficients and R2 only (the t rows follow).
        "long: intercept": 0.00243,
        "long: market": 0.47617,
        "long: smb": -0.06506,
        "long: hml": 0.52539,
        "long: momentum": -0.04456,
        "long: reversal": 0.09601,
        "long: r2": 0.48,
        "short: intercept": -0.00521,
        "short: market": 0.50772,
        "short: smb": -0.06616,
        "short: hml": 0.48025,
        "short: momentum": 0.00361,
        "short: reversal": 0.02365,
        "short: r2": 0.49,
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
        # The regression block (p. 821): each book less the 30-day bill on
        # the five factors, coefficients and R2 only (the t rows follow).
        "long: intercept": 0.00287,
        "long: market": 0.4852,
        "long: smb": 0.0112,
        "long: hml": 0.39451,
        "long: momentum": -0.10901,
        "long: reversal": 0.17288,
        "long: r2": 0.78,
        "short: intercept": -0.00426,
        "short: market": 0.56217,
        "short: smb": 0.03453,
        "short: hml": 0.41175,
        "short: momentum": -0.00589,
        "short: reversal": 0.0783,
        "short: r2": 0.75,
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
        # The regression block (p. 821): each book less the 30-day bill on
        # the five factors, coefficients and R2 only (the t rows follow).
        "long: intercept": -0.00101,
        "long: market": 0.58571,
        "long: smb": 0.22192,
        "long: hml": 0.25732,
        "long: momentum": -0.08832,
        "long: reversal": 0.39208,
        "long: r2": 0.97,
        "short: intercept": -0.00613,
        "short: market": 0.73091,
        "short: smb": 0.29271,
        "short: hml": 0.31134,
        "short: momentum": 0.09245,
        "short: reversal": 0.19131,
        "short: r2": 0.93,
    },
}
#: Table 7's regression block: the seven rows the paper prints for each book, in its order.
TABLE7_REGRESSION_ROWS = [f"{side}: {row}" for side in ("long", "short") for row in FACTOR_ROWS]
TABLE7_PCT = {r for r in TABLE7_ROWS if not r.endswith("serial correlation")}
TABLE7_PCT |= {r for r in TABLE7_REGRESSION_ROWS if r.endswith("intercept")}
#: The Newey-West t-statistics Table 7 prints under each coefficient (six lags, p. 821).
#: Printed beside ours and not scored, the way Table 4's alpha t-statistics are.
PAPER_TABLE7_T: dict[str, dict[str, float]] = {
    "top5": {
        "long: intercept": 0.47,
        "long: market": 4.6,
        "long: smb": -1.74,
        "long: hml": 7.12,
        "long: momentum": -1.48,
        "long: reversal": 1.83,
        "short: intercept": -2.74,
        "short: market": 6.19,
        "short: smb": -2.0,
        "short: hml": 6.92,
        "short: momentum": -0.65,
        "short: reversal": 1.13,
    },
    "top20": {
        "long: intercept": 1.27,
        "long: market": 6.68,
        "long: smb": -0.8,
        "long: hml": 9.36,
        "long: momentum": -1.21,
        "long: reversal": 1.26,
        "short: intercept": -3.35,
        "short: market": 8.44,
        "short: smb": -1.22,
        "short: hml": 9.47,
        "short: momentum": 0.1,
        "short: reversal": 0.55,
    },
    "101-120": {
        "long: intercept": 2.85,
        "long: market": 10.23,
        "long: smb": 0.27,
        "long: hml": 9.76,
        "long: momentum": -3.53,
        "long: reversal": 4.33,
        "short: intercept": -4.26,
        "short: market": 9.74,
        "short: smb": 0.95,
        "short: hml": 11.54,
        "short: momentum": -0.21,
        "short: reversal": 1.9,
    },
    "all": {
        "long: intercept": -1.32,
        "long: market": 14.99,
        "long: smb": 3.45,
        "long: hml": 7.49,
        "long: momentum": -3.53,
        "long: reversal": 10.44,
        "short: intercept": -5.22,
        "short: market": 12.13,
        "short: smb": 3.15,
        "short: hml": 8.11,
        "short: momentum": 2.81,
        "short: reversal": 2.98,
    },
}
#: Table 7's four performance rows per book: the block the check prints first, in row order.
TABLE7_PAPER_PERFORMANCE = {p: {r: PAPER_TABLE7[p][r] for r in TABLE7_ROWS} for p in PORTFOLIOS}

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
#: The steps whose output reads the French and Goyal-Welch factor files: ``tables`` writes the
#: regression rows (Tables 4, 7 and 8, Figure 4) and ``check`` scores them. Neither ``table3``
#: nor ``figure1`` opens a factor file.
FACTOR_STEPS = ("tables", "check")
_SIC_FALLBACKS: tuple[pd.Series, ...] | None = None

#: ``--cohort-weights``: how the overlapping cohorts are weighted into one
#: monthly series ("equal", the shipped Jegadeesh-Titman average).
COHORT_WEIGHTS = "equal"
#: {(wait, portfolio): {cohort: weight}} when ``COHORT_WEIGHTS`` is not "equal".
_COHORT_WEIGHTS: dict | None = None

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


CACHE_FORMAT = 7
#: Format 7: each cohort also stores ``daily.parquet``, the daily fully-invested
#: series of the four one-day-wait portfolios (date, portfolio, ret), which is
#: what Table 5 Panel B summarises. It is additional output: the monthly rows
#: are unchanged, byte for byte.
T1_CAPITALS = ("committed", "employed", "committed_count", "employed_count", "employed_literal")
#: The capital convention and key under which ``aggregate`` files each portfolio's
#: daily fully-invested strategy series (the daily counterpart of "employed").
DAILY_CAPITAL = "employed_daily"
#: ``--capital-base``: the series Tables 1, 3, 4, 5 Panel A and 8 and Figure 4 read
#: as "fully invested" ("employed", the value-weighted books, shipped) and as
#: "committed" ("committed", the paper's own one-pair-in-N scaling). The readings
#: of REVIEW_NOTES sections 25, 29 and 76 name the other bases.
T1_FI = "employed"
T1_COMMITTED = "committed"
T3_FI = "employed"
#: Extra capital series a run caches when its base is not one of the shipped ones
#: (empty by default, so a default cache keeps exactly the rows it always had).
EXTRA_CAPITALS: tuple[str, ...] = ()


def read_cache_meta(universe: str) -> dict | None:
    meta = cohort_dir(universe) / "cache_meta.json"
    return json.loads(meta.read_text()) if meta.exists() else None


def _expected_meta(continued: bool) -> dict:
    return {
        "normalization": "continued" if continued else "rebased",
        "format": CACHE_FORMAT,
        # Format 6: Tables 1 and 3 compound each book before subtracting (REVIEW_NOTES 54).
        "monthly_aggregation": "books",
        # Format 7: the daily fully-invested series of the one-day-wait portfolios
        # is cached too (``daily.parquet``), for Table 5 Panel B.
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
                "short_weights", "size_deciles_top", "long_delisting_loss", "waste_sic",
                "trigger_mult", "fresh_divergence", "capital_base",
                "demote_frozen", "demote_frozen_share", "share_classes",
                "share_classes_map",
                "processed_source"):
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
    #: Footnote 4's robustness check (RFS p. 804): a delisting long leg returns -100%.
    long_delisting_loss: bool = False
    #: Sector of waste management (SIC 4950-4959): ``industrials`` or ``utilities``.
    waste_sic: str = "industrials"
    #: Entry threshold in formation sigmas (default 2.0, the paper's 2-sigma rule).
    trigger_mult: float = 2.0
    #: "Fresh divergence" reading of the entry rule (default off).
    fresh_divergence: bool = False
    #: Capital series to cache on top of the shipped ones (``--capital-base``).
    extra_capitals: tuple[str, ...] = ()
    #: Demote pairs with a frozen-quote leg from the ranking: ``none`` (shipped),
    #: ``one`` (either leg) or ``both`` (REVIEW_NOTES section 40).
    demote_frozen: str = "none"
    #: A leg counts as frozen when its quote is unchanged on more than this share
    #: of the formation window's days.
    demote_frozen_share: float = 0.90
    #: Parquet map of the permnos the wide share-class reading adds
    #: (``--share-classes wide``); None keeps the shipped share filter.
    share_classes_file: str | None = None
    #: ``--delist-last-px`` reading (REVIEW_NOTES 94): the delisting-code classes whose
    #: terminal row books the last available price instead of the delisting return.
    #: ``off`` is the shipped rule, "the delisting return, or the last available price".
    delist_last_px: str = "off"


#: CRSP ``delactiontype`` classes behind ``--delist-last-px``.
_DELIST_LAST_PX_CLASSES = {
    "merge": ("MER",),
    "nondistress": ("MER", "GEX", "GLI"),
    "all": ("MER", "GDR", "GEX", "GLI", "LOS"),
}
_DELISTED: dict[tuple[str, ...], frozenset] = {}


def _delisting_permnos(classes: tuple[str, ...]) -> frozenset:
    """Permnos whose CRSP delisting action is one of ``classes`` (cached per call set).

    Reads ``delisting.parquet`` from the WRDS API directory; only the option path uses
    it, so a default build never opens the file.
    """
    key = tuple(classes)
    if key in _DELISTED:
        return _DELISTED[key]
    from project.paths import WRDS_API_DIR

    path = WRDS_API_DIR / "delisting.parquet"
    if not path.exists():
        raise SystemExit(f"--delist-last-px needs {path}")
    frame = pd.read_parquet(path, columns=["permno", "delactiontype"])
    keep = frame["delactiontype"].isin(classes)
    _DELISTED[key] = frozenset(int(p) for p in frame.loc[keep, "permno"])
    return _DELISTED[key]


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


_SHARE_CLASS_CACHE: dict[str, pd.Index] = {}


def _share_class_permnos(path: str | None) -> pd.Index | None:
    """The permnos a wide share-class run adds to ``common`` (None: nobody)."""
    if _no_path(path):
        return None
    key = str(Path(path))
    if key not in _SHARE_CLASS_CACHE:
        frame = pd.read_parquet(key, columns=["permno"])
        _SHARE_CLASS_CACHE[key] = pd.Index(frame["permno"].to_numpy(dtype=np.int64))
    return _SHARE_CLASS_CACHE[key]


def _no_path(path: str | None) -> bool:
    """True when ``path`` names no file for this run."""
    return path is None or str(path).strip().lower() in ("", "none")


def _frozen_quote_permnos(panel: pd.DataFrame, universe: str, share: float) -> pd.Index:
    """Permnos whose formation quote is unchanged on more than ``share`` of its days.

    The same day definition the near-frozen-quote screen uses (no recorded
    volume and an unchanged price), read only over the rows that pass the
    universe's own flags, so the demotion and the screen cannot disagree about
    which days count as quote-only.
    """
    columns = ["permno", "vol_zero", "vol_pos", "ret"]
    missing = [c for c in columns if c not in panel.columns]
    if missing:
        raise SystemExit(
            f"--demote-frozen needs the formation panel's {missing}; "
            "it is read with --max-stale-share set (the default 0.95 does)"
        )
    rows = panel.loc[universe_flags(panel, universe), columns]
    stale = ~rows["vol_zero"] & ~rows["vol_pos"] & rows["ret"].fillna(0.0).eq(0.0)
    frac = stale.groupby(rows["permno"]).mean()
    return frac.index[frac > share]


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


def _daily_rows(pname: str, daily: pd.Series) -> list[dict]:
    """The cached rows of one portfolio's daily series (Table 5 Panel B).

    A day on which the portfolio holds no position is NaN in
    ``portfolio_daily``; it is skipped rather than stored, which is what the
    daily overlap average does with it anyway (it averages the cohorts trading
    that day), and it keeps the cache small.
    """
    return [
        {"date": ts, "portfolio": pname, "ret": float(v)}
        for ts, v in daily.dropna().items()
    ]


def build_cohort(job: Job) -> tuple[int, int]:
    """Build one cohort and cache everything the tables need.

    Loads the formation and trading data once, forms unrestricted and
    within-sector pairs, simulates them and writes under
    ``cohort_dir(universe)/YYYY-MM/``: ``pairs.parquet``, per wait
    ``w{wait}_trades.parquet`` and ``w{wait}_opened.parquet``, ``monthly.parquet``
    (each cohort's monthly returns for Tables 1 and 3), ``daily.parquet`` (the
    one-day-wait portfolios' daily fully-invested returns, Table 5 Panel B) and
    ``summary.json`` (Table 2 inputs, Panel B, universe and sector counts),
    written last. The daily rows are additional output: the monthly cache the
    tables read is unchanged, byte for byte.
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
        panel=form_panel, extra_permnos=_share_class_permnos(job.share_classes_file),
    )
    if job.size_deciles_top is not None:
        # Table 9 Panel A's size screen: pairs form only inside the top deciles.
        # It reads the label day, which is also read below for the sectors and
        # Table 2 Panel B inputs, so that day is loaded once, before the screen.
        universe = restrict_to_size_deciles(
            universe, row["cap"], row["exch"], row["common"], job.size_deciles_top
        )
    frozen = (
        _frozen_quote_permnos(form_panel, job.universe, job.demote_frozen_share)
        if job.demote_frozen != "none" else None
    )
    form = form_panel.loc[form_panel["permno"].isin(set(universe)), ["permno", "date", "ret"]]
    del form_panel
    prices = normalized_prices(form.pivot(index="date", columns="permno", values="ret").sort_index())
    del form
    issuers = _issuer_series() if job.exclude_same_issuer else None
    pairs = select_pairs(prices, issuers, job.trigger_sigma)
    if frozen is not None:
        pairs = demote_frozen_pairs(pairs, frozen, job.demote_frozen)

    labels = sectors_for(row["siccd"].reindex(universe).fillna(0),
                         *_sic_fallbacks(job.cohorts_root), telephone=job.telephone_sic,
                         waste=job.waste_sic)
    sector_pairs = select_pairs_within_groups(prices, labels, issuers, job.trigger_sigma)
    if frozen is not None:
        sector_pairs = pd.concat(
            [demote_frozen_pairs(g.drop(columns="group"), frozen, job.demote_frozen)
             .assign(group=label)
             for label, g in sector_pairs.groupby("group", sort=True)],
            ignore_index=True,
        )
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
    if job.delist_last_px != "off":
        # REVIEW_NOTES 94 / contract R10-A: read "using the delisting return, or the last
        # available price" (p. 804) by delisting-code class. The selected classes book a
        # zero return on their terminal row -- the last available price -- instead of
        # CRSP's delisting return; every other class keeps the shipped treatment.
        classes = _DELIST_LAST_PX_CLASSES[job.delist_last_px]
        selected = [p for p in rets.columns if p in _delisting_permnos(classes)]
        if selected:
            rets[selected] = rets[selected].where(~term[selected], 0.0)

    coh_dir = cohort_path(job)
    coh_dir.mkdir(parents=True, exist_ok=True)
    (coh_dir / "summary.json").unlink(missing_ok=True)
    pairs.to_parquet(coh_dir / "pairs.parquet")
    sigma = pairs.set_index("rank")["sigma"]
    rows: list[dict] = []
    daily_rows: list[dict] = []
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
        result = simulate_cohort(pairs, rets, term, wait=wait, start_levels=levels,
                                 long_delisting_loss=job.long_delisting_loss,
                                 trigger_mult=job.trigger_mult,
                                 fresh_divergence=job.fresh_divergence)
        result.trades.to_parquet(coh_dir / f"w{wait}_trades.parquet")
        result.opened.rename("opened").to_frame().to_parquet(coh_dir / f"w{wait}_opened.parquet")
        for pname, ranks in PORTFOLIOS.items():
            for capital in (*T1_CAPITALS, *job.extra_capitals):
                monthly = portfolio_monthly(result, ranks, capital, job.short_weights)
                rows += _monthly_rows("t1", "", wait, pname, capital, monthly)
            long_daily, short_daily = portfolio_legs(result, ranks, job.short_weights)
            for name, daily in zip(LEG_CAPITALS, (long_daily, short_daily)):
                rows += _monthly_rows("t1", "", wait, pname, name, cohort_monthly(daily))
            if wait == 1:
                summary["trading"][pname] = trading_components(
                    result, sigma, ranks, job.trigger_mult)
                # Table 5 Panel B's series: the fully-invested ("employed") daily
                # return, the long book minus the short book with a day on which no
                # pair holds a position left out (``portfolio_daily`` returns NaN,
                # ``_daily_rows`` drops it).
                daily_rows += _daily_rows(
                    pname, portfolio_daily(result, ranks, "employed", job.short_weights))
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
        result = simulate_cohort(sp, rets, term, wait=1, start_levels=levels,
                                 long_delisting_loss=job.long_delisting_loss,
                                 trigger_mult=job.trigger_mult,
                                 fresh_divergence=job.fresh_divergence)
        for pname, ranks in TABLE3_PORTFOLIOS.items():
            if ranks is not None and len(sp) < max(ranks):
                continue
            for capital in (*TABLE3_CAPITALS, *job.extra_capitals):
                monthly = portfolio_monthly(result, ranks, capital, job.short_weights)
                rows += _monthly_rows("t3", sector, 1, pname, capital, monthly)

    pd.DataFrame(rows, columns=["table", "sector", "wait", "portfolio", "capital",
                                "month_end", "ret"]).to_parquet(coh_dir / "monthly.parquet")
    pd.DataFrame(daily_rows, columns=["date", "portfolio", "ret"]).to_parquet(
        coh_dir / "daily.parquet")
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
    """``project.table7.strategy_series`` with this run's ``--cohort-weights``.

    The overlap average lives in ``project.table7``; this wrapper only picks the
    weights (equal-weighted by cohort, the shipped reading, unless
    ``--cohort-weights`` chose another; REVIEW_NOTES sections 27 and 76).
    """
    weights = _cohort_weights_for(frame) if COHORT_WEIGHTS != "equal" else None
    return strategy_series(frame, end_ts, weights)


def _cohort_weights_for(frame: pd.DataFrame) -> dict | None:
    """This frame's per-cohort weights under ``--cohort-weights``, or None."""
    if _COHORT_WEIGHTS is None or frame.empty:
        return None
    row = frame.iloc[0]
    if "table" not in frame.columns or row["table"] not in ("t1", "t3"):
        # Table 9 Panel A reads the screened side cache and Table 5 Panel B the
        # daily series; neither carries a trade log for this reading, so both
        # keep the equal-weighted average (REVIEW_NOTES section 76).
        return None
    table = _COHORT_WEIGHTS.get((int(row["wait"]), row["portfolio"]))
    return table


def cohort_weight_table(
    kind: str, cohorts: list[tuple[int, int]], universe: str, waits: tuple[int, ...],
) -> dict[tuple[int, str], dict]:
    """Per-cohort weights for the overlap average (``--cohort-weights``).

    ``selected``: the number of pairs the cohort selected for that portfolio
    (the pool size for "all", the rank count otherwise), one weight for the
    cohort's whole window. ``positions``: the number of the portfolio's pairs
    holding a position in each of its months, read from the cached one-day-wait
    trade log of the same wait -- one pooled book, the reading of the paper's
    "one of six traders" sentence. Returns {(wait, portfolio): {cohort: weight}}.

    Table 3's sector engines keep no trade log in the cache, so their monthly
    rows take the unrestricted portfolio's weights for the same wait (the one
    approximation this reading makes; REVIEW_NOTES section 76 says so).
    """
    out: dict[tuple[int, str], dict] = {}
    for year, month in cohorts:
        coh = cohort_dir(universe) / f"{year:04d}-{month:02d}"
        pool = int(json.loads((coh / "summary.json").read_text())["pairs"])
        cohort_ts = pd.Timestamp(year, month, 1) + pd.offsets.MonthEnd(0)
        for wait in waits:
            path = coh / f"w{wait}_trades.parquet"
            trades = pd.read_parquet(path) if kind == "positions" else None
            for pname, ranks in PORTFOLIOS.items():
                sel = list(ranks) if ranks is not None else list(range(1, pool + 1))
                sel = [r for r in sel if r <= pool]
                if kind == "selected":
                    weight = float(len(sel))
                else:
                    weight = _open_counts_by_month(trades, sel, cohort_ts)
                out.setdefault((wait, pname), {})[cohort_ts] = weight
    return out


def _open_counts_by_month(
    trades: pd.DataFrame, sel: list[int], cohort_ts: pd.Timestamp,
) -> pd.Series:
    """Pairs of ``sel`` holding a position on each month-end of the window."""
    months = pd.date_range(cohort_ts, periods=6, freq="ME")
    if trades is None or trades.empty:
        return pd.Series(0.0, index=months)
    part = trades[trades["rank"].isin(sel)]
    opens = pd.to_datetime(part["open_date"])
    closes = pd.to_datetime(part["close_date"])
    counts = []
    for end in months:
        start = end - pd.offsets.MonthBegin(1)
        counts.append(float(((opens <= end) & (closes >= start)).sum()))
    return pd.Series(counts, index=months, dtype=float)


def load_daily_returns(
    cohorts: list[tuple[int, int]], universe: str,
) -> dict[str, dict[pd.Timestamp, pd.Series]]:
    """Each cohort's cached daily fully-invested series, per portfolio.

    Returns ``{portfolio: {cohort first trading month: Series indexed by date}}``,
    the argument ``aggregate`` needs for the daily overlap average. Format 7
    caches ``daily.parquet`` (date, portfolio, ret) with the one-day-wait
    portfolios only; a cohort cache without it is refused by ``verify_cache``, so
    a missing file here means a hand-edited cache and is named rather than
    skipped.
    """
    out: dict[str, dict[pd.Timestamp, pd.Series]] = {p: {} for p in PORTFOLIOS}
    for year, month in cohorts:
        coh = cohort_dir(universe) / f"{year:04d}-{month:02d}"
        path = coh / "daily.parquet"
        if not path.exists():
            raise SystemExit(
                f"{path} is missing: the cache predates format {CACHE_FORMAT}; "
                "rebuild it with --force"
            )
        frame = pd.read_parquet(path)
        first = pd.Timestamp(year, month, 1)
        for pname, g in frame.groupby("portfolio", sort=True):
            out.setdefault(pname, {})[first] = pd.Series(
                g["ret"].to_numpy(), index=pd.DatetimeIndex(g["date"])
            )
    return out


def aggregate(
    monthly: pd.DataFrame, summaries: list[dict], waits: tuple[int, ...], end: tuple[int, int],
    cohorts: list[tuple[int, int]] | None = None, reversal_factor: str = "losers_only",
    daily: dict[str, dict[pd.Timestamp, pd.Series]] | None = None,
    panel_a_cohorts: str = "complete",
) -> tuple[dict, dict, dict, pd.Series]:
    """Tables 1 and 2 from cached cohort summaries, and the daily strategy series.

    Returns (strategy, trading, composition, universe): ``strategy[wait][portfolio]
    [capital]`` is the strategy's monthly return Series, ``trading[portfolio]``
    the Table 2 Panel A Series (wait 1), ``composition[portfolio]`` the Panel B
    Series and ``universe`` the stocks / pairs / pairs-opened means.

    ``daily`` (``load_daily_returns``) adds ``strategy[1][portfolio]
    [DAILY_CAPITAL]``: the same Jegadeesh-Titman overlap average one level down,
    each trading day's equal-weighted mean over the cohorts trading that day of
    the cohort's daily fully-invested return, which is Table 5 Panel B's series.
    Without it that entry is an empty Series.
    """
    end_ts = pd.Timestamp(month_end(*end))
    t1 = monthly[monthly["table"] == "t1"]
    groups = dict(tuple(t1.groupby(["wait", "portfolio", "capital"], sort=False)))
    empty = pd.Series(dtype=float, index=pd.DatetimeIndex([]))
    strategy = {
        w: {
            p: {
                c: _strategy_series(groups[(w, p, c)], end_ts) if (w, p, c) in groups else empty
                for c in (*T1_CAPITALS, *LEG_CAPITALS, *EXTRA_CAPITALS)
            }
            for p in PORTFOLIOS
        }
        for w in waits
    }
    if 1 in waits:
        # The daily series is the one-day-wait series, so it lives under wait 1.
        # ``overlap_average`` is frequency-agnostic: it buckets each cohort's
        # rows by their own timestamps, so at daily frequency it averages the
        # cohorts trading each day exactly as the monthly one averages the
        # cohorts trading each month.
        for pname in PORTFOLIOS:
            frames = (daily or {}).get(pname)
            strategy[1][pname][DAILY_CAPITAL] = (
                overlap_average(frames) if frames else empty
            )
    trading = {}
    if 1 in waits:
        labels = [f"{year:04d}-{month:02d}" for year, month in cohorts] if cohorts else None
        trading = {
            p: trading_stats_from_components(
                [s["trading"][p] for s in summaries], labels,
                completed=panel_a_cohorts == "complete")
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



def table9a_from_cache(cache_root: Path, universe: str, cohorts: list[tuple[int, int]],
                       end: tuple[int, int]) -> pd.DataFrame:
    """Table 9 Panel A's statistics from the screened (top three size deciles) cache.

    The screened universe is a second, complete cohort cache built with
    ``--size-deciles-top 3`` (Section 3.9, p. 824), so the check step can read it
    without rebuilding the main one. The statistics are ``summary_stats`` over the
    same one-day-wait series the Table 1 Panel B section uses -- ``employed`` for
    every row and the ``committed`` series for the last one -- so the two sections
    cannot drift apart.
    """
    global CACHE_ROOT_OVERRIDE
    root = Path(cache_root)
    if not (root / "cohorts").is_dir():
        raise SystemExit(
            f"Table 9 Panel A needs the screened cohort cache, and {root} has no "
            "cohorts/ directory. Build it with:\n"
            f"  python scripts/03_replicate.py --steps tables --size-deciles-top 3 "
            f"--cache-root {root} --workers 1\n"
            "or pass --table9a-cache <dir> (--table9a-cache none leaves the section out)."
        )
    saved = CACHE_ROOT_OVERRIDE
    CACHE_ROOT_OVERRIDE = root
    try:
        monthly, _summaries = load_summaries(cohorts, universe)
    finally:
        CACHE_ROOT_OVERRIDE = saved
    end_ts = pd.Timestamp(month_end(*end))
    t1 = monthly[(monthly["table"] == "t1") & (monthly["wait"] == 1)]
    columns: dict[str, pd.Series] = {}
    for pname in PORTFOLIOS:
        part = t1[t1["portfolio"] == pname]
        employed = summary_stats(
            _strategy_series(part[part["capital"] == "employed"], end_ts))
        committed = summary_stats(
            _strategy_series(part[part["capital"] == "committed"], end_ts))
        row = employed.copy()
        row["committed_mean"] = float(committed["mean"])
        columns[pname] = row
    return pd.DataFrame(columns)


def table9b_from_cache(cache_root: Path, cohorts: list[tuple[int, int]],
                       end: tuple[int, int]) -> pd.DataFrame:
    """Table 9 Panel B's statistics from the recall cache the claim script writes.

    ``scripts/claims/table9b_recalls.py run --out-root <root>`` caches one
    ``monthly.parquet`` per cohort under ``<root>/cohorts/YYYY-MM/`` with a
    ``run`` column; this reads the primary reading's rows (``rearm``) and
    aggregates them exactly as the Table 1 and Table 9 Panel A sections do --
    the overlap average (``_strategy_series``) and ``summary_stats`` -- with the
    committed series supplying the last row. The cache is a second, derived
    artifact: it is read, never written, and the main cache it was simulated from
    is the same one the rest of the check reads.
    """
    root = Path(cache_root)
    if not (root / "cohorts").is_dir():
        raise SystemExit(
            f"Table 9 Panel B needs the recall cohort cache, and {root} has no "
            "cohorts/ directory. Build it with:\n"
            "  python scripts/claims/table9b_recalls.py run --workers 8 "
            "--cache-root <shared vol_common> --out-root <dir>\n"
            "or pass --table9b-cache <dir> (--table9b-cache none leaves the section out)."
        )
    frames: list[pd.DataFrame] = []
    missing: list[str] = []
    for year, month in cohorts:
        path = root / "cohorts" / f"{year:04d}-{month:02d}" / "monthly.parquet"
        if not path.exists():
            missing.append(f"{year:04d}-{month:02d}")
            continue
        frame = pd.read_parquet(path)
        frame = frame[frame["run"] == TABLE9B_RUN]
        frame["cohort"] = pd.Timestamp(year, month, 1) + pd.offsets.MonthEnd(0)
        frames.append(frame.loc[:, ["portfolio", "capital", "month_end", "ret", "cohort"]])
    if missing:
        sample = ", ".join(missing[:6])
        raise SystemExit(
            f"Table 9 Panel B's recall cache {root} is missing {len(missing)} of "
            f"{len(cohorts)} cohorts (e.g. {sample}); rerun the build command above."
        )
    monthly = pd.concat(frames, ignore_index=True)
    end_ts = pd.Timestamp(month_end(*end))
    columns: dict[str, pd.Series] = {}
    for pname in PORTFOLIOS:
        part = monthly[monthly["portfolio"] == pname]
        employed = summary_stats(
            _strategy_series(part[part["capital"] == "employed"], end_ts))
        committed = summary_stats(
            _strategy_series(part[part["capital"] == "committed"], end_ts))
        row = employed.copy()
        row["committed_mean"] = float(committed["mean"])
        columns[pname] = row
    return pd.DataFrame(columns)


def table6_from_cache(cache_root: Path) -> pd.DataFrame:
    """Table 6's cells, averaged over replications, from the bootstrap's cohort outputs.

    ``scripts/claims/table6_random_pairs.py --mode run`` writes one ``.npz`` per cohort
    beside a stamp naming the close rule, the seed and the replication count. The
    claim's own reader aggregates them (``table6_report.collect``), so this section and
    ``report/replication/claims/TABLE6.md`` cannot drift apart. Only the primary design
    is scored: ``--close true``, each random position closed with the true trade it
    replaces (REVIEW_NOTES sections 54 and 65).
    """
    root = Path(cache_root)
    stamp = root / "run_params.json"
    if not (root / "cohorts").is_dir() or not stamp.exists():
        raise SystemExit(
            f"Table 6 needs the random-pair bootstrap's per-cohort outputs, and {root} has "
            "no cohorts/ directory with run_params.json. Build it with:\n"
            "  python scripts/claims/table6_random_pairs.py --mode run --reps 200 "
            "--committed-capital book-share "
            f"--workers 8 --out-root {root}\n"
            "or pass --table6-cache <dir> (--table6-cache none leaves the section out)."
        )
    params = json.loads(stamp.read_text())
    if params.get("close_rule") != "true":
        raise SystemExit(
            f"{root} holds a --close {params.get('close_rule')} run; the scored Table 6 is "
            "the primary reading, --close true (REVIEW_NOTES section 54)"
        )
    sys.path.insert(0, str(ROOT / "scripts" / "claims"))
    import table6_report

    stats, _diffs, _meta = table6_report.collect(root, int(params["reps"]))
    frame = pd.DataFrame(index=list(PAPER_TABLE6), columns=list(TABLE6_PORTS), dtype=float)
    for _, row in stats.iterrows():
        panel = PANEL_OF_WAIT[int(row["wait"])]
        for stat in ("mean", "std", "median"):
            frame.loc[f"{panel}|{row['capital']}|{stat}", row["portfolio"]] = float(
                row[f"rep_{stat}"])
    return frame


def delist100_from_cache(cache_root: Path, cohorts: list[tuple[int, int]],
                         end: tuple[int, int]) -> pd.Series:
    """Footnote 4's numbers from the --long-delisting-loss cache (no wait, top 20).

    The cache is a complete second cohort cache built with --long-delisting-loss
    (the extreme delisting assumption of footnote 4, p. 804); the driver reads its
    no-wait top-20 fully invested monthly series and summarises it the way the
    footnote does -- a mean and a standard deviation in percent a month.
    """
    global CACHE_ROOT_OVERRIDE
    root = Path(cache_root)
    meta_path = root / "cohorts" / "cache_meta.json"
    if not meta_path.is_file():
        raise SystemExit(
            f"Footnote 4 needs the delisting-loss cohort cache, and {root} has no "
            "cohorts/cache_meta.json. Build it with:\n"
            f"  make delist100  (python scripts/03_replicate.py --steps tables "
            f"--long-delisting-loss --cache-root {root} --workers 1)\n"
            "or pass --delist-cache <dir> (--delist-cache none leaves the cells out)."
        )
    meta = json.loads(meta_path.read_text())
    if not meta.get("long_delisting_loss"):
        raise SystemExit(
            f"{root} was not built with --long-delisting-loss (its stamp says "
            f"{meta.get('long_delisting_loss')!r}); rebuild it with make delist100."
        )
    saved = CACHE_ROOT_OVERRIDE
    CACHE_ROOT_OVERRIDE = root
    try:
        monthly, _summaries = load_summaries(cohorts, PRIMARY_UNIVERSE)
    finally:
        CACHE_ROOT_OVERRIDE = saved
    end_ts = pd.Timestamp(month_end(*end))
    t1 = monthly[(monthly["table"] == "t1") & (monthly["wait"] == 0)]
    part = t1[(t1["portfolio"] == "top20") & (t1["capital"] == "employed")]
    series = _strategy_series(part, end_ts)
    stats = summary_stats(series)
    return pd.Series({"mean": float(stats["mean"]), "std": float(stats["std"]),
                      "n_months": int(series.notna().sum())})


def _daily_autocorr(series: pd.Series) -> float:
    """Lag-1 autocorrelation over consecutive trading days (Table 5 Panel B).

    The counterpart of ``monthly_autocorr`` one frequency down: the series is
    reindexed to the exchange calendar between its first and last day, so a gap
    never pairs two days that are not trading-day neighbours. The paper states
    no estimator for Panel B's serial correlation any more than for Panel A's
    ("Serial correlation", p. 816); this is the same reading.
    """
    s = pd.Series(series).dropna().sort_index()
    if len(s) <= 2:
        return float("nan")
    cal = trading_calendar(s.index.min().date(), s.index.max().date())
    return float(s.reindex(cal).autocorr(lag=1))


DAILY_ROWS = ["mean", "std", "serial_correlation", "var_1", "var_5", "var_10", "var_25",
              "share_negative", "min"]


def _daily_risk_stats(series: pd.Series) -> pd.Series:
    """Table 5 Panel B's nine statistics for one portfolio's daily returns.

    Percentiles are linearly interpolated (pandas' default, as in Panel A);
    "share_negative" is the paper's "Probability of return below 0", the share of
    days with a strictly negative return; "min" is "Minimum historical
    observation", the worst day. All nine are on the daily series itself, so none
    of them repeats a monthly row.
    """
    s = pd.Series(series).dropna()
    if s.empty:
        return pd.Series({row: np.nan for row in DAILY_ROWS})
    return pd.Series({
        "mean": float(s.mean()),
        "std": float(s.std(ddof=1)),
        "serial_correlation": _daily_autocorr(s),
        **{f"var_{q}": quantile(s, q / 100) for q in (1, 5, 10, 25)},
        "share_negative": share_negative(s),
        "min": float(s.min()),
    }).reindex(DAILY_ROWS)


def guard_factor_inputs(steps: list[str] | tuple[str, ...], allow_missing: bool) -> None:
    """Stop before a run that would silently score a smaller cell set than 865.

    A fresh checkout carries the French and Goyal-Welch archives as Git LFS pointers, and
    every loader below treats an unreadable factor file the same way: it prints a warning and
    returns None. The tables then lose their regression rows and the check still prints a
    score -- 544 cells rather than 865 -- which reads like a result (REVIEW_NOTES section 88).
    When a step that reads the factor files is asked for, name the files and the fix and
    exit non-zero; ``--allow-missing-factors`` is the explicit way back to the old fallback.
    """
    if not set(steps) & set(FACTOR_STEPS):
        return
    problems = factor_problem_files()
    if not problems:
        return
    listing = "\n".join(f"  {path} ({why})" for path, why in problems)
    if allow_missing:
        print(f"warning: --allow-missing-factors: these files are not readable, so the rows "
              f"that need them are left out:\n{listing}", file=sys.stderr)
        return
    print("factor files are not readable, so the check would print a score over fewer than "
          f"865 cells:\n{listing}\n"
          "Fix: `git lfs pull` in this checkout, or copy the real archives over "
          "data/raw/french, data/raw/french_vintage_2005 and data/raw/goyal_welch. To run "
          "without the factor rows anyway, pass --allow-missing-factors.", file=sys.stderr)
    raise SystemExit(1)


def _factors_or_none() -> pd.DataFrame | None:
    """French's five factors, or None (with a warning) while the LFS files are not pulled."""
    try:
        return load_factors()[FACTORS]
    except (FileNotFoundError, ValueError) as err:
        print(f"warning: factor files unavailable ({err}); the regression rows of Tables 4 "
              "and 8 and Figure 4's residual correlations are not computed", file=sys.stderr)
        return None


def _risk_free_or_none() -> pd.Series | None:
    """French's 30-day bill return, or None while the factor files are not pulled.

    Table 7's note (p. 821): "The returns in the bottom half of the table are in excess of
    the 30-day Treasury bill returns", so each book's series is reduced by the same ``rf``
    column the factor files carry - one rate for the whole table, not one per book.
    """
    try:
        return load_factors()["rf"]
    except (FileNotFoundError, ValueError) as err:
        print(f"warning: factor files unavailable ({err}); Table 7's regression block is "
              "not computed", file=sys.stderr)
        return None


def _losers_only_or_none() -> pd.Series | None:
    """The losers-only reversal series for the unscored alternative, or None while unavailable."""
    try:
        return load_losers_only()
    except (FileNotFoundError, ValueError) as err:
        print(f"warning: prior-return deciles unavailable ({err}); the reversal-factor "
              "alternative is not computed", file=sys.stderr)
        return None


def load_reversal_csv(path: str | Path) -> pd.Series:
    """A reversal series from a CSV with a ``month`` and a ``reversal`` column (contract Pb).

    ``month`` is a month end (``YYYY-MM-DD`` or ``YYYYMM``); ``reversal`` is a monthly return in
    decimals. Months the file does not cover are dropped from the scored regressions by the
    frame's ``dropna``, so a candidate needs no filler rows.
    """
    frame = pd.read_csv(Path(path))
    missing = {"month", "reversal"} - set(frame.columns)
    if missing:
        raise ValueError(f"{path}: missing column(s) {sorted(missing)}")
    months = pd.to_datetime(frame["month"].astype(str).str.replace(r"(\d{6})$", r"\1", regex=True))
    return pd.Series(frame["reversal"].to_numpy(dtype=float),
                     index=months + pd.offsets.MonthEnd(0),
                     name="reversal").sort_index().dropna()


#: The series ``--reversal-factor csv`` scores, set from ``--reversal-csv`` in ``main``.
REVERSAL_CSV: str | None = None


def _reversal_names(reversal_factor: str) -> tuple[str, str]:
    """(name of the unscored series, name of the scored series) for the ablation blocks."""
    if reversal_factor == "losers_only":
        return "French's ST_Rev", "the losers-only series"
    if reversal_factor == "csv":
        return "the losers-only series", "the candidate series"
    return "the losers-only series", "ST_Rev"


def scored_factors_or_none(reversal_factor: str,
                           reversal_csv: str | None = None
                           ) -> tuple[pd.DataFrame | None, pd.Series | None]:
    """The scored five-factor frame and the other reversal series (the unscored block).

    ``losers_only`` (the default) scores the series the paper's own Table 8 regressions imply
    (``load_losers_only``, REVIEW_NOTES section 61) and leaves French's ST_Rev to the unscored
    alternative; ``st_rev`` is the row-18 convention, with the roles swapped; ``csv`` scores the
    series in ``reversal_csv`` (contract Pb's candidates, REVIEW_NOTES section 73) and prints the
    losers-only series unscored beside it.
    """
    factors = _factors_or_none()
    if factors is None:
        return None, None
    other = _losers_only_or_none()
    if other is None:
        return factors, None
    if reversal_factor == "csv":
        path = reversal_csv or REVERSAL_CSV
        if not path:
            raise ValueError("--reversal-factor csv needs --reversal-csv PATH")
        series = load_reversal_csv(path)
        scored = factors.assign(reversal=series.reindex(factors.index)).dropna()
        return scored, other
    if reversal_factor == "losers_only":
        scored = factors.assign(reversal=other.reindex(factors.index)).dropna()
        return scored, factors["reversal"]
    return factors, other


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
            tstat = factor_tstats(part, alt)
            out.update({f"{half}_{r}": float(coef[r]) for r in FACTOR_ROWS})
            out.update({f"{half}_t_{r}": float(tstat[r]) for r in FACTOR_ROWS if r != "r2"})
        rows[pname] = pd.Series(out)
    frame = pd.DataFrame(rows)
    frame.index.name = "statistic"
    frame.to_csv(out_dir / "reversal_alternative.csv")


def _reversal_alternative_section(out_dir: Path, total: list,
                                  reversal_factor: str = "losers_only") -> list[str]:
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
    if reversal_factor == "losers_only":
        lines = ["## Reversal factor: French's ST_Rev, the text's long-short factor (unscored)", "",
                 "The scored regressions above use the losers-only series the paper's own Table 8",
                 "arithmetic implies, not the long-short factor its text describes: the printed",
                 "reversal standard deviation is 0.0723 before 1989, which ST_Rev (0.0259) cannot",
                 "be, while the equal-weighted bottom three prior-month deciles less the T-bill",
                 "give 0.0685 with the implied +0.81 market and +0.79 SMB correlations (REVIEW_NOTES",
                 "sections 51 and 61). The rows below repeat the regressions with ST_Rev in place",
                 "of the scored series. They are not scored.", ""]
        scored_name = "the losers-only series"
    elif reversal_factor == "csv":
        lines = ["## Reversal factor: the losers-only series (unscored)", "",
                 "The scored regressions above use the candidate series named in the header",
                 "(`--reversal-csv`, contract Pb, REVIEW_NOTES section 73). The rows below repeat",
                 "the regressions with the losers-only series, the equal-weighted bottom three",
                 "prior-month deciles less the T-bill, in its place. They are not scored.", ""]
        scored_name = "the candidate series"
    else:
        lines = ["## Reversal factor: the paper's own, as Table 8 implies it (unscored)", "",
                 "The scored regressions above use French's ST_Rev, the long-short factor the paper",
                 "describes. The paper built its own reversal factor, and its Table 8 regressions are",
                 "consistent only with a factor whose standard deviation is near the printed 0.072",
                 "before 1989 and whose correlation with the market is about +0.8: the profile of a",
                 "long-only portfolio of prior-month losers, not of a long-short factor (REVIEW_NOTES",
                 "section 51, `scripts/audit_reversal_factor.py`). The rows below repeat the",
                 "regressions with that series, French's equal-weighted bottom three prior-month",
                 "deciles less the T-bill, in place of ST_Rev. They are not scored.", ""]
        scored_name = "ST_Rev"
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
            scored_key = f"t_{r}" if half == "full" else f"{half}_t_{r}"
            scored_frame = t4 if half == "full" else t8
            if r == "r2" or f"{half}_t_{r}" not in alt.index \
                    or scored_key not in scored_frame.index:
                continue
            t_cells = []
            for p in PORTFOLIOS:
                i = list(PORTFOLIOS).index(p)
                paper_t = (PAPER_TABLE4_T[r][i] if half == "full"
                           else PAPER_TABLE8_T[f"{half}_{r}"][i])
                ours_t = float(alt.loc[f"{half}_t_{r}", p])
                scored_t = (float(t4.loc[f"t_{r}", p]) if half == "full"
                            else float(t8.loc[f"{half}_t_{r}", p]))
                mark = _mark(ours_t, paper_t)
                alt_marks.append(mark)
                scored_marks.append(_mark(scored_t, paper_t))
                t_cells.append(f"{ours_t:.2f} vs {paper_t:.2f} {mark}")
            lines.append(f"| t: {r} | " + " | ".join(t_cells) + " |")
        lines.append("")
    def points(m):
        return m.count("✓") + 0.5 * m.count("~")
    scored_total = points(total)
    lines += [(f"With this series the {len(alt_marks)} regression cells would score "
               f"{points(alt_marks):.1f}, against {points(scored_marks):.1f} with {scored_name}, "
               f"and the "
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
            row.update({f"ibbotson_t_{r}": float(v)
                        for r, v in factor_tstats(s, ibbotson).items()})
        t4[pname] = pd.Series(row)
    frame = pd.DataFrame(t4)
    frame.index.name = "statistic"
    frame.to_csv(out_dir / "table4.csv")

    if factors is not None:
        ep = factors["market"].reindex(series["top5"].index).dropna()
        pd.Series({"mean": float(ep.mean()), "std": float(ep.std(ddof=1)),
                   "sharpe": float(ep.mean() / ep.std(ddof=1)),
                   "serial_correlation": monthly_autocorr(ep)},
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

    if factors is not None:
        # Table 8's published "Factor sd" column, for comparison with the same factor
        # frame the regressions use (the option's reversal series included). The windows
        # are the scored series' own months, so the standard deviations are measured
        # over exactly the months Table 8's two panels regress.
        window = series["top20"].index
        frame = factors.reindex(window)
        sd_rows = {}
        for name in FACTORS:
            s = frame[name].dropna()
            sd_rows[name] = {
                "pre": float(s[s.index <= split].std(ddof=1)),
                "post": float(s[s.index > split].std(ddof=1)),
            }
        sd_frame = pd.DataFrame(sd_rows).T
        sd_frame.index.name = "factor"
        sd_frame.to_csv(out_dir / "table8_factor_sd.csv")


def write_outputs(
    strategy: dict,
    trading: dict,
    waits: tuple[int, ...],
    n_cohorts: int,
    out_dir: Path,
    composition: dict[str, pd.Series] | None = None,
    uni_summary: pd.Series | None = None,
    reversal_factor: str = "losers_only",
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    frames = []
    for wait in waits:
        for pname in PORTFOLIOS:
            for capital in (*T1_CAPITALS, *EXTRA_CAPITALS):
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
                employed = summary_stats(strategy[wait][pname][T1_FI])
                committed = summary_stats(strategy[wait][pname][T1_COMMITTED])
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

        # Table 7 (scored since 2026-10-25, its regression block since row 18): the two
        # books the fully-invested return is the difference of, summarised the way the
        # paper prints them - four performance rows and, below them, the five-factor
        # regression of each book's own return less the 30-day bill (the note, p. 821).
        # The factors are the frame Table 4 uses (`scored_factors_or_none`, the option's
        # reversal series), so the two tables cannot disagree about the factor model; the
        # other reversal series is regressed the same way and written beside it, unscored.
        factors, alt_reversal = (
            scored_factors_or_none(reversal_factor) if 1 in waits else (None, None))
        bill = _risk_free_or_none() if factors is not None else None
        alt_factors = (
            factors.assign(reversal=alt_reversal.reindex(factors.index)).dropna()
            if factors is not None and alt_reversal is not None else None
        )
        if 1 in waits:
            t7, t7_alt = {}, {}
            for pname in PORTFOLIOS:
                legs = {"long": strategy[1][pname]["long_book"],
                        "short": strategy[1][pname]["short_book"]}
                rows, alt_rows = {}, {}
                for side, series in legs.items():
                    st = summary_stats(series)
                    rows[f"{side}: mean monthly return"] = st["mean"]
                    rows[f"{side}: standard error (Newey-West)"] = st["nw_se"]
                    rows[f"{side}: standard deviation"] = st["std"]
                    rows[f"{side}: monthly serial correlation"] = monthly_autocorr(series)
                    if bill is None:
                        continue
                    book = regression_rows(excess(series, bill), factors)
                    rows.update({f"{side}: {key}": float(book[key]) for key in FACTOR_ROWS})
                    rows.update({f"{side}: t_{key}": float(book[f"t_{key}"])
                                 for key in FACTOR_ROWS if key != "r2"})
                    if alt_factors is not None:
                        alt = regression_rows(excess(series, bill), alt_factors)
                        alt_rows.update({f"{side}: {key}": float(alt[key])
                                         for key in FACTOR_ROWS})
                        alt_rows.update({f"{side}: t_{key}": float(alt[f"t_{key}"])
                                         for key in FACTOR_ROWS if key != "r2"})
                t7[pname] = pd.Series(rows)
                if alt_rows:
                    t7_alt[pname] = pd.Series(alt_rows)
            table7 = pd.DataFrame(t7)
            table7.index.name = "metric"
            table7.to_csv(out_dir / "table7.csv")
            if t7_alt:
                alt_table7 = pd.DataFrame(t7_alt)
                alt_table7.index.name = "metric"
                alt_table7.to_csv(out_dir / "table7_reversal_alternative.csv")
            else:
                (out_dir / "table7_reversal_alternative.csv").unlink(missing_ok=True)
        else:
            (out_dir / "table7.csv").unlink(missing_ok=True)
            (out_dir / "table7_reversal_alternative.csv").unlink(missing_ok=True)

        # Table 5 Panel A's serial correlation and percentiles, Table 8's split at
        # 1988-12 and Table 4 and Figure 4, all of the one-day-wait series. An earlier
        # run's files go first, so a run without wait 1 prints "Not run".
        for fname in (*DIAGNOSTIC_FILES, "table5b_daily.csv", *RISK_FILES):
            (out_dir / fname).unlink(missing_ok=True)
        if 1 in waits:
            var_rows, sub_rows = {}, {}
            split = pd.Timestamp(*SUBPERIOD_SPLIT, 1) + pd.offsets.MonthEnd(0)
            for pname in PORTFOLIOS:
                s = strategy[1][pname][T1_FI].dropna()
                var_rows[pname] = pd.Series({
                    "serial_correlation": monthly_autocorr(s),
                    **{f"var_{q}": quantile(s, q / 100) for q in (1, 5, 10, 25)},
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
            employed = {p: strategy[1][p][T1_FI].dropna() for p in PORTFOLIOS}
            # Table 5 Panel B: the same nine statistics on the daily series the
            # cache stores since format 7 (REVIEW_NOTES section 62).
            panel_b = pd.DataFrame(
                {p: _daily_risk_stats(strategy[1][p][DAILY_CAPITAL]) for p in PORTFOLIOS}
            ).reindex(DAILY_ROWS)
            panel_b.index.name = "statistic"
            panel_b.to_csv(out_dir / "table5b_daily.csv")
            write_risk_tables(employed, factors, out_dir, _ibbotson_or_none())
            if alt_reversal is not None:
                write_reversal_alternative(employed, factors, alt_reversal, out_dir)

    if trading:
        t2 = pd.DataFrame(trading)
        t2.index.name = "statistic"
        t2.to_csv(out_dir / "table2_panelA.csv")

    if composition:
        t2b = pd.DataFrame(composition)
        t2b.index.name = "statistic"
        t2b.to_csv(out_dir / "table2_panelB.csv")

    # Section 1.2's hold-out sentence: the top 20 portfolio, fully invested, over
    # 1999-2002. The no-wait series is the scored reading and the one-day-wait series
    # prints beside it, unscored; both are written so the check step reads them rather
    # than recomputing the aggregation.
    hold = {}
    for wait in waits:
        s = strategy[wait]["top20"][T1_FI].dropna()
        part = s[(s.index >= pd.Timestamp("1999-01-31"))
                 & (s.index <= pd.Timestamp("2002-12-31"))]
        st = summary_stats(part)
        hold[f"wait{wait}"] = {
            "mean_annual": 12.0 * float(st["mean"]),
            "sd_annual": float(np.sqrt(12.0) * st["std"]),
            "t_stat": float(st["t_stat"]),
            "n_months": int(part.size),
        }
    pd.DataFrame(hold).T.rename_axis("reading").to_csv(out_dir / "holdout_1999.csv")

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
                    ours = summary_stats(strategy[wait][pname][T1_FI])[metric]
                cells.append(_fmt(ours, paper))
            lines.append(f"| {metric} | " + " | ".join(cells) + " |")
        lines.append("")
    if 0 in waits or 1 in waits:
        lines += [
            (
                "'Fully invested' = value-weighted return of the open long positions minus"
                " that of the open short positions (eq. 2); 'committed capital' scales it by"
                " the share of selected pairs holding a position."
                " `mean_employed_literal` (table1.csv only) uses METHOD.md's literal"
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
            "panel row on that date. 'Average decile difference for mixed pairs'",
            "is the mean gap over pairs whose stocks sit in different deciles, as",
            "the paper defines it (p. 809). Such a mean cannot be below 1, so the",
            "printed 0.97 is a reported gap; the all-pairs average is",
            "`avg_decile_diff_all_pairs` (table2_panelB.csv only; REVIEW_NOTES",
            "sections 34 and 54).",
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
          digits: int = 2, sig: int = 3, fmt_spec: str | None = None) -> str:
    fmt = (lambda v: f"{100 * v:.{digits}f}%") if pct else (lambda v: f"{v:.{sig}g}")
    if fmt_spec is not None:
        fmt = lambda v, s=fmt_spec: format(v, s)
    mark = _mark(ours, paper)
    if not mark and paper == 0 and np.isfinite(ours):
        # A printed zero: _mark's relative gap is undefined at a target of exactly
        # zero, so the cell asks whether ours prints the same value at the paper's
        # own precision. Table 5 Panel B's 101-120 serial correlation is the one
        # such value in the check ("0.00", p. 816; REVIEW_NOTES section 62).
        mark = "✓" if fmt(ours) == fmt(paper) else "✗"
    tally.append(mark)
    if not np.isfinite(ours):
        return f"NA / {fmt(paper)}"
    return f"{fmt(ours)} / {fmt(paper)} {mark}" if show_mark else f"{fmt(ours)} / {fmt(paper)}"


def _portfolio_table(frame: pd.DataFrame, paper_tab: dict, title: str, pct: set,
                     tally: list, show_mark: bool = True, digits: int = 2,
                     spec: dict[str, str] | None = None) -> list[str]:
    """A check block with one row per paper statistic and one column per portfolio.

    ``spec`` overrides the number format of named rows (``{"serial_correlation":
    ".2f"}``); the default is the block's own percentage or three-significant-digit
    format, so every other block is unaffected.
    """
    spec = spec or {}
    lines = [f"## {title}", "", "| statistic | " + " | ".join(PORTFOLIOS) + " |",
             "|---|" + "---|" * len(PORTFOLIOS)]
    for stat in paper_tab["top5"]:
        cells = [_cell(float(frame.loc[stat, p]), paper_tab[p][stat], stat in pct, tally,
                       show_mark, digits, fmt_spec=spec.get(stat)) for p in PORTFOLIOS]
        lines.append(f"| {stat} | " + " | ".join(cells) + " |")
    return lines


def _t_key(stat: str) -> str:
    """The frame's t-statistic row for a coefficient row of Tables 4, 7 or 8."""
    if stat.startswith("ibbotson_"):
        return "ibbotson_t_" + stat[len("ibbotson_"):]
    if stat.startswith(("pre_", "post_")):
        half, name = stat.split("_", 1)
        return f"{half}_t_{name}"
    return "t_" + stat


def _coefficient_table(frame: pd.DataFrame, paper_tab: dict, paper_t: dict, title: str,
                       pct: set, tally: list, digits: int = 2,
                       spec: dict[str, str] | None = None) -> list[str]:
    """A check block with each coefficient row followed by its scored t-statistic row."""
    lines = [f"## {title}", "", "| statistic | " + " | ".join(PORTFOLIOS) + " |",
             "|---|" + "---|" * len(PORTFOLIOS)]
    for stat in paper_tab["top5"]:
        cells = [_cell(float(frame.loc[stat, p]), paper_tab[p][stat], stat in pct, tally,
                       digits=digits, fmt_spec=(spec or {}).get(stat)) for p in PORTFOLIOS]
        lines.append(f"| {stat} | " + " | ".join(cells) + " |")
        if stat not in paper_t:
            continue
        tkey = _t_key(stat)
        t_cells = [_cell(float(frame.loc[tkey, p]), paper_t[stat][i], False, tally,
                         digits=digits) for i, p in enumerate(PORTFOLIOS)]
        lines.append(f"| t: {stat} | " + " | ".join(t_cells) + " |")
    return lines


def _table7_regression_block(frame: pd.DataFrame, tally: list) -> list[str]:
    """Table 7's regression block: seven scored rows per book, the t-statistics unscored.

    The paper prints each coefficient over its Newey-West t-statistic; only the
    coefficients and R2 are compared, as in Tables 4 and 8, and the t rows read
    "ours vs paper" (the shape ``_alpha_t_rows`` uses) so the scorer skips them.
    The row labels are the ones ``table7.csv`` carries, the paper's column order.
    """
    if not TABLE7_REGRESSION_ROWS or TABLE7_REGRESSION_ROWS[0] not in frame.index:
        return ["", "Regression block: not run (needs the factor files; the `tables` step",
                "warns when they are not pulled)."]
    rows = []
    for key in TABLE7_REGRESSION_ROWS:
        cells = [_cell(float(frame.loc[key, p]), PAPER_TABLE7[p][key], key in TABLE7_PCT, tally)
                 for p in PORTFOLIOS]
        rows.append(f"| {key} | " + " | ".join(cells) + " |")
        side, name = key.split(": ", 1)
        if name == "r2":
            continue
        t_key = f"{side}: t_{name}"
        t_cells = [_cell(float(frame.loc[t_key, p]), PAPER_TABLE7_T[p][key], False, tally)
                   for p in PORTFOLIOS]
        rows.append(f"| t: {key} | " + " | ".join(t_cells) + " |")
    return rows


def _table7_reversal_block(out_dir: Path, frame: pd.DataFrame,
                           reversal_factor: str) -> list[str]:
    """The same 56 regression cells under the other reversal series, unscored.

    Table 4's alternative-factor block prints "ours vs paper mark" without the scored
    cells' " / ", so the scorer skips these; they are the ablation the reversal ambiguity
    (REVIEW_NOTES section 51) needs, since the block's score depends on which series the
    paper's own factor is. The scored rows above use the driver's ``--reversal-factor``.
    """
    path = out_dir / "table7_reversal_alternative.csv"
    if not path.exists() or TABLE7_REGRESSION_ROWS[0] not in frame.index:
        return []
    alt = pd.read_csv(path, index_col=0)
    label, scored_name = _reversal_names(reversal_factor)
    lines = ["", f"### The same block with {label} in the reversal column (unscored)", "",
             f"The scored rows above use {scored_name}. These are the same 56 cells with the",
             "other series; marked only for comparison, they do not count.", "",
             "| statistic | " + " | ".join(PORTFOLIOS) + " |",
             "|---|" + "---|" * len(PORTFOLIOS)]
    alt_marks, scored_marks = [], []
    for key in TABLE7_REGRESSION_ROWS:
        cells = []
        for p in PORTFOLIOS:
            ours, paper = float(alt.loc[key, p]), PAPER_TABLE7[p][key]
            mark = _mark(ours, paper)
            alt_marks.append(mark)
            scored_marks.append(_mark(float(frame.loc[key, p]), paper))
            fmt = (lambda v: f"{100 * v:.2f}%") if key in TABLE7_PCT else (lambda v: f"{v:.3g}")
            cells.append(f"{fmt(ours)} vs {fmt(paper)} {mark}")
        lines.append(f"| {key} | " + " | ".join(cells) + " |")
        side, name = key.split(": ", 1)
        if name == "r2":
            continue
        t_key = f"{side}: t_{name}"
        t_cells = []
        for p in PORTFOLIOS:
            ours_t = float(alt.loc[t_key, p])
            paper_t = PAPER_TABLE7_T[p][key]
            mark = _mark(ours_t, paper_t)
            alt_marks.append(mark)
            scored_marks.append(_mark(float(frame.loc[t_key, p]), paper_t))
            t_cells.append(f"{ours_t:.2f} vs {paper_t:.2f} {mark}")
        lines.append(f"| t: {key} | " + " | ".join(t_cells) + " |")

    def points(marks: list[str]) -> float:
        return marks.count("✓") + 0.5 * marks.count("~")

    lines += ["", (f"With {label} these {len(alt_marks)} regression cells score "
               f"{points(alt_marks):.1f} of {len(alt_marks)}, against "
               f"{points(scored_marks):.1f} with {scored_name}."), ""]
    return lines


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


def _table5b_note() -> list[str]:
    """The conventions Table 5 Panel B's section states (REVIEW_NOTES section 62).

    Prose, not a table row: the scorer counts a cell only in a markdown table row
    that holds an "ours / paper" body, so a note cannot be mistaken for one.
    """
    return [
        "The daily series is the monthly series' own object one level down: each trading",
        "day carries the equal-weighted mean over the cohorts trading that day of the",
        "cohort's daily fully-invested return, the Jegadeesh-Titman overlap average at",
        "daily frequency, and a day on which a cohort holds no position is skipped there",
        "exactly as a NaN month is skipped in the monthly average. The cohort cache stores",
        "that series since format 7, so the block is reproducible from the cache alone.",
        "Every row is a function of the daily returns, so none of the nine repeats a",
        "monthly row of Table 5 Panel A or Table 1 Panel B. Percentiles are linearly",
        "interpolated (pandas' default, as in Panel A) and serial correlation is the lag-1",
        "autocorrelation of consecutive trading days; the paper states neither estimator.",
        "The paper prints the 101-120 serial correlation as 0.00, a rounded zero, where a",
        "ratio is undefined, so that cell is marked on whether ours prints the same two",
        "decimals. The top five, top twenty and 101-120 columns agree within a few percent",
        "on every row. The \"all\" column is the loosest: its daily standard deviation is",
        "0.191% against the paper's 0.169%, 1.13 times, and each quantile moves with it",
        "(that gap was 1.44 times before the position-weighted short, REVIEW_NOTES 29).",
        "That is the inconsistency COVERAGE.md item 4 records inside the paper itself,",
        "where its monthly \"all\" standard deviation is 9.3 of its own daily units while",
        "the other three columns imply 4-7; it is reported, not adjusted.",
    ]


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


def _reversal_factor_header(reversal_factor: str) -> list[str]:
    """The check header's description of the scored reversal factor."""
    if reversal_factor == "losers_only":
        return [
            "The scored five-factor block's reversal factor is our reading, not the paper's",
            "stated definition. The paper's own series is unidentified: its printed statistics",
            "pin a 2.19%/month premium at 7.23% monthly volatility, a before-1989 standard",
            "deviation of 0.0723, and Table 8 Panel A loadings that need a factor correlated",
            "+0.81 with the market and +0.79 with SMB, which no long-short construction",
            "reaches (REVIEW_NOTES section 51). The scored rows use the equal-weighted bottom",
            "three prior-month deciles less the T-bill instead: standard deviation 0.0685",
            "before 1989, correlations +0.84 with the market and +0.77 with SMB, premium",
            "1.30%/month against the implied 2.19%. That is a hypothesis that the paper's",
            "factor lacks its short leg, i.e. an error in the paper, not a settled reading",
            "(REVIEW_NOTES section 61). French's ST_Rev is printed unscored below;",
            "--reversal-factor st_rev restores SCORE_LOG.md row 18's block (262.0).",
        ]
    if reversal_factor == "csv":
        name = Path(REVERSAL_CSV).name if REVERSAL_CSV else "the named CSV"
        return [
            "The scored five-factor block's reversal factor is the candidate series in",
            f"`{name}` (`--reversal-factor csv --reversal-csv`), one construction of the",
            "p. 813 sentence and footnote 7 chosen by its distance to the standard deviation",
            "and four correlations Table 8's own arithmetic implies in both subperiods",
            "(contract Pb; REVIEW_NOTES section 73, claims/REVERSAL_SUBPERIODS.md). It is a",
            "candidate reading measured here, not a change of default: the losers-only",
            "series is printed unscored below, and the default remains it",
            "(--reversal-factor losers_only: SCORE_LOG.md row 20).",
        ]
    return [
        "The scored five-factor block uses French's ST_Rev, the long-short reversal factor the",
        "text describes (SCORE_LOG.md row 18); the losers-only series the paper's Table 8",
        "arithmetic implies is printed unscored below (--reversal-factor losers_only, the",
        "default since row 20, scores it instead: REVIEW_NOTES section 61).",
    ]


def _factor_vintage_header(factor_vintage: str) -> list[str]:
    """The check header's description of the vintage of French's factors the regressions use."""
    if factor_vintage == "2005":
        return [
            "The five factors are French's 2005 archives, the vintage the paper had: the",
            "Internet Archive's captures of 30 September and 29 October 2005",
            "(`F-F_Research_Data_Factors.zip`, `F-F_Momentum_Factor.zip`), committed whole",
            "under `data/raw/french_vintage_2005` with their provenance. They reproduce",
            "Table 8's printed factor standard deviations; the files downloaded today do not,",
            "HML's after-1988 standard deviation being 7.8% short (REVIEW_NOTES section 72).",
            "The prior-month deciles the reversal series is built from are today's: the",
            "earliest archived prior-1-0 file is from 2007 and matches them.",
        ]
    return [
        "The five factors are French's files as downloaded today (`data/raw/french`), not the",
        "2005 vintage the paper used; `--factor-vintage 2005` restores it, and REVIEW_NOTES",
        "section 72 shows that vintage reproducing Table 8's printed factor standard",
        "deviations. The prior-month deciles the reversal series is built from are today's.",
    ]


def write_replication_check(out_dir: Path, fig_dir: Path, universe: str,
                            short_weights: str,
                            table9a: pd.DataFrame | None = None,
                            table9b: pd.DataFrame | None = None,
                            table6: pd.DataFrame | None = None,
                            delist100: pd.Series | None = None,
                            reversal_factor: str = "losers_only") -> Path:
    """Compare Figures 1 and 4 and Tables 1-4, 5 Panels A and B, 7 and 8 with the paper."""
    portfolio, disclosure = _short_weight_header(short_weights)
    reversal = _reversal_factor_header(reversal_factor)
    vintage_note = _factor_vintage_header(vintage())
    lines = [
        (f"# Replication check: GGR (2006) Figures 1 and 4, Tables 1-4, 5 Panels A and B, "
         f"6, 7 and 8 ({universe})"),
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
        "evidence, and claims/CONVENTIONS_865.md prices every convention this header",
        "names on all 865 cells: its row 9 - same issuer allowed, the near-frozen filter",
        "off, the trigger's sigma taken about the mean instead of the RMS about zero -",
        "gains 6.5 and is not adopted. Telephone utilities are",
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
        "Tables 1 and 3 compound the long and the short book to monthly returns",
        "and then subtract, as the paper's own Table 1 = Table 7 identity requires",
        "(pp. 807 and 821; REVIEW_NOTES sections 33 and 54). Table 5 Panel B is the same",
        "overlap average at daily frequency (``DAILY_CAPITAL``), percentiles linearly",
        "interpolated and serial correlation the lag-1 autocorrelation of consecutive",
        "trading days, neither of which the paper states; REVIEW_NOTES section 62 gives the",
        "marks, the daily cache's construction and the paper's own \"all\" daily column,",
        "which does not agree with its monthly \"all\" and is reported, not adjusted.",
        *disclosure,
        "",
        *reversal,
        "",
        *vintage_note,
        "",
        "The same arithmetic is in GAPS.md and `scripts/paper_consistency.py`.",
        "",
        "The score total, its history and how it is counted live in SCORE_LOG.md. The",
        "open gaps are in GAPS.md; the 1999 NBER draft is scored separately",
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
                    key = (sector, p, T3_FI)
                    ours = float(t3.loc[key, stat]) if key in t3.index else np.nan
                    cells.append(_cell(ours, ports[p][i], stat in PCT_STATS, tally))
                lines.append(f"| {stat} | " + " | ".join(cells) + " |")
            lines.append("")
        lines += [_tally_line(tally), ""]
        summary.append("Table 3: " + _tally_line(tally))
        marks += tally

    base291 = list(marks)
    perf7 = []
    if (out_dir / "table7.csv").exists():
        t7 = pd.read_csv(out_dir / "table7.csv", index_col=0)
        tally = []
        perf7 = []
        title = "Table 7 (long and short books, one-day wait)"
        perf7 = []
        lines += _portfolio_table(t7, TABLE7_PAPER_PERFORMANCE, title, TABLE7_PCT, perf7)
        rest7 = []
        lines += _table7_regression_block(t7, rest7)
        tally = perf7 + rest7
        lines += ["", _tally_line(tally), "",
                  "The regression block is each book's own monthly return less the 30-day",
                  "bill (Table 7's note, p. 821) on the same five factors Table 4 uses, with",
                  "Newey-West t-statistics at six lags; coefficients, R2 and the t-statistics are",
                  "scored (SCORE_LOG row 25).",
                  ""]
        lines += _table7_reversal_block(out_dir, t7, reversal_factor)
        summary.append("Table 7: " + _tally_line(tally))
        marks += tally
    base323 = list(base291) + perf7

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
        "its recipe; coefficients, R2 and the Newey-West t-statistics at six lags are scored,",
        "and its factor standard deviations are too (under Table 8). Table 4's equity-premium column is",
        "French's Mkt-RF, the regressions' market",
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
    for fname, paper_tab, paper_t, title, pct, digits, spec in (
        ("table4.csv", PAPER_TABLE4, PAPER_TABLE4_T,
         "Table 4 (systematic risk, one-day wait)", TABLE4_PCT, 3, {}),
        ("table5_var.csv", PAPER_TABLE5, None,
         "Table 5 Panel A (monthly value at risk)",
         {"var_1", "var_5", "var_10", "var_25"}, 3, {}),
        ("table5b_daily.csv", PAPER_TABLE5B, None,
         "Table 5 Panel B (daily value at risk)",
         TABLE5B_PCT, 3, {"serial_correlation": ".2f"}),
        ("table8_subperiod.csv", PAPER_TABLE8, PAPER_TABLE8_T,
         "Table 8 (subperiod analysis)", TABLE8_PCT, 3, {}),
    ):
        if not (out_dir / fname).exists():
            why = ("Not run (needs a cohort cache at format 7, rebuilt with `--force`, and",
                   "the one-day-wait series: `--wait 1`).") if fname == "table5b_daily.csv" else (
                "Not run (needs the one-day-wait series from the", "`tables` step with `--wait 1`).")
            lines += [f"## {title}", "", *why, ""]
            continue
        raw = pd.read_csv(out_dir / fname, index_col=0)
        t_keys = [_t_key(s) for s in paper_tab["top5"] if s in paper_t] if paper_t else []
        frame = raw.reindex(list(paper_tab["top5"]) + t_keys)
        tally = []
        if paper_t is None:
            lines += _portfolio_table(frame, paper_tab, title, pct, tally, digits=digits,
                                      spec=spec)
        else:
            lines += _coefficient_table(frame, paper_tab, paper_t, title, pct, tally,
                                        digits=digits, spec=spec)
        if title.startswith("Table 4") and (out_dir / "table4_equity_premium.csv").exists():
            ep = pd.read_csv(out_dir / "table4_equity_premium.csv", index_col=0).iloc[:, 0]
            lines += ["", "| statistic | French's Mkt-RF (ours / paper) |", "|---|---|"]
            for stat, paper in PAPER_EQUITY_PREMIUM.items():
                lines.append(f"| equity premium: {stat} | "
                             + _cell(float(ep.get(stat, np.nan)), paper,
                                     stat in {"mean", "std"}, tally, digits=digits) + " |")
        if fname == "table5b_daily.csv":
            lines += ["", *_table5b_note()]
        if title.startswith("Table 8") and (out_dir / "table8_factor_sd.csv").exists():
            fsd = pd.read_csv(out_dir / "table8_factor_sd.csv", index_col=0)
            lines += ["", "Table 8's published \"Factor sd\" column: these cells measure the factor",
                      "inputs the regressions above are built from, over the same months.",
                      "The first four are French's series at the vintage the run names: at the",
                      "paper's 2005 files they reproduce the printed values (REVIEW_NOTES",
                      "sections 49 and 71), today's HML being 7.8% short after 1988; the reversal",
                      "cell is the hypothesis of section 61 (the",
                      "losers-only series), which is why its after-1988 value is the one",
                      "that misses.", "",
                      "| statistic | before 1989 | after 1988 |", "|---|---|---|"]
            for name in FACTORS:
                cells = []
                for half in ("pre", "post"):
                    ours = float(fsd.loc[name, half])
                    paper = PAPER_TABLE8_FACTOR_SD[half][name]
                    mark = _mark(ours, paper)
                    tally.append(mark)
                    cells.append(f"{ours:.5f} / {paper:.5f} {mark}")
                lines.append(f"| factor sd: {name} | " + " | ".join(cells) + " |")
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

    text_tally: list = []
    lines += [
        "## Numbers printed in the text",
        "",
        "The paper prints three result numbers outside its tables: the all-pair",
        "portfolio's average size in the captions of Tables 1, 5, 8 and 9 (\"The",
        "average number of pairs in the all-pair portfolio is 2057\"), section 1.2's",
        "hold-out sentence (p. 800), and footnote 4's delisting result (p. 804). Each",
        "is scored once here.",
        "",
        "| check | ours / paper |",
        "|---|---|",
    ]
    uni_path = out_dir / "universe_summary.csv"
    if uni_path.exists():
        uni = pd.read_csv(uni_path, index_col=0)["value"]
        ours_pairs = float(uni["mean_pairs_per_cohort"])
        paper_pairs = PAPER_UNIVERSE["mean_pairs_per_cohort"]
        mark = _mark(ours_pairs, paper_pairs)
        text_tally.append(mark)
        lines.append("| the average number of pairs in the all-pair portfolio | "
                     f"{ours_pairs:.0f} / {paper_pairs:.0f} {mark} |")
    hold_path = out_dir / "holdout_1999.csv"
    if hold_path.exists():
        hold = pd.read_csv(hold_path, index_col=0)
        lines += [
            "",
            "Section 1.2's hold-out sentence (top 20, fully invested, 1999-2002): the",
            "scored reading is the no-wait rule, as REVIEW_NOTES section 17 recorded",
            "before these cells were scored; annual figures are twelve times the monthly",
            "mean and the square root of twelve times the monthly standard deviation,",
            "and the t-statistic is the six-lag Newey-West t of the monthly mean.",
            "",
            "| statistic | ours / paper |",
            "|---|---|",
        ]
        labels = {"mean_annual": "annual excess return",
                  "sd_annual": "annual standard deviation",
                  "t_stat": "Newey-West t-statistic"}
        for key, label in labels.items():
            lines.append(f"| {label} | "
                         + _cell(float(hold.loc["wait0", key]), PAPER_HOLDOUT[key],
                                 key != "t_stat", text_tally) + " |")
        if "wait1" in hold.index:
            alt = hold.loc["wait1"]
            lines += ["",
                      ("One-day-wait reading, unscored: "
                      f"{100 * float(alt['mean_annual']):.1f}% vs {100 * PAPER_HOLDOUT['mean_annual']:.1f}%; "
                      f"{100 * float(alt['sd_annual']):.1f}% vs {100 * PAPER_HOLDOUT['sd_annual']:.1f}%; "
                      f"t {float(alt['t_stat']):.1f} vs {PAPER_HOLDOUT['t_stat']:.2f}.")]
    if delist100 is not None:
        lines += [
            "",
            "Footnote 4's delisting assumption (top 20, no wait), from the cache",
            "--delist-cache names (make delist100 builds it with --long-delisting-loss):",
            "",
            "| statistic | ours / paper |",
            "|---|---|",
        ]
        for key, label in (("mean", "mean monthly return"),
                           ("std", "standard deviation")):
            lines.append(f"| {label} | "
                         + _cell(float(delist100[key]), PAPER_FOOTNOTE4[key], True,
                                 text_tally) + " |")
    lines += ["", _tally_line(text_tally), ""]
    summary.append("Numbers printed in the text: " + _tally_line(text_tally))
    marks += text_tally

    if table9a is not None:
        tally9a: list = []
        lines += [
            "## Table 9 Panel A (top three size deciles, one-day wait)",
            "",
            "Section 3.9 (p. 824): pairs formed only from stocks in the top three size",
            "deciles. The rows are Table 1 Panel B's statistics over that screened",
            "universe, from the cache --table9a-cache names (make table9a builds it).",
            "",
            "The printed skewness and kurtosis rows are scored as printed: our skewness",
            "against the row labelled Skewness, our kurtosis against Kurtosis. Those two",
            "rows contradict Table 1's (COVERAGE.md, where the published version",
            "contradicts itself, 1: the row labelled Kurtosis reads 0.02-1.77 and the",
            "one labelled Skewness 7.01-11.67). The swapped reading is printed below as",
            "an unscored diagnostic; the paper's values are the paper's.",
            "",
            "| statistic | " + " | ".join(PORTFOLIOS) + " |",
            "|---|" + "---|" * len(PORTFOLIOS),
        ]
        for stat in PAPER_TABLE9A["top5"]:
            cells = []
            for p in PORTFOLIOS:
                ours = float(table9a.loc[stat, p])
                cells.append(_cell(ours, PAPER_TABLE9A[p][stat],
                                   stat in PCT_STATS, tally9a))
            lines.append("| " + stat + " | " + " | ".join(cells) + " |")
        lines += ["", "The two transposed rows, read swapped (unscored):", ""]
        lines.append("| statistic | " + " | ".join(PORTFOLIOS) + " |")
        lines.append("|---|" + "---|" * len(PORTFOLIOS))
        for stat in ("skew", "kurtosis"):
            other = "kurtosis" if stat == "skew" else "skew"
            cells = []
            for p in PORTFOLIOS:
                ours = float(table9a.loc[stat, p])
                cells.append(f"{ours:.2f} vs {PAPER_TABLE9A[p][other]:.2f}")
            label = TABLE9A_SWAP_LABELS[stat]
            lines.append(f"| {stat} vs printed {label} | " + " | ".join(cells) + " |")
        lines += ["", _tally_line(tally9a), ""]
        summary.append("Table 9 Panel A: " + _tally_line(tally9a))
        marks += tally9a

    if table9b is not None:
        tally9b: list = []
        lines += [
            "## Table 9 Panel B (short recalls on high volume, one-day wait)",
            "",
            "Section 3.9 (pp. 824-825): recalls on the short positions, and the closing",
            "of the pair, on days with high volume -- daily volume more than one",
            "standard deviation above its average over the 18 months (both split",
            "adjusted). High volume is the paper's proxy for divergence of opinion.",
            "The note fixes the rule: \"Panel B reports the summary statistics for the",
            "rule that waits one day before opening and closing the position\", 474",
            "monthly observations, Newey-West six lags, absolute kurtosis.",
            "",
            "The reading is the same-day recall close (REVIEW_NOTES section 74,",
            "claims/TABLE9B_READINGS.md): a recalled short ends the pair at the close of",
            "the flagged day itself, also under the one-day wait, because the text has",
            "the closing happen \"on days with high volume\" and a recall is forced",
            "rather than a trading decision the wait applies to. The pair is re-entered",
            "only after the spread has come back inside two sigma and a *new* divergence",
            "fires. This reading scores 21.0 of 44 against 18.0 for the next-day close",
            "(section 58's reading, --table9b-cache data/processed/replication/",
            "vol_common_recalls), and like every reading measured it raises the mean",
            "against Table 1 Panel B where the paper's falls by 4-13 bp, so claim 20 (b)",
            "stays unreplicated. The rows are Table 1 Panel B's statistics over the",
            "per-cohort monthly series in the cache --table9b-cache names (make table9b",
            "builds it with --reading R1), with the committed series supplying the last row.",
            "",
            "| statistic | " + " | ".join(PORTFOLIOS) + " |",
            "|---|" + "---|" * len(PORTFOLIOS),
        ]
        for stat in PAPER_TABLE9B["top5"]:
            cells = []
            for p in PORTFOLIOS:
                ours = float(table9b.loc[stat, p])
                cells.append(_cell(ours, PAPER_TABLE9B[p][stat],
                                   stat in PCT_STATS, tally9b))
            label = {"mean": "mean (fully invested)", "committed_mean": "mean (committed)"}
            lines.append(f"| {label.get(stat, stat)} | " + " | ".join(cells) + " |")
        lines += ["", _tally_line(tally9b), ""]
        summary.append("Table 9 Panel B: " + _tally_line(tally9b))
        marks += tally9b
    if table6 is not None:
        tally6: list = []

        lines += [
            "## Table 6 (random pairs sorted on prior one-month return)",
            "",
            "Section 3.6 (pp. 818-819): at each true-pair opening the bootstrap",
            "replaces the two legs with random securities drawn from the same decile",
            "of the previous month's return, opens and closes them with the true trade",
            "and averages each cell over the 200 replications. Our cells are our own",
            "draws against our own true-pair series from the same cache, not the",
            "paper's measurement, so this is the least comparable block in the check",
            "(REVIEW_NOTES section 65). The values come from the per-cohort outputs",
            "that --table6-cache names (make table6 runs the bootstrap).",
            "",
            "The caption (p. 819) says 'value-weighted portfolios of n pairs', so the",
            "committed rows are the value-weighted book scaled by the share of pairs",
            "open (the book-share reading, REVIEW_NOTES section 75): that literal-to-",
            "book-share choice is Table 6's own, and the literal series stays the",
            "definition for Tables 1, 3, 7 and 9, whose captions do not say",
            "'value-weighted portfolios'.",
            "",
            TABLE6_HEADER,
        ]
        for panel, panel_label in TABLE6_PANELS.items():
            for capital, block_label in TABLE6_BLOCKS.items():
                for stat, stat_label in TABLE6_STATS.items():
                    key = f"{panel}|{capital}|{stat}"
                    cells = [
                        _cell(float(table6.loc[key, port]), PAPER_TABLE6[key][port],
                              False, tally6, sig=5)
                        for port in TABLE6_PORTS
                    ]
                    label = f"{panel_label}, {block_label}: {stat_label}"
                    lines.append(f"| {label} | " + " | ".join(cells) + " |")
        lines += ["", _tally_line(tally6), ""]
        summary.append("Table 6: " + _tally_line(tally6))
        marks += tally6

    lines += _reversal_alternative_section(out_dir, marks, reversal_factor)

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
    return Job(**{**data, "end": tuple(data["end"]), "waits": tuple(data["waits"]),
                  "extra_capitals": tuple(data.get("extra_capitals") or ())})


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


def _share_classes_path(reading: str, path: str | None) -> str | None:
    """The permno map a ``--share-classes wide`` run reads (None: no widening)."""
    if reading == "common":
        return None
    return path or str(ROOT / "data" / "raw" / "shareclass_sb_ad.parquet")


def _share_classes_stamp(path: str | None) -> str | None:
    """The map's identity for the cache stamp (12 hex digits), None without a map."""
    if path is None or str(path).strip().lower() in ("", "none"):
        return None
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:12]


def _estimator_options(args) -> None:
    """Point the moment tables at the requested estimator conventions (R10-B).

    Four switches, each with the shipped reading as its default, so an
    unswitched run is byte-identical: ``--moments`` (raw Pearson moments, the
    reading the caption's "Absolute kurtosis is reported" asks for, p. 807),
    ``--quantile-method`` (Table 5's percentiles), ``--sign-zero`` ("< 0", the
    printed row label) and ``--nw-correction`` (Newey-West with or without the
    n/(n-k) factor). ``--ibbotson-market`` is the fifth, in ``project.factors``.
    """
    set_moments(args.moments)
    set_quantile_method(args.quantile_method)
    set_sign_zero(args.sign_zero)
    set_nw_correction(args.nw_correction)
    set_ibbotson_market(args.ibbotson_market)


def _capital_base_options(base: str) -> None:
    """Point the tables at the requested fully-invested base (``--capital-base``).

    ``book`` is the shipped reading and leaves every global untouched. ``count``
    swaps in the payoff-count series the cache already holds; ``gross`` and
    ``long`` are the two book-scaling bases, which have to be built, so they are
    added to the cache's capital columns for this run only.
    """
    global T1_FI, T1_COMMITTED, T3_FI, EXTRA_CAPITALS
    if base == "book":
        return
    if base == "count":
        T1_FI, T1_COMMITTED, T3_FI = "employed_count", "committed_count", "employed_count"
        return
    name = "gross_base" if base == "gross" else "long_base"
    T1_FI = name
    T3_FI = name
    EXTRA_CAPITALS = (name,)


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
    # Stamped only when on, so a default cache's stamp is unchanged.
    if getattr(args, "long_delisting_loss", False):
        options["long_delisting_loss"] = True
    if getattr(args, "delist_last_px", "off") != "off":
        options["delist_last_px"] = args.delist_last_px
    if getattr(args, "waste_sic", "industrials") != "industrials":
        options["waste_sic"] = args.waste_sic
    if getattr(args, "trigger_mult", 2.0) != 2.0:
        options["trigger_mult"] = args.trigger_mult
    if getattr(args, "fresh_divergence", False):
        options["fresh_divergence"] = True
    # Stamped only for the bases that add a column to the cache: "count" selects
    # a series every cache already holds, so it reads the default cache as is.
    if getattr(args, "capital_base", "book") != "book" and EXTRA_CAPITALS:
        options["capital_base"] = args.capital_base
    if getattr(args, "demote_frozen", "none") != "none":
        options["demote_frozen"] = args.demote_frozen
        options["demote_frozen_share"] = args.demote_frozen_share
    if getattr(args, "share_classes", "common") != "common":
        options["share_classes"] = args.share_classes
        digest = _share_classes_stamp(_share_classes_path(
            args.share_classes, getattr(args, "share_classes_file", None)))
        if digest:
            options["share_classes_map"] = digest
    # A panel chosen with GGR_PROCESSED_DIR (another data vintage) is stamped by its
    # provenance file, so its cohorts never share a cache with the default panel's.
    source = processed_source_identity()
    if source is not None:
        options["processed_source"] = source
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
        "--waste-sic", choices=("industrials", "utilities"), default="industrials",
        help="sector of waste management, SIC 4950-4959: Industrials, as GICS has it "
             "(default; REVIEW_NOTES section 24), or Utilities with the rest of SIC 49",
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
        "--trigger-mult", type=float, default=2.0, metavar="SIGMAS",
        help="entry and exit band in formation sigmas (default 2.0, the paper's "
             "2-sigma rule; 2.33 is the reading that reproduces the paper's printed "
             "average trigger, REVIEW_NOTES sections 40 and 76)",
    )
    parser.add_argument(
        "--demote-frozen", choices=("none", "one", "both"), default="none",
        help="rank pairs whose leg(s) are frozen quotes after the rest, pool intact: "
             "off (default), when either leg is frozen, or only when both are "
             "(REVIEW_NOTES sections 40 and 77)",
    )
    parser.add_argument(
        "--demote-frozen-share", type=float, default=0.90, metavar="SHARE",
        help="a leg is frozen when its quote is unchanged on more than this share of "
             "the formation window's days (default 0.90)",
    )
    parser.add_argument(
        "--share-classes", choices=("common", "wide"), default="common",
        help="the share filter of the formation universe: CRSP's ordinary common "
             "shares only (default), or those plus the shares-of-beneficial-interest "
             "and ADR classes the map names (REVIEW_NOTES section 77)",
    )
    parser.add_argument(
        "--share-classes-file", default=None, metavar="PARQUET",
        help="permno map --share-classes wide adds; default "
             "data/raw/shareclass_sb_ad.parquet, the value none the shipped filter",
    )
    parser.add_argument(
        "--moments", choices=("raw", "sample"), default="raw",
        help="skewness and kurtosis of the moment rows: raw Pearson central moments "
             "(default; the caption's 'Absolute kurtosis is reported', p. 807) or the "
             "bias-corrected spreadsheet moments (contract R10-B)",
    )
    parser.add_argument(
        "--quantile-method", choices=QUANTILE_METHODS, default="linear",
        help="interpolation of Table 5's VaR percentiles: pandas' linear default (the "
             "shipped reading) or another numpy method (contract R10-B)",
    )
    parser.add_argument(
        "--sign-zero", choices=("strict", "nonpositive"), default="strict",
        help="the 'Observations with excess return < 0' boundary: a strictly negative "
             "month (default, the printed label) or also a zero month (R10-B)",
    )
    parser.add_argument(
        "--nw-correction", choices=("none", "df"), default="none",
        help="Newey-West standard errors without (default) or with statsmodels' n/(n-k) "
             "small-sample factor; the paper states neither (contract R10-B)",
    )
    parser.add_argument(
        "--ibbotson-market", choices=("geometric", "excess"), default="geometric",
        help="Table 4's Ibbotson market leg: a geometric difference like the other three "
             "premia (default) or the arithmetic S&P 500 minus T-bill the caption's "
             "'in excess of' reads as (contract R10-B)",
    )
    parser.add_argument(
        "--capital-base", choices=("book", "count", "gross", "long"), default="book",
        help="the fully-invested series Tables 1, 3, 4, 5 Panel A and 8 and Figure 4 read: "
             "the value-weighted books (default), the payoff counts sum(pi)/n_t, the "
             "gross-book base 2 sum(dL-dS)/(sum L + sum S) or the long-book base "
             "sum(dL-dS)/sum L (REVIEW_NOTES sections 25, 29 and 77)",
    )
    parser.add_argument(
        "--cohort-weights", choices=("equal", "positions", "selected"), default="equal",
        help="weight the overlapping cohorts equally (default, the Jegadeesh-Titman "
             "average the paper describes) or by the pairs a cohort holds in each "
             "month / by the pairs it selected (REVIEW_NOTES sections 27 and 76)",
    )
    parser.add_argument(
        "--allow-missing-factors", action="store_true",
        help="run the factor steps even when the French or Goyal-Welch files are Git LFS "
             "pointers or missing, leaving their rows out (the old silent fallback: the "
             "check then prints a score over 544 cells, not 865). Default: exit non-zero "
             "and name the files.",
    )
    parser.add_argument(
        "--panel-a-cohorts", choices=("complete", "all"), default="complete",
        help="Table 2 Panel A's cross-cohort moments over the cohorts whose six-month "
             "window completes inside the sample (default, as the row's 'per six-month "
             "period' wording asks) or over all of them, censored windows included",
    )
    parser.add_argument(
        "--fresh-divergence", action="store_true",
        help="open only on a divergence inside the trading period: a pair whose "
             "spread is already outside the band at the end of formation waits "
             "until the spread returns inside it (default off)",
    )
    parser.add_argument(
        "--reversal-factor", choices=("st_rev", "losers_only", "csv"), default="losers_only",
        help="the scored reversal factor of the five-factor block: the losers-only series the "
             "paper's Table 8 arithmetic implies (default), French's ST_Rev, the long-short "
             "factor the text describes, or a series read from --reversal-csv (contract Pb; "
             "REVIEW_NOTES section 73). The losers-only series is printed unscored",
    )
    parser.add_argument(
        "--reversal-csv", default=None,
        help="CSV with month and reversal columns giving the scored series when "
             "--reversal-factor csv (REVIEW_NOTES section 73)",
    )
    parser.add_argument(
        "--factor-vintage", choices=("2005", "current"), default="2005",
        help="vintage of French's factors that Tables 4, 7 and 8 and Figure 4 regress on: the "
             "2005 archives the paper used, data/raw/french_vintage_2005 (default; "
             "REVIEW_NOTES section 72), or the files downloaded today",
    )
    parser.add_argument(
        "--size-deciles-top", type=_decile_count, default=None,
        help="form pairs only among stocks in the largest N CRSP size deciles at the "
             "formation end (Table 9 Panel A uses 3); default off (no size screen)",
    )
    parser.add_argument(
        "--delist-last-px", choices=("off", *_DELIST_LAST_PX_CLASSES), default="off",
        help="read the delisting sentence of p. 804 by delisting-code class: the chosen "
             "classes book the last available price on their terminal row (no delisting "
             "return), every other class keeps CRSP's return. merge = 2xx mergers, "
             "nondistress = mergers and exchange/listing moves, all = every class; "
             "default off, the shipped per-row rule (REVIEW_NOTES 94)",
    )
    parser.add_argument(
        "--long-delisting-loss", action="store_true",
        help="the robustness check of the paper's footnote 4 (RFS p. 804): an open "
             "position's long leg returns -100%% on its delisting row (the short leg "
             "keeps its actual return); default off",
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
        "--table9a-cache", default=None, metavar="DIR",
        help="screened cohort cache (--size-deciles-top 3) the check reads Table 9 "
             "Panel A from; default data/processed/replication/vol_common_top3, "
             "the value none leaves the section out",
    )
    parser.add_argument(
        "--table9b-cache", default=None, metavar="DIR",
        help="recall cohort cache (scripts/claims/table9b_recalls.py run --out-root "
             "DIR) the check reads Table 9 Panel B from; default "
             "data/processed/replication/vol_common_recalls_r1, the value none leaves "
             "the section out",
    )
    parser.add_argument(
        "--table6-cache", default=None, metavar="DIR",
        help="per-cohort outputs of scripts/claims/table6_random_pairs.py --mode run "
             "--committed-capital book-share (the caption's value-weighted "
             "portfolios) that the check reads Table 6 from; default "
             "data/processed/replication/vol_common_t6_book, the value none leaves "
             "the section out",
    )
    parser.add_argument(
        "--delist-cache", default=None, metavar="DIR",
        help="cohort cache built with --long-delisting-loss, which the check reads "
             "footnote 4's two cells from; default "
             "data/processed/replication/vol_common_delist100, the value none leaves "
             "them out",
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
    _capital_base_options(args.capital_base)
    _estimator_options(args)
    set_vintage(args.factor_vintage)
    global REVERSAL_CSV
    REVERSAL_CSV = args.reversal_csv
    if args.reversal_factor == "csv" and not args.reversal_csv:
        raise SystemExit("--reversal-factor csv needs --reversal-csv PATH")
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
    guard_factor_inputs(steps, args.allow_missing_factors)
    start = parse_month(args.start)
    end = parse_month(args.end)
    waits = tuple(int(w) for w in args.wait.split(","))
    continued = args.normalization == "continued"
    global CACHE_ROOT_OVERRIDE, OUT_ROOT_OVERRIDE, FORMATION_OPTIONS
    global COHORT_WEIGHTS, _COHORT_WEIGHTS
    _capital_base_options(args.capital_base)
    exclude_same_issuer = args.same_issuer == "exclude"
    FORMATION_OPTIONS = formation_options(args)
    cohorts_root = None
    if args.cache_root:
        CACHE_ROOT_OVERRIDE = Path(args.cache_root).resolve()
        cohorts_root = str(CACHE_ROOT_OVERRIDE / "cohorts")
    if args.out_root:
        OUT_ROOT_OVERRIDE = Path(args.out_root).resolve()
    args.cohorts_root = cohorts_root
    share_classes_file = _share_classes_path(args.share_classes, args.share_classes_file)
    cohorts = cohort_months(start, end)
    if args.stride > 1:
        cohorts = cohorts[:: args.stride]
    if args.limit_cohorts is not None:
        cohorts = cohorts[: args.limit_cohorts]
    out_dir = tables_dir(args.universe)
    fig_dir = figures_dir(args.universe)
    if args.cohort_weights != "equal" and ("tables" in steps or "table3" in steps):
        COHORT_WEIGHTS = args.cohort_weights
        _COHORT_WEIGHTS = cohort_weight_table(args.cohort_weights, cohorts, args.universe, waits)

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
                    size_deciles_top=args.size_deciles_top,
                    long_delisting_loss=args.long_delisting_loss, waste_sic=args.waste_sic,
                    delist_last_px=args.delist_last_px,
                    trigger_mult=args.trigger_mult,
                    fresh_divergence=args.fresh_divergence,
                    extra_capitals=EXTRA_CAPITALS,
                    demote_frozen=args.demote_frozen,
                    demote_frozen_share=args.demote_frozen_share,
                    share_classes_file=share_classes_file)
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
            daily = load_daily_returns(cohorts, args.universe) if 1 in waits else None
            strategy, trading, composition, uni_summary = aggregate(
                monthly, summaries, waits, end, cohorts,
                reversal_factor=args.reversal_factor, daily=daily,
                panel_a_cohorts=args.panel_a_cohorts)
            write_outputs(strategy, trading, waits, len(cohorts), out_dir, composition,
                          uni_summary, args.reversal_factor)
            print(f"Tables 1 and 2 written to {out_dir}", flush=True)
        if "table3" in steps:
            write_table3(*table3_from_cache(monthly, summaries, end), out_dir)
            print(f"Table 3 written to {out_dir}", flush=True)

    if "figure1" in steps:
        verify_cache(args.universe, continued)
        info = figure1(args.universe, fig_dir)
        print(f"Figure 1: rank {info['rank']}, trades {info['trades']}, saved {info['png']}")

    if "check" in steps:
        table9a = None
        root = args.table9a_cache
        if root is None:
            root = str(ROOT / "data" / "processed" / "replication" / "vol_common_top3")
        if str(root).lower() != "none":
            table9a = table9a_from_cache(Path(root), args.universe, cohorts, end)
        table9b = None
        root = args.table9b_cache
        if root is None:
            root = str(ROOT / "data" / "processed" / "replication" / "vol_common_recalls_r1")
        if str(root).lower() != "none":
            table9b = table9b_from_cache(Path(root), cohorts, end)
        table6 = None
        t6_root = args.table6_cache
        if t6_root is None:
            t6_root = str(ROOT / "data" / "processed" / "replication" / "vol_common_t6_book")
        if str(t6_root).lower() != "none":
            table6 = table6_from_cache(Path(t6_root))
        delist100 = None
        root = args.delist_cache
        if root is None:
            root = str(ROOT / "data" / "processed" / "replication" / "vol_common_delist100")
        if str(root).lower() != "none":
            delist100 = delist100_from_cache(Path(root), cohorts, end)
        path = write_replication_check(out_dir, fig_dir, args.universe, args.short_weights,
                                       table9a, table9b, table6=table6, delist100=delist100,
                                       reversal_factor=args.reversal_factor)
        print(f"Replication check written to {path}")


if __name__ == "__main__":
    main()
