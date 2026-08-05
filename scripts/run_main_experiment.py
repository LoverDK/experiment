"""Run the fixed-seed main protocol and write tables plus PNG figures."""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from causal_atlas_sim.experiments import (
    ExperimentSummaryRow,
    MainExperimentConfig,
    MainExperimentResult,
    rows_as_dicts,
    run_main_experiment,
)


RESULTS_DIR = PROJECT_ROOT / "results"
FIGURES_DIR = RESULTS_DIR / "figures"
METHOD_COLORS = {
    "atlas": "#1f77b4",
    "atlas_no_rejection": "#d62728",
    "semantic_forced": "#2ca02c",
    "nearest_semantic": "#9467bd",
    "global_mean": "#ff7f0e",
}


def main() -> None:
    result = run_main_experiment(MainExperimentConfig())
    RESULTS_DIR.mkdir(exist_ok=True)
    FIGURES_DIR.mkdir(exist_ok=True)
    _write_table(result)
    _write_metadata(result)
    _write_figures(result)
    print(
        json.dumps(
            {
                "rows": len(result.rows),
                "table": str(RESULTS_DIR / "main_experiment_summary.csv"),
                "metadata": str(RESULTS_DIR / "main_experiment_metadata.json"),
                "figures": [
                    str(FIGURES_DIR / "main_experiment_acceptance.png"),
                    str(FIGURES_DIR / "main_experiment_mae.png"),
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def _write_table(result: MainExperimentResult) -> None:
    rows = rows_as_dicts(result)
    with (RESULTS_DIR / "main_experiment_summary.csv").open(
        "w", newline="", encoding="utf-8"
    ) as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _write_metadata(result: MainExperimentResult) -> None:
    (RESULTS_DIR / "main_experiment_metadata.json").write_text(
        json.dumps(result.to_dict()["config"], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _write_figures(result: MainExperimentResult) -> None:
    _draw_sweep_chart(
        result.rows,
        metric="acceptance_rate",
        output=FIGURES_DIR / "main_experiment_acceptance.png",
        title="Causal ATLAS acceptance across controlled sweeps",
        y_label="acceptance rate",
        methods=("atlas",),
        y_limits=(0.0, 1.05),
    )
    _draw_sweep_chart(
        result.rows,
        metric="accepted_mae",
        output=FIGURES_DIR / "main_experiment_mae.png",
        title="Accepted-point MAE across controlled sweeps",
        y_label="accepted MAE",
        methods=result.config.methods,
        y_limits=None,
    )


def _draw_sweep_chart(
    rows: Iterable[ExperimentSummaryRow],
    *,
    metric: str,
    output: Path,
    title: str,
    y_label: str,
    methods: tuple[str, ...],
    y_limits: tuple[float, float] | None,
) -> None:
    width, height = 1800, 1120
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    title_font = _font(34)
    panel_font = _font(20)
    label_font = _font(16)
    small_font = _font(14)
    draw.text((60, 30), title, fill="#17202a", font=title_font)
    grouped: dict[str, list[ExperimentSummaryRow]] = defaultdict(list)
    for row in rows:
        grouped[row.sweep_key].append(row)
    sweeps = list(grouped.values())
    values = [
        getattr(row, metric)
        for sweep_rows in sweeps
        for row in sweep_rows
        if row.method in methods and getattr(row, metric) is not None
    ]
    if y_limits is None:
        upper = max(values) if values else 1.0
        y_limits = (0.0, upper * 1.15 if upper > 0.0 else 1.0)
    panel_width, panel_height = 800, 420
    origins = ((70, 130), (940, 130), (70, 640), (940, 640))
    for (left, top), sweep_rows in zip(origins, sweeps, strict=True):
        _draw_panel(
            draw,
            sweep_rows,
            left=left,
            top=top,
            width=panel_width,
            height=panel_height,
            metric=metric,
            methods=methods,
            y_limits=y_limits,
            panel_font=panel_font,
            label_font=label_font,
            small_font=small_font,
        )
    image.save(output)


def _draw_panel(
    draw: ImageDraw.ImageDraw,
    rows: list[ExperimentSummaryRow],
    *,
    left: int,
    top: int,
    width: int,
    height: int,
    metric: str,
    methods: tuple[str, ...],
    y_limits: tuple[float, float],
    panel_font: ImageFont.ImageFont,
    label_font: ImageFont.ImageFont,
    small_font: ImageFont.ImageFont,
) -> None:
    first = rows[0]
    plot_left, plot_top = left + 90, top + 60
    plot_right, plot_bottom = left + width - 30, top + height - 75
    draw.text((left, top), first.sweep_label, fill="#17202a", font=panel_font)
    draw.rectangle((plot_left, plot_top, plot_right, plot_bottom), outline="#68727d", width=2)
    minimum, maximum = y_limits
    for tick in range(5):
        proportion = tick / 4
        y = int(plot_bottom - proportion * (plot_bottom - plot_top))
        value = minimum + proportion * (maximum - minimum)
        draw.line((plot_left, y, plot_right, y), fill="#e5e8eb", width=1)
        draw.text((left + 8, y - 8), f"{value:.2f}", fill="#4d5966", font=small_font)

    by_method: dict[str, list[ExperimentSummaryRow]] = defaultdict(list)
    for row in rows:
        if row.method in methods:
            by_method[row.method].append(row)
    for method in methods:
        series = sorted(by_method[method], key=lambda row: row.level)
        if not series:
            continue
        x_values = [row.level for row in series]
        x_min, x_max = min(x_values), max(x_values)

        def x_position(value: float) -> int:
            if x_min == x_max:
                return (plot_left + plot_right) // 2
            return int(
                plot_left
                + (value - x_min) / (x_max - x_min) * (plot_right - plot_left)
            )

        points: list[tuple[int, int] | None] = []
        for row in series:
            value = getattr(row, metric)
            if value is None:
                points.append(None)
                continue
            y = int(
                plot_bottom
                - (value - minimum) / (maximum - minimum) * (plot_bottom - plot_top)
            )
            points.append((x_position(row.level), y))
        color = METHOD_COLORS[method]
        for first_point, second_point in zip(points, points[1:]):
            if first_point is not None and second_point is not None:
                draw.line((*first_point, *second_point), fill=color, width=4)
        for point in points:
            if point is not None:
                draw.ellipse(
                    (point[0] - 5, point[1] - 5, point[0] + 5, point[1] + 5),
                    fill=color,
                    outline="white",
                    width=1,
                )
        for row in series:
            x = x_position(row.level)
            label = f"{row.level:g}"
            text_width = draw.textbbox((0, 0), label, font=small_font)[2]
            draw.text(
                (x - text_width // 2, plot_bottom + 12),
                label,
                fill="#4d5966",
                font=small_font,
            )
    legend_x, legend_y = plot_left, top + height - 35
    for index, method in enumerate(methods):
        x = legend_x + index * 145
        draw.line((x, legend_y + 9, x + 20, legend_y + 9), fill=METHOD_COLORS[method], width=4)
        draw.text((x + 27, legend_y), method, fill="#2f3b46", font=small_font)
    draw.text((left, plot_top - 25), metric.replace("_", " "), fill="#4d5966", font=label_font)


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
