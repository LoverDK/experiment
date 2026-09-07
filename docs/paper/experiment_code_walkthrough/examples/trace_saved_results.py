"""Recompute representative paper quantities without writing any artifacts."""
from pathlib import Path
import math

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
RESULTS = ROOT / "results"


def read(relative):
    return pd.read_csv(RESULTS / relative)


def same(actual, expected):
    np.testing.assert_allclose(actual, expected, rtol=1e-9, atol=1e-11)


def main():
    diagnostics = read("certificate_diagnostics_summary.csv")
    published = diagnostics.atlas_accepted.astype(bool)
    released_mae = diagnostics.loc[published, "atlas_absolute_error"].mean()
    raw_mae = diagnostics.atlas_absolute_error.mean()
    summary = read("synthetic_benchmark_summary.csv").set_index("method")
    same(released_mae, summary.loc["atlas", "mae"])
    same(raw_mae, summary.loc["atlas_no_rejection", "mae"])
    print("MAIN: targets / released", len(diagnostics), int(published.sum()))
    print("MAIN: released MAE / all-target MAE", released_mae, raw_mae)

    synthetic = read("extensions/synthetic_baselines_records.csv")
    nominal = synthetic[synthetic.scenario == "nominal"]
    paired = nominal.pivot(index="seed", columns="method", values="absolute_error")
    difference = paired.ridge_meta_regression - paired.atlas_no_rejection
    mean_diff = difference.mean()
    mcse = difference.std(ddof=1) / np.sqrt(len(difference))
    stored = read("extensions/synthetic_paired_summary.csv")
    stored = stored[(stored.scenario == "nominal") & (stored.method == "ridge_meta_regression")].iloc[0]
    same(mean_diff, stored.difference)
    same(mcse, stored.mcse)
    print("B.3: nominal ridge minus ATLAS paired MAE / MCSE", mean_diff, mcse)

    predictions = read("validation_v3/selection_predictions.csv")
    test = predictions[(predictions.part == "test") & (predictions.scenario == "moderate")]
    rank_summary = read("validation_v3/selection_rank_bootstrap.csv")
    for method in ("atlas", "ridge_meta_regression", "rbf_kernel_ridge"):
        method_test = test[test.method == method].sort_values(["score", "replicate"])
        selected = method_test.head(round(len(method_test) * .5))
        row = rank_summary[(rank_summary.scenario == "moderate") &
                           (rank_summary.method == method) & (rank_summary.fraction == .5)].iloc[0]
        same(selected.error.mean(), row.mae)
        print("B.3: moderate 50%", method, len(selected), selected.error.mean())

    mechanisms = read("validation_v3/mechanism_records.csv")
    cell = mechanisms[(mechanisms.surface == "threshold") &
                      (mechanisms.change == "baseline") & (mechanisms.method == "atlas")]
    mech_summary = read("validation_v3/mechanism_summary.csv")
    row = mech_summary[(mech_summary.surface == "threshold") &
                       (mech_summary.change == "baseline") & (mech_summary.method == "atlas")].iloc[0]
    same(cell.error.mean(), row.error)
    print("B.2: threshold baseline MAE / coverage / width", cell.error.mean(), cell.covered.mean(), cell.width.mean())

    effects = read("validation_v3/nuisance_effect_records.csv")
    cell = effects[(effects.n == 400) & (effects.propensity == "balanced") & (effects.method == "quadratic_known")]
    rmse = np.sqrt(np.mean(cell.error**2))
    nuisance_summary = read("validation_v3/nuisance_effect_summary.csv")
    row = nuisance_summary[(nuisance_summary.n == 400) & (nuisance_summary.propensity == "balanced") &
                           (nuisance_summary.method == "quadratic_known")].iloc[0]
    same(rmse, row.rmse)
    print("B.2: fitted nuisance source records / RMSE", len(cell), rmse)

    dependence = read("validation_v3/dependence_records.csv")
    cell = dependence[(dependence.surface == "constant") & (dependence.correlation == .7)]
    print("B.2: dependence coverage", cell.groupby("method").covered.mean().to_dict())
    constants = read("validation_v3/constant_records.csv")
    print("B.2: nominal constant-factor widths", constants[constants.scenario == "nominal"].groupby("factor").width.mean().to_dict())

    semi = read("extensions/nsw_semisynthetic_records.csv")
    cell = semi[(semi.surface == "smooth") & (semi.method == "atlas_no_rejection")]
    replicate_means = cell.groupby("replicate").absolute_error.mean()
    semi_summary = read("extensions/nsw_semisynthetic_summary.csv")
    row = semi_summary[(semi_summary.surface == "smooth") & (semi_summary.method == "atlas_no_rejection")].iloc[0]
    same(replicate_means.mean(), row.mae)
    same(replicate_means.std(ddof=1)/np.sqrt(len(replicate_means)), row.mae_mcse)
    print("B.4: semi-synthetic rows / independent replicates / MAE", len(cell), len(replicate_means), row.mae)

    nsw = read("validation_v3/nsw_stability_records.csv")
    valid = nsw[["replicate", "anchor", "k"]].drop_duplicates()
    failures = read("validation_v3/nsw_stability_failures.csv")
    assert len(valid) + len(failures) == 120
    print("B.4: valid NSW designs / failed designs", len(valid), len(failures))

    hillstrom = read("validation_v3/hillstrom_records.csv")
    visit = hillstrom[(hillstrom.outcome == "visit") & (hillstrom.interval == "source_loo_empirical") &
                     (hillstrom.level == .9)]
    print("B.4: Hillstrom visit all-cell MAE", visit.groupby("method").error.mean().to_dict())
    infinite = hillstrom[(hillstrom.interval == "source_loo_empirical") & (hillstrom.level == .95)]
    assert np.isinf(infinite.width).all()
    print("B.4: 95% residual rank / available residuals", math.ceil(18*.95), 17)

    bridge = read("validation_v3/bridge_checks_8192.csv")
    retained = bridge[bridge.family == "retained_certificates"]
    assert len(retained) == 72
    assert retained.bound_holds.all() and (retained.lower_bound > 0).all()
    print("B.5: retained checks", len(retained))
    print(retained.groupby("budget")[["selected_value", "optimum", "lower_bound"]].mean().to_string())
    print("Saved-result arithmetic checks passed. No files were written.")


if __name__ == "__main__":
    main()
