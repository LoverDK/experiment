"""Run Theorem 5.4 partial-identification simulations and write artifacts."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from causal_atlas_sim.partial_identification import (
    PartialIdentificationExperimentConfig,
    PartialIdentificationSummaryRow,
    _summarize_one,
    run_partial_identification_experiment,
)

RESULTS_DIR = PROJECT_ROOT / "results"
TABLES_DIR = RESULTS_DIR / "tables"
FIGURES_DIR = RESULTS_DIR / "figures"
COLORS = {
    "rejection_rate": "#d62728",
    "partial_id_nonempty_rate": "#2ca02c",
    "partial_id_coverage": "#1f77b4",
    "reference_width": "#9467bd",
    "partial_id_width": "#ff7f0e",
}


def main() -> None:
    result = run_partial_identification_experiment(
        PartialIdentificationExperimentConfig()
    )
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
                "summary": str(
                    RESULTS_DIR / "partial_identification_summary.csv"
                ),
                "seed_summary": str(
                    RESULTS_DIR / "partial_identification_seed_summary.csv"
                ),
                "metadata": str(
                    RESULTS_DIR / "partial_identification_metadata.json"
                ),
                "tables": str(
                    TABLES_DIR / "partial_identification_tables.md"
                ),
                "figure": str(
                    FIGURES_DIR / "partial_identification_overview.png"
                ),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def _write_summary_csv(
    rows: tuple[PartialIdentificationSummaryRow, ...],
) -> None:
    values = [row.as_dict() for row in rows]
    with (RESULTS_DIR / "partial_identification_summary.csv").open(
        "w", newline="", encoding="utf-8"
    ) as output:
        writer = csv.DictWriter(output, fieldnames=list(values[0]))
        writer.writeheader()
        writer.writerows(values)


def _write_seed_csv(result) -> None:
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
                _summarize_one(
                    scenario,
                    records,
                    result.config.z_value,
                ).as_dict()
                | {
                    "seed_batch": seed_batch,
                    "base_seed": base_seed,
                }
            )
    with (RESULTS_DIR / "partial_identification_seed_summary.csv").open(
        "w", newline="", encoding="utf-8"
    ) as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _write_metadata(result) -> None:
    (RESULTS_DIR / "partial_identification_metadata.json").write_text(
        json.dumps(result.to_dict()["config"], ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )


def _write_markdown_tables(
    rows: tuple[PartialIdentificationSummaryRow, ...],
) -> None:
    fields = (
        "scenario_label",
        "rejection_rate",
        "partial_id_nonempty_rate",
        "partial_id_coverage",
        "partial_id_coverage_on_rejected",
        "mean_partial_id_width_on_rejected",
        "mean_reference_width_on_rejected",
        "mean_width_reduction_fraction_on_rejected",
        "mean_oracle_hull_distance",
        "mean_nonidentification_separation",
    )
    lines = [
        "# Partial-identification experiment tables",
        "",
        "All rows pool 300 repetitions from three independent base seeds.",
        "The interval intersects six simultaneously certified weight-specific",
        "intervals: support-optimized, compatible-uniform, and four nearest",
        "design-compatible semantic singletons.",
        "",
        "## Table 1. Theorem 5.4 fallback after failed composition",
        "",
        _markdown_table(rows, fields),
        "",
        "Oracle hull distance and nonidentification separation are evaluation",
        "metrics only. They are not supplied to ATLAS or the interval builder.",
    ]
    (TABLES_DIR / "partial_identification_tables.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def _markdown_table(
    rows: tuple[PartialIdentificationSummaryRow, ...],
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


def _write_overview_figure(
    rows: tuple[PartialIdentificationSummaryRow, ...],
) -> None:
    width, height = 1900, 1050
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    draw.text(
        (55, 30),
        "Theorem 5.4 partial identification after failed composition",
        fill="#17202a",
        font=_font(34),
    )
    _draw_rate_panel(draw, rows, 60, 130, 860, 780)
    _draw_width_panel(draw, rows, 980, 130, 860, 780)
    image.save(FIGURES_DIR / "partial_identification_overview.png")


def _draw_rate_panel(draw, rows, left, top, width, height) -> None:
    metrics = (
        "rejection_rate",
        "partial_id_nonempty_rate",
        "partial_id_coverage",
    )
    labels = {
        "rejection_rate": "rejection",
        "partial_id_nonempty_rate": "nonempty partial ID",
        "partial_id_coverage": "partial-ID coverage",
    }
    _draw_axes(
        draw,
        left,
        top,
        width,
        height,
        "rejection, nonempty, and coverage rates",
        1.0,
    )
    scenario_labels = _scenario_labels()
    plot_left = left + 80
    plot_bottom = top + height - 125
    group_width = (width - 125) // len(rows)
    bar_width = 28
    for scenario_index, row in enumerate(rows):
        center = plot_left + scenario_index * group_width + group_width // 2
        draw.text(
            (center - 55, plot_bottom + 45),
            scenario_labels[row.scenario_key],
            fill="#4d5966",
            font=_font(14),
        )
        for metric_index, metric in enumerate(metrics):
            value = getattr(row, metric)
            x0 = center + (metric_index - 1) * (bar_width + 8)
            y0 = int(plot_bottom - value * (height - 175))
            draw.rectangle(
                (x0, y0, x0 + bar_width, plot_bottom),
                fill=COLORS[metric],
            )
    _draw_legend(draw, left + 80, top + height - 40, metrics, labels)


def _draw_width_panel(draw, rows, left, top, width, height) -> None:
    metrics = ("reference_width", "partial_id_width")
    labels = {
        "reference_width": "single certified interval",
        "partial_id_width": "intersection partial ID",
    }
    maximum = max(
        max(
            row.mean_reference_width_on_rejected or 0.0,
            row.mean_partial_id_width_on_rejected or 0.0,
        )
        for row in rows
    )
    axis_maximum = max(1.0, maximum * 1.15)
    _draw_axes(
        draw,
        left,
        top,
        width,
        height,
        "mean width on rejected targets",
        axis_maximum,
    )
    scenario_labels = _scenario_labels()
    plot_left = left + 80
    plot_bottom = top + height - 125
    group_width = (width - 125) // len(rows)
    bar_width = 46
    for scenario_index, row in enumerate(rows):
        center = plot_left + scenario_index * group_width + group_width // 2
        draw.text(
            (center - 55, plot_bottom + 45),
            scenario_labels[row.scenario_key],
            fill="#4d5966",
            font=_font(14),
        )
        values = (
            row.mean_reference_width_on_rejected or 0.0,
            row.mean_partial_id_width_on_rejected or 0.0,
        )
        for metric_index, (metric, value) in enumerate(zip(metrics, values, strict=True)):
            x0 = center + (metric_index - 0.5) * (bar_width + 10)
            y0 = int(
                plot_bottom
                - value / axis_maximum * (height - 175)
            )
            draw.rectangle(
                (x0, y0, x0 + bar_width, plot_bottom),
                fill=COLORS[metric],
            )
    _draw_legend(draw, left + 80, top + height - 40, metrics, labels)


def _draw_axes(draw, left, top, width, height, title, maximum) -> None:
    plot_left, plot_top = left + 80, top + 50
    plot_right, plot_bottom = left + width - 35, top + height - 125
    draw.text((left, top), title, fill="#17202a", font=_font(18))
    draw.rectangle(
        (plot_left, plot_top, plot_right, plot_bottom),
        outline="#68727d",
        width=2,
    )
    for tick in range(5):
        proportion = tick / 4
        y = int(plot_bottom - proportion * (plot_bottom - plot_top))
        value = proportion * maximum
        draw.line(
            (plot_left, y, plot_right, y),
            fill="#e5e8eb",
            width=1,
        )
        draw.text(
            (left + 5, y - 8),
            f"{value:.2f}",
            fill="#4d5966",
            font=_font(14),
        )


def _draw_legend(draw, left, top, metrics, labels) -> None:
    for index, metric in enumerate(metrics):
        x = left + index * 220
        draw.rectangle((x, top + 4, x + 18, top + 20), fill=COLORS[metric])
        draw.text(
            (x + 24, top),
            labels[metric],
            fill="#2f3b46",
            font=_font(14),
        )


def _scenario_labels() -> dict[str, str]:
    return {
        "nominal": "nominal",
        "moderate_mismatch": "mismatch .25",
        "strong_mismatch": "mismatch .60",
        "severe_mismatch": "mismatch .80",
    }


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
