"""Run Theorem 5.6 bridge-design simulations and write artifacts."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from causal_atlas_sim.bridge_experiment import (
    BridgeExperimentConfig,
    BridgeExperimentResult,
    BridgeSummaryRow,
    _summarize_one,
    bridge_budget_path_rows,
    run_bridge_experiment,
)
from causal_atlas_sim.dgp import (
    EFFECT_ABSOLUTE_BOUND,
    EFFECT_CURVATURE_BOUND,
    EFFECT_LIPSCHITZ_BOUND,
    HIDDEN_MODERATOR_LIPSCHITZ_BOUND,
)

RESULTS_DIR = PROJECT_ROOT / "results"
TABLES_DIR = RESULTS_DIR / "tables"
FIGURES_DIR = RESULTS_DIR / "figures"
POLICY_COLORS = {
    "causal_greedy": "#2f6f4e",
    "semantic_greedy": "#d08c21",
    "random": "#b33c54",
}


def main() -> None:
    result = run_bridge_experiment(BridgeExperimentConfig())
    RESULTS_DIR.mkdir(exist_ok=True)
    TABLES_DIR.mkdir(exist_ok=True)
    FIGURES_DIR.mkdir(exist_ok=True)
    _write_summary_csv(result.rows)
    _write_budget_path_csv(result)
    _write_seed_csv(result)
    _write_metadata(result)
    _write_markdown_tables(result.rows)
    _write_overview_figure(result)
    print(
        json.dumps(
            {
                "summary_rows": len(result.rows),
                "record_count": len(result.records),
                "summary": str(RESULTS_DIR / "bridge_experiment_summary.csv"),
                "budget_path": str(
                    RESULTS_DIR / "bridge_budget_path_summary.csv"
                ),
                "seed_summary": str(
                    RESULTS_DIR / "bridge_experiment_seed_summary.csv"
                ),
                "metadata": str(RESULTS_DIR / "bridge_experiment_metadata.json"),
                "tables": str(TABLES_DIR / "bridge_experiment_tables.md"),
                "figure": str(FIGURES_DIR / "bridge_experiment_overview.png"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def _write_summary_csv(rows: tuple[BridgeSummaryRow, ...]) -> None:
    values = [row.as_dict() for row in rows]
    with (RESULTS_DIR / "bridge_experiment_summary.csv").open(
        "w", newline="", encoding="utf-8"
    ) as output:
        writer = csv.DictWriter(output, fieldnames=list(values[0]))
        writer.writeheader()
        writer.writerows(values)


def _write_budget_path_csv(result: BridgeExperimentResult) -> None:
    values = [row.as_dict() for row in bridge_budget_path_rows(result)]
    with (RESULTS_DIR / "bridge_budget_path_summary.csv").open(
        "w", newline="", encoding="utf-8"
    ) as output:
        writer = csv.DictWriter(output, fieldnames=list(values[0]))
        writer.writeheader()
        writer.writerows(values)


def _write_seed_csv(result: BridgeExperimentResult) -> None:
    rows = []
    for scenario in result.config.scenarios:
        for policy in result.config.policies:
            for seed_batch, base_seed in enumerate(result.config.base_seeds):
                records = [
                    record
                    for record in result.records
                    if record.scenario_key == scenario.key
                    and record.policy_key == policy.key
                    and record.seed_batch == seed_batch
                ]
                rows.append(
                    _summarize_one(
                        scenario,
                        policy,
                        records,
                        result.config,
                    ).as_dict()
                    | {"seed_batch": seed_batch, "base_seed": base_seed}
                )
    with (RESULTS_DIR / "bridge_experiment_seed_summary.csv").open(
        "w", newline="", encoding="utf-8"
    ) as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _write_metadata(result: BridgeExperimentResult) -> None:
    payload = result.to_dict()["config"] | {
        "theorem": "Theorem 5.6",
        "definition": "Definition 5.2 bridge value of information",
        "certificate_constants": {
            "effect_lipschitz_bound": EFFECT_LIPSCHITZ_BOUND,
            "effect_curvature_bound": EFFECT_CURVATURE_BOUND,
            "hidden_moderator_lipschitz_bound": (
                HIDDEN_MODERATOR_LIPSCHITZ_BOUND
            ),
            "effect_absolute_bound": EFFECT_ABSOLUTE_BOUND,
        },
        "objective": (
            "conditional marginal expected reduction of the current "
            "Theorem 5.4 partial-identification diameter"
        ),
        "marginal_estimator": (
            "predict each unmeasured bridge effect from the public archive, "
            "integrate future partial-identification diameters under a declared "
            "normal design model with Gauss-Hermite quadrature, then update "
            "adaptively after observing the selected bridge"
        ),
        "inconsistency_handling": (
            "an empty Theorem 5.4 intersection is recorded as mutually "
            "inconsistent certificates under Lemma 5.1; it is never assigned "
            "zero diameter or counted as successful shrinkage"
        ),
        "policies": {
            "causal_greedy": "full observed mechanism representation",
            "semantic_greedy": "semantic coordinates (s1, s2) only",
            "random": "uniform random candidate without marginal optimization",
        },
        "oracle_evaluation": (
            "true mechanism hull distance and bridge measurement error are "
            "evaluation-only quantities"
        ),
        "theorem_scope": (
            "Theorem 5.6 is conditional on monotonicity and weak submodularity; "
            "this simulation reports policy shrinkage and does not assume or prove "
            "those properties"
        ),
    }
    (RESULTS_DIR / "bridge_experiment_metadata.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _write_markdown_tables(rows: tuple[BridgeSummaryRow, ...]) -> None:
    fields = (
        "scenario_key",
        "policy_key",
        "bridge_budget",
        "budget_completion_rate",
        "mean_selected_bridge_count",
        "planning_inconsistency_rate",
        "evaluation_inconsistency_rate",
        "mean_initial_diameter",
        "mean_final_diameter",
        "mean_diameter_shrinkage",
        "shrinkage_fraction",
        "mean_initial_oracle_hull_distance",
        "mean_final_oracle_hull_distance",
        "between_seed_final_diameter_sd",
    )
    lines = [
        "# Theorem 5.6 bridge-design experiment tables",
        "",
        "Each row pools 300 repetitions from three independent base seeds.",
        "The diameter is the Theorem 5.4 partial-identification intersection",
        "evaluated using the full observed representation.",
        "",
        "## Table 1. Bridge value by selection policy",
        "",
        _markdown_table(rows, fields),
        "",
        "The causal greedy policy plans with all four public coordinates; the",
        "semantic policy plans with only (s1, s2). Oracle hull distance and",
        "bridge measurement error are not supplied to either policy.",
        "",
        "## Table 2. Interpretation",
        "",
        "- `mean_diameter_shrinkage` is empirical Definition 5.2 bridge value",
        "  among paths whose evaluation intersection remains nonempty.",
        "- `planning_inconsistency_rate` and `evaluation_inconsistency_rate`",
        "  report empty intersections as Lemma 5.1 diagnostics, never as zero",
        "  diameter or successful shrinkage.",
        "- `mean_final_oracle_hull_distance` is an evaluation-only support check.",
        "- The experiment compares policies; it does not prove weak submodularity.",
    ]
    (TABLES_DIR / "bridge_experiment_tables.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def _markdown_table(
    rows: tuple[BridgeSummaryRow, ...],
    fields: tuple[str, ...],
) -> str:
    header = "| " + " | ".join(fields) + " |"
    divider = "| " + " | ".join("---" for _ in fields) + " |"
    body = []
    for row in rows:
        values = row.as_dict()
        body.append(
            "| "
            + " | ".join(_format_value(values[field]) for field in fields)
            + " |"
        )
    return "\n".join((header, divider, *body))


def _format_value(value) -> str:
    if value is None:
        return "NA"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def _write_overview_figure(result: BridgeExperimentResult) -> None:
    width, height = 2100, 1150
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    draw.text(
        (55, 30),
        "Theorem 5.6 bridge design: diameter shrinkage",
        fill="#17202a",
        font=_font(34),
    )
    _draw_final_diameter_panel(
        draw,
        result.rows,
        left=55,
        top=130,
        width=980,
        height=900,
    )
    _draw_budget_panel(
        draw,
        result,
        left=1060,
        top=130,
        width=980,
        height=900,
    )
    image.save(FIGURES_DIR / "bridge_experiment_overview.png")


def _draw_final_diameter_panel(
    draw: ImageDraw.ImageDraw,
    rows: tuple[BridgeSummaryRow, ...],
    *,
    left: int,
    top: int,
    width: int,
    height: int,
) -> None:
    title = "final certificate diameter by policy"
    plot_left, plot_top = left + 80, top + 55
    plot_right, plot_bottom = left + width - 25, top + height - 150
    maximum = max(row.mean_initial_diameter for row in rows) * 1.15
    _draw_axes(draw, left, top, plot_left, plot_top, plot_right, plot_bottom, title, maximum)
    scenario_order = []
    for row in rows:
        if row.scenario_key not in scenario_order:
            scenario_order.append(row.scenario_key)
    group_width = (plot_right - plot_left) / len(scenario_order)
    bar_width = 32
    for scenario_index, scenario_key in enumerate(scenario_order):
        scenario_rows = [row for row in rows if row.scenario_key == scenario_key]
        center = plot_left + (scenario_index + 0.5) * group_width
        label = scenario_key
        draw.multiline_text(
            (center - 50, plot_bottom + 22),
            label,
            fill="#4d5966",
            font=_font(13),
            align="center",
        )
        for policy_index, row in enumerate(scenario_rows):
            if row.mean_final_diameter is None:
                continue
            x0 = center + (policy_index - 1) * (bar_width + 8) - bar_width / 2
            y0 = plot_bottom - row.mean_final_diameter / maximum * (plot_bottom - plot_top)
            draw.rectangle(
                (int(x0), int(y0), int(x0 + bar_width), plot_bottom),
                fill=POLICY_COLORS[row.policy_key],
            )
    _draw_legend(draw, left + 80, top + height - 48)


def _draw_budget_panel(
    draw: ImageDraw.ImageDraw,
    result: BridgeExperimentResult,
    *,
    left: int,
    top: int,
    width: int,
    height: int,
) -> None:
    title = "severe mismatch: expected diameter by bridge budget"
    plot_left, plot_top = left + 80, top + 55
    plot_right, plot_bottom = left + width - 25, top + height - 150
    paths = {}
    severe_key = next(
        scenario.key
        for scenario in result.config.scenarios
        if scenario.target_shift_fraction == max(
            item.target_shift_fraction for item in result.config.scenarios
        )
    )
    for policy in result.config.policies:
        records = [
            record
            for record in result.records
            if record.scenario_key == severe_key and record.policy_key == policy.key
        ]
        paths[policy.key] = [
            sum(values) / len(values) if values else None
            for index in range(result.config.bridge_budget + 1)
            for values in [
                [
                    record.evaluation_diameter_path[
                        min(index, len(record.evaluation_diameter_path) - 1)
                    ]
                    for record in records
                    if np.isfinite(
                        record.evaluation_diameter_path[
                            min(index, len(record.evaluation_diameter_path) - 1)
                        ]
                    )
                ]
            ]
        ]
    finite_values = [
        value for path in paths.values() for value in path if value is not None
    ]
    maximum = max(finite_values) * 1.15
    _draw_axes(draw, left, top, plot_left, plot_top, plot_right, plot_bottom, title, maximum)
    for policy in result.config.policies:
        path = paths[policy.key]
        points = []
        for index, value in enumerate(path):
            if value is None:
                continue
            x = plot_left + index / result.config.bridge_budget * (plot_right - plot_left)
            y = plot_bottom - value / maximum * (plot_bottom - plot_top)
            points.append((int(x), int(y)))
        draw.line(points, fill=POLICY_COLORS[policy.key], width=5)
        for x, y in points:
            draw.ellipse((x - 6, y - 6, x + 6, y + 6), fill=POLICY_COLORS[policy.key])
    for index in range(result.config.bridge_budget + 1):
        x = plot_left + index / result.config.bridge_budget * (plot_right - plot_left)
        draw.text(
            (int(x - 7), plot_bottom + 22),
            str(index),
            fill="#4d5966",
            font=_font(13),
        )
    _draw_legend(draw, left + 80, top + height - 48)


def _draw_axes(
    draw: ImageDraw.ImageDraw,
    left: int,
    top: int,
    plot_left: int,
    plot_top: int,
    plot_right: int,
    plot_bottom: int,
    title: str,
    maximum: float,
) -> None:
    draw.text((left, top), title, fill="#17202a", font=_font(19))
    draw.rectangle(
        (plot_left, plot_top, plot_right, plot_bottom),
        outline="#68727d",
        width=2,
    )
    for tick in range(5):
        proportion = tick / 4
        y = int(plot_bottom - proportion * (plot_bottom - plot_top))
        draw.line((plot_left, y, plot_right, y), fill="#e5e8eb", width=1)
        draw.text(
            (left + 5, y - 8),
            f"{proportion * maximum:.2f}",
            fill="#4d5966",
            font=_font(13),
        )


def _draw_legend(draw: ImageDraw.ImageDraw, left: int, top: int) -> None:
    labels = {
        "causal_greedy": "causal-support greedy",
        "semantic_greedy": "semantic-only greedy",
        "random": "random bridge",
    }
    for index, policy_key in enumerate(labels):
        x = left + index * 275
        draw.rectangle((x, top + 3, x + 18, top + 19), fill=POLICY_COLORS[policy_key])
        draw.text(
            (x + 24, top),
            labels[policy_key],
            fill="#2f3b46",
            font=_font(13),
        )


def _font(size: int) -> ImageFont.ImageFont:
    for candidate in (
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ):
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


if __name__ == "__main__":
    main()
