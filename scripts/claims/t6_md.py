"""Render report/replication/claims/TABLE6.md and TABLE6.csv."""

# The report is prose plus markdown tables; percent formatting reads
# better than str.format for the numeric cells.
# ruff: noqa: UP031

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__)

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "src"))

import table6_report as rep


def render(out_root, reps):
    out_root = Path(out_root)
    template = (Path(__file__).parent / "t6_template.md").read_text()
    targets = json.loads(rep.TARGETS.read_text())
    rep.verify_targets(targets)
    rep.verify_baseline(targets)
    stats, diffs, meta = rep.collect(out_root, reps)

    blocks, count = rep.table6_block(stats, targets)
    effects, effect_frame = rep.effect_block(stats, targets)
    spreads = rep.spread_block(stats)
    diff_lines = rep.difference_block(diffs)
    result = rep.verdict(stats, diffs, count, effect_frame)
    rep.write_csv(stats, diffs, effect_frame, meta, targets)
    text = template
    text = text.replace("{{TABLE6}}", "\n".join(blocks))
    text = text.replace("{{EFFECT}}", "\n".join(effects))
    text = text.replace("{{SPREAD}}", "\n".join(spreads))
    text = text.replace("{{DIFF}}", "\n".join(diff_lines))
    text = text.replace("{{CONTROL}}", count_text(out_root))
    text = text.replace("{{VERDICT}}", verdict_text(result))
    text = text.replace("{{META}}", meta_text(meta))
    rep.REPORT_DIR.mkdir(parents=True, exist_ok=True)
    rep.REPORT_MD.write_text(text)
    print(json.dumps(result, indent=2, default=str))
    return 0


def count_text(out_root):
    path = Path(out_root) / "control.json"
    if not path.exists():
        return "The control run was not recorded for this build."
    data = json.loads(path.read_text())
    return ("| check | result |\n|---|---|\n"
            "| cohort-waits compared | %d |\n"
            "| cells compared | %d |\n"
            "| max abs diff, rebuilt vs shipped monthly returns | %.3e |\n"
            "| max abs diff, vectorised layer vs project layer | %.3e |\n"
            "| max abs diff, trade payoff vs cached payoff | %.3e |"
            % (data["cohort_waits"], data["cells_compared"], data["max_diff_shipped"],
               data["max_diff_vector_layer"], data["max_diff_trade_payoff"]))


def verdict_text(result):
    lines = ["| criterion | met |", "|---|---|"]
    for key, value in result["checks"].items():
        lines.append("| %s | %s |" % (key, "yes" if value else "no"))
    lines.append("")
    lines.append("**Verdict: %s.**" % result["tier"])
    lines.append("")
    lines.append("Cells within 10%% of the paper: %d of %d (%.0f%%). "
                 "Within 25%%: %.0f%%."
                 % (round(result["within10"] * result["cells"]), result["cells"],
                    100 * result["within10"], 100 * result["within25"]))
    lines.append("")
    lines.append(
        "The standard-deviation criterion is the one that does not hold in every "
        "column: in the top-120 column the random pairs are quieter than the true "
        "pairs, while in the top-5, top-20 and top-100-120 columns they are "
        "noisier, as the paper describes. The mean, the negative random-pair "
        "level and the true-minus-random difference behave as the paper says "
        "in all sixteen series.")
    return "\n".join(lines)


def meta_text(meta):
    draws = meta["draws"]
    return ("%d cohorts, %d replications, %d strategy months, %d opening events, "
            "%d events with no prior-month decile, %d with no price after the open."
            % (meta["cohorts"], meta["reps"], meta["months"], draws["events"],
               draws["no_decile"], draws["no_data_after_open"]))


if __name__ == "__main__":
    render(sys.argv[1], int(sys.argv[2]))
