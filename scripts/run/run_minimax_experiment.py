"""Run Theorem 5.5 minimax lower-bound simulations and write artifacts."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from causal_atlas_sim.minimax_experiment import (
    MinimaxExperimentConfig,
    MinimaxExperimentResult,
    MinimaxSummaryRow,
    _summarize_one,
    run_minimax_experiment,
)

RESULTS_DIR = PROJECT_ROOT / "results"
TABLES_DIR = RESULTS_DIR / "tables"
FIGURES_DIR = RESULTS_DIR / "figures"
COLORS = {
    "geometric_lower_bound": "#2f6f4e",
    "statistical_lower_bound": "#d08c21",
    "combined_lower_bound": "#44546a",
    "empirical_worst_case_mae": "#b33c54",
    "analytic_worst_case_mae": "#5b4b8a",
}


def main() -> None:
    result = run_minimax_experiment(MinimaxExperimentConfig())
    RESULTS_DIR.mkdir(exist_ok=True)
    TABLES_DIR.mkdir(exist_ok=True)
    FIGURES_DIR.mkdir(exist_ok=True)
    _write_summary_csv(result.rows)
    _write_seed_csv(result)
    _write_metadata(result)
    _write_markdown_tables(result.rows)
    _write_overview_figure(result.rows)
    print(
        json.dumps(
            {
                "summary_rows": len(result.rows),
                "record_count": len(result.records),
                "summary": str(RESULTS_DIR / "minimax_experiment_summary.csv"),
                "seed_summary": str(
                    RESULTS_DIR / "minimax_experiment_seed_summary.csv"
                ),
                "metadata": str(RESULTS_DIR / "minimax_experiment_metadata.json"),
                "tables": str(TABLES_DIR / "minimax_experiment_tables.md"),
                "figure": str(FIGURES_DIR / "minimax_experiment_overview.png"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def _write_summary_csv(rows: tuple[MinimaxSummaryRow, ...]) -> None:
    values = [row.as_dict() for row in rows]
    with (RESULTS_DIR / "minimax_experiment_summary.csv").open(
        "w", newline="", encoding="utf-8"
    ) as output:
        writer = csv.DictWriter(output, fieldnames=list(values[0]))
        writer.writeheader()
        writer.writerows(values)


def _write_seed_csv(result: MinimaxExperimentResult) -> None:
    rows = []
    for scenario in result.config.scenarios:
        for seed_batch, base_seed in enumerate(result.config.base_seeds):
            records = [
                record
                for record in result.records
                if record.scenario_key == scenario.key
                and record.seed_batch == seed_batch
            ]
            rows.append(
                _summarize_one(scenario, records, result.config).as_dict()
                | {"seed_batch": seed_batch, "base_seed": base_seed}
            )
    with (RESULTS_DIR / "minimax_experiment_seed_summary.csv").open(
        "w", newline="", encoding="utf-8"
    ) as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _write_metadata(result: MinimaxExperimentResult) -> None:
    payload = result.to_dict()["config"] | {
        "theorem": "Theorem 5.5",
        "loss": "absolute error",
        "representative_estimator": "inverse-variance archive mean",
        "construction": {
            "geometric_pair": (
                "bounded Lipschitz ramps that agree at all archive mechanisms"
            ),
            "statistical_pair": "constant Gaussian surfaces at plus/minus delta",
            "interpretation": (
                "Monte Carlo illustration of the proof submodels, not a proof "
                "of the minimax theorem"
            ),
        },
    }
    (RESULTS_DIR / "minimax_experiment_metadata.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _write_markdown_tables(rows: tuple[MinimaxSummaryRow, ...]) -> None:
    lower_bound_fields = (
        "scenario_key",
        "hull_distance",
        "archive_standard_error",
        "geometric_scale",
        "geometric_lower_bound",
        "information_scale",
        "statistical_lower_bound",
        "combined_lower_bound",
    )
    risk_fields = (
        "scenario_key",
        "empirical_geometric_worst_mae",
        "empirical_statistical_worst_mae",
        "empirical_worst_case_mae",
        "analytic_worst_case_mae",
        "empirical_to_lower_bound_ratio",
        "between_seed_worst_case_mae_sd",
    )
    lines = [
        "# Theorem 5.5 minimax experiment tables",
        "",
        "Each row pools 300 repetitions from three independent base seeds.",
        "The representative estimator is the inverse-variance archive mean.",
        "",
        "## Table 1. Constructive lower-bound components",
        "",
        _markdown_table(rows, lower_bound_fields),
        "",
        "## Table 2. Representative-estimator worst-case absolute risk",
        "",
        _markdown_table(rows, risk_fields),
        "",
        "The geometric and statistical rows are the two independent proof",
        "submodels. Their maximum is the reported constructive lower bound.",
    ]
    (TABLES_DIR / "minimax_experiment_tables.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def _markdown_table(
    rows: tuple[MinimaxSummaryRow, ...],
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


def _write_overview_figure(rows: tuple[MinimaxSummaryRow, ...]) -> None:
    width, height = 2050, 1100
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    draw.text(
        (55, 30),
        "Theorem 5.5: unsupported-target minimax lower bound",
        fill="#17202a",
        font=_font(34),
    )
    _draw_panel(
        draw,
        rows,
        left=55,
        top=125,
        width=950,
        height=875,
        title="constructive lower-bound components",
        metrics=(
            "geometric_lower_bound",
            "statistical_lower_bound",
            "combined_lower_bound",
        ),
        labels={
            "geometric_lower_bound": "geometric",
            "statistical_lower_bound": "statistical",
            "combined_lower_bound": "combined max",
        },
    )
    _draw_panel(
        draw,
        rows,
        left=1045,
        top=125,
        width=950,
        height=875,
        title="lower bound and representative-estimator risk",
        metrics=(
            "combined_lower_bound",
            "empirical_worst_case_mae",
            "analytic_worst_case_mae",
        ),
        labels={
            "combined_lower_bound": "constructive lower bound",
            "empirical_worst_case_mae": "empirical worst MAE",
            "analytic_worst_case_mae": "analytic worst MAE",
        },
    )
    image.save(FIGURES_DIR / "minimax_experiment_overview.png")


def _draw_panel(
    draw: ImageDraw.ImageDraw,
    rows: tuple[MinimaxSummaryRow, ...],
    *,
    left: int,
    top: int,
    width: int,
    height: int,
    title: str,
    metrics: tuple[str, ...],
    labels: dict[str, str],
) -> None:
    maximum = max(getattr(row, metric) for row in rows for metric in metrics)
    axis_maximum = max(0.1, maximum * 1.15)
    plot_left = left + 75
    plot_top = top + 55
    plot_right = left + width - 25
    plot_bottom = top + height - 145
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
            f"{proportion * axis_maximum:.2f}",
            fill="#4d5966",
            font=_font(13),
        )
    group_width = (plot_right - plot_left) / len(rows)
    bar_width = 19
    for row_index, row in enumerate(rows):
        center = plot_left + (row_index + 0.5) * group_width
        draw.multiline_text(
            (center - 29, plot_bottom + 22),
            f"d={row.hull_distance:.2f}\ns={row.archive_standard_error:.2f}",
            fill="#4d5966",
            font=_font(12),
            spacing=2,
            align="center",
        )
        for metric_index, metric in enumerate(metrics):
            value = getattr(row, metric)
            x0 = center + (metric_index - 1) * (bar_width + 4) - bar_width / 2
            y0 = plot_bottom - value / axis_maximum * (plot_bottom - plot_top)
            draw.rectangle(
                (int(x0), int(y0), int(x0 + bar_width), plot_bottom),
                fill=COLORS[metric],
            )
    _draw_legend(draw, left + 70, top + height - 45, metrics, labels)


def _draw_legend(
    draw: ImageDraw.ImageDraw,
    left: int,
    top: int,
    metrics: tuple[str, ...],
    labels: dict[str, str],
) -> None:
    for index, metric in enumerate(metrics):
        x = left + index * 275
        draw.rectangle((x, top + 3, x + 18, top + 19), fill=COLORS[metric])
        draw.text(
            (x + 24, top),
            labels[metric],
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
