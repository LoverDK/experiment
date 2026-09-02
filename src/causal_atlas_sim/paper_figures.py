"""Build submission-facing figures and tables from committed result files only."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

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
    "semantic_forced": PALETTE["red"],
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
        *_build_certificate_diagnostic(results_dir, figures_dir),
        *_build_selective_uncertainty(results_dir, figures_dir),
        *_build_rejection_bridge(results_dir, figures_dir),
        *_build_nsw_diagnostics(results_dir, figures_dir),
        *_build_nsw_certificate_diagnostic(results_dir, figures_dir),
        *_build_legacy_synthetic_validation(results_dir, figures_dir),
        *_build_legacy_nsw_validation(results_dir, figures_dir),
        *_write_support_failure_tables(results_dir, tables_dir),
        *_write_legacy_layout_tables(results_dir, tables_dir),
    ]
    # Keep stable, paper-facing names alongside the descriptive overview names.
    for source_stem, paper_stem in (
        ("selective_uncertainty_overview", "figure3_selective_uncertainty"),
        ("rejection_bridge_overview", "figure4_rejection_bridge"),
        ("nsw_diagnostics_overview", "figure5_nsw"),
    ):
        for extension in ("png", "pdf"):
            source = figures_dir / f"{source_stem}.{extension}"
            alias = figures_dir / f"{paper_stem}.{extension}"
            alias.write_bytes(source.read_bytes())
            outputs.append(alias)
    return tuple(outputs)


def _build_synthetic_overview(results_dir: Path, figures_dir: Path) -> tuple[Path, ...]:
    """Build the main synthetic figure from the saved diagnostic records.

    The layout follows the high-information legacy composition while assigning every
    panel to the causal-support claim: intuition, full error distributions, the
    representation grid, and the one-factor hidden-shift stress test.
    """
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
    )[:36]
    hidden_values = [
        *[_number(row["nearest_semantic_hidden_moderator"]) for row in chosen],
        *[_number(row["target_hidden_moderator"]) for row in chosen],
    ]
    norm = plt.Normalize(min(hidden_values), max(hidden_values))
    for row in chosen:
        x0, y0 = _number(row["nearest_semantic_s1"]), _number(row["nearest_semantic_s2"])
        x1, y1 = _number(row["target_s1"]), _number(row["target_s2"])
        ax.plot([x0, x1], [y0, y1], color=PALETTE["neutral_light"], linewidth=0.7, zorder=1)
        ax.scatter(x0, y0, c=[_number(row["nearest_semantic_hidden_moderator"])], cmap="coolwarm", norm=norm, s=30, marker="o", edgecolor="black", linewidth=0.3, zorder=2)
        points = ax.scatter(x1, y1, c=[_number(row["target_hidden_moderator"])], cmap="coolwarm", norm=norm, s=42, marker="^", edgecolor="black", linewidth=0.3, zorder=3)
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
        values = np.asarray([_number(row[column]) for row in diagnostics if method != "atlas" or _boolean(row["atlas_accepted"])])
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
    ax.set_title("C  Representation advantage across the grid", loc="left", fontweight="bold")
    fig.colorbar(image, ax=ax, label=r"$\Delta_{rep}$: semantic MAE - ATLAS MAE")

    ax = axes[1, 1]
    proxy_slice = [row for row in sensitivity if np.isclose(_number(row["proxy_uncertainty"]), 0.10)]
    proxy_slice.sort(key=lambda row: _number(row["hidden_shift_fraction"]))
    shifts = [_number(row["hidden_shift_fraction"]) for row in proxy_slice]
    advantage = [_number(row["representation_advantage"]) for row in proxy_slice]
    release = [_number(row["atlas_acceptance_rate"]) for row in proxy_slice]
    ax.plot(shifts, advantage, color=PALETTE["blue_main"], marker="o", linewidth=2, label=r"$\Delta_{rep}$")
    ax.set(xlabel="Hidden-moderator shift", ylabel="Representation advantage", ylim=(0.0, None))
    ax2 = ax.twinx()
    ax2.plot(shifts, release, color=PALETTE["red"], marker="s", linewidth=1.8, label="ATLAS release rate")
    ax2.set_ylabel("ATLAS release rate", color=PALETTE["red"])
    ax2.set_ylim(0.0, 1.03)
    ax.set_title("D  Hidden shift raises the representation gain", loc="left", fontweight="bold")
    handles, labels = ax.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(handles + handles2, labels + labels2, fontsize=8, loc="upper left")

    fig.suptitle("Figure 2. Synthetic validation of causal composability", fontsize=14, fontweight="bold")
    outputs = list(finalize_figure(fig, figures_dir / "figure2_synthetic_validation"))
    # Keep the established name as a compatibility alias for existing paper scripts.
    for extension in ("png", "pdf"):
        source = figures_dir / f"figure2_synthetic_validation.{extension}"
        alias = figures_dir / f"synthetic_composability_overview.{extension}"
        alias.write_bytes(source.read_bytes())
        outputs.append(alias)
    return tuple(outputs)


def _build_certificate_diagnostic(results_dir: Path, figures_dir: Path) -> tuple[Path, ...]:
    """Move the target-level certificate/error diagnostic to Appendix B.4."""
    diagnostics = _read_csv(results_dir / "certificate_diagnostics_summary.csv")
    fig, ax = plt.subplots(figsize=(6.8, 5.0))
    accepted = [row for row in diagnostics if _boolean(row["atlas_accepted"])]
    rejected = [row for row in diagnostics if not _boolean(row["atlas_accepted"])]
    for rows, label, color, marker in (
        (accepted, "released", PALETTE["blue_main"], "o"),
        (rejected, "rejected", PALETTE["red"], "x"),
    ):
        ax.scatter([_number(row["certificate_radius"]) for row in rows], [_number(row["atlas_absolute_error"]) for row in rows], s=24, alpha=0.62, color=color, marker=marker, label=label)
    maximum = max(max(_number(row["certificate_radius"]) for row in diagnostics), max(_number(row["atlas_absolute_error"]) for row in diagnostics))
    ax.plot([0, maximum], [0, maximum], linestyle="--", color=PALETTE["neutral"], linewidth=1.1, label="$y=x$")
    threshold = _number(diagnostics[0]["scientific_tolerance"])
    ax.axvline(threshold, linestyle=":", color=PALETTE["gold"], linewidth=1.7, label="release threshold")
    ax.set(xlabel="Certificate radius", ylabel="Absolute estimation error", xlim=(0, maximum * 1.03), ylim=(0, maximum * 1.03))
    ax.set_title("Certificate radius versus realized error", fontweight="bold")
    ax.legend(fontsize=8)
    fig.suptitle("Appendix B.4. Target-level certificate diagnostic", fontsize=12, fontweight="bold")
    return finalize_figure(fig, figures_dir / "appendix_certificate_diagnostic")


def _build_legacy_synthetic_validation(
    results_dir: Path,
    figures_dir: Path,
) -> tuple[Path, ...]:
    """Recreate the original four-panel synthetic layout with current results."""

    diagnostics = _read_csv(results_dir / "certificate_diagnostics_summary.csv")
    sensitivity = _read_csv(results_dir / "representation_sensitivity_summary.csv")
    paths = _read_csv(results_dir / "bridge_budget_path_summary.csv")
    fig, axes = plt.subplots(2, 2, figsize=(13.2, 9.2))

    ax = axes[0, 0]
    ranked = sorted(
        diagnostics,
        key=lambda row: -(
            abs(
                _number(row["target_hidden_moderator"])
                - _number(row["nearest_semantic_hidden_moderator"])
            )
            / (
                np.hypot(
                    _number(row["target_s1"])
                    - _number(row["nearest_semantic_s1"]),
                    _number(row["target_s2"])
                    - _number(row["nearest_semantic_s2"]),
                )
                + 0.03
            )
        ),
    )[:36]
    hidden_values = [
        *[_number(row["nearest_semantic_hidden_moderator"]) for row in ranked],
        *[_number(row["target_hidden_moderator"]) for row in ranked],
    ]
    norm = plt.Normalize(min(hidden_values), max(hidden_values))
    for row in ranked:
        x0 = _number(row["nearest_semantic_s1"])
        y0 = _number(row["nearest_semantic_s2"])
        x1 = _number(row["target_s1"])
        y1 = _number(row["target_s2"])
        ax.plot(
            [x0, x1],
            [y0, y1],
            color=PALETTE["neutral_light"],
            linewidth=0.7,
            zorder=1,
        )
        ax.scatter(
            x0,
            y0,
            c=[_number(row["nearest_semantic_hidden_moderator"])],
            cmap="coolwarm",
            norm=norm,
            s=30,
            marker="o",
            edgecolor="black",
            linewidth=0.3,
            zorder=2,
        )
        target = ax.scatter(
            x1,
            y1,
            c=[_number(row["target_hidden_moderator"])],
            cmap="coolwarm",
            norm=norm,
            s=42,
            marker="^",
            edgecolor="black",
            linewidth=0.3,
            zorder=3,
        )
        if not _boolean(row["atlas_accepted"]):
            ax.scatter(x1, y1, marker="x", color="black", s=27, linewidth=0.9, zorder=4)
    fig.colorbar(target, ax=ax, label="Hidden moderator", fraction=0.046, pad=0.04)
    ax.set(xlabel="Semantic coordinate $s_1$", ylabel="Semantic coordinate $s_2$")
    ax.set_title("A  Semantic proximity can hide moderator gaps", loc="left", fontweight="bold")
    ax.text(
        0.02,
        0.02,
        "circle: nearest archive object   triangle: target   x: rejected",
        transform=ax.transAxes,
        fontsize=7.5,
    )

    ax = axes[0, 1]
    error_columns = (
        ("atlas", "atlas_absolute_error", True),
        ("atlas_no_rejection", "atlas_no_rejection_absolute_error", False),
        ("semantic_forced", "semantic_forced_absolute_error", False),
        ("nearest_semantic", "nearest_semantic_absolute_error", False),
        ("global_mean", "global_mean_absolute_error", False),
        ("oracle_latent_support", "oracle_latent_support_absolute_error", False),
    )
    violin_values: list[np.ndarray] = []
    labels: list[str] = []
    methods: list[str] = []
    for method, column, released_only in error_columns:
        rows = (
            [row for row in diagnostics if _boolean(row["atlas_accepted"])]
            if released_only
            else diagnostics
        )
        violin_values.append(np.asarray([_number(row[column]) for row in rows]))
        methods.append(method)
        labels.append(
            {
                "atlas": "ATLAS\n(released)",
                "atlas_no_rejection": "ATLAS\nno rejection",
                "semantic_forced": "Semantic\nforced",
                "nearest_semantic": "Nearest\nsemantic",
                "global_mean": "Global\nmean",
                "oracle_latent_support": "Oracle latent\nsupport",
            }[method]
        )
    parts = ax.violinplot(violin_values, showmeans=False, showmedians=False, widths=0.78)
    for body, method in zip(parts["bodies"], methods, strict=True):
        body.set_facecolor(METHOD_COLORS[method])
        body.set_edgecolor("white")
        body.set_alpha(0.76)
    for index, values in enumerate(violin_values, start=1):
        lower, median, upper = np.quantile(values, [0.25, 0.50, 0.75])
        ax.plot([index - 0.20, index + 0.20], [median, median], color="black", linewidth=1.3)
        ax.plot([index, index], [lower, upper], color="black", linewidth=1.0)
    ax.set_xticks(range(1, len(labels) + 1), labels, fontsize=7.5)
    ax.set(ylabel="Absolute error against known target effect", ylim=(0.0, None))
    ax.set_title("B  Causal support improves reconstruction", loc="left", fontweight="bold")

    ax = axes[1, 0]
    severe_paths = [row for row in paths if row["scenario_key"] == "severe"]
    policy_labels = {
        "causal_greedy": "Causal-support greedy",
        "semantic_greedy": "Semantic-only greedy",
        "random": "Random bridge",
    }
    for policy in ("causal_greedy", "semantic_greedy", "random"):
        selected = sorted(
            (row for row in severe_paths if row["policy_key"] == policy),
            key=lambda row: int(row["budget"]),
        )
        ax.plot(
            [int(row["budget"]) for row in selected],
            [_number(row["mean_diameter"]) for row in selected],
            color=POLICY_COLORS[policy],
            marker="o",
            linewidth=2.0,
            label=policy_labels[policy],
        )
    ax.set_xticks([0, 1, 2, 3, 4])
    ax.set(xlabel="Bridge-experiment budget", ylabel="Mean partial-ID diameter")
    ax.set_title("C  Targeted bridges shrink the unidentified region fastest", loc="left", fontweight="bold")
    ax.legend(fontsize=8)

    ax = axes[1, 1]
    hidden_grid = sorted({_number(row["hidden_shift_fraction"]) for row in sensitivity})
    proxy_grid = sorted({_number(row["proxy_uncertainty"]) for row in sensitivity})
    matrix = np.full((len(proxy_grid), len(hidden_grid)), np.nan)
    for row in sensitivity:
        matrix[
            proxy_grid.index(_number(row["proxy_uncertainty"])),
            hidden_grid.index(_number(row["hidden_shift_fraction"])),
        ] = _number(row["representation_advantage"])
    bound = max(abs(np.nanmin(matrix)), abs(np.nanmax(matrix)), 1e-8)
    image = ax.imshow(matrix, origin="lower", aspect="auto", cmap="RdBu_r", vmin=-bound, vmax=bound)
    ax.set_xticks(range(len(hidden_grid)), [f"{value:.1f}" for value in hidden_grid])
    ax.set_yticks(range(len(proxy_grid)), [f"{value:.2f}" for value in proxy_grid])
    ax.set(xlabel="Hidden-moderator shift", ylabel="Proxy uncertainty")
    ax.set_title("D  Advantage concentrates where semantics mislead", loc="left", fontweight="bold")
    fig.colorbar(image, ax=ax, label="Semantic MAE - ATLAS MAE", fraction=0.046, pad=0.04)

    fig.suptitle(
        "Original-layout companion: synthetic validation with the current protocol",
        fontsize=14,
        fontweight="bold",
    )
    return finalize_figure(fig, figures_dir / "legacy_layout_synthetic_validation")


def _build_legacy_nsw_validation(
    results_dir: Path,
    figures_dir: Path,
) -> tuple[Path, ...]:
    """Recreate the original NSW four-panel layout with current saved results."""

    archive = _read_csv(results_dir / "nsw_archive_map_summary.csv")
    diagnostics = _read_csv(results_dir / "nsw_diagnostics_summary.csv")
    method_errors = _read_csv(results_dir / "nsw_method_error_records.csv")
    coordinates = {row["object_id"]: (_number(row["pc1"]), _number(row["pc2"])) for row in archive}
    effect_values: dict[str, list[float]] = {}
    for row in diagnostics:
        effect_values.setdefault(row["target_object_id"], []).append(_number(row["heldout_local_contrast"]))
    mean_effect = {key: float(np.mean(values)) for key, values in effect_values.items()}
    fig, axes = plt.subplots(2, 2, figsize=(13.2, 9.2))

    ax = axes[0, 0]
    colors = [mean_effect.get(row["object_id"], 0.0) for row in archive]
    bound = max(abs(min(colors)), abs(max(colors)), 1e-8)
    points = ax.scatter(
        [_number(row["pc1"]) for row in archive],
        [_number(row["pc2"]) for row in archive],
        c=colors,
        cmap="coolwarm",
        vmin=-bound,
        vmax=bound,
        s=40,
        alpha=0.76,
        edgecolor="white",
        linewidth=0.35,
    )
    split = [row for row in diagnostics if row["seed_batch"] == "0" and row["replicate"] == "0"]
    for accepted, label, color, marker in (
        (True, "accepted holdout", PALETTE["blue_main"], "D"),
        (False, "rejected holdout", "black", "x"),
    ):
        selected = [row for row in split if _boolean(row["accepted"]) == accepted]
        ax.scatter(
            [coordinates[row["target_object_id"]][0] for row in selected],
            [coordinates[row["target_object_id"]][1] for row in selected],
            color=color,
            marker=marker,
            s=42,
            linewidth=1.0,
            label=label,
            zorder=4,
        )
    fig.colorbar(points, ax=ax, label="Mean held-out local contrast ($1000s)", fraction=0.046, pad=0.04)
    ax.set(xlabel="PCA mechanism coordinate 1", ylabel="PCA mechanism coordinate 2")
    ax.set_title("A  Local contrasts form a heterogeneous archive", loc="left", fontweight="bold")
    ax.legend(fontsize=8)

    ax = axes[0, 1]
    method_order = ("atlas", "atlas_no_rejection", "semantic_forced", "nearest_semantic", "global_mean")
    labels = {
        "atlas": "ATLAS",
        "atlas_no_rejection": "ATLAS\nno rejection",
        "semantic_forced": "Semantic\nforced",
        "nearest_semantic": "Nearest\nsemantic",
        "global_mean": "Global\nmean",
    }
    distributions = [
        np.asarray(
            [
                _number(row["absolute_reconstruction_error"])
                for row in method_errors
                if row["method"] == method
            ]
        )
        for method in method_order
    ]
    parts = ax.violinplot(
        distributions,
        positions=np.arange(len(method_order)),
        showmeans=False,
        showmedians=False,
        showextrema=False,
        widths=0.78,
    )
    for body, method in zip(parts["bodies"], method_order, strict=True):
        body.set_facecolor(METHOD_COLORS[method])
        body.set_edgecolor(METHOD_COLORS[method])
        body.set_alpha(0.22)
    jitter_rng = np.random.default_rng(20260816)
    for index, (method, values) in enumerate(
        zip(method_order, distributions, strict=True)
    ):
        sample_size = min(180, len(values))
        sample = jitter_rng.choice(values, size=sample_size, replace=False)
        jitter = jitter_rng.uniform(-0.18, 0.18, size=sample_size)
        ax.scatter(
            np.full(sample_size, index) + jitter,
            sample,
            s=9,
            alpha=0.24,
            color=METHOD_COLORS[method],
            edgecolor="none",
        )
        lower, median, upper = np.quantile(values, [0.25, 0.50, 0.75])
        ax.plot([index, index], [lower, upper], color="black", linewidth=1.4)
        ax.plot(
            [index - 0.18, index + 0.18],
            [median, median],
            color="black",
            linewidth=1.6,
        )
    ax.set_xticks(
        range(len(method_order)),
        [labels[method] for method in method_order],
        fontsize=7.5,
    )
    ax.set(ylabel="Absolute error against held-out local contrast", ylim=(0.0, None))
    ax.set_title("B  Full holdout error distributions", loc="left", fontweight="bold")
    ax.text(
        0.02,
        0.96,
        "points: fixed visual sample   bars: median and IQR",
        transform=ax.transAxes,
        fontsize=7.5,
        va="top",
    )

    ax = axes[1, 0]
    for accepted, label, color, marker in (
        (True, "accepted", PALETTE["blue_main"], "o"),
        (False, "rejected", PALETTE["red"], "x"),
    ):
        selected = [row for row in diagnostics if _boolean(row["accepted"]) == accepted]
        ax.scatter(
            [_number(row["heldout_local_contrast"]) for row in selected],
            [_number(row["reconstructed_contrast"]) for row in selected],
            s=14,
            alpha=0.22,
            color=color,
            marker=marker,
            label=label,
        )
    values = [
        *[_number(row["heldout_local_contrast"]) for row in diagnostics],
        *[_number(row["reconstructed_contrast"]) for row in diagnostics],
    ]
    low, high = min(values), max(values)
    ax.plot([low, high], [low, high], linestyle="--", color=PALETTE["neutral"], linewidth=1.2)
    ax.set(xlabel="Held-out local contrast ($1000s)", ylabel="Reconstructed contrast ($1000s)")
    ax.set_title("C  Calibration against noisy held-out contrasts", loc="left", fontweight="bold")
    ax.legend(fontsize=8)

    ax = axes[1, 1]
    points = ax.scatter(
        [_number(row["support_component"]) for row in diagnostics],
        [_number(row["interval_width"]) for row in diagnostics],
        c=[_number(row["absolute_reconstruction_error"]) for row in diagnostics],
        cmap="magma_r",
        s=18,
        alpha=0.48,
    )
    ax.set(xlabel="Support component of certificate", ylabel="Reported interval width")
    ax.set_title("D  Diagnostics expose where support is weak", loc="left", fontweight="bold")
    fig.colorbar(points, ax=ax, label="Absolute reconstruction error", fraction=0.046, pad=0.04)

    fig.suptitle(
        "Original-layout companion: NSW local-contrast validation with the current protocol",
        fontsize=14,
        fontweight="bold",
    )
    return finalize_figure(fig, figures_dir / "legacy_layout_nsw_validation")


def _build_selective_uncertainty(results_dir: Path, figures_dir: Path) -> tuple[Path, ...]:
    risk = _read_csv(results_dir / "risk_coverage_summary.csv")
    curves = _read_csv(results_dir / "calibration_curve_summary.csv")
    failures = _read_csv(results_dir / "calibration_experiment_summary.csv")
    diagnostics = _read_csv(results_dir / "certificate_diagnostics_summary.csv")
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

    policies = ("honest_atlas", "wald_only", "understated_smoothness", "semantic_forced")
    policy_labels = {
        "honest_atlas": "Honest ATLAS",
        "wald_only": "Wald only",
        "understated_smoothness": "Understated smoothness",
        "semantic_forced": "Semantic forced",
    }
    ax = axes[0, 1]
    # Each policy is drawn as a connected path through the four nominal levels.
    # Small deterministic offsets keep coincident coverage=1 points readable while
    # preserving their exact numeric coordinates in the underlying records.
    nominal_labels = {0.8: "0.80", 0.9: "0.90", 0.95: "0.95", 0.975: "0.975"}
    policy_styles = {
        "honest_atlas": {"color": PALETTE["blue_main"], "linewidth": 2.6, "marker": "o", "zorder": 4},
        "wald_only": {"color": PALETTE["neutral"], "linewidth": 1.6, "marker": "s", "zorder": 2},
        "understated_smoothness": {"color": PALETTE["red_light"], "linewidth": 1.6, "marker": "^", "zorder": 2},
        "semantic_forced": {"color": PALETTE["red"], "linewidth": 1.8, "marker": "D", "zorder": 3},
    }
    label_offsets = {
        # Use alternating horizontal and vertical tiers because all four
        # nominal levels for these policies have empirical coverage near one.
        "honest_atlas": [(-18, 10), (6, 22), (-18, -15), (6, -27)],
        "wald_only": [(7, -13), (7, 7), (7, -13), (7, 7)],
        "understated_smoothness": [(-24, 10), (6, 22), (-24, -15), (6, -27)],
        "semantic_forced": [(-24, 10), (6, 22), (-24, -15), (6, -27)],
    }
    for policy in policies:
        selected = sorted((row for row in curves if row["policy"] == policy), key=lambda row: _number(row["confidence_level"]))
        style = policy_styles[policy]
        x_values = [_number(row["mean_width"]) for row in selected]
        y_values = [_number(row["empirical_coverage"]) for row in selected]
        ax.plot(x_values, y_values, label=policy_labels[policy], **style)
        for index, (row, x_value, y_value) in enumerate(zip(selected, x_values, y_values, strict=True)):
            ax.annotate(
                nominal_labels[_number(row["confidence_level"])],
                (x_value, y_value),
                xytext=label_offsets[policy][index],
                textcoords="offset points",
                fontsize=7,
                color=style["color"],
                fontweight="bold" if policy == "honest_atlas" else "normal",
                bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.78, "pad": 0.35},
                zorder=6,
            )
    ax.set(xlabel="Mean interval width", ylabel="Empirical coverage", ylim=(0.15, 1.08))
    ax.set_title("B  Coverage--width frontiers", loc="left", fontweight="bold")
    ax.legend(fontsize=8, loc="lower right")

    ax = axes[1, 0]
    component_names = (
        ("representation_term", "Representation"),
        ("curvature_term", "Curvature"),
        ("hidden_moderator_term", "Hidden moderator"),
        ("statistical_term", "Statistical"),
    )
    groups = ("released", "rejected")
    component_colors = (PALETTE["blue_main"], PALETTE["gold"], PALETTE["red"], PALETTE["neutral"])
    means = {
        group: [
            float(np.mean([_number(row[column]) for row in diagnostics if _boolean(row["atlas_accepted"]) == (group == "released")]))
            for column, _ in component_names
        ]
        for group in groups
    }
    positions = np.arange(len(component_names))
    width = 0.36
    ax.bar(positions - width / 2, means["released"], width, color=PALETTE["blue_main"], label="Released")
    ax.bar(positions + width / 2, means["rejected"], width, color=PALETTE["red"], label="Rejected")
    ax.set_xticks(positions, [label for _, label in component_names], rotation=18, ha="right", fontsize=8)
    ax.set_ylabel("Mean certificate component")
    ax.set_title("C  What drives rejection?", loc="left", fontweight="bold")
    ax.legend(fontsize=8)

    ax = axes[1, 1]
    scenario_order = ("strong_semantic_mismatch", "severe_semantic_mismatch")
    scenario_labels = {scenario_order[0]: "Strong", scenario_order[1]: "Severe"}
    policy_order = ("certified_atlas", "no_rejection", "understated_smoothness")
    policy_labels_d = {
        "certified_atlas": "Certified ATLAS",
        "no_rejection": "No rejection",
        "understated_smoothness": "Understated smoothness",
    }
    d_styles = {
        "certified_atlas": {"color": PALETTE["blue_main"], "linestyle": "-", "linewidth": 2.6, "zorder": 4},
        "no_rejection": {"color": PALETTE["blue_secondary"], "linestyle": "--", "linewidth": 1.8, "zorder": 2},
        "understated_smoothness": {"color": PALETTE["red"], "linestyle": "-.", "linewidth": 2.0, "zorder": 3},
    }
    for policy in policy_order:
        selected = {row["scenario_key"]: row for row in failures if row["policy_key"] == policy}
        x_values = [_number(selected[scenario]["release_rate"]) for scenario in scenario_order]
        y_values = [_number(selected[scenario]["released_interval_coverage"]) for scenario in scenario_order]
        style = d_styles[policy]
        ax.plot(x_values, y_values, label=policy_labels_d[policy], **style)
        # Marker shape carries the mismatch scenario, while color/line style
        # carries the policy. Draw the square first so an exact overlap still
        # leaves the strong-mismatch circle visibly identifiable.
        for scenario, x_value, y_value in reversed(tuple(zip(scenario_order, x_values, y_values, strict=True))):
            ax.scatter(
                x_value,
                y_value,
                s=45,
                marker="s" if scenario == scenario_order[1] else "o",
                color=style["color"],
                edgecolors="white",
                linewidths=0.75,
                zorder=style["zorder"] + 1,
            )
        # Direct labels are reserved for the two trajectories whose scenario
        # values are most informative; the marker legend labels both scenarios
        # for every policy without repeating text at the coincident baseline.
        if policy == "certified_atlas":
            label_offsets_d = ((7, -16), (7, 7))
            for scenario, x_value, y_value, offset in zip(scenario_order, x_values, y_values, label_offsets_d, strict=True):
                ax.annotate(
                    scenario_labels[scenario],
                    (x_value, y_value),
                    xytext=offset,
                    textcoords="offset points",
                    fontsize=7,
                    color=style["color"],
                    fontweight="bold",
                    bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.78, "pad": 0.35},
                    zorder=6,
                )
        elif policy == "understated_smoothness":
            for scenario, x_value, y_value in zip(scenario_order, x_values, y_values, strict=True):
                ax.annotate(
                    scenario_labels[scenario],
                    (x_value, y_value),
                    xytext=(-38, 7 if scenario == scenario_order[0] else -15),
                    textcoords="offset points",
                    fontsize=7,
                    color=style["color"],
                    bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.78, "pad": 0.35},
                    zorder=6,
                )
    ax.set(xlabel="Release rate", ylabel="Released-target / conditional interval coverage", xlim=(-0.02, 1.03), ylim=(0.65, 1.05))
    ax.set_title("D  Valid certificates reject rather than undercover", loc="left", fontweight="bold")
    policy_legend = ax.legend(fontsize=8, loc="lower left", bbox_to_anchor=(0.02, 0.08), title="Policy", title_fontsize=8)
    ax.add_artist(policy_legend)
    scenario_handles = [
        Line2D([0], [0], marker="o", linestyle="None", color=PALETTE["neutral"], markerfacecolor=PALETTE["neutral"], markeredgecolor="white", markersize=6, label="Strong mismatch"),
        Line2D([0], [0], marker="s", linestyle="None", color=PALETTE["neutral"], markerfacecolor=PALETTE["neutral"], markeredgecolor="white", markersize=6, label="Severe mismatch"),
    ]
    ax.legend(handles=scenario_handles, fontsize=7, loc="upper center", bbox_to_anchor=(0.50, 0.99), title="Scenario marker", title_fontsize=7)
    ax.text(0.38, 0.04, "No rejection: strong and severe overlap at (1, 1).", transform=ax.transAxes, fontsize=7)
    fig.suptitle("Figure 3. Selective prediction and honest uncertainty", fontsize=14, fontweight="bold")
    return finalize_figure(fig, figures_dir / "selective_uncertainty_overview")


def _build_rejection_bridge(results_dir: Path, figures_dir: Path) -> tuple[Path, ...]:
    partial = _read_csv(results_dir / "partial_identification_summary.csv")
    paths = _read_csv(results_dir / "bridge_budget_path_summary.csv")
    optimum = _read_csv(results_dir / "bridge_optimality_summary.csv")
    bridge = _read_csv(results_dir / "bridge_experiment_summary.csv")
    partial.sort(key=lambda row: _number(row["mean_oracle_hull_distance"]))
    fig, axes = plt.subplots(2, 2, figsize=(13.2, 9.2))
    x = [_number(row["mean_oracle_hull_distance"]) for row in partial]

    ax = axes[0, 0]
    ax.plot(x, [_number(row["mean_partial_id_width_on_rejected"]) for row in partial], color=PALETTE["red"], marker="s", linewidth=2)
    ax.set(xlabel=r"Target-shift / support-stress parameter $\rho$ (evaluation only)", ylabel="PI diameter on rejected targets")
    ax.set_title("A  Support stress widens the identified set", loc="left", fontweight="bold")

    ax = axes[0, 1]
    severe_paths = [row for row in paths if row["scenario_key"] == "severe"]
    for policy in ("causal_greedy", "semantic_greedy", "random"):
        selected = sorted((row for row in severe_paths if row["policy_key"] == policy), key=lambda row: int(row["budget"]))
        ax.plot([int(row["budget"]) for row in selected], [_number(row["mean_diameter"]) for row in selected], color=POLICY_COLORS[policy], marker="o", linewidth=1.8, label=policy.replace("_", " "))
    ax.scatter([int(row["budget"]) for row in optimum], [_number(row["optimal_mean_final_diameter"]) for row in optimum], color="black", marker="D", s=42, label="Ex-post exhaustive oracle", zorder=5)
    ax.set_xticks([0, 1, 2, 3, 4])
    ax.set(xlabel="Bridge budget", ylabel="Partial-identification diameter")
    ax.set_title("B  Bridge budget paths", loc="left", fontweight="bold")
    ax.legend(fontsize=7)

    ax = axes[1, 0]
    scenario_order = ("supported", "moderate", "strong", "severe")
    scenario_labels = {"supported": "Supported", "moderate": "Moderate", "strong": "Strong", "severe": "Severe"}
    policy_order = ("causal_greedy", "semantic_greedy", "random")
    policy_labels = {"causal_greedy": "Causal greedy", "semantic_greedy": "Semantic greedy", "random": "Random"}
    for policy in policy_order:
        selected = {row["scenario_key"]: row for row in bridge if row["policy_key"] == policy}
        values = [_number(selected[scenario]["mean_final_oracle_hull_distance"]) for scenario in scenario_order]
        ax.plot(range(len(scenario_order)), values, marker="o", linewidth=1.8, color=POLICY_COLORS[policy], label=policy_labels[policy])
    initial = {
        scenario: next(row for row in bridge if row["scenario_key"] == scenario and row["policy_key"] == "causal_greedy")
        for scenario in scenario_order
    }
    ax.plot(range(len(scenario_order)), [_number(initial[scenario]["mean_initial_oracle_hull_distance"]) for scenario in scenario_order], color=PALETTE["neutral"], linestyle="--", marker="x", linewidth=1.2, label="Initial archive hull")
    ax.set_xticks(range(len(scenario_order)), [scenario_labels[scenario] for scenario in scenario_order], rotation=15)
    ax.set_yscale("log")
    ax.set(
        xlabel="Evaluation scenario",
        ylabel="True-mechanism hull distance (evaluation-only; log scale)",
    )
    ax.set_title("C  Evaluation-only mechanism diagnostic", loc="left", fontweight="bold")
    ax.legend(fontsize=7)

    ax = axes[1, 1]
    budgets = [_number(row["budget"]) for row in optimum]
    ratios = [_number(row["greedy_to_optimal_value_ratio"]) for row in optimum]
    ax.plot(budgets, ratios, color=PALETTE["blue_main"], marker="D", linewidth=2, label="Greedy value / exhaustive value")
    ax.axhline(1.0, color=PALETTE["neutral"], linestyle="--", linewidth=1)
    ax.set_xticks([1, 2, 3])
    ax.set(xlabel="Bridge budget", ylabel="Greedy / ex-post exhaustive value", ylim=(0.95, 1.01))
    ax.set_title("D  Greedy is close to the ex-post benchmark", loc="left", fontweight="bold")
    ax.text(
        0.03,
        0.06,
        "Ex-post exhaustive oracle\n(evaluation-only benchmark)",
        transform=ax.transAxes,
        fontsize=7.5,
        va="bottom",
    )
    for budget, ratio in zip(budgets, ratios, strict=True):
        ax.annotate(
            f"{ratio:.1%}",
            (budget, ratio),
            xytext=(0, 9),
            textcoords="offset points",
            ha="center",
            fontsize=8,
            fontweight="bold",
            color=PALETTE["blue_main"],
        )
    fig.suptitle("Figure 4. From failed composition to experiment design", fontsize=14, fontweight="bold")
    return finalize_figure(fig, figures_dir / "rejection_bridge_overview")


def _build_nsw_diagnostics(results_dir: Path, figures_dir: Path) -> tuple[Path, ...]:
    archive = _read_csv(results_dir / "nsw_archive_map_summary.csv")
    diagnostics = _read_csv(results_dir / "nsw_diagnostics_summary.csv")
    method_errors = _read_csv(results_dir / "nsw_method_error_records.csv")
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
    method_order = ("atlas", "atlas_no_rejection", "semantic_forced", "nearest_semantic", "global_mean")
    for method in method_order:
        values = np.asarray([_number(row["absolute_reconstruction_error"]) for row in method_errors if row["method"] == method])
        values.sort()
        ax.step(values, np.arange(1, len(values) + 1) / len(values), where="post", linewidth=1.8, color=METHOD_COLORS[method], label=METHOD_LABELS[method].replace(" (conditional on release)", ""))
    ax.set(xlabel="Absolute reconstruction error", ylabel="Empirical CDF", ylim=(0.0, 1.02))
    ax.set_title("C  Full raw-reconstruction error distributions", loc="left", fontweight="bold")
    ax.legend(fontsize=7, loc="lower right")
    fig.suptitle("Figure 5. NSW reconstruction stress test", fontsize=14, fontweight="bold")
    return finalize_figure(fig, figures_dir / "nsw_diagnostics_overview")


def _build_nsw_certificate_diagnostic(results_dir: Path, figures_dir: Path) -> tuple[Path, ...]:
    """Move the NSW certificate/error scatter to Appendix B.8."""
    diagnostics = _read_csv(results_dir / "nsw_diagnostics_summary.csv")
    metadata = json.loads((results_dir / "nsw_experiment_metadata.json").read_text(encoding="utf-8"))
    fig, ax = plt.subplots(figsize=(6.8, 5.0))
    widths = [_number(row["interval_width"]) for row in diagnostics]
    points = ax.scatter([_number(row["certificate_radius"]) for row in diagnostics], [_number(row["absolute_reconstruction_error"]) for row in diagnostics], c=widths, cmap="viridis", s=18, alpha=0.58)
    tolerance = float(metadata["scientific_tolerance"])
    ax.axvline(tolerance, linestyle=":", color=PALETTE["red"], linewidth=1.6, label="release threshold")
    fig.colorbar(points, ax=ax, label="Reported interval width")
    ax.set(xlabel="Certificate radius", ylabel="Absolute reconstruction error")
    ax.set_title("Certificate radius versus reconstruction error", fontweight="bold")
    ax.legend(fontsize=8)
    fig.suptitle("Appendix B.8. NSW target-level certificate diagnostic", fontsize=12, fontweight="bold")
    return finalize_figure(fig, figures_dir / "appendix_nsw_certificate_diagnostic")


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


def _write_legacy_layout_tables(
    results_dir: Path,
    tables_dir: Path,
) -> tuple[Path, ...]:
    """Write current-protocol analogues of the original paper's Tables 1--3."""

    method_names = {
        "atlas": "Causal ATLAS",
        "atlas_no_rejection": "ATLAS, no rejection",
        "semantic_forced": "Semantic forced",
        "nearest_semantic": "Nearest semantic",
        "global_mean": "Global mean",
        "oracle_latent_support": "Oracle latent support*",
    }
    synthetic = _read_csv(results_dir / "synthetic_benchmark_summary.csv")
    table1_rows = [
        (
            method_names[row["method"]],
            f"{_number(row['release_rate']):.3f}",
            f"{_number(row['mae']):.3f}",
            f"{_number(row['rmse']):.3f}",
            f"{_number(row['sign_accuracy']):.3f}",
            f"{_number(row['interval_coverage']):.3f}",
            f"{_number(row['mean_interval_width']):.3f}",
        )
        for row in synthetic
    ]
    outputs = [
        *_write_dual_format_table(
            tables_dir / "legacy_layout_table1_synthetic",
            title="Original Table 1 analogue: synthetic reconstruction (current protocol)",
            headers=("Method", "Release", "MAE", "RMSE", "Sign", "Coverage", "Width"),
            rows=table1_rows,
            caption=(
                "Current-protocol analogue of the original synthetic holdout table. "
                "ATLAS errors are conditional on release; the latent-support oracle is evaluation-only."
            ),
            label="tab:legacy-layout-synthetic",
        )
    ]

    bridge = _read_csv(results_dir / "bridge_experiment_summary.csv")
    bridge_names = {
        "causal_greedy": "Causal-support greedy",
        "semantic_greedy": "Semantic-only greedy",
        "random": "Random bridge",
    }
    severe = [row for row in bridge if row["scenario_key"] == "severe"]
    table2_rows = [
        (
            bridge_names[row["policy_key"]],
            f"{_number(row['mean_initial_diameter']):.3f}",
            f"{_number(row['mean_final_diameter']):.3f}",
            f"{_number(row['shrinkage_fraction']):.3f}",
            f"{_number(row['budget_completion_rate']):.3f}",
        )
        for row in severe
    ]
    outputs.extend(
        _write_dual_format_table(
            tables_dir / "legacy_layout_table2_bridge",
            title="Original Table 2 analogue: severe-mismatch bridge design (current protocol)",
            headers=("Method", "Initial diameter", "Final diameter", "Shrinkage", "Completion"),
            rows=table2_rows,
            caption=(
                "Current-protocol analogue of the original bridge-design ablation in the severe-mismatch scenario."
            ),
            label="tab:legacy-layout-bridge",
        )
    )

    nsw = _read_csv(results_dir / "nsw_experiment_summary.csv")
    nsw_records = _read_csv(results_dir / "nsw_method_error_records.csv")
    released_mae = _released_mae_by_method(nsw_records)
    table3_rows = [
        (
            method_names[row["method"]],
            f"{_number(row['mae']):.3f}",
            f"{released_mae[row['method']]:.3f}",
            f"{_number(row['median_absolute_error']):.3f}",
            f"{_number(row['sign_accuracy']):.3f}",
            f"{_number(row['interval_coverage']):.3f}",
            f"{_number(row['mean_interval_width']):.3f}",
            f"{_number(row['rejection_rate']):.3f}",
        )
        for row in nsw
    ]
    outputs.extend(
        _write_dual_format_table(
            tables_dir / "legacy_layout_table3_nsw",
            title="Original Table 3 analogue: NSW local-contrast reconstruction (current protocol)",
            headers=("Method", "All-target MAE", "Released MAE", "Median AE", "Sign", "Inclusion", "Width", "Rejection"),
            rows=table3_rows,
            caption=(
                "Current-protocol analogue of the original NSW table. All-target MAE evaluates the point estimator over every raw reconstruction; Released MAE evaluates the released branch only. ATLAS and no-rejection share the same all-target point metrics because they use identical point weights, while forced baselines release all targets. Inclusion refers to the noisy held-out local contrast."
            ),
            label="tab:legacy-layout-nsw",
        )
    )
    return tuple(outputs)


def _released_mae_by_method(records: list[dict[str, str]]) -> dict[str, float]:
    """Aggregate released-branch MAE from saved target-level NSW records.

    Causal ATLAS is selective and uses only accepted records. The ablations and
    forced baselines release every target under the fixed protocol, so their
    released-only metric is the all-target metric by construction.
    """

    grouped: dict[str, list[float]] = {}
    for row in records:
        method = row["method"]
        if method == "atlas" and not _boolean(row["accepted"]):
            continue
        grouped.setdefault(method, []).append(_number(row["absolute_reconstruction_error"]))
    if not grouped:
        raise ValueError("No NSW records available for released-only aggregation.")
    return {method: float(np.mean(values)) for method, values in grouped.items()}


def _write_dual_format_table(
    output_base: Path,
    *,
    title: str,
    headers: tuple[str, ...],
    rows: list[tuple[str, ...]],
    caption: str,
    label: str,
) -> tuple[Path, Path]:
    output_base.parent.mkdir(parents=True, exist_ok=True)
    md_path = output_base.with_suffix(".md")
    tex_path = output_base.with_suffix(".tex")

    markdown = [
        f"# {title}",
        "",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---", *["---:"] * (len(headers) - 1)]) + " |",
    ]
    markdown.extend("| " + " | ".join(row) + " |" for row in rows)
    md_path.write_text("\n".join(markdown) + "\n", encoding="utf-8")

    alignment = "l" + "r" * (len(headers) - 1)
    latex = [
        "% Generated by scripts/build/build_paper_figures.py; do not edit.",
        "\\begin{table}[t]",
        "\\centering",
        "\\small",
        f"\\caption{{{caption}}}",
        f"\\label{{{label}}}",
        f"\\begin{{tabular}}{{{alignment}}}",
        "\\toprule",
        " & ".join(headers) + " \\\\",
        "\\midrule",
    ]
    latex.extend(" & ".join(row) + " \\\\" for row in rows)
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
