"""Monthly risk factors and factor regressions for GGR (2006) Tables 4 and 8 and Figure 4.

The paper regresses the one-day-wait excess returns on "the three factors of Fama
and French (1996), augmented by two additional factors": Carhart's momentum and a
one-month reversal factor. The factors come from Kenneth French's data library,
committed under ``data/raw/french`` (Git LFS; ``git lfs pull`` fetches them).

Reversal: the paper defines its factor as prior-month winners minus losers but
expects, and prints, positive exposures for pairs portfolios, which buy losers. The
printed signs are those of losers minus winners, French's ``ST_Rev``, which is
used as is. French added ST_Rev to his library in 2006, after the paper was written; the
paper built its own factor. Table 8 identifies that factor: its regressions are consistent only
with a standard deviation near the printed 0.072 before 1989 and a correlation of about +0.8
with the market, the profile of a long-only portfolio of prior-month losers rather than of a
long-short factor (REVIEW_NOTES section 51). ``load_losers_only`` returns that series for the
check's unscored alternative; the scored regressions keep ST_Rev.

Table 4's second model uses "Ibbotson factors": the market, the small-stock premium, the bond
default premium and the bond horizon premium, each a monthly geometric difference. Ibbotson's
long-term corporate and government bond returns are the ``corpr`` and ``ltr`` columns of Goyal
and Welch's predictor data (``data/raw/goyal_welch``, the 2005 edition, Git LFS). Ibbotson's
small-company series is rebuilt from CRSP by its documented recipe: NYSE common stocks in the
bottom two capitalization deciles, re-formed every five years and value weighted, through 1981,
then the DFA Small Company fund. The large-company series is the CRSP S&P 500 total return and
the T-bill the CRSP 30-day bill.
"""

from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from project.paths import ROOT, WRDS_API_DIR

FRENCH_DIR = ROOT / "data" / "raw" / "french"
FACTOR_FILES = {
    "F-F_Research_Data_Factors_CSV.zip": {"Mkt-RF": "market", "SMB": "smb", "HML": "hml",
                                          "RF": "rf"},
    "F-F_Momentum_Factor_CSV.zip": {"Mom": "momentum"},
    "F-F_ST_Reversal_Factor_CSV.zip": {"ST_Rev": "reversal"},
}
FACTORS = ["market", "smb", "hml", "momentum", "reversal"]
#: French's 2005 archives, the vintage GGR used (``data/raw/french_vintage_2005``): the same
#: five series in his pre-2006 plain-text layout, whose momentum column is ``UMD``.
VINTAGE_2005_DIR = ROOT / "data" / "raw" / "french_vintage_2005"
FACTOR_FILES_2005 = {
    "F-F_Research_Data_Factors.zip": {"Mkt-RF": "market", "SMB": "smb", "HML": "hml",
                                      "RF": "rf"},
    "F-F_Momentum_Factor.zip": {"UMD": "momentum"},
}
VINTAGES = ("2005", "current")
#: The library default. The scored check asks for ``2005``; ``current`` keeps today's files.
DEFAULT_VINTAGE = "current"
_VINTAGE = DEFAULT_VINTAGE
#: French's ten prior-month-return deciles; their equal-weighted block gives ``load_losers_only``.
LOSERS_FILE = "10_Portfolios_Prior_1_0_CSV.zip"
GOYAL_WELCH = ROOT / "data" / "raw" / "goyal_welch" / "PredictorData_original_2005.xls"
IBBOTSON_FACTORS = ["market", "small_premium", "default_premium", "horizon_premium"]
#: What Git writes in place of a file it keeps in its large-file store. Reading such a file as
#: data does not fail loudly: the loaders' callers warn and carry on with fewer rows.
LFS_POINTER_PREFIX = b"version https://git-lfs"
#: The small-company series switches from the CRSP rebuild to the DFA fund in January 1982.
DFA_START = pd.Timestamp("1982-01-31")
#: Table 4's Ibbotson market leg: the caption's "calculated in excess of Treasury bill
#: returns" (arithmetic, ``"excess"``) or a geometric difference like the other three
#: premia (``"geometric"``, the shipped reading).
IBBOTSON_MARKETS = ("geometric", "excess")
_IBBOTSON_MARKET = "geometric"


def _monthly_block(text: str, title: str | None = None) -> pd.DataFrame:
    """The first block of YYYYMM rows in a French CSV (the monthly one), in decimals.

    ``title`` starts the search at the first line containing it, for files that hold several
    monthly blocks (value and equal weighted).
    """
    lines = text.splitlines()
    if title is not None:
        start = next((i for i, line in enumerate(lines) if title in line), None)
        if start is None:
            raise ValueError(f"no block titled {title!r}")
        lines = lines[start:]
    cols, rows = None, []
    for line in lines:
        parts = [p.strip() for p in line.split(",")]
        if len(parts) > 1 and parts[0] == "" and cols is None:
            cols = parts[1:]
        elif cols is not None and len(parts) > 1 and len(parts[0]) == 6 and parts[0].isdigit():
            rows.append([parts[0], *[float(x) for x in parts[1:]]])
        elif cols is not None and rows:
            break
    if not rows:
        raise ValueError("no monthly rows found")
    frame = pd.DataFrame(rows, columns=["ym", *cols])
    frame.index = pd.to_datetime(frame.pop("ym"), format="%Y%m") + pd.offsets.MonthEnd(0)
    return frame / 100.0


def _csv_member(z: zipfile.ZipFile) -> str:
    """The archive's first CSV member, so the read does not depend on the entry order."""
    names = z.namelist()
    return next((n for n in names if n.lower().endswith(".csv")), names[0])


def _french_text(path: Path) -> str:
    """The CSV inside one of French's zip files; refuses a missing file or an LFS pointer."""
    if not path.exists():
        raise FileNotFoundError(f"{path} not found")
    data = path.read_bytes()
    if data.startswith(LFS_POINTER_PREFIX):
        raise FileNotFoundError(f"{path} is a Git LFS pointer; run `git lfs pull`")
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        return z.read(_csv_member(z)).decode("latin1")


def _txt_monthly_block(text: str) -> pd.DataFrame:
    """The monthly block of a French plain-text file (whitespace columns), in decimals.

    The pre-2006 layout: a header line naming the columns (``Mkt-RF  SMB  HML  RF``, or
    ``UMD``), then ``YYYYMM`` rows, then a blank line and an annual block whose first column is
    a four-digit year. The block starts at the first all-letter header line whose next
    non-blank line begins with a six-digit month, which skips the prose heading these files
    carry (it says "created by CMPT_ME_BEME_RETS using the 200508 CRSP database").
    """
    lines = [line.rstrip() for line in text.splitlines()]
    start = None
    for i, line in enumerate(lines):
        parts = line.split()
        word = re.compile(r"[A-Za-z][\w\-]*")
        if not parts or not all(word.fullmatch(p) for p in parts):
            continue
        following = next((x for x in lines[i + 1:] if x.split()), None)
        if following is not None and re.fullmatch(r"\d{6}", following.split()[0]):
            start = i
            break
    if start is None:
        raise ValueError("no monthly block found")
    cols = lines[start].split()
    rows = []
    for line in lines[start + 1:]:
        parts = line.split()
        if not parts:
            continue
        if not re.fullmatch(r"\d{6}", parts[0]):
            break
        rows.append([parts[0], *[float(x) for x in parts[1:]]])
    if not rows:
        raise ValueError("no monthly rows found")
    frame = pd.DataFrame(rows, columns=["ym", *cols])
    frame.index = pd.to_datetime(frame.pop("ym"), format="%Y%m") + pd.offsets.MonthEnd(0)
    return frame / 100.0


def vintage() -> str:
    """The vintage of French's factors the loaders read unless told otherwise."""
    return _VINTAGE


def set_ibbotson_market(kind: str) -> None:
    """Table 4's Ibbotson market leg: ``"geometric"`` (shipped) or arithmetic ``"excess"``.

    The caption reads "S&P 500 returns are calculated in excess of Treasury bill returns"
    beside three factors it calls "monthly geometric difference" (p. 814), so the arithmetic
    reading is the caption's own for this leg; the two series differ by about 1.5 bp a month
    and the shipped default is the geometric one all four legs share. See
    `report/replication/claims/DEFINITION_AUDIT.md`.
    """
    global _IBBOTSON_MARKET
    if kind not in IBBOTSON_MARKETS:
        raise ValueError(f"unknown Ibbotson market reading {kind!r}; choose from "
                         f"{IBBOTSON_MARKETS}")
    _IBBOTSON_MARKET = kind


def set_vintage(name: str) -> None:
    """Choose the vintage of French's factors: ``"2005"`` (the paper's) or ``"current"``."""
    global _VINTAGE
    if name not in VINTAGES:
        raise ValueError(f"unknown factor vintage {name!r}; choose from {VINTAGES}")
    _VINTAGE = name


def vintage_dir(name: str | None = None) -> Path:
    """The directory holding one vintage's archives: French's 2005 files, or today's."""
    name = _VINTAGE if name is None else name
    if name not in VINTAGES:
        raise ValueError(f"unknown factor vintage {name!r}; choose from {VINTAGES}")
    return VINTAGE_2005_DIR if name == "2005" else FRENCH_DIR


def factor_inputs(vintage: str | None = None) -> list[Path]:
    """The raw factor files a scored run reads, in read order, existing or not.

    ``load_factors``, ``load_losers_only`` and ``load_ibbotson_factors`` read nothing else, so
    a guard over this list reaches every input the tables depend on. The reversal archive and
    the decile archive are today's files whatever the vintage (see the module notes), and
    Goyal and Welch's predictor workbook only feeds Table 4's Ibbotson model.
    """
    name = _VINTAGE if vintage is None else vintage
    directory = vintage_dir(name)
    archive = FACTOR_FILES_2005 if name == "2005" else FACTOR_FILES
    paths = [directory / filename for filename in archive]
    paths.append(FRENCH_DIR / "F-F_ST_Reversal_Factor_CSV.zip")
    paths.append(FRENCH_DIR / LOSERS_FILE)
    paths.append(GOYAL_WELCH)
    seen: set[Path] = set()
    out = []
    for path in paths:
        if path not in seen:
            seen.add(path)
            out.append(path)
    return out


def factor_problem_files(paths: list[Path] | None = None) -> list[tuple[Path, str]]:
    """(path, why) for the factor files that cannot be read as data.

    ``why`` is one of ``"missing"`` (no such file) and ``"git-lfs pointer"`` (the file exists
    but holds Git's pointer line, because ``git lfs pull`` has not run in this checkout). A
    real archive answers an empty list. ``paths`` defaults to ``factor_inputs()``.
    """
    problems = []
    for path in factor_inputs() if paths is None else paths:
        path = Path(path)
        if not path.exists():
            problems.append((path, "missing"))
            continue
        if is_lfs_pointer(path):
            problems.append((path, "git-lfs pointer"))
    return problems


def is_lfs_pointer(path: str | Path) -> bool:
    """Whether one file is Git's pointer stub rather than the data it names."""
    path = Path(path)
    if not path.exists():
        return False
    with path.open("rb") as handle:
        return handle.read(len(LFS_POINTER_PREFIX)) == LFS_POINTER_PREFIX


def load_factors(french_dir: Path | None = None,
                 vintage: str | None = None) -> pd.DataFrame:
    """Monthly market, SMB, HML, momentum, reversal and the T-bill rate, indexed by month end.

    ``vintage="2005"`` reads French's 2005 archives in their plain-text layout (the files the
    paper had; see ``VINTAGE_2005_DIR``), ``vintage="current"`` today's CSV files, and the
    default is the module's ``set_vintage`` choice. ``french_dir`` names the directory to read
    instead of the vintage's own.

    Raises ``FileNotFoundError`` when a file is missing or is still a Git LFS pointer.
    """
    name = _VINTAGE if vintage is None else vintage
    directory = Path(french_dir) if french_dir is not None else vintage_dir(name)
    if name == "2005":
        frames = []
        for filename, rename in FACTOR_FILES_2005.items():
            block = _txt_monthly_block(_french_text(directory / filename))
            frames.append(block[list(rename)].rename(columns=rename))
        # the reversal column is today's ST_Rev either way: French added it to the library
        # in 2006, after the paper, and its block is a decile spread, not a revision
        block = _monthly_block(_french_text(FRENCH_DIR / "F-F_ST_Reversal_Factor_CSV.zip"))
        block.columns = [c.strip() for c in block.columns]
        frames.append(block[["ST_Rev"]].rename(columns={"ST_Rev": "reversal"}))
        return pd.concat(frames, axis=1, join="inner")
    frames = []
    for filename, rename in FACTOR_FILES.items():
        block = _monthly_block(_french_text(directory / filename))
        block.columns = [c.strip() for c in block.columns]
        frames.append(block[list(rename)].rename(columns=rename))
    return pd.concat(frames, axis=1, join="inner")


def load_losers_only(french_dir: Path | None = None,
                     vintage: str | None = None) -> pd.Series:
    """Equal-weighted prior-month losers (French's deciles 1-3) in excess of the T-bill.

    A long-only series with no short leg: the reversal factor the paper's Table 8 regressions
    imply (standard deviation 0.0685 before 1989 against the printed 0.0723, correlations with
    market, SMB, HML and momentum +0.84 / +0.77 / -0.20 / -0.12 against an implied +0.81 / +0.79 /
    -0.18 / -0.16). An unscored alternative, not the factor the paper describes.

    The deciles are today's: the earliest archived prior-return file is from 2007 and matches
    them, so only the excess return changes with the vintage (``vintage``'s ``RF``).
    """
    decile_dir = Path(french_dir) if french_dir is not None else FRENCH_DIR
    deciles = _monthly_block(_french_text(decile_dir / LOSERS_FILE),
                             "Equal Weighted Returns -- Monthly")
    rf = load_factors(french_dir, vintage)["rf"]
    losers = deciles.iloc[:, :3].mean(axis=1)
    return (losers - rf).dropna().rename("reversal")


def factor_regression(y: pd.Series, factors: pd.DataFrame) -> pd.Series:
    """OLS of ``y`` on ``factors`` with an intercept: intercept, one loading per column, R2.

    Months missing from either side are dropped. Coefficients only; the paper's
    Newey-West t-statistics come from ``factor_tstats``.
    """
    data = pd.concat([pd.Series(y, name="y"), factors], axis=1, join="inner").dropna()
    if len(data) <= factors.shape[1] + 1:
        return pd.Series(np.nan, index=["intercept", *factors.columns, "r2"])
    X = np.column_stack([np.ones(len(data)), data[factors.columns].to_numpy()])
    yv = data["y"].to_numpy()
    beta, *_ = np.linalg.lstsq(X, yv, rcond=None)
    resid = yv - X @ beta
    r2 = 1.0 - resid @ resid / ((yv - yv.mean()) @ (yv - yv.mean()))
    return pd.Series([*beta, r2], index=["intercept", *factors.columns, "r2"])


def factor_tstats(y: pd.Series, factors: pd.DataFrame, lags: int = 6) -> pd.Series:
    """Newey-West t-statistics of the same regression: intercept and one per loading.

    The paper's estimator ("Newey-West correction with six lags", Tables 4 and 8): the
    Bartlett-weighted sum of the score autocovariances up to ``lags``, with no small-sample
    degrees-of-freedom correction (the paper states none).
    """
    data = pd.concat([pd.Series(y, name="y"), factors], axis=1, join="inner").dropna()
    names = ["intercept", *factors.columns]
    if len(data) <= factors.shape[1] + 1:
        return pd.Series(np.nan, index=names)
    X = np.column_stack([np.ones(len(data)), data[factors.columns].to_numpy()])
    yv = data["y"].to_numpy()
    beta, *_ = np.linalg.lstsq(X, yv, rcond=None)
    scores = X * (yv - X @ beta)[:, None]
    meat = scores.T @ scores
    for lag in range(1, lags + 1):
        cross = scores[lag:].T @ scores[:-lag]
        meat += (1 - lag / (lags + 1)) * (cross + cross.T)
    bread = np.linalg.inv(X.T @ X)
    se = np.sqrt(np.diag(bread @ meat @ bread))
    return pd.Series(beta / se, index=names)


def factor_residuals(y: pd.Series, factors: pd.DataFrame) -> pd.Series:
    """Residuals of the same regression (intercept excluded), indexed like ``y``."""
    coef = factor_regression(y, factors)
    data = pd.concat([pd.Series(y, name="y"), factors], axis=1, join="inner").dropna()
    fitted = data[factors.columns].to_numpy() @ coef[factors.columns].to_numpy()
    return pd.Series(data["y"].to_numpy() - coef["intercept"] - fitted, index=data.index)


def _month_end(dates) -> pd.DatetimeIndex:
    return pd.DatetimeIndex(pd.to_datetime(dates)) + pd.offsets.MonthEnd(0)


def small_company_stocks(monthly: pd.DataFrame, dfa: pd.Series) -> pd.Series:
    """Ibbotson's small-company return series, rebuilt: CRSP through 1981, then the DFA fund.

    ``monthly`` holds CRSP monthly stock rows (``permno``, ``mthcaldt``, ``primaryexch``,
    ``securitytype``, ``sharetype``, ``mthcap``, ``mthret``, ``mthretx``) from January 1961.
    Portfolios are formed at December 1960, 1965, 1970, 1975 and 1980 from the NYSE common
    stocks in the bottom fifth by capitalization and held for five years, value weighted with
    buy-and-hold weights; a stock that stops trading drops out. ``dfa`` is the DFA Small
    Company fund's monthly return, used from 1982.
    """
    m = monthly.copy()
    m["d"] = _month_end(m["mthcaldt"])
    m = m[m["d"] <= pd.Timestamp("1981-12-31")]
    # December 1960's capitalization is backed out of January 1961's.
    jan = m[m["d"] == pd.Timestamp("1961-01-31")].copy()
    jan["d"] = pd.Timestamp("1960-12-31")
    jan["mthcap"] = jan["mthcap"] / (1 + jan["mthretx"])
    jan["mthret"] = np.nan
    m = pd.concat([jan, m]).drop_duplicates(["d", "permno"])
    cap = m.pivot(index="d", columns="permno", values="mthcap")
    ret = m.pivot(index="d", columns="permno", values="mthret")
    info = m.set_index(["d", "permno"])
    out = {}
    for year in (1960, 1965, 1970, 1975, 1980):
        start = pd.Timestamp(f"{year}-12-31")
        if start not in cap.index:
            continue
        rows = info.loc[start]
        ok = ((rows["primaryexch"] == "N") & (rows["securitytype"] == "EQTY")
              & (rows["sharetype"] == "NS") & (rows["mthcap"] > 0))
        caps = rows.loc[ok, "mthcap"].sort_values()
        small = caps.index[: round(len(caps) * 0.2)]
        weight = cap.loc[start, small]
        for month in pd.date_range(start + pd.offsets.MonthEnd(1), periods=60, freq="ME"):
            if month not in ret.index:
                break
            r = ret.loc[month, small]
            live = r.notna() & weight.notna() & (weight > 0)
            out[month] = float((weight[live] * r[live]).sum() / weight[live].sum())
            weight = weight * (1 + r)
    crsp = pd.Series(out, dtype=float).sort_index()
    dfa = pd.Series(dfa, dtype=float)
    return pd.concat([crsp[crsp.index < DFA_START], dfa[dfa.index >= DFA_START]]).dropna()


def load_ibbotson_factors(goyal_path: Path = GOYAL_WELCH,
                          wrds_dir: Path = WRDS_API_DIR) -> pd.DataFrame:
    """Table 4's Ibbotson factors, monthly, as geometric differences (see the module notes).

    Raises ``FileNotFoundError`` when an input is missing or still a Git LFS pointer, and
    ``ImportError`` when no reader for the ``.xls`` file is installed.
    """
    goyal_path = Path(goyal_path)
    if not goyal_path.exists():
        raise FileNotFoundError(f"{goyal_path} not found")
    if is_lfs_pointer(goyal_path):
        raise FileNotFoundError(f"{goyal_path} is a Git LFS pointer; run `git lfs pull`")
    gw = pd.read_excel(goyal_path, sheet_name="Monthly")
    gw.index = _month_end(gw["yyyymm"].astype(int).astype(str).str.cat(["01"] * len(gw)))
    sp = pd.read_parquet(wrds_dir / "sp500_monthly.parquet", columns=["caldt", "vwretd"])
    tb = pd.read_parquet(wrds_dir / "treasuries_monthly.parquet", columns=["caldt", "t30ret"])
    dfa = pd.read_parquet(wrds_dir / "dfscx_monthly.parquet", columns=["caldt", "mret"])
    monthly = pd.read_parquet(wrds_dir / "monthly_stocks.parquet", columns=[
        "permno", "mthcaldt", "primaryexch", "securitytype", "sharetype", "mthcap", "mthret",
        "mthretx"])
    large = pd.Series(sp["vwretd"].to_numpy(), index=_month_end(sp["caldt"]))
    bill = pd.Series(tb["t30ret"].to_numpy(), index=_month_end(tb["caldt"]))
    small = small_company_stocks(monthly, pd.Series(dfa["mret"].to_numpy(),
                                                    index=_month_end(dfa["caldt"])))
    frame = pd.DataFrame({
        "market": (large - bill if _IBBOTSON_MARKET == "excess"
                   else (1 + large) / (1 + bill) - 1),
        "small_premium": (1 + small) / (1 + large) - 1,
        "default_premium": (1 + gw["corpr"]) / (1 + gw["ltr"]) - 1,
        "horizon_premium": (1 + gw["ltr"]) / (1 + bill) - 1,
    })
    return frame.dropna()

