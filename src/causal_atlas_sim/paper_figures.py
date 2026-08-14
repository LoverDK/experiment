"""Build submission-facing figures and tables from committed result files only."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable

import matplotlib.pyplot as plt
import numpy as np

from .figure_style import PALETTE, FigureStyle, apply_publication_style, finalize_figure


METHOD_COLORS = {
    "atlas": PALETTE["blue_main"],
    "atlas_no_rejection": PALETTE["blue_secondary"],
    "semantic_forced": PALETTE["red"],
    "nearest_semantic": PALETTE["gold"],
    "global_mean": PALETTE["neutral"],
    "oracle_latent_support": PALETTE["green"],
}
METHOD_LABELS = {
    "atlas": "ATLAS (conditional on release)",
    "atlas_no_rejection": "ATLAS, no rejection",
    "semantic_forced": "Semantic forced",
    "nearest_semantic": "Nearest semantic",
    "global_mean": "Global mean",
    "oracle_latent_support": "Oracle latent support (evaluation only)",
}
POLICY_COLORS = {
    "certified_atlas": PALETTE["blue_main"],
    "honest_atlas": PALETTE["blue_main"],
    "no_rejection": PALETTE["blue_secondary"],
    "wald_only": PALETTE["neutral"],
    "understated_smoothness": PALETTE["red"],
    "causal_greedy": PALETTE["blue_main"],
    "semantic_greedy": PALETTE["red"],
    "random": PALETTE["neutral"],
}


def build_paper_figures(results_dir: Path) -> tuple[Path, ...]:
    """Read saved result files and create Figures 2--5 plus support tables."""

    results_dir = Path(results_dir)
    figures_dir = results_dir / "figures"
    tables_dir = results_dir / "tables"
    apply_publication_style(FigureStyle(font_size=10, axes_linewidth=1.3))
    outputs = [
        *_build_synthetic_overview(results_dir, figures_dir),
        *_build_selective_uncertainty(results_dir, figures_dir),
        *_build_rejection_bridge(results_dir, figures_dir),
        *_build_nsw_diagnostics(results_dir, figures_dir),
        *_write_support_failure_tables(results_dir, tables_dir),
    ]
    return tuple(outputs)


def _build_synthetic_overview(results_dir: Path, figures_dir: Path) -> tuple[Path, ...]:
    diagnostics = _read_csv(results_dir / "certificate_diagnostics_summary.csv")
    sensitivity = _read_csv(results_dir / "representation_sensitivity_summary.csv")
    fig, axes = plt.subplots(2, 2, figsize=(13.2, 9.2))

    ax = axes[0, 0]
    chosen = sorted(
        diagnostics,
        key=lambda row: -(
            abs(_number(row["target_hidden_moderator"]) - _number(row["nearest_semantic_hidden_moderator"]))
            / (
                np.hypot(
                    _number(row["target_s1"]) - _number(row["nearest_semantic_s1"]),
                    _number(row["target_s2"]) - _number(row["nearest_semantic_s2"]),
                )
                + 0.03
            )
        ),
    )[:14]
    hidden_values = [
        *[_number(row["nearest_semantic_hidden_moderator"]) for row in chosen],
        *[_number(row["target_hidden_moderator"]) for row in chosen],
    ]
    norm = plt.Normalize(min(hidden_values), max(hidden_values))
    for row in chosen:
        x0, y0 = _number(row["nearest_semantic_s1"]), _number(row["nearest_semantic_s2"])
        x1, y1 = _number(row["target_s1"]), _number(row["target_s2"])
        ax.plot([x0, x1], [y0, y1], color=PALETTE["neutral_light"], linewidth=0.8, zorder=1)
        ax.scatter(x0, y0, c=[_number(row["nearest_semantic_hidden_moderator"])], cmap="coolwarm", norm=norm, s=40, marker="o", edgecolor="black", linewidth=0.35, zorder=2)
        points = ax.scatter(x1, y1, c=[_number(row["target_hidden_moderator"])], cmap="coolwarm", norm=norm, s=55, marker="^", edgecolor="black", linewidth=0.35, zorder=3)
    fig.colorbar(points, ax=ax, label="Hidden moderator", fraction=0.046, pad=0.04)
    ax.set(xlabel="Semantic coordinate $s_1$", ylabel="Semantic coordinate $s_2$")
    ax.set_title("A  Semantic neighbors can differ causally", loc="left", fontweight="bold")
    ax.text(0.02, 0.02, "circle: archive neighbor   triangle: target", transform=ax.transAxes, fontsize=8)

    ax = axes[0, 1]
    error_columns = {
        "atlas": "atlas_absolute_error",
        "atlas_no_rejection": "atlas_no_rejection_absolute_error",
        "semantic_forced": "semantic_forced_absolute_error",
        "nearest_semantic": "nearest_semantic_absolute_error",
        "global_mean": "global_mean_absolute_error",
        "oracle_latent_support": "oracle_latent_support_absolute_error",
    }
    for method, column in error_columns.items():
        values = np.asarray(
            [
                _number(row[column])
                for row in diagnostics
                if method != "atlas" or _boolean(row["atlas_accepted"])
            ]
        )
        values.sort()
        ax.step(values, np.arange(1, len(values) + 1) / len(values), where="post", label=METHOD_LABELS[method], color=METHOD_COLORS[method], linewidth=1.8)
    ax.set(xlabel="Absolute estimation error", ylabel="Empirical CDF", ylim=(0.0, 1.02))
    ax.set_title("B  Full error distributions", loc="left", fontweight="bold")
    ax.legend(fontsize=7, loc="lower right")

    ax = axes[1, 0]
    hidden_grid = sorted({_number(row["hidden_shift_fraction"]) for row in sensitivity})
    proxy_grid = sorted({_number(row["proxy_uncertainty"]) for row in sensitivity})
    matrix = np.full((len(proxy_grid), len(hidden_grid)), np.nan)
    for row in sensitivity:
        matrix[proxy_grid.index(_number(row["proxy_uncertainty"])), hidden_grid.index(_number(row["hidden_shift_fraction"]))] = _number(row["representation_advantage"])
    bound = max(abs(np.nanmin(matrix)), abs(np.nanmax(matrix)), 1e-8)
    image = ax.imshow(matrix, origin="lower", aspect="auto", cmap="RdBu_r", vmin=-bound, vmax=bound)
    ax.set_xticks(range(len(hidden_grid)), [f"{value:.1f}" for value in hidden_grid])
    ax.set_yticks(range(len(proxy_grid)), [f"{value:.2f}" for value in proxy_grid])
    ax.set(xlabel="Hidden-moderator shift", ylabel="Proxy uncertainty")
    ax.set_title("C  Representation advantage", loc="left", fontweight="bold")
    fig.colorbar(image, ax=ax, label=r"$\Delta_{rep}$: semantic MAE - ATLAS MAE")

    ax = axes[1, 1]
    accepted = [row for row in diagnostics if _boolean(row["atlas_accepted"])]
    rejected = [row for row in diagnostics if not _boolean(row["atlas_accepted"])]
    for rows, label, color, marker in (
        (accepted, "accepted", PALETTE["blue_main"], "o"),
        (rejected, "rejected", PALETTE["red"], "x"),
    ):
        ax.scatter([_number(row["certificate_radius"]) for row in rows], [_number(row["atlas_absolute_error"]) for row in rows], s=22, alpha=0.62, color=color, marker=marker, label=label)
    maximum = max(
        max(_number(row["certificate_radius"]) for row in diagnostics),
        max(_number(row["atlas_absolute_error"]) for row in diagnostics),
    )
    ax.plot([0, maximum], [0, maximum], linestyle="--", color=PALETTE["neutral"], linewidth=1.1, label="$y=x$")
    threshold = _number(diagnostics[0]["scientific_tolerance"])
    ax.axvline(threshold, linestyle=":", color=PALETTE["gold"], linewidth=1.7, label="release threshold")
    ax.set(xlabel="Certificate radius", ylabel="Absolute estimation error", xlim=(0, maximum * 1.03), ylim=(0, maximum * 1.03))
    ax.set_title("D  Certificate versus realized error", loc="left", fontweight="bold")
    ax.legend(fontsize=8)

    fig.suptitle("Figure 2. Why causal composability requires more than semantic similarity", fontsize=14, fontweight="bold")
    return finalize_figure(fig, figures_dir / "synthetic_composability_overview")


def _build_selective_uncertainty(results_dir: Path, figures_dir: Path) -> tuple[Path, ...]:
    risk = _read_csv(results_dir / "risk_coverage_summary.csv")
    curves = _read_csv(results_dir / "calibration_curve_summary.csv")
    failures = _read_csv(results_dir / "calibration_experiment_summary.csv")
    fig, axes = plt.subplots(2, 2, figsize=(12.8, 8.8))

    ax = axes[0, 0]
    rows = sorted(
        (row for row in risk if row["conditional_mae"] != ""),
        key=lambda row: _number(row["acceptance_rate"]),
    )
    ax.plot([_number(row["acceptance_rate"]) for row in rows], [_optional_number(row["conditional_mae"]) for row in rows], color=PALETTE["blue_main"], marker="o", linewidth=2)
    label_thresholds = {1.25, 1.50, 1.65, 2.00}
    for index, row in enumerate(rows):
        threshold = row["threshold"]
        threshold_value = _number(threshold)
        if np.isinf(threshold_value):
            label = "no rejection"
        elif threshold_value in label_thresholds:
            label = f"{threshold_value:.2f}"
        else:
            continue
        offset = (4, 7) if index % 2 == 0 else (4, -13)
        ax.annotate(label, (_number(row["acceptance_rate"]), _number(row["conditional_mae"])), xytext=offset, textcoords="offset points", fontsize=7)
    ax.set(xlabel="Release / acceptance rate", ylabel="Conditional MAE", xlim=(-0.02, 1.03))
    ax.set_title("A  Risk-coverage frontier", loc="left", fontweight="bold")

    policies = ("honest_atlas", "wald_only", "understated_smoothness")
    policy_labels = {"honest_atlas": "Honest ATLAS", "wald_only": "Wald only", "understated_smoothness": "Understated smoothness"}
    ax = axes[0, 1]
    ax.plot([0.78, 0.99], [0.78, 0.99], linestyle="--", color=PALETTE["neutral"], linewidth=1)
    for policy in ("honest_atlas", "wald_only"):
        selected = sorted((row for row in curves if row["policy"] == policy), key=lambda row: _number(row["confidence_level"]))
        ax.plot([_number(row["confidence_level"]) for row in selected], [_number(row["empirical_coverage"]) for row in selected], marker="o", linewidth=1.8, color=POLICY_COLORS[policy], label=policy_labels[policy])
    ax.set(xlabel="Nominal coverage", ylabel="Empirical coverage", xlim=(0.78, 0.99), ylim=(0.15, 1.03))
    ax.set_title("B  Nominal versus empirical coverage", loc="left", fontweight="bold")
    ax.legend(fontsize=8)
    ax.text(0.02, 0.03, "Understated smoothness coincides at 1.0 and is omitted.", transform=ax.transAxes, fontsize=7)

    ax = axes[1, 0]
    for policy in policies:
        selected = sorted((row for row in curves if row["policy"] == policy), key=lambda row: _number(row["mean_width"]))
        ax.plot([_number(row["mean_width"]) for row in selected], [_number(row["empirical_coverage"]) for row in selected], marker="o", linewidth=1.8, color=POLICY_COLORS[policy], label=policy_labels[policy])
    ax.set(xlabel="Mean interval width", ylabel="Empirical coverage", ylim=(0.15, 1.03))
    ax.set_title("C  Coverage paid for by interval width", loc="left", fontweight="bold")

    ax = axes[1, 1]
    scenario_markers = {"strong_semantic_mismatch": "o", "severe_semantic_mismatch": "s"}
    for policy in ("certified_atlas", "no_rejection", "understated_smoothness"):
        selected = [row for row in failures if row["scenario_key"] in scenario_markers and row["policy_key"] == policy]
        selected.sort(key=lambda row: row["scenario_key"])
        ax.plot([_number(row["release_rate"]) for row in selected], [_number(row["overall_interval_coverage"]) for row in selected], color=POLICY_COLORS[policy], linewidth=1.4, label=policy.replace("_", " "))
        for row in selected:
            ax.scatter(_number(row["release_rate"]), _number(row["overall_interval_coverage"]), color=POLICY_COLORS[policy], marker=scenario_markers[row["scenario_key"]], s=48)
    ax.set(xlabel="Release rate", ylabel="Overall interval coverage", xlim=(-0.02, 1.03), ylim=(0.65, 1.03))
    ax.set_title("D  Failure boundary under mismatch", loc="left", fontweight="bold")
    ax.legend(fontsize=8)
    ax.text(0.02, 0.04, "circle: strong mismatch   square: severe mismatch", transform=ax.transAxes, fontsize=7)
    fig.suptitle("Figure 3. Selective prediction and honest uncertainty", fontsize=14, fontweight="bold")
    return finalize_figure(fig, figures_dir / "selective_uncertainty_overview")


def _build_rejection_bridge(results_dir: Path, figures_dir: Path) -> tuple[Path, ...]:
    partial = _read_csv(results_dir / "partial_identification_summary.csv")
    paths = _read_csv(results_dir / "bridge_budget_path_summary.csv")
    optimum = _read_csv(results_dir / "bridge_optimality_summary.csv")
    partial.sort(key=lambda row: _number(row["mean_oracle_hull_distance"]))
    fig, axes = plt.subplots(1, 3, figsize=(15.2, 4.5))
    x = [_number(row["mean_oracle_hull_distance"]) for row in partial]

    ax = axes[0]
    ax.plot(x, [1.0 - _number(row["rejection_rate"]) for row in partial], color=PALETTE["blue_main"], marker="o", linewidth=2)
    ax.set(xlabel="Evaluation-only support deterioration", ylabel="Release probability", ylim=(-0.02, 1.03))
    ax.set_title("A  Support deterioration to release", loc="left", fontweight="bold")

    ax = axes[1]
    ax.plot(x, [_number(row["mean_partial_id_width_on_rejected"]) for row in partial], color=PALETTE["red"], marker="s", linewidth=2)
    ax.set(xlabel="Evaluation-only support deterioration", ylabel="PI diameter on rejected targets")
    ax.set_title("B  Rejection to identified-set width", loc="left", fontweight="bold")

    ax = axes[2]
    severe_paths = [row for row in paths if row["scenario_key"] == "severe"]
    for policy in ("causal_greedy", "semantic_greedy", "random"):
        selected = sorted((row for row in severe_paths if row["policy_key"] == policy), key=lambda row: int(row["budget"]))
        ax.plot([int(row["budget"]) for row in selected], [_number(row["mean_diameter"]) for row in selected], color=POLICY_COLORS[policy], marker="o", linewidth=1.8, label=policy.replace("_", " "))
    ax.scatter([int(row["budget"]) for row in optimum], [_number(row["optimal_mean_final_diameter"]) for row in optimum], color="black", marker="D", s=42, label="Ex-post exhaustive oracle", zorder=5)
    ax.set_xticks([0, 1, 2, 3, 4])
    ax.set(xlabel="Bridge budget", ylabel="Partial-identification diameter")
    ax.set_title("C  Bridge budget path", loc="left", fontweight="bold")
    ax.legend(fontsize=7)
    fig.suptitle("Figure 4. From failed composition to experiment design", fontsize=14, fontweight="bold")
    return finalize_figure(fig, figures_dir / "rejection_bridge_overview")


def _build_nsw_diagnostics(results_dir: Path, figures_dir: Path) -> tuple[Path, ...]:
    archive = _read_csv(results_dir / "nsw_archive_map_summary.csv")
    diagnostics = _read_csv(results_dir / "nsw_diagnostics_summary.csv")
    metadata = json.loads((results_dir / "nsw_experiment_metadata.json").read_text(encoding="utf-8"))
    fig, axes = plt.subplots(1, 3, figsize=(15.2, 4.5))

    ax = axes[0]
    colors = [_optional_number(row["atlas_acceptance_rate"]) for row in archive]
    points = ax.scatter([_number(row["pc1"]) for row in archive], [_number(row["pc2"]) for row in archive], c=colors, cmap="RdYlBu", vmin=0.0, vmax=1.0, s=34, edgecolor="black", linewidth=0.25)
    fig.colorbar(points, ax=ax, label="ATLAS release frequency")
    ax.set(xlabel="PCA coordinate 1", ylabel="PCA coordinate 2")
    ax.set_title("A  NSW local-object archive map", loc="left", fontweight="bold")

    ax = axes[1]
    for accepted, label, color, marker in ((True, "accepted", PALETTE["blue_main"], "o"), (False, "rejected", PALETTE["red"], "x")):
        selected = [row for row in diagnostics if _boolean(row["accepted"]) == accepted]
        ax.scatter([_number(row["heldout_local_contrast"]) for row in selected], [_number(row["reconstructed_contrast"]) for row in selected], s=18, alpha=0.5, color=color, marker=marker, label=label)
    values = [*[_number(row["heldout_local_contrast"]) for row in diagnostics], *[_number(row["reconstructed_contrast"]) for row in diagnostics]]
    low, high = min(values), max(values)
    ax.plot([low, high], [low, high], linestyle="--", color=PALETTE["neutral"], linewidth=1)
    ax.set(xlabel="Held-out local contrast", ylabel="Raw reconstructed contrast")
    ax.set_title("B  Reconstruction against held-out contrasts", loc="left", fontweight="bold")
    ax.legend(fontsize=8)

    ax = axes[2]
    widths = [_number(row["interval_width"]) for row in diagnostics]
    points = ax.scatter([_number(row["certificate_radius"]) for row in diagnostics], [_number(row["absolute_reconstruction_error"]) for row in diagnostics], c=widths, cmap="viridis", s=18, alpha=0.58)
    tolerance = float(metadata["scientific_tolerance"])
    ax.axvline(tolerance, linestyle=":", color=PALETTE["red"], linewidth=1.6, label="release threshold")
    fig.colorbar(points, ax=ax, label="Reported interval width")
    ax.set(xlabel="Certificate radius", ylabel="Absolute reconstruction error")
    ax.set_title("C  Certificate diagnostic", loc="left", fontweight="bold")
    ax.legend(fontsize=8)
    fig.suptitle("Figure 5. NSW reconstruction and certificate diagnostics", fontsize=14, fontweight="bold")
    return finalize_figure(fig, figures_dir / "nsw_diagnostics_overview")


def _write_support_failure_tables(results_dir: Path, tables_dir: Path) -> tuple[Path, ...]:
    rows = _read_csv(results_dir / "partial_identification_summary.csv")
    tables_dir.mkdir(parents=True, exist_ok=True)
    md_path = tables_dir / "support_failure_table.md"
    tex_path = tables_dir / "support_failure_table.tex"
    markdown = [
        "# Support deterioration, rejection, and partial identification",
        "",
        "| Scenario | Rejection | PI nonempty | PI coverage on rejected | PI diameter on rejected |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        markdown.append(
            f"| {row['scenario_label']} | {_number(row['rejection_rate']):.3f} | "
            f"{_number(row['partial_id_nonempty_rate']):.3f} | {_number(row['partial_id_coverage_on_rejected']):.3f} | "
            f"{_number(row['mean_partial_id_width_on_rejected']):.3f} |"
        )
    md_path.write_text("\n".join(markdown) + "\n", encoding="utf-8")
    latex = [
        "% Generated by scripts/build/build_paper_figures.py; do not edit.",
        "\\begin{table}[t]",
        "\\centering",
        "\\caption{Support deterioration, rejection, and partial identification.}",
        "\\label{tab:support-failure}",
        "\\begin{tabular}{lrrrr}",
        "\\toprule",
        "Scenario & Rejection & Nonempty & Coverage & Diameter \\\\",
        "\\midrule",
    ]
    for row in rows:
        latex.append(
            f"{row['scenario_label']} & {_number(row['rejection_rate']):.3f} & "
            f"{_number(row['partial_id_nonempty_rate']):.3f} & {_number(row['partial_id_coverage_on_rejected']):.3f} & "
            f"{_number(row['mean_partial_id_width_on_rejected']):.3f} \\\\"
        )
    latex.extend(["\\bottomrule", "\\end{tabular}", "\\end{table}"])
    tex_path.write_text("\n".join(latex) + "\n", encoding="utf-8")
    return md_path, tex_path


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as source:
        return list(csv.DictReader(source))


def _number(value: str | float | int | None) -> float:
    if value is None or value == "":
        raise ValueError("A required numeric result is missing.")
    return float(value)


def _optional_number(value: str | float | int | None) -> float:
    if value is None or value == "":
        return float("nan")
    return float(value)


def _boolean(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    return value.strip().lower() in {"true", "1", "yes"}
