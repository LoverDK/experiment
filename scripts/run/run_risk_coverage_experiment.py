"""Run and save the synthetic risk--coverage frontier."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from causal_atlas_sim.risk_coverage import RiskCoverageConfig, run_risk_coverage_experiment

RESULTS_DIR = PROJECT_ROOT / "results"
FIGURES_DIR = RESULTS_DIR / "figures"
TABLES_DIR = RESULTS_DIR / "tables"


def main() -> None:
    result = run_risk_coverage_experiment(RiskCoverageConfig())
    RESULTS_DIR.mkdir(exist_ok=True)
    FIGURES_DIR.mkdir(exist_ok=True)
    TABLES_DIR.mkdir(exist_ok=True)
    values = [row.as_dict() for row in result.rows]
    with (RESULTS_DIR / "risk_coverage_summary.csv").open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=list(values[0]))
        writer.writeheader()
        writer.writerows(values)
    (RESULTS_DIR / "risk_coverage_metadata.json").write_text(
        json.dumps(result.to_dict()["config"], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    _write_table(result.rows)
    _write_figure(result.rows)
    print(json.dumps({"rows": len(result.rows), "figure": str(FIGURES_DIR / "risk_coverage_curve.png")}, ensure_ascii=False, indent=2))


def _write_table(rows) -> None:
    lines = [
        "# Risk--coverage frontier",
        "",
        "所有点来自同一批 300 个 target。有限阈值行只在证书半径不超过阈值时发布；",
        "最后一行是 acceptance=1 的 no-rejection 端点。条件 MAE 不能脱离发布率单独比较。",
        "",
        "| threshold | acceptance | conditional MAE | conditional RMSE | coverage | width |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        threshold = "no rejection" if row.threshold == float("inf") else f"{row.threshold:.2f}"
        lines.append(
            f"| {threshold} | {row.acceptance_rate:.4f} | {_f(row.conditional_mae)} | "
            f"{_f(row.conditional_rmse)} | {_f(row.conditional_interval_coverage)} | "
            f"{_f(row.conditional_mean_width)} |"
        )
    (TABLES_DIR / "risk_coverage_tables.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_figure(rows) -> None:
    points = [row for row in rows if row.conditional_mae is not None]
    width, height = 1400, 900
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    draw.text((55, 30), "Risk--coverage frontier", fill="#17202a", font=_font(34))
    left, top, right, bottom = 130, 130, 1320, 770
    draw.rectangle((left, top, right, bottom), outline="#68727d", width=2)
    max_mae = max(row.conditional_mae for row in points) * 1.12
    for tick in range(6):
        x = left + tick / 5 * (right - left)
        y = bottom - tick / 5 * (bottom - top)
        draw.line((x, top, x, bottom), fill="#e5e8eb")
        draw.line((left, y, right, y), fill="#e5e8eb")
        draw.text((x - 12, bottom + 18), f"{tick / 5:.1f}", fill="#4d5966", font=_font(14))
        draw.text((45, y - 8), f"{tick / 5 * max_mae:.2f}", fill="#4d5966", font=_font(14))
    coordinates = [
        (
            int(left + row.acceptance_rate * (right - left)),
            int(bottom - row.conditional_mae / max_mae * (bottom - top)),
        )
        for row in points
    ]
    draw.line(coordinates, fill="#2f6f4e", width=5)
    for index, ((x, y), row) in enumerate(zip(coordinates, points, strict=True)):
        color = "#b33c54" if row.acceptance_rate == 1.0 else "#2f6f4e"
        draw.ellipse((x - 7, y - 7, x + 7, y + 7), fill=color)
        if index in {0, len(points) - 1} or abs(row.threshold - 1.65) < 1e-9:
            label = "no rejection" if row.acceptance_rate == 1.0 else f"delta={row.threshold:.2f}"
            draw.text((x + 10, y - 25), label, fill="#2f3b46", font=_font(14))
    draw.text((560, 825), "target acceptance rate", fill="#17202a", font=_font(18))
    draw.text((20, 85), "conditional MAE", fill="#17202a", font=_font(18))
    image.save(FIGURES_DIR / "risk_coverage_curve.png")


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
