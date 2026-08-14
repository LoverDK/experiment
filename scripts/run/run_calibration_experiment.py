"""Run certificate calibration stress tests and write report artifacts."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from causal_atlas_sim.calibration_experiment import (
    CalibrationExperimentConfig,
    CalibrationSummaryRow,
    _summarize_one,
    run_calibration_experiment,
)

RESULTS_DIR = PROJECT_ROOT / "results"
TABLES_DIR = RESULTS_DIR / "tables"
FIGURES_DIR = RESULTS_DIR / "figures"
COLORS = {
    "certified_atlas": "#1f77b4",
    "no_rejection": "#d62728",
    "understated_smoothness": "#9467bd",
}


def main() -> None:
    result = run_calibration_experiment(CalibrationExperimentConfig())
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
                "summary": str(RESULTS_DIR / "calibration_experiment_summary.csv"),
                "seed_summary": str(
                    RESULTS_DIR / "calibration_experiment_seed_summary.csv"
                ),
                "tables": str(TABLES_DIR / "calibration_experiment_tables.md"),
                "figure": str(FIGURES_DIR / "calibration_experiment_overview.png"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def _write_summary_csv(rows: tuple[CalibrationSummaryRow, ...]) -> None:
    values = [row.as_dict() for row in rows]
    with (RESULTS_DIR / "calibration_experiment_summary.csv").open(
        "w", newline="", encoding="utf-8"
    ) as output:
        writer = csv.DictWriter(output, fieldnames=list(values[0]))
        writer.writeheader()
        writer.writerows(values)


def _write_seed_csv(result) -> None:
    rows = []
    for scenario in result.config.scenarios:
        for policy in result.config.policies:
            for seed_batch in range(len(result.config.base_seeds)):
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
                        result.config.z_value,
                    ).as_dict()
                    | {
                        "seed_batch": seed_batch,
                        "base_seed": result.config.base_seeds[seed_batch],
                    }
                )
    with (RESULTS_DIR / "calibration_experiment_seed_summary.csv").open(
        "w", newline="", encoding="utf-8"
    ) as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _write_metadata(result) -> None:
    (RESULTS_DIR / "calibration_experiment_metadata.json").write_text(
        json.dumps(result.to_dict()["config"], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _write_markdown_tables(result) -> None:
    rows = list(result.rows)
    certified = [
        row for row in rows if row.policy_key == "certified_atlas"
    ]
    failure_rows = [
        row
        for row in rows
        if row.scenario_key
        in {"strong_semantic_mismatch", "severe_semantic_mismatch"}
    ]
    heterogeneity_rows = [
        row
        for row in rows
        if row.scenario_key == "heterogeneous_hidden_radii"
    ]
    lines = [
        "# Certificate calibration and failure-boundary tables",
        "",
        "All rows pool 300 repetitions from three independent base seeds.",
        "",
        "## Table 1. Certified ATLAS calibration",
        "",
        _markdown_table(
            certified,
            (
                "scenario_label",
                "release_rate",
                "mean_raw_mae",
                "released_mae",
                "overall_interval_coverage",
                "mean_certificate_radius",
            ),
        ),
        "",
        "## Table 2. Strong-mismatch release policies",
        "",
        _markdown_table(
            failure_rows,
            (
                "scenario_label",
                "policy_key",
                "release_rate",
                "released_mae",
                "released_interval_coverage",
                "released_interval_uncovered_rate",
                "released_above_tolerance_rate",
            ),
        ),
        "",
        "## Table 3. Heterogeneous hidden-radius scenario",
        "",
        _markdown_table(
            heterogeneity_rows,
            (
                "policy_key",
                "release_rate",
                "released_mae",
                "released_interval_coverage",
                "mean_certificate_radius",
            ),
        ),
        "",
        "The understated-smoothness policy intentionally uses false bounds and is",
        "included to demonstrate calibration failure, not as a valid estimator.",
    ]
    (TABLES_DIR / "calibration_experiment_tables.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def _markdown_table(rows: list[CalibrationSummaryRow], fields: tuple[str, ...]) -> str:
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


def _write_overview_figure(rows: tuple[CalibrationSummaryRow, ...]) -> None:
    width, height = 1900, 1050
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    draw.text(
        (55, 30),
        "Certificate calibration and failure-boundary experiment",
        fill="#17202a",
        font=_font(34),
    )
    _draw_grouped_bars(
        draw,
        rows,
        metric="release_rate",
        title="point-release rate",
        left=60,
        top=130,
        width=860,
        height=780,
        y_limits=(0.0, 1.0),
    )
    _draw_grouped_bars(
        draw,
        rows,
        metric="released_interval_coverage",
        title="released-point interval coverage",
        left=980,
        top=130,
        width=860,
        height=780,
        y_limits=(0.0, 1.0),
    )
    image.save(FIGURES_DIR / "calibration_experiment_overview.png")


def _draw_grouped_bars(
    draw,
    rows,
    *,
    metric,
    title,
    left,
    top,
    width,
    height,
    y_limits,
):
    label_font = _font(18)
    small_font = _font(14)
    plot_left, plot_top = left + 80, top + 50
    plot_right, plot_bottom = left + width - 35, top + height - 125
    draw.text((left, top), title, fill="#17202a", font=label_font)
    draw.rectangle((plot_left, plot_top, plot_right, plot_bottom), outline="#68727d", width=2)
    for tick in range(5):
        proportion = tick / 4
        y = int(plot_bottom - proportion * (plot_bottom - plot_top))
        draw.line((plot_left, y, plot_right, y), fill="#e5e8eb", width=1)
        draw.text((left + 5, y - 8), f"{proportion:.2f}", fill="#4d5966", font=small_font)

    scenario_order = []
    for row in rows:
        if row.scenario_key not in scenario_order:
            scenario_order.append(row.scenario_key)
    labels = {
        "nominal": "nominal",
        "heterogeneous_hidden_radii": "hetero radii",
        "strong_semantic_mismatch": "mismatch .60",
        "severe_semantic_mismatch": "mismatch .80",
    }
    policies = ("certified_atlas", "no_rejection", "understated_smoothness")
    group_width = max(1, (plot_right - plot_left) // len(scenario_order))
    bar_width = 26
    for scenario_index, scenario in enumerate(scenario_order):
        center = plot_left + scenario_index * group_width + group_width // 2
        draw.text(
            (center - 45, plot_bottom + 50),
            labels[scenario],
            fill="#4d5966",
            font=small_font,
        )
        for policy_index, policy in enumerate(policies):
            row = next(
                item
                for item in rows
                if item.scenario_key == scenario and item.policy_key == policy
            )
            value = getattr(row, metric)
            if value is None:
                continue
            x0 = center + (policy_index - 1) * (bar_width + 8)
            y0 = int(plot_bottom - value * (plot_bottom - plot_top))
            draw.rectangle((x0, y0, x0 + bar_width, plot_bottom), fill=COLORS[policy])
    _draw_legend(draw, plot_left, top + height - 40, policies, small_font)


def _draw_legend(draw, left, top, policies, font):
    labels = {
        "certified_atlas": "certified ATLAS",
        "no_rejection": "no rejection",
        "understated_smoothness": "understated bounds",
    }
    for index, policy in enumerate(policies):
        x = left + index * 190
        draw.rectangle((x, top + 4, x + 18, top + 20), fill=COLORS[policy])
        draw.text((x + 24, top), labels[policy], fill="#2f3b46", font=font)


def _font(size: int) -> ImageFont.ImageFont:
    for candidate in ("C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf"):
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


if __name__ == "__main__":
    main()
