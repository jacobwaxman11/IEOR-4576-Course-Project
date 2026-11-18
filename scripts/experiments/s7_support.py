"""Does anything outside the score support the S7 universe? Referee tests (contract R7-D).

S7 (REVIEW_NOTES 81, claims/FULLSET_RESCORE.md section 4) drops the ``sharetype='NS'``
filter from the formation universe. It scores 417.5 against the shipped 411.0. The rule
for an unstated convention is independent, non-fitted support, so this script measures
only the handles the score does not reward, plus the 1999 NBER draft as a veto, and
reads the shipped (``NS``) cache against the wide caches built by contract R6-A:

    ns      data/processed/replication/vol_common     (shipped, 411.0)
    s7all   /tmp/S/s7all  SB + AD + CE, 1690 permnos  (417.5 on R6-A's base)
    s7      /tmp/S/s7     SB + AD,      1677 permnos  (414.5)
    s7sb    /tmp/S/s7sb   SB only,       299 permnos  (408.0)
    s7ad    /tmp/S/s7ad   AD only,      1378 permnos  (418.0)

Two subcommands; every read is of a cache or of ``data/raw`` / ``data/processed/crsp``,
and every write goes to ``--out`` (or the driver's ``--out-root``):

``check`` runs the shipped driver (``03_replicate.py --aggregate-only``) on one cache
with its ``_mark`` wrapped, so each scored cell of the check is recorded at full
precision (the markdown rounds to three digits), and writes ``cells.json`` beside the
check. The cell list is the check's own: the same regex ``replication_score.py`` uses,
asserted to add up to the printed score.

``report`` reads the caches and the ``cells.json`` files and writes, to ``--out``:

    counts.csv / counts.md        pairs, stocks and p. 812's sector counts per cohort,
                                  over 474 / first 408 / last 66 cohorts and three eras
    table2a.csv                   Table 2 Panel A as the check computes it (wait 1,
                                  complete cohorts) for every cache
    edition1999.csv / .json       the draft's 136 cells (408 cohorts) for every cache
    added.csv                     per (variant, cohort, permno) added stock: map class,
                                  raw share type / exchange / US-incorporation flag on the
                                  label day, and whether it sits in a top-5 / top-20 /
                                  101-120 pair
    slots.csv                     per (variant, cohort, portfolio) pair slots that hold an
                                  added leg (direct), an NS pair moved in by rank shifts
                                  (indirect), or the NS pair itself (same)
    changes_<variant>.csv         every cell whose mark differs from ``ns``, with both
                                  gaps, the band edge crossed, each side's distance from
                                  it, and the composition of the cell's portfolio window
    margins.md                    the summary tables S7_SUPPORT.md quotes

Reproduce (from the worktree root; about 2 min per check at one worker, 3 min report):

    Q=$(git rev-parse --show-toplevel)
    R=$Q/data/processed/replication
    SIDE="--table9a-cache $R/vol_common_top3 --table9b-cache $R/vol_common_recalls_r1 \
      --table6-cache $R/vol_common_t6_book --delist-cache $R/vol_common_delist100"
    P=$Q/.venv/bin/python
    OMP_NUM_THREADS=2 $P scripts/experiments/s7_support.py check -- --universe vol_common \
      --aggregate-only --workers 1 --cache-root $R/vol_common $SIDE \
      --out-root $PWD/.private/s7d2/ns --steps tables,table3,figure1,check
    OMP_NUM_THREADS=2 $P scripts/experiments/s7_support.py check -- --universe vol_common \
      --aggregate-only --workers 1 --cache-root /tmp/S/s7all $SIDE \
      --share-classes wide --share-classes-file /tmp/allcls.parquet \
      --out-root $PWD/.private/s7d2/s7all --steps tables,table3,figure1,check
    # s7ad: --share-classes-file /tmp/ad_only.parquet; s7 and s7sb were stamped before the
    # map hash was, so they read with --share-classes-file none (the stamp has no map);
    # s7full: --cache-root $Q/.review/r7/A/wide_main with its maps/shareclass_all.parquet.
    # check asserts the "2005 archives" paragraph is in the check it just wrote, so a run
    # that picked up today's factor files cannot be compared with the shipped 411.0.
    $P scripts/experiments/s7_support.py report --out $Q/.review/r7/D/report \
      --cells ns=.private/s7d2/ns --cells s7all=.private/s7d2/s7all ...  # one per variant

No WRDS connection, no cohort build, no write under ``data/``.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

Q = ROOT
NS_CACHE = Q / "data" / "processed" / "replication" / "vol_common"
#: name -> (cache root, permno map it was built with). s7's map is R6-A's default
#: ``data/raw/shareclass_sb_ad.parquet`` of worktree r5-S; /tmp/sbmix.parquet is the
#: same file (sha256 178de40c806b).
VARIANTS = {
    "s7all": ("/tmp/S/s7all", "/tmp/allcls.parquet"),
    "s7": ("/tmp/S/s7", "/tmp/sbmix.parquet"),
    "s7sb": ("/tmp/S/s7sb", "/tmp/sb_only.parquet"),
    "s7ad": ("/tmp/S/s7ad", "/tmp/ad_only.parquet"),
    # Contract R7-A's complete EQTY/COM set, SB + AD + UG + CE (2079 permnos, sha256
    # 5433e8b4be8d), read from its scratch: the one no-selection reading.
    "s7full": (str(Q / ".review/r7/A/wide_main"),
               str(Q / ".review/r7/A/maps/shareclass_all.parquet")),
}
CLASS_MAPS = {"SB": "/tmp/sb_only.parquet", "AD": "/tmp/ad_only.parquet",
              "ALL": "/tmp/allcls.parquet"}

PORTFOLIOS = ("top5", "top20", "101-120", "all")
RANKS = {"top5": (1, 5), "top20": (1, 20), "101-120": (101, 120), "all": None}
SECTORS = ("Utilities", "Transportation", "Financials", "Industrials")
#: p. 812 (Table 3 caption); p. 807 etc. (2057); NBER w7032 p. 25-26 (1870, 408 cohorts).
PAPER_SECTORS = {"Utilities": 156, "Transportation": 61, "Financials": 371, "Industrials": 1729}
PAPER_PAIRS, DRAFT_PAIRS = 2057.0, 1870.0
IMPLIED_LATE_PAIRS = (474 * PAPER_PAIRS - 408 * DRAFT_PAIRS) / 66
#: Table 2 Panel A, pairs traded per six-month period (p. 809), and the draft's Table II A.
PAPER_T2A_TRADED = {"top5": 4.81, "top20": 19.30, "101-120": 19.41, "all": 1944.22}
DRAFT_T2A_TRADED = {"top5": 4.97, "top20": 19.81, "101-120": 19.77, "all": 1814.46}

SPLIT_1989 = "1989-01"   # Table 8's subperiods, by the cohort's first trading month
ERAS = (("1963-07..1988-12", "1963-07", "1988-12"),
        ("1989-01..1997-06", "1989-01", "1997-06"),
        ("1997-07..2002-12", "1997-07", "2002-12"))
WINDOWS = {
    "all 474": ("1963-07", "2002-12"),
    "first 408": ("1963-07", "1997-06"),
    "last 66": ("1997-07", "2002-12"),
    "pre-1989": ("1963-07", "1988-12"),
    "post-1988": ("1989-01", "2002-12"),
    # section 1.2's hold-out: trading months 1999-2002, i.e. cohorts starting 1998-08 on
    "1999-2002": ("1998-08", "2002-12"),
}

CELL = re.compile(r"^\s*(?P<o>.+?) / (?P<p>.+?)\s+(?P<m>✓|~|✗)\s*$")
EDGES = (0.10, 0.25)


# --------------------------------------------------------------------------- check


def _driver():
    spec = importlib.util.spec_from_file_location("repl03_s7d", ROOT / "scripts" / "03_replicate.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["repl03_s7d"] = module
    spec.loader.exec_module(module)
    return module


def _number(text: str) -> tuple[float, float] | None:
    """A printed cell value and half a unit of its last printed digit."""
    s = text.strip()
    pct = s.endswith("%")
    if pct:
        s = s[:-1]
    m = re.fullmatch(r"([-+]?)(\d*)(?:\.(\d*))?(?:e([-+]?\d+))?", s)
    if not m or not (m.group(2) or m.group(3)):
        return None
    try:
        value = float(s)
    except ValueError:
        return None
    decimals = len(m.group(3) or "")
    exp = int(m.group(4) or 0)
    half = 0.5 * 10.0 ** (exp - decimals)
    if pct:
        value, half = value / 100, half / 100
    return value, half


def parse_check(path: Path) -> list[dict]:
    """Every marked "ours / paper" cell of the check, in document order."""
    lines = path.read_text(encoding="utf-8").splitlines()
    cells, section, header = [], "", []
    seen: dict[tuple, int] = {}
    for i, line in enumerate(lines):
        if line.startswith("#"):
            section, header = line.lstrip("#").strip(), []
            continue
        if not line.lstrip().startswith("|"):
            continue
        parts = [c.strip() for c in line.strip().strip("|").split("|")]
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        if nxt.lstrip().startswith("|---"):
            header = parts
            continue
        if " / " not in line:
            continue
        for j, body in enumerate(parts[1:], start=1):
            m = CELL.match(body)
            if not m:
                continue
            col = header[j] if j < len(header) else f"col{j}"
            key = (section, parts[0], col)
            seen[key] = seen.get(key, 0) + 1
            if seen[key] > 1:
                key = (section, f"{parts[0]} #{seen[key]}", col)
            cells.append({"section": key[0], "row": key[1], "col": key[2],
                          "ours_text": m.group("o"), "paper_text": m.group("p"),
                          "mark": m.group("m")})
    return cells


def _attach(cells: list[dict], records: list[tuple[float, float, str]]) -> int:
    """Give each parsed cell the full-precision (ours, paper) its ``_mark`` call saw."""
    used = [False] * len(records)
    ptr, matched = 0, 0

    def fits(k: int, cell: dict, o: tuple | None, p: tuple | None) -> bool:
        ro, rp, rm = records[k]
        if used[k] or not (rm == cell["mark"] or (rm == "" and rp == 0)):
            return False
        if o is None or p is None:
            return False
        return (abs(ro - o[0]) <= o[1] * 1.001 + 1e-12
                and abs(rp - p[0]) <= p[1] * 1.001 + 1e-12)

    for cell in cells:
        o, p = _number(cell["ours_text"]), _number(cell["paper_text"])
        hit = next((k for k in range(ptr, len(records)) if fits(k, cell, o, p)), None)
        if hit is None:
            hit = next((k for k in range(len(records)) if fits(k, cell, o, p)), None)
        if hit is None:
            cell["ours"], cell["paper"], cell["exact"] = (
                o[0] if o else np.nan, p[0] if p else np.nan, False)
            continue
        used[hit] = True
        ptr = hit + 1
        matched += 1
        cell["ours"], cell["paper"], cell["exact"] = records[hit][0], records[hit][1], True
    return matched


def cmd_check(driver_args: list[str]) -> int:
    driver = _driver()
    records: list[tuple[float, float, str]] = []
    original = driver._mark

    def recording_mark(ours, paper):
        mark = original(ours, paper)
        records.append((float(ours), float(paper), mark))
        return mark

    driver._mark = recording_mark
    sys.argv = ["03_replicate.py", *driver_args]
    driver.main()
    out_root = Path(driver_args[driver_args.index("--out-root") + 1])
    check = out_root / "tables" / "replication_check.md"
    cells = parse_check(check)
    matched = _attach(cells, records)
    marks = [c["mark"] for c in cells]
    score = marks.count("✓") + 0.5 * marks.count("~")
    printed = re.search(r"^- Score: ([\d.]+) of (\d+)", check.read_text(encoding="utf-8"), re.MULTILINE)
    assert printed and float(printed.group(1)) == score and int(printed.group(2)) == len(cells), (
        f"parsed {score} of {len(cells)} against the printed {printed and printed.groups()}")
    (out_root / "cells.json").write_text(json.dumps(cells, ensure_ascii=False, indent=1))
    # The shipped check is the 2005-vintage one (COMMON_R7's factor-vintage trap): a run
    # that silently picked up today's files would not be comparable to 411.0.
    vintage = (driver_args[driver_args.index("--factor-vintage") + 1]
               if "--factor-vintage" in driver_args else "2005")
    has_2005 = "2005 archives" in check.read_text(encoding="utf-8")
    if vintage == "2005" and not has_2005:
        raise SystemExit(f"{check} has no '2005 archives' paragraph but asked for the 2005 vintage")
    print(f"cells.json: {len(cells)} cells, score {score}, {matched} at full precision, "
          f"factor vintage {vintage} (2005 paragraph: {has_2005})")
    return 0


# --------------------------------------------------------------------------- report


def cohort_names() -> list[str]:
    return [p.strftime("%Y-%m") for p in pd.period_range("1963-07", "2002-12", freq="M")]


def _in(c: str, window: tuple[str, str]) -> bool:
    return window[0] <= c <= window[1]


def _era(c: str) -> str:
    return next(name for name, a, b in ERAS if a <= c <= b)


def load_summaries(root: Path) -> pd.DataFrame:
    rows = []
    for c in cohort_names():
        s = json.loads((root / "cohorts" / c / "summary.json").read_text())
        row = {"cohort": c, "stocks": s["stocks"], "pairs": s["pairs"],
               "opened_w1": s.get("opened_w1", np.nan)}
        for sec in SECTORS:
            row[sec] = s["sector_counts"][sec]
        for p in PORTFOLIOS:
            row[f"traded_{p}"] = s["trading"][p]["n_opened"]
        rows.append(row)
    return pd.DataFrame(rows).set_index("cohort")


def counts_table(frames: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, str]:
    """Pairs and stocks per cohort, and the sector counts, by window and era."""
    out = []
    windows = {**{k: WINDOWS[k] for k in ("all 474", "first 408", "last 66")},
               **{name: (a, b) for name, a, b in ERAS}}
    for name, f in frames.items():
        for wname, w in windows.items():
            sub = f[[_in(c, w) for c in f.index]]
            rec = {"cache": name, "window": wname, "cohorts": len(sub),
                   "pairs": sub["pairs"].mean(), "stocks": sub["stocks"].mean(),
                   "pairs_per_stock": (sub["pairs"] / sub["stocks"]).mean()}
            for sec in SECTORS:
                rec[sec] = sub[sec].mean()
            out.append(rec)
    table = pd.DataFrame(out)
    md = ["| cache | window | cohorts | pairs | stocks | Util | Transp | Fin | Indus |",
          "|---|---|---|---|---|---|---|---|---|"]
    for _, r in table.iterrows():
        md.append(f"| {r.cache} | {r.window} | {r.cohorts} | {r.pairs:,.1f} | {r.stocks:,.1f} | "
                  f"{r.Utilities:.1f} | {r.Transportation:.1f} | {r.Financials:.1f} | "
                  f"{r.Industrials:,.1f} |")
    return table, "\n".join(md)


def table2a_rows(frames_dirs: dict[str, Path]) -> pd.DataFrame:
    from project.evaluation import trading_stats_from_components
    rows = []
    names = cohort_names()
    for name, root in frames_dirs.items():
        comps = {p: [] for p in PORTFOLIOS}
        for c in names:
            s = json.loads((root / "cohorts" / c / "summary.json").read_text())
            for p in PORTFOLIOS:
                comps[p].append(s["trading"][p])
        for p in PORTFOLIOS:
            stats = trading_stats_from_components(comps[p], names, completed=True)
            complete = sum(not x.get("censored", False) for x in comps[p])
            rows.append({"cache": name, "portfolio": p, "complete_cohorts": complete,
                         **stats.to_dict()})
    return pd.DataFrame(rows)


def edition_rows(frames_dirs: dict[str, Path]) -> tuple[pd.DataFrame, dict]:
    from project import edition1999 as ed
    rows, summaries = [], {}
    names = ed.cohort_names()
    for name, root in frames_dirs.items():
        cells = ed.score_cohort_dir(root / "cohorts", names)
        summaries[name] = ed.summarize(cells)
        for (table, setting, port, stat), (o, q, m) in cells.items():
            rows.append({"cache": name, "table": table, "setting": setting, "portfolio": port,
                         "statistic": stat, "ours": o, "paper": q, "mark": m})
    return pd.DataFrame(rows), summaries


def _pairs(root: Path, c: str) -> pd.DataFrame:
    return pd.read_parquet(root / "cohorts" / c / "pairs.parquet",
                           columns=["rank", "permno_1", "permno_2"])


def _label_rows(permnos: list[int]) -> pd.DataFrame:
    """Raw CRSP rows of ``permnos``: share type, exchange, incorporation, by day."""
    import pyarrow.dataset as ds

    from project.data import RAW_DAILY_DIR
    cols = ["permno", "dlycaldt", "primaryexch", "securitytype", "securitysubtype",
            "sharetype", "usincflg", "issuertype", "ticker"]
    files = sorted(str(p) for p in RAW_DAILY_DIR.glob("*.parquet")
                   if 1962 <= int(p.stem) <= 2002)
    table = ds.dataset(files, format="parquet").to_table(
        columns=cols, filter=ds.field("permno").isin(sorted(permnos)))
    frame = table.to_pandas()
    frame["dlycaldt"] = pd.to_datetime(frame["dlycaldt"])
    return frame.sort_values(["dlycaldt", "permno"]).reset_index(drop=True)


def added_and_slots(variants: dict[str, tuple[Path, Path]], ns_root: Path
                    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Added stocks per cohort, and the direct / indirect / same pair slots."""
    names = cohort_names()
    sb = set(pd.read_parquet(CLASS_MAPS["SB"])["permno"].astype(int))
    ad = set(pd.read_parquet(CLASS_MAPS["AD"])["permno"].astype(int))
    ce = set(pd.read_parquet(CLASS_MAPS["ALL"])["permno"].astype(int)) - sb - ad
    ns_pairs = {c: _pairs(ns_root, c) for c in names}
    ns_legs = {c: set(f["permno_1"]) | set(f["permno_2"]) for c, f in ns_pairs.items()}
    added_rows, slot_rows, checks = [], [], []
    for name, (root, map_path) in variants.items():
        mp = set(pd.read_parquet(map_path)["permno"].astype(int))
        for c in names:
            w = _pairs(root, c)
            legs = set(w["permno_1"]) | set(w["permno_2"])
            added = legs - ns_legs[c]
            lost = ns_legs[c] - legs
            w_add = w["permno_1"].isin(added) | w["permno_2"].isin(added)
            n = ns_pairs[c]
            n_keys = set(zip(n["permno_1"], n["permno_2"]))
            w_keys = list(zip(w["permno_1"], w["permno_2"]))
            in_ns = np.array([k in n_keys for k in w_keys])
            # NS-NS pairs of the wide cache that the NS cache does not have: by the
            # nearest-neighbour rule there should be none.
            # A cohort the wide map leaves untouched must be the NS cohort to the
            # last return: the engine control for caches built on another branch.
            same_monthly = np.nan
            if not added and not lost:
                a = pd.read_parquet(ns_root / "cohorts" / c / "monthly.parquet")
                b = pd.read_parquet(root / "cohorts" / c / "monthly.parquet")
                same_monthly = float(a.shape == b.shape and np.allclose(
                    a["ret"].to_numpy(float), b["ret"].to_numpy(float), equal_nan=True,
                    rtol=0, atol=1e-12))
            checks.append({"variant": name, "cohort": c, "added_not_in_map": len(added - mp),
                           "ns_legs_lost": len(lost),
                           "new_ns_pairs": int((~w_add.to_numpy() & ~in_ns).sum()),
                           "dropped_ns_pairs": len(n_keys - set(w_keys)),
                           "untouched": int(not added and not lost),
                           "untouched_identical": same_monthly})
            for p, r in RANKS.items():
                if r is None:
                    sel_w = np.ones(len(w), bool)
                    n_win = n_keys
                else:
                    sel_w = ((w["rank"] >= r[0]) & (w["rank"] <= r[1])).to_numpy()
                    nn = n[(n["rank"] >= r[0]) & (n["rank"] <= r[1])]
                    n_win = set(zip(nn["permno_1"], nn["permno_2"]))
                keys_w = [k for k, s in zip(w_keys, sel_w) if s]
                direct = int((w_add.to_numpy() & sel_w).sum())
                same = sum(k in n_win for k in keys_w)
                slot_rows.append({"variant": name, "cohort": c, "portfolio": p,
                                  "slots": int(sel_w.sum()), "direct": direct,
                                  "indirect": int(sel_w.sum()) - direct - same, "same": same,
                                  "ns_slots": len(n_win),
                                  "ns_left": len(n_win - set(keys_w))})
            for permno in added:
                legs_of = w[(w["permno_1"] == permno) | (w["permno_2"] == permno)]["rank"]
                added_rows.append({
                    "variant": name, "cohort": c, "permno": permno,
                    "map_class": ("SB" if permno in sb else "AD" if permno in ad
                                  else "CE" if permno in ce else "UG"),
                    "best_rank": int(legs_of.min()),
                    "in_top5": bool((legs_of <= 5).any()),
                    "in_top20": bool((legs_of <= 20).any()),
                    "in_101_120": bool(((legs_of >= 101) & (legs_of <= 120)).any()),
                })
    added_df = pd.DataFrame(added_rows)
    # Label-day attributes from the raw file: the last row before the cohort's first month.
    raw = _label_rows(sorted(set(added_df["permno"])))
    added_df["start"] = pd.to_datetime(added_df["cohort"] + "-01")
    added_df = added_df.sort_values("start")
    raw = raw.rename(columns={"dlycaldt": "label_day"})
    lab = pd.merge_asof(added_df, raw.sort_values("label_day"), left_on="start",
                        right_on="label_day", by="permno", direction="backward",
                        allow_exact_matches=False)
    lab["era"] = lab["cohort"].map(_era)
    return lab.drop(columns=["start"]), pd.DataFrame(slot_rows), pd.DataFrame(checks)


# ----------------------------------------------------------------- cell changes


def _gap(o: float, p: float) -> float:
    return abs(o / p - 1) if p else np.nan


def _crossed(g0: float, g1: float) -> list[float]:
    lo, hi = min(g0, g1), max(g0, g1)
    return [e for e in EDGES if lo < e <= hi or lo <= e < hi]


def cell_scope(section: str, row: str, col: str) -> tuple[tuple[str, ...], str, str | None]:
    """(portfolios, window, sector) a check cell is computed from; () when the cell
    reads a side cache or factor data that the formation universe cannot move."""
    port = {"top5": "top5", "top20": "top20", "101-120": "101-120", "all": "all"}
    if section.startswith("Table 3 stocks"):
        return (), "all 474", row
    if section.startswith("Table 3:"):
        sector = section.split(":")[1].split("(")[0].strip()
        return (port.get(col, col),), "all 474", sector
    if section.startswith("Table 8"):
        if row.startswith("factor sd"):
            return (), "", None
        window = "pre-1989" if "pre_" in row else "post-1988"
        return (port.get(col, col),), window, None
    if section.startswith("Figure 4"):
        window = ("pre-1989" if "before 1989" in row else
                  "post-1988" if "after 1988" in row else "all 474")
        return ("top20", "101-120"), window, None
    if section.startswith("Numbers printed"):
        if "average number of pairs" in row:
            return ("all",), "all 474", None
        if "delisting" in section or row in ("mean monthly return", "standard deviation"):
            return (), "", None  # footnote 4: the shared --delist-cache
        return ("top20",), "1999-2002", None
    if section.startswith(("Table 9", "Table 6")):
        return (), "", None  # side caches, shared and unchanged
    if col in port:
        return (port[col],), "all 474", None
    return (), "", None


def compare_cells(base: list[dict], other: list[dict]) -> pd.DataFrame:
    b = {(c["section"], c["row"], c["col"]): c for c in base}
    rows = []
    for c in other:
        k = (c["section"], c["row"], c["col"])
        if k not in b:
            continue
        c0 = b[k]
        g0, g1 = _gap(c0["ours"], c0["paper"]), _gap(c["ours"], c["paper"])
        crossed = _crossed(g0, g1) if c0["mark"] != c["mark"] else []
        edge0 = min(crossed, key=lambda e: abs(g0 - e)) if crossed else (
            min(EDGES, key=lambda e: abs(g0 - e)))
        edge1 = min(crossed, key=lambda e: abs(g1 - e)) if crossed else edge0
        pts = {"✓": 1.0, "~": 0.5, "✗": 0.0}
        rows.append({"section": k[0], "row": k[1], "col": k[2], "paper": c0["paper"],
                     "ours_ns": c0["ours"], "ours_wide": c["ours"],
                     "mark_ns": c0["mark"], "mark_wide": c["mark"],
                     "delta": pts[c["mark"]] - pts[c0["mark"]],
                     "gap_ns": g0, "gap_wide": g1,
                     "edge": edge0 if crossed else np.nan,
                     "dist_ns": abs(g0 - edge0), "dist_wide": abs(g1 - edge1),
                     "nearest_edge_ns": min(abs(g0 - e) for e in EDGES),
                     "exact": bool(c0.get("exact")) and bool(c.get("exact"))})
    return pd.DataFrame(rows)


def attribute(changes: pd.DataFrame, slots: pd.DataFrame, added: pd.DataFrame,
              counts_ns: pd.DataFrame, counts_w: pd.DataFrame, variant: str) -> pd.DataFrame:
    """The composition of each changed cell's portfolio window under ``variant``."""
    s = slots[slots["variant"] == variant]
    out = []
    for _, r in changes.iterrows():
        ports, window, sector = cell_scope(r["section"], r["row"], r["col"])
        rec = {"direct_share": np.nan, "indirect_share": np.nan, "changed_cohorts": np.nan,
               "sector_added_per_cohort": np.nan, "sector_cohorts_with_added": np.nan,
               "scope": f"{'/'.join(ports) or '-'} | {window or '-'} | {sector or '-'}"}
        if window and ports and sector is None:
            w = WINDOWS[window]
            sub = s[s["portfolio"].isin(ports) & s["cohort"].between(*w)]
            tot = sub["slots"].sum()
            rec["direct_share"] = sub["direct"].sum() / tot if tot else np.nan
            rec["indirect_share"] = sub["indirect"].sum() / tot if tot else np.nan
            per = sub.groupby("cohort")[["direct", "indirect"]].sum().sum(axis=1)
            rec["changed_cohorts"] = float((per > 0).mean())
        if sector is not None:
            d = counts_w[sector] - counts_ns[sector]
            rec["sector_added_per_cohort"] = d.mean()
            rec["sector_cohorts_with_added"] = float((d > 0).mean())
            # Table 3's within-sector pairs are not cached, so no slot shares: a sector
            # cohort can only differ when an added stock lands in that sector.
        out.append(rec)
    return pd.concat([changes.reset_index(drop=True), pd.DataFrame(out)], axis=1)


def paper_md(counts: pd.DataFrame, t2a: pd.DataFrame, ed_rows: pd.DataFrame) -> str:
    """Each count handle against its printed value, like for like, as ours / paper - 1."""
    def rel(o: float, p: float) -> str:
        return f"{o:,.1f} ({o / p - 1:+.1%})"

    c = counts.set_index(["cache", "window"])
    caches = list(dict.fromkeys(counts["cache"]))
    head = "| handle (window) | printed | " + " | ".join(caches) + " |"
    lines = [head, "|---|---|" + "---|" * len(caches)]

    def row(label: str, printed: float, values: list[float]) -> None:
        lines.append(f"| {label} | {printed:,.2f} | " + " | ".join(
            rel(v, printed) for v in values) + " |")

    row("pairs per cohort, all-pair portfolio (474 cohorts; RFS captions)", PAPER_PAIRS,
        [c.loc[(k, "all 474"), "pairs"] for k in caches])
    row("pairs per cohort (first 408 cohorts; 1999 draft Tables I-II)", DRAFT_PAIRS,
        [c.loc[(k, "first 408"), "pairs"] for k in caches])
    row("pairs per cohort (last 66; implied, hypothesis)", IMPLIED_LATE_PAIRS,
        [c.loc[(k, "last 66"), "pairs"] for k in caches])
    row("stocks per cohort, sum of p. 812's four sectors (474)", sum(PAPER_SECTORS.values()),
        [c.loc[(k, "all 474"), "stocks"] for k in caches])
    for sec, printed in PAPER_SECTORS.items():
        row(f"{sec} stocks per cohort (474; p. 812)", printed,
            [c.loc[(k, "all 474"), sec] for k in caches])
    t = t2a.set_index(["cache", "portfolio"])
    for p, printed in PAPER_T2A_TRADED.items():
        n = int(t.loc[(caches[0], p), "complete_cohorts"])
        row(f"Table 2 A pairs traded, {p} (wait 1, {n} complete cohorts; p. 809)", printed,
            [t.loc[(k, p), "avg_pairs_traded_per_period"] for k in caches])
    e = ed_rows[(ed_rows["table"] == "Table II A") & (ed_rows["statistic"] == "pairs traded")]
    e = e.set_index(["cache", "portfolio"])
    for p, printed in DRAFT_T2A_TRADED.items():
        row(f"draft Table II A pairs traded, {p} (wait 0, first 408)", printed,
            [e.loc[(k, p), "ours"] for k in caches])
    return "\n".join(lines)


#: (474 x RFS - 408 x draft) / 66 on the rows both editions print; the hypothesis that the
#: published edition's first 408 cohorts are the draft's (late_exchange_universe.py).
IMPLIED_LATE = {"trig_top5": 0.0952, "trig_top20": 0.1016, "trig_101-120": 0.1207,
                "trig_all": 0.2746, "util_top5": 0.164, "util_top20": 0.030,
                "fin_top5": 0.543, "fin_top20": 0.686, "ind_top5": 0.274, "ind_top20": 0.202,
                "mix_top5": 0.441, "mix_top20": 0.531}


def late_profile_md(roots: dict[str, Path]) -> str:
    """The last 66 cohorts' formation profile against the implied late sample."""
    keys = {"util": "weight_utilities", "fin": "weight_financials",
            "ind": "weight_industrials", "mix": "share_mixed_sector_pairs"}
    late = [c for c in cohort_names() if c >= "1997-07"]
    rows = {}
    for name, root in roots.items():
        vals: dict[str, list[float]] = {k: [] for k in IMPLIED_LATE}
        for c in late:
            s = json.loads((root / "cohorts" / c / "summary.json").read_text())
            for k in IMPLIED_LATE:
                kind, p = k.split("_", 1)
                vals[k].append(s["trading"][p]["trigger"] if kind == "trig"
                               else s["composition"][p][keys[kind]])
        rows[name] = {k: float(np.nanmean(v)) for k, v in vals.items()}
    names = list(rows)
    lines = ["| row (last 66 cohorts) | implied | " + " | ".join(names) + " |",
             "|---|---|" + "---|" * len(names)]
    for k, imp in IMPLIED_LATE.items():
        lines.append(f"| {k} | {imp:.3f} | " + " | ".join(
            f"{rows[n][k]:.3f}" for n in names) + " |")
    return "\n".join(lines)


def added_md(added: pd.DataFrame, slots: pd.DataFrame) -> str:
    """Who the added stocks are, and where they land, per variant and era."""
    lines = []
    n_coh = {name: sum(a <= c <= b for c in cohort_names()) for name, a, b in ERAS}
    n_coh["all 474"] = 474
    for v, g in added.groupby("variant", sort=False):
        g = g.assign(era_all="all 474")
        d = g.drop_duplicates("permno")
        cls = d["map_class"].value_counts()
        ever = g.groupby("permno")[["in_top5", "in_top20", "in_101_120"]].any()
        map_path = Path(VARIANTS[v][1])
        carried = len(pd.read_parquet(map_path)) if map_path.exists() else "?"
        lines += [f"### {v}", "",
                  f"Distinct permnos added: {len(d)} of the {carried} the map carries; "
                  f"stock-cohorts {len(g)}; classes "
                  + ", ".join(f"{k} {int(cls.get(k, 0))}" for k in ("SB", "AD", "CE", "UG"))
                  + "; label-day share type "
                  + ", ".join(f"{k} {n}" for k, n in
                              d["sharetype"].value_counts().items()),
                  "",
                  (f"Ever in a top-5 pair: {int(ever['in_top5'].sum())} permnos; top-20: "
                   f"{int(ever['in_top20'].sum())}; 101-120: {int(ever['in_101_120'].sum())}; "
                   f"exchange N/A/Q {int((d['primaryexch'] == 'N').sum())}/"
                   f"{int((d['primaryexch'] == 'A').sum())}/"
                   f"{int((d['primaryexch'] == 'Q').sum())};"
                   f"not US-incorporated {int((d['usincflg'] == 'N').sum())}"), "",
                  ("| era | added per cohort | SB | AD | CE | UG | NYSE | AMEX | Nasdaq | "
                   "non-US inc. | label-day share type NS |"),
                  "|---|---|---|---|---|---|---|---|---|---|---|"]
        for era_col in ("era", "era_all"):
            for era, e in g.groupby(era_col, sort=False):
                k = n_coh[era]
                cls = e["map_class"].value_counts()
                ex = e["primaryexch"].value_counts()
                lines.append(
                    f"| {era} | {len(e) / k:.1f} | {cls.get('SB', 0) / k:.1f} | "
                    f"{cls.get('AD', 0) / k:.1f} | {cls.get('CE', 0) / k:.1f} | "
                    f"{cls.get('UG', 0) / k:.1f} | "
                    f"{ex.get('N', 0) / k:.1f} | {ex.get('A', 0) / k:.1f} | "
                    f"{ex.get('Q', 0) / k:.1f} | {(e['usincflg'] == 'N').mean():.0%} | "
                    f"{(e['sharetype'] == 'NS').mean():.0%} |")
        s = slots[slots["variant"] == v].assign(era=lambda f: f["cohort"].map(_era))
        lines += ["", ("Pair slots holding an added leg (direct) and NS pairs moved in by rank "
                       "shifts (indirect), per cohort; cohorts with at least one direct slot:"), "",
                  "| era | portfolio | slots | direct | indirect | cohorts with direct |",
                  "|---|---|---|---|---|---|"]
        for era in [e[0] for e in ERAS] + ["all 474"]:
            sub = s if era == "all 474" else s[s["era"] == era]
            for p in PORTFOLIOS:
                q = sub[sub["portfolio"] == p]
                lines.append(f"| {era} | {p} | {q['slots'].mean():.1f} | "
                             f"{q['direct'].mean():.2f} | {q['indirect'].mean():.2f} | "
                             f"{(q['direct'] > 0).sum()} of {len(q)} |")
        lines.append("")
    return "\n".join(lines)


def attribution_md(att: pd.DataFrame) -> str:
    """Changed cells by block and portfolio, with the composition of their windows."""
    a = att.copy()
    a["block"] = a["section"].str.split(" \\(").str[0]
    a["port"] = a["scope"].str.split(" \\| ").str[0]
    a["edge_sitter"] = a[["dist_ns", "dist_wide"]].min(axis=1) <= 0.025
    g = a.groupby(["block", "port"], sort=False).agg(
        cells=("delta", "size"), up=("delta", lambda d: int((d > 0).sum())),
        down=("delta", lambda d: int((d < 0).sum())), net=("delta", "sum"),
        within_2_5pp=("edge_sitter", "sum"),
        direct=("direct_share", "mean"), indirect=("indirect_share", "mean"),
        sector_added=("sector_added_per_cohort", "mean"))
    lines = [("| block | portfolio(s) | changed | up | down | net | within 2.5pp of the edge "
              "| direct slot share | indirect slot share | sector stocks added per cohort |"),
             "|---|---|---|---|---|---|---|---|---|---|"]

    def pct(x: float) -> str:
        return "-" if pd.isna(x) else f"{x:.1%}"

    for (block, port), r in g.iterrows():
        sec = "-" if pd.isna(r.sector_added) else f"{r.sector_added:.1f}"
        lines.append(f"| {block} | {port} | {r.cells} | {r.up} | {r.down} | {r.net:+.1f} | "
                     f"{int(r.within_2_5pp)} | {pct(r.direct)} | {pct(r.indirect)} | {sec} |")
    lines.append(f"| total | | {len(a)} | {(a.delta > 0).sum()} | {(a.delta < 0).sum()} | "
                 f"{a.delta.sum():+.1f} | {int(a.edge_sitter.sum())} | | |")
    return "\n".join(lines)


def printed_gap_md(counts: pd.DataFrame) -> str:
    """The six printed stock and pair levels: mean |gap|, and the sector mix."""
    c = counts.set_index(["cache", "window"])
    caches = list(dict.fromkeys(counts["cache"]))
    levels = {"pairs": PAPER_PAIRS, "stocks": sum(PAPER_SECTORS.values()), **PAPER_SECTORS}
    total = sum(PAPER_SECTORS.values())
    lines = ["| cache | mean abs gap, the six printed levels | Util | Transp | Fin | Indus |",
             "|---|---|---|---|---|---|"]
    for k in caches:
        r = c.loc[(k, "all 474")]
        gaps = [abs(r[q] / p - 1) for q, p in levels.items()]
        share = [r[s] / r["stocks"] for s in SECTORS]
        lines.append(f"| {k} | {np.mean(gaps):.2%} | "
                     + " | ".join(f"{v:.2%}" for v in share) + " |")
    lines.append("| printed | - | " + " | ".join(
        f"{PAPER_SECTORS[s] / total:.2%}" for s in SECTORS) + " |")
    return "\n".join(lines)


def _bucket(d: float) -> str:
    return ("<=1pp" if d <= 0.01 else "1-2.5pp" if d <= 0.025 else
            "2.5-5pp" if d <= 0.05 else ">5pp")


def stability_md(ch: pd.DataFrame, all_ns: pd.DataFrame) -> str:
    """Net points by how far each changed cell sits from the edge it crosses."""
    moved = ch[ch["mark_ns"] != ch["mark_wide"]].copy()
    moved["closest"] = moved[["dist_ns", "dist_wide"]].min(axis=1)
    lines = ["| min(distance from edge, NS or wide) | cells | up | down | net points |",
             "|---|---|---|---|---|"]
    for b in ("<=1pp", "1-2.5pp", "2.5-5pp", ">5pp"):
        sub = moved[moved["closest"].map(_bucket) == b]
        lines.append(f"| {b} | {len(sub)} | {(sub.delta > 0).sum()} | {(sub.delta < 0).sum()} "
                     f"| {sub.delta.sum():+.1f} |")
    lines.append(f"| all | {len(moved)} | {(moved.delta > 0).sum()} | {(moved.delta < 0).sum()} "
                 f"| {moved.delta.sum():+.1f} |")
    lines += ["", ("| net counting only changes with both sides more than d from the edge | d "
                   "| cells | net |"), "|---|---|---|---|"]
    for d in (0.01, 0.025, 0.05):
        sub = moved[moved["closest"] > d]
        lines.append(f"| | {d:.1%} | {len(sub)} | {sub.delta.sum():+.1f} |")
    base = all_ns["nearest_edge_ns"]
    lines += ["", ("Share of cells within d of a band edge under NS (all scored cells, against "
                   "the cells that change mark):"), "",
              "| d | all cells | changed cells |", "|---|---|---|"]
    for d in (0.01, 0.025, 0.05):
        lines.append(f"| {d:.1%} | {(base <= d).mean():.1%} ({(base <= d).sum()} of {len(base)}) "
                     f"| {(moved['dist_ns'] <= d).mean():.1%} ({(moved['dist_ns'] <= d).sum()} "
                     f"of {len(moved)}) |")
    move = (moved["gap_wide"] - moved["gap_ns"]).abs()
    rel = (ch["ours_wide"] - ch["ours_ns"]).abs() / ch["ours_ns"].abs().replace(0, np.nan)
    big = moved[move > 0.25]["col"]
    lines += ["", ("How far the values move: cells whose printed number changes at all "
                   f"{int(ch['ours_ns'].ne(ch['ours_wide']).sum())} of {len(ch)}, "
                   f"{int((rel > 1e-4).sum())} of them by more than 0.01%; among the changed "
                   f"marks the |gap| movement is median {move.median():.3f}, "
                   f">10pp {int((move > 0.10).sum())}, >25pp {int((move > 0.25).sum())}, "
                   f"max {move.max():.2f}; {int((big == '101-120').sum())} of the >25pp movers "
                   "sit in the 101-120 column.")]
    return "\n".join(lines)


def _md(frame: pd.DataFrame, fmt: str = "{:g}") -> str:
    """A DataFrame as a markdown table (the venv has no ``tabulate``)."""
    cols = [str(frame.index.name or "")] + [str(c) for c in frame.columns]
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for idx, row in frame.iterrows():
        vals = [fmt.format(v) if isinstance(v, (int, float, np.number)) else str(v) for v in row]
        lines.append(f"| {idx} | " + " | ".join(vals) + " |")
    return "\n".join(lines)


def cmd_report(args: argparse.Namespace) -> int:
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    variants = {k: (Path(r), Path(m)) for k, (r, m) in VARIANTS.items()
                if k in args.variants}
    roots = {"ns": NS_CACHE, **{k: v[0] for k, v in variants.items()}}
    md = []

    # 1-2. counts
    frames = {k: load_summaries(r) for k, r in roots.items()}
    pd.concat({k: f for k, f in frames.items()}, names=["cache"]).to_csv(out / "counts.csv")
    counts, counts_md = counts_table(frames)
    counts.to_csv(out / "counts_windows.csv", index=False)
    md += ["## Counts by window", "", counts_md, ""]
    t2a = table2a_rows(roots)
    t2a.to_csv(out / "table2a.csv", index=False)
    piv = t2a.pivot(index="cache", columns="portfolio", values="avg_pairs_traded_per_period")
    md += ["## Table 2 A pairs traded per period (wait 1, complete cohorts)", "",
           _md(piv[list(PORTFOLIOS)], "{:,.2f}"), ""]

    # 3. the 1999 draft
    ed_rows, ed_sum = edition_rows(roots)
    ed_rows.to_csv(out / "edition1999.csv", index=False)
    (out / "edition1999.json").write_text(json.dumps(ed_sum, indent=1))
    md += ["## 1999 draft (408 cohorts)", "", "| cache | Table I | II A | II B | total |",
           "|---|---|---|---|---|"]
    for k, s in ed_sum.items():
        md.append(f"| {k} | {s['Table I']['score']} | {s['Table II A']['score']} | "
                  f"{s['Table II B']['score']} | {s['total']['score']} |")
    md += ["", "## Every count handle against its printed value", "",
           paper_md(counts, t2a, ed_rows), "",
           "## The six printed levels and the sector mix", "",
           printed_gap_md(counts), "",
           "## The late 66 cohorts against the implied late sample (hypothesis)", "",
           late_profile_md(roots), ""]

    # 4. added securities and slots
    added, slots, checks = added_and_slots(variants, NS_CACHE)
    added.to_csv(out / "added.csv", index=False)
    slots.to_csv(out / "slots.csv", index=False)
    checks.to_csv(out / "checks.csv", index=False)
    md += ["## Consistency checks (sums over 474 cohorts)", "",
           _md(checks.groupby("variant")[["added_not_in_map", "ns_legs_lost", "new_ns_pairs",
                                      "dropped_ns_pairs", "untouched",
                                      "untouched_identical"]].sum()), ""]
    md += ["## The added securities", "", added_md(added, slots), ""]

    # 5. cells
    if args.cells:
        cells = {}
        for item in args.cells:
            k, path = item.split("=", 1)
            cells[k] = json.loads((Path(path) / "cells.json").read_text())
        base = cells["ns"]
        all_ns = compare_cells(base, base)
        for k, cl in cells.items():
            if k == "ns":
                continue
            ch = compare_cells(base, cl)
            changed = ch[ch["mark_ns"] != ch["mark_wide"]]
            att = attribute(changed, slots, added, frames["ns"], frames[k], k)
            att.to_csv(out / f"changes_{k}.csv", index=False)
            score = sum({"✓": 1, "~": 0.5}.get(c["mark"], 0) for c in cl)
            md += [f"## Mark changes, {k} against ns (score {score} of {len(cl)})", "",
                   stability_md(ch, all_ns), "", attribution_md(att), ""]
    (out / "margins.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check", help="run the driver with full-precision cell capture; "
                                 "driver arguments follow --")
    rep = sub.add_parser("report")
    rep.add_argument("--out", required=True)
    rep.add_argument("--variants", nargs="+", default=list(VARIANTS))
    rep.add_argument("--cells", action="append", default=[],
                     help="name=run dir holding cells.json (one must be ns=...)")
    argv = sys.argv[1:]
    if argv and argv[0] == "check":
        rest = argv[1:]
        if rest and rest[0] == "--":
            rest = rest[1:]
        return cmd_check(rest)
    return cmd_report(parser.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
