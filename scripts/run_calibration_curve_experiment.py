"""Run and save confidence-level coverage--width calibration curves."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from causal_atlas_sim.calibration_curve import CalibrationCurveConfig, run_calibration_curve_experiment

RESULTS_DIR = PROJECT_ROOT / "results"
FIGURES_DIR = RESULTS_DIR / "figures"
TABLES_DIR = RESULTS_DIR / "tables"
COLORS = {
    "honest_atlas": "#2f6f4e",
    "wald_only": "#b33c54",
    "semantic_forced": "#d08c21",
    "understated_smoothness": "#6f5a8a",
    "no_hidden_moderator_inflation": "#4f6d8a",
}


def main() -> None:
    result = run_calibration_curve_experiment(CalibrationCurveConfig())
    RESULTS_DIR.mkdir(exist_ok=True)
    FIGURES_DIR.mkdir(exist_ok=True)
    TABLES_DIR.mkdir(exist_ok=True)
    values = [row.as_dict() for row in result.rows]
    with (RESULTS_DIR / "calibration_curve_summary.csv").open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=list(values[0]))
        writer.writeheader()
        writer.writerows(values)
    (RESULTS_DIR / "calibration_curve_metadata.json").write_text(
        json.dumps(result.to_dict()["config"], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    _write_table(result.rows)
    _write_figure(result.rows)
    print(json.dumps({"rows": len(result.rows), "figure": str(FIGURES_DIR / "calibration_curve.png")}, ensure_ascii=False, indent=2))


def _write_table(rows) -> None:
    lines = [
        "# Confidence-level calibration and width",
        "",
        "覆盖率必须和平均区间宽度共同解释。`wald_only`、低报平滑界和去除隐藏调节",
        "膨胀是诊断性对照，不是具有完整理论保证的替代估计器。",
        "",
        "| nominal | policy | release | coverage | width | released coverage | released width |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row.confidence_level:.3f} | {row.policy} | {row.release_rate:.4f} | "
            f"{row.empirical_coverage:.4f} | {row.mean_width:.4f} | "
            f"{_f(row.conditional_coverage)} | {_f(row.conditional_width)} |"
        )
    (TABLES_DIR / "calibration_curve_tables.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_figure(rows) -> None:
    width, height = 1800, 900
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    draw.text((55, 30), "Calibration and interval width", fill="#17202a", font=_font(34))
    _draw_panel(draw, rows, "empirical_coverage", "empirical coverage", 60, 130, 800, 620, 1.05)
    max_width = max(row.mean_width for row in rows) * 1.10
    _draw_panel(draw, rows, "mean_width", "mean interval width", 930, 130, 800, 620, max_width)
    image.save(FIGURES_DIR / "calibration_curve.png")


def _draw_panel(draw, rows, field, title, left, top, width, height, maximum) -> None:
    plot_left, plot_top = left + 80, top + 55
    plot_right, plot_bottom = left + width - 25, top + height - 80
    draw.text((left, top), title, fill="#17202a", font=_font(20))
    draw.rectangle((plot_left, plot_top, plot_right, plot_bottom), outline="#68727d", width=2)
    policies = tuple(COLORS)
    for tick in range(5):
        p = tick / 4
        y = plot_bottom - p * (plot_bottom - plot_top)
        draw.line((plot_left, y, plot_right, y), fill="#e5e8eb")
        draw.text((left + 5, y - 8), f"{p * maximum:.2f}", fill="#4d5966", font=_font(13))
    for policy in policies:
        selected = sorted((row for row in rows if row.policy == policy), key=lambda row: row.confidence_level)
        points = []
        for row in selected:
            x = plot_left + (row.confidence_level - 0.78) / 0.215 * (plot_right - plot_left)
            y = plot_bottom - getattr(row, field) / maximum * (plot_bottom - plot_top)
            points.append((int(x), int(y)))
        draw.line(points, fill=COLORS[policy], width=4)
        for x, y in points:
            draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=COLORS[policy])
    if field == "empirical_coverage":
        nominal = []
        for level in (0.80, 0.90, 0.95, 0.975):
            x = plot_left + (level - 0.78) / 0.215 * (plot_right - plot_left)
            y = plot_bottom - level / maximum * (plot_bottom - plot_top)
            nominal.append((int(x), int(y)))
        draw.line(nominal, fill="#68727d", width=2)
    for level in (0.80, 0.90, 0.95, 0.975):
        x = plot_left + (level - 0.78) / 0.215 * (plot_right - plot_left)
        draw.text((int(x - 18), plot_bottom + 18), f"{level:.3f}", fill="#4d5966", font=_font(12))
    for index, policy in enumerate(policies):
        x = left + 10 + (index % 3) * 250
        y = top + height + 10 + (index // 3) * 28
        draw.rectangle((x, y + 3, x + 16, y + 17), fill=COLORS[policy])
        draw.text((x + 22, y), policy, fill="#2f3b46", font=_font(12))


def _f(value) -> str:
    return "NA" if value is None else f"{value:.4f}"


def _font(size: int):
    for candidate in ("C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf"):
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            pass
    return ImageFont.load_default()


if __name__ == "__main__":
    main()
