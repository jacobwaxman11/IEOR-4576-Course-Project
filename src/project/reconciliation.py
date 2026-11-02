"""Validate the complete reconciled baseline and isolated robustness experiments.

Run after the commands in report/replication/PR_RECONCILIATION.md. This checks
actual cached observations locally; only aggregate evidence is written to results/.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from project.fidelity import validate_outputs
from project.import_ui import file_sha256


def validate(root: Path, cache: Path) -> dict:
    evidence = {"runs": {}, "isolation": {}, "artifact_sha256": {}}
    baseline = cache / "baseline/cohorts"
    for name in ("baseline", "delisting", "waste_utilities"):
        evidence["runs"][name] = validate_outputs(root / name, cache / name, 474)
        for filename in ("table1.csv", "monthly_returns.parquet", "replication_check.md"):
            path = root / name / "tables" / filename
            evidence["artifact_sha256"][f"{name}/{filename}"] = file_sha256(path)
        if name == "baseline":
            continue
        settings = dict(evidence["runs"][name]["settings"])
        option, value = (("long_delisting_loss", True) if name == "delisting"
                         else ("waste_sic", "utilities"))
        if settings.pop(option, None) != value or settings != evidence["runs"]["baseline"]["settings"]:
            raise ValueError(f"More than the intended robustness setting changed: {name}")
        target = cache / name / "cohorts"
        pairs, trades = 0, 0
        for cohort in sorted(baseline.glob("????-??")):
            pd.testing.assert_frame_equal(
                pd.read_parquet(cohort / "pairs.parquet"),
                pd.read_parquet(target / cohort.name / "pairs.parquet"), check_exact=True,
            )
            pairs += 1
            for wait in (0, 1):
                filename = f"w{wait}_trades.parquet"
                a = pd.read_parquet(cohort / filename)
                b = pd.read_parquet(target / cohort.name / filename)
                if name == "delisting":
                    # The optional stress changes payoffs, never selection or trade timing.
                    a, b = a.drop(columns="payoff"), b.drop(columns="payoff")
                pd.testing.assert_frame_equal(a, b, check_exact=True)
                trades += 1
        evidence["isolation"][name] = {"pair_selections": pairs, "trade_logs": trades}
    # Sector relabeling must leave the complete unrestricted monthly panel unchanged.
    filename = "tables/monthly_returns.parquet"
    pd.testing.assert_frame_equal(
        pd.read_parquet(root / "baseline" / filename),
        pd.read_parquet(root / "waste_utilities" / filename), check_exact=True,
    )
    evidence["isolation"]["waste_utilities"]["monthly_panel_exact"] = True

    table6 = root / "table6_true"
    stamp = json.loads((table6 / "accounting_meta.json").read_text())
    if stamp["parameters"]["close_rule"] != "true":
        raise ValueError("Expected the isolated true-close Table 6 experiment")
    cells = pd.read_csv(table6 / "report/TABLE6.csv")
    cells = cells[cells.table == "table6"]
    if len(cells) != 48 or not (cells[["n_months", "cohorts", "replications"]]
                              == [474, 479, 200]).all().all():
        raise ValueError("Incomplete full-sample Table 6 report")
    control = json.loads((table6 / "control.json").read_text())
    if control["cohort_waits"] != 958 or control["cells_compared"] != 7664:
        raise ValueError("Incomplete Table 6 matched control")
    for key in ("max_diff_shipped", "max_diff_vector_layer", "max_diff_trade_payoff"):
        if not 0 <= control[key] < 1e-12:
            raise ValueError(f"Table 6 control failed: {key}")
    evidence["table6"] = {"settings": stamp, "control": control,
                          "marks": cells["mark"].value_counts().to_dict()}
    return evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("results/replication/reconciliation"))
    parser.add_argument("--cache", type=Path, default=Path("data/processed/replication/reconciliation"))
    args = parser.parse_args()
    evidence = validate(args.root, args.cache)
    output = args.root / "validation.json"
    output.write_text(json.dumps(evidence, indent=2, allow_nan=False) + "\n")
    print(f"Validated 3 full runs and Table 6; aggregate evidence: {output}")
    print(json.dumps(evidence["isolation"], indent=2))


if __name__ == "__main__":
    main()
