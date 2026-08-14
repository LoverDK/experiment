"""Run the multi-seed formal experiment and write paper-facing artifacts."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from causal_atlas_sim.formal_experiment import (
    FormalExperimentConfig,
    FormalSummaryRow,
    _summarize_one,
    run_formal_experiment,
)

RESULTS_DIR = PROJECT_ROOT / "results"
TABLES_DIR = RESULTS_DIR / "tables"
FIGURES_DIR = RESULTS_DIR / "figures"
COLORS = {
    "atlas": "#1f77b4",
    "atlas_no_rejection": "#d62728",
    "atlas_no_variance_penalty": "#17becf",
    "atlas_top4_candidates": "#8c564b",
    "semantic_forced": "#2ca02c",
    "nearest_semantic": "#9467bd",
    "global_mean": "#ff7f0e",
}


def main() -> None:
    result = run_formal_experiment(FormalExperimentConfig())
    RESULTS_DIR.mkdir(exist_ok=True)
    TABLES_DIR.mkdir(exist_ok=True)
    FIGURES_DIR.mkdir(exist_ok=True)
    _write_summary_csv(result.rows)
    _write_seed_csv(result)
    _write_metadata(result)
    _write_markdown_tables(result)
    _write_overview_figure(result.rows)
    print(
        json.dumps(
            {
                "summary_rows": len(result.rows),
                "record_count": len(result.records),
                "summary": str(RESULTS_DIR / "formal_experiment_summary.csv"),
                "seed_summary": str(RESULTS_DIR / "formal_experiment_seed_summary.csv"),
                "tables": str(TABLES_DIR / "formal_experiment_tables.md"),
                "figure": str(FIGURES_DIR / "formal_experiment_overview.png"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def _write_summary_csv(rows: tuple[FormalSummaryRow, ...]) -> None:
    values = [row.as_dict() for row in rows]
    with (RESULTS_DIR / "formal_experiment_summary.csv").open(
        "w", newline="", encoding="utf-8"
    ) as output:
        writer = csv.DictWriter(output, fieldnames=list(values[0]))
        writer.writeheader()
        writer.writerows(values)


def _write_seed_csv(result) -> None:
    rows = []
    for scenario in result.config.scenarios:
        for estimator in result.config.estimators:
            for seed_batch in range(len(result.config.base_seeds)):
                records = [
                    record
                    for record in result.records
                    if record.scenario_key == scenario.key
                    and record.estimator_key == estimator.key
                    and record.seed_batch == seed_batch
                ]
                rows.append(
                    _summarize_one(
                        scenario,
                        estimator,
                        records,
                        result.config.z_value,
                    ).as_dict()
                    | {"seed_batch": seed_batch, "base_seed": result.config.base_seeds[seed_batch]}
                )
    with (RESULTS_DIR / "formal_experiment_seed_summary.csv").open(
        "w", newline="", encoding="utf-8"
    ) as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _write_metadata(result) -> None:
    (RESULTS_DIR / "formal_experiment_metadata.json").write_text(
        json.dumps(result.to_dict()["config"], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _write_markdown_tables(result) -> None:
    rows = list(result.rows)
    nominal = [row for row in rows if row.scenario_key == "nominal"]
    atlas_sensitivity = [
        row for row in rows if row.estimator_key == "atlas"
    ]
    ablations = [
        row
        for row in nominal
        if row.estimator_key in {
            "atlas",
            "atlas_no_rejection",
            "atlas_no_variance_penalty",
            "atlas_top4_candidates",
        }
    ]
    lines = [
        "# Formal experiment tables",
        "",
        "All rows pool 300 repetitions from three independent base seeds.",
        "",
        "## Table 1. Nominal benchmark",
        "",
        _markdown_table(
            nominal,
            (
                "estimator_key",
                "acceptance_rate",
                "accepted_mae",
                "accepted_rmse",
                "interval_coverage",
                "mean_interval_width",
            ),
        ),
        "",
        "## Table 2. ATLAS sensitivity across formal scenarios",
        "",
        _markdown_table(
            atlas_sensitivity,
            (
                "scenario_label",
                "acceptance_rate",
                "acceptance_ci_lower",
                "acceptance_ci_upper",
                "accepted_mae",
                "interval_coverage",
                "between_seed_acceptance_sd",
            ),
        ),
        "",
        "## Table 3. Nominal ablations",
        "",
        _markdown_table(
            ablations,
            (
                "estimator_key",
                "acceptance_rate",
                "accepted_mae",
                "accepted_bias",
                "interval_coverage",
                "mean_certificate_radius",
            ),
        ),
        "",
        "Rows with an empty accepted MAE correspond to complete rejection, not a failed run.",
    ]
    (TABLES_DIR / "formal_experiment_tables.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def _markdown_table(rows: list[FormalSummaryRow], fields: tuple[str, ...]) -> str:
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


def _write_overview_figure(rows: tuple[FormalSummaryRow, ...]) -> None:
    width, height = 1900, 1050
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    title_font = _font(34)
    label_font = _font(18)
    small_font = _font(14)
    draw.text(
        (55, 30),
        "Formal multi-seed benchmark and ablation overview",
        fill="#17202a",
        font=title_font,
    )
    _draw_acceptance_panel(draw, rows, 60, 130, 860, 780, label_font, small_font)
    _draw_nominal_mae_panel(draw, rows, 980, 130, 860, 780, label_font, small_font)
    image.save(FIGURES_DIR / "formal_experiment_overview.png")


def _draw_acceptance_panel(draw, rows, left, top, width, height, label_font, small_font):
    scenarios = []
    for row in rows:
        if row.estimator_key == "atlas" and row.scenario_key not in scenarios:
            scenarios.append(row.scenario_key)
    estimators = ("atlas", "atlas_no_rejection", "atlas_top4_candidates")
    labels = {
        "nominal": "nominal",
        "semantic_mismatch_010": "mismatch .10",
        "semantic_mismatch_025": "mismatch .25",
        "hidden_radius_040": "hidden .40",
        "sample_size_100": "n = 100",
        "sample_size_1000": "n = 1000",
    }
    _draw_axes(draw, left, top, width, height, "acceptance rate", (0.0, 1.0), label_font, small_font)
    bar_width = 24
    group_width = max(1, (width - 125) // len(scenarios))
    for scenario_index, scenario in enumerate(scenarios):
        center = left + 105 + scenario_index * group_width + group_width // 2
        draw.text(
            (center - 50, top + height - 75),
            labels[scenario],
            fill="#4d5966",
            font=small_font,
        )
        for estimator_index, estimator in enumerate(estimators):
            row = next(
                item
                for item in rows
                if item.scenario_key == scenario and item.estimator_key == estimator
            )
            x0 = center + (estimator_index - 1) * (bar_width + 6)
            y1 = top + height - 125
            y0 = int(y1 - row.acceptance_rate * (height - 175))
            draw.rectangle((x0, y0, x0 + bar_width, y1), fill=COLORS[estimator])
    _draw_legend(draw, left + 90, top + height - 40, estimators, small_font)


def _draw_nominal_mae_panel(draw, rows, left, top, width, height, label_font, small_font):
    nominal = [row for row in rows if row.scenario_key == "nominal"]
    labels = {
        "atlas": "atlas",
        "atlas_no_rejection": "no reject",
        "atlas_no_variance_penalty": "no variance",
        "atlas_top4_candidates": "top-4",
        "semantic_forced": "semantic",
        "nearest_semantic": "nearest",
        "global_mean": "global",
    }
    _draw_axes(draw, left, top, width, height, "accepted MAE", (0.0, 0.7), label_font, small_font)
    for index, row in enumerate(nominal):
        x0 = left + 105 + index * ((width - 160) // len(nominal))
        value = row.accepted_mae or 0.0
        y1 = top + height - 125
        y0 = int(y1 - value / 0.7 * (height - 175))
        draw.rectangle(
            (x0, y0, x0 + 70, y1),
            fill=COLORS[row.estimator_key],
        )
        draw.text(
            (x0, top + height - 75),
            labels[row.estimator_key],
            fill="#4d5966",
            font=small_font,
        )


def _draw_axes(draw, left, top, width, height, label, limits, label_font, small_font):
    plot_left, plot_top = left + 80, top + 50
    plot_right, plot_bottom = left + width - 35, top + height - 125
    draw.text((left, top), label, fill="#17202a", font=label_font)
    draw.rectangle((plot_left, plot_top, plot_right, plot_bottom), outline="#68727d", width=2)
    minimum, maximum = limits
    for tick in range(5):
        proportion = tick / 4
        y = int(plot_bottom - proportion * (plot_bottom - plot_top))
        value = minimum + proportion * (maximum - minimum)
        draw.line((plot_left, y, plot_right, y), fill="#e5e8eb", width=1)
        draw.text((left + 5, y - 8), f"{value:.2f}", fill="#4d5966", font=small_font)


def _draw_legend(draw, left, top, estimators, font):
    for index, estimator in enumerate(estimators):
        x = left + index * 160
        draw.rectangle((x, top + 4, x + 18, top + 20), fill=COLORS[estimator])
        draw.text((x + 24, top), estimator[:18], fill="#2f3b46", font=font)


def _font(size: int) -> ImageFont.ImageFont:
    for candidate in ("C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf"):
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


if __name__ == "__main__":
    main()
