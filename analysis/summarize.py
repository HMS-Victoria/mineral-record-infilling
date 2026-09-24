"""Check report averages from published aggregate tables; no model execution."""

import csv
import json
import math
from collections import Counter
from pathlib import Path
from statistics import mean


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "robustness"


def close(actual, expected, label):
    if not math.isclose(actual, expected, rel_tol=0, abs_tol=1e-12):
        raise ValueError(f"{label}: {actual} != {expected}")


def run():
    with (RESULTS / "main_metrics.csv").open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    saved = json.loads((RESULTS / "summary.json").read_text(encoding="utf-8"))
    if len(rows) != 576:
        raise ValueError("Expected 576 published aggregate rows")
    keys = ("method", "model_seed", "L_km", "keep_fraction", "context_repeat", "region", "target")
    if len({tuple(r[k] for k in keys) for r in rows}) != len(rows):
        raise ValueError("Duplicate aggregate keys")
    if any(r["phase"] != "merged" for r in rows):
        raise ValueError("Expected metrics calculated after merging phases")

    def average(method, keep, field):
        selected = [r for r in rows if r["method"] == method
                    and int(r["L_km"]) == 10 and float(r["keep_fraction"]) == keep]
        # The complete balanced design makes this equivalent to equal averaging
        # over region, target, model seed, then context repeat. Validate balance.
        repeats = {"0"} if keep == 1 else {"101", "211", "307"}
        seeds = {"17", "29", "43"} if method == "mineral_only_zero_geo" else (
            {"731"} if method == "spatial_rf" else {"0"})
        expected = {(seed, rep, region, target) for seed in seeds for rep in repeats
                    for region in ("nevada", "arizona", "colorado")
                    for target in ("Gold", "Copper")}
        counts = Counter((r["model_seed"], r["context_repeat"], r["region"], r["target"])
                         for r in selected)
        if set(counts) != expected or any(n != 1 for n in counts.values()):
            raise ValueError(f"Unbalanced design for {method}, keep={keep}")
        values = [float(r[field]) for r in selected]
        if not all(math.isfinite(value) for value in values):
            raise ValueError("Missing or nonfinite metric; do not silently omit")
        return mean(values)

    nn = "mineral_only_zero_geo"
    print("L=10 km, full white-block context (equal-weight averages)")
    print("method                         AP        coverage5")
    for method in ("kernel_density", nn, "spatial_rf", "nearest"):
        print(f"{method:30s} {average(method, 1, 'ap'):.6f}  {average(method, 1, 'coverage_5'):.2%}")

    nn_ap = average(nn, 1, "ap")
    baseline_ap = average(saved["primary_baseline"], 1, "ap")
    close(nn_ap, saved["nn_ap"], "nn AP")
    close(baseline_ap, saved["baseline_ap"], "baseline AP")
    close(nn_ap - baseline_ap, saved["primary_ap_difference"], "primary AP difference")
    close((nn_ap - baseline_ap) / baseline_ap, saved["primary_relative_difference"], "relative AP difference")
    close(average(nn, 1, "coverage_5") - average(saved["primary_baseline"], 1, "coverage_5"),
          saved["coverage5_difference"], "coverage5 difference")
    for method, expected in saved["all_preset_baselines"].items():
        close(average(method, 1, "ap"), expected["baseline_ap"], method)
        close(nn_ap - average(method, 1, "ap"), expected["ap_difference"], method + " AP difference")
        close(average(nn, 1, "coverage_5") - average(method, 1, "coverage_5"),
              expected["coverage5_difference"], method + " coverage5 difference")

    print("\nL=10 km, reduced white-block context")
    for keep in (0.5, 0.25):
        expected = saved["sparse_screening"][str(keep)]
        ap_nn = average(nn, keep, "ap")
        ap_kde = average("kernel_density", keep, "ap")
        delta_cov = average(nn, keep, "coverage_5") - average("kernel_density", keep, "coverage_5")
        close(ap_nn - ap_kde, expected["ap_difference"], f"keep={keep} AP difference")
        close(delta_cov, expected["coverage5_difference"], f"keep={keep} coverage5 difference")
        print(f"keep={keep:.0%}: NN AP={ap_nn:.6f}, KDE AP={ap_kde:.6f}, delta coverage5={delta_cov*100:+.4f} pp")
    print("\nPASS: published aggregate averages match summary.json (absolute tolerance 1e-12).")
    print("This check does not reconstruct grid-level AP or constitute new geological validation.")


if __name__ == "__main__":
    run()
