"""Run the NSW real-data reconstruction protocol and write artifacts."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from causal_atlas_sim.nsw_experiment import (
    NSW_METHODS,
    NswExperimentConfig,
    NswExperimentResult,
    NswSummaryRow,
    _summarize_method,
    nsw_archive_map_rows,
    nsw_diagnostic_rows,
    nsw_method_error_rows,
    run_nsw_experiment,
)

DATA_PATH = PROJECT_ROOT / "data" / "nsw_dw.dta"
RESULTS_DIR = PROJECT_ROOT / "results"
TABLES_DIR = RESULTS_DIR / "tables"
FIGURES_DIR = RESULTS_DIR / "figures"
METHOD_COLORS = {
    "atlas": "#2f6f4e",
    "atlas_no_rejection": "#4f6d8a",
    "semantic_forced": "#d08c21",
    "nearest_semantic": "#b33c54",
    "global_mean": "#6f5a8a",
}
METHOD_LABELS = {
    "atlas": "Causal ATLAS",
    "atlas_no_rejection": "No rejection",
    "semantic_forced": "Semantic forced",
    "nearest_semantic": "Nearest semantic",
    "global_mean": "Global mean",
}


def main() -> None:
    result = run_nsw_experiment(DATA_PATH, NswExperimentConfig())
    RESULTS_DIR.mkdir(exist_ok=True)
    TABLES_DIR.mkdir(exist_ok=True)
    FIGURES_DIR.mkdir(exist_ok=True)
    _write_summary_csv(result.rows)
    _write_seed_csv(result)
    _write_diagnostic_csvs(result)
    _write_metadata(result)
    _write_markdown_tables(result.rows)
    _write_overview_figure(result.rows)
    print(
        json.dumps(
            {
                "local_objects": len(result.archive.objects),
                "summary_rows": len(result.rows),
                "record_count": len(result.records),
                "summary": str(RESULTS_DIR / "nsw_experiment_summary.csv"),
                "seed_summary": str(
                    RESULTS_DIR / "nsw_experiment_seed_summary.csv"
                ),
                "diagnostics": str(
                    RESULTS_DIR / "nsw_diagnostics_summary.csv"
                ),
                "archive_map": str(
                    RESULTS_DIR / "nsw_archive_map_summary.csv"
                ),
                "method_error_records": str(
                    RESULTS_DIR / "nsw_method_error_records.csv"
                ),
                "metadata": str(RESULTS_DIR / "nsw_experiment_metadata.json"),
                "tables": str(TABLES_DIR / "nsw_experiment_tables.md"),
                "figure": str(FIGURES_DIR / "nsw_experiment_overview.png"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def _write_summary_csv(rows: tuple[NswSummaryRow, ...]) -> None:
    values = [row.as_dict() for row in rows]
    with (RESULTS_DIR / "nsw_experiment_summary.csv").open(
        "w", newline="", encoding="utf-8"
    ) as output:
        writer = csv.DictWriter(output, fieldnames=list(values[0]))
        writer.writeheader()
        writer.writerows(values)


def _write_diagnostic_csvs(result: NswExperimentResult) -> None:
    for filename, rows in (
        ("nsw_diagnostics_summary.csv", nsw_diagnostic_rows(result)),
        ("nsw_archive_map_summary.csv", nsw_archive_map_rows(result)),
        ("nsw_method_error_records.csv", nsw_method_error_rows(result)),
    ):
        values = [row.as_dict() for row in rows]
        with (RESULTS_DIR / filename).open(
            "w", newline="", encoding="utf-8"
        ) as output:
            writer = csv.DictWriter(output, fieldnames=list(values[0]))
            writer.writeheader()
            writer.writerows(values)


def _write_seed_csv(result: NswExperimentResult) -> None:
    rows = []
    for method in NSW_METHODS:
        for seed_batch, base_seed in enumerate(result.config.base_seeds):
            records = [
                record
                for record in result.records
                if record.method == method and record.seed_batch == seed_batch
            ]
            rows.append(
                _summarize_method(method, records).as_dict()
                | {"seed_batch": seed_batch, "base_seed": base_seed}
            )
    with (RESULTS_DIR / "nsw_experiment_seed_summary.csv").open(
        "w", newline="", encoding="utf-8"
    ) as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _write_metadata(result: NswExperimentResult) -> None:
    objects = result.archive.objects
    payload = result.to_dict()["config"] | {
        "stage": 12,
        "paper_section": "Section 6.2 and Appendix B: Real-Data NSW Archive",
        "source": result.archive.source_metadata,
        "local_object_protocol": {
            "distance": "Euclidean distance in eight standardized covariates",
            "anchor_filter": (
                "exclude the top five percent of center norms and neighborhood "
                "radii, then deterministic farthest-point coverage"
            ),
            "effect": (
                "local randomized treated-minus-control difference in mean "
                "1978 earnings, measured in thousands of dollars"
            ),
            "standard_error": "Welch standard error for the two local arms",
            "overlap_score": "4 * p_local * (1 - p_local)",
            "radius": "root mean squared standardized distance to local context",
            "object_count": len(objects),
            "neighborhood_size": result.config.n_neighbors,
            "treated_count_range": [
                min(item.treated_count for item in objects),
                max(item.treated_count for item in objects),
            ],
            "control_count_range": [
                min(item.control_count for item in objects),
                max(item.control_count for item in objects),
            ],
        },
        "blind_evaluation": (
            "held-out effect estimates and held-out standard errors are not read "
            "by any estimator; both are retained only as noisy evaluation references"
        ),
        "method_protocol": {
            "atlas": (
                "semantic candidate retrieval followed by regularized convex "
                "composition in all covariates, overlap, and radius; reject when "
                "the observable certificate exceeds the fixed tolerance"
            ),
            "atlas_no_rejection": (
                "same point weights as ATLAS, forced publication, and a certificate "
                "with only the prespecified no-rejection bias fraction"
            ),
            "semantic_forced": (
                "inverse-distance weights on demographics only: age, education, "
                "race indicators, marital status, and no-degree status"
            ),
            "nearest_semantic": "single closest demographic context",
            "global_mean": "uniform mean of all remaining local effects",
        },
        "metric_scope": (
            "MAE, sign, and coverage use the noisy held-out local contrast as the "
            "reference; they are not ground-truth subgroup-effect metrics"
        ),
        "target_level_outputs": {
            "method_error_file": "results/nsw_method_error_records.csv",
            "method_error_rows": len(result.records),
            "records_per_method": len(result.records) // len(NSW_METHODS),
            "scope": (
                "shared held-out targets for all five methods; used to plot "
                "empirical absolute-error distributions"
            ),
        },
        "reproduction_scope": (
            "the focal paper does not report neighborhood size, anchor selection, "
            "coordinate split, split seeds, or certificate tuning; this fixed "
            "protocol reproduces the experiment structure, not Table 3 values exactly"
        ),
    }
    (RESULTS_DIR / "nsw_experiment_metadata.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _write_markdown_tables(rows: tuple[NswSummaryRow, ...]) -> None:
    lines = [
        "# NSW real-data local-contrast reconstruction",
        "",
        "Each row pools held-out local-object predictions across three independent",
        "base seeds. The target local contrast is a noisy evaluation reference, not",
        "a ground-truth subgroup effect.",
        "",
        "| method | MAE | median AE | sign accuracy | coverage | mean width | rejection |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        *[
            f"| {row.method} | {row.mae:.4f} | "
            f"{row.median_absolute_error:.4f} | {row.sign_accuracy:.4f} | "
            f"{row.interval_coverage:.4f} | {row.mean_interval_width:.4f} | "
            f"{row.rejection_rate:.4f} |"
            for row in rows
        ],
        "",
        "The Causal ATLAS and no-rejection rows use identical point weights. Their",
        "difference is the rejection decision and the prespecified certificate",
        "ablation, so their MAE, median AE, and sign accuracy should match.",
        "",
        "Coverage here means that the reported interval contains the held-out local",
        "contrast estimate. It does not establish coverage of an unobserved true local",
        "effect because the held-out contrast itself has sampling noise.",
    ]
    (TABLES_DIR / "nsw_experiment_tables.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def _write_overview_figure(rows: tuple[NswSummaryRow, ...]) -> None:
    width, height = 2050, 1120
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    draw.text(
        (55, 30),
        "NSW local-contrast reconstruction",
        fill="#17202a",
        font=_font(34),
    )
    _draw_metric_panel(
        draw,
        rows,
        "Holdout reconstruction error",
        "mae",
        left=55,
        top=125,
        panel_width=950,
        panel_height=850,
    )
    _draw_rate_panel(
        draw,
        rows,
        left=1050,
        top=125,
        panel_width=950,
        panel_height=850,
    )
    draw.text(
        (55, 1040),
        "Effects are in thousands of dollars; held-out contrasts are noisy references.",
        fill="#4d5966",
        font=_font(17),
    )
    image.save(FIGURES_DIR / "nsw_experiment_overview.png")


def _draw_metric_panel(
    draw: ImageDraw.ImageDraw,
    rows: tuple[NswSummaryRow, ...],
    title: str,
    field: str,
    *,
    left: int,
    top: int,
    panel_width: int,
    panel_height: int,
) -> None:
    draw.text((left, top), title, fill="#17202a", font=_font(21))
    plot_left = left + 235
    plot_top = top + 70
    plot_right = left + panel_width - 35
    row_height = 130
    maximum = max(getattr(row, field) for row in rows) * 1.20
    for index, row in enumerate(rows):
        y = plot_top + index * row_height
        draw.text(
            (left, y + 15),
            METHOD_LABELS[row.method],
            fill="#2f3b46",
            font=_font(17),
        )
        bar_end = plot_left + int(
            getattr(row, field) / maximum * (plot_right - plot_left)
        )
        draw.rectangle(
            (plot_left, y, bar_end, y + 54),
            fill=METHOD_COLORS[row.method],
        )
        draw.text(
            (bar_end + 12, y + 13),
            f"{getattr(row, field):.3f}",
            fill="#2f3b46",
            font=_font(16),
        )
    draw.line(
        (plot_left, plot_top - 12, plot_left, plot_top + row_height * len(rows) - 58),
        fill="#68727d",
        width=2,
    )


def _draw_rate_panel(
    draw: ImageDraw.ImageDraw,
    rows: tuple[NswSummaryRow, ...],
    *,
    left: int,
    top: int,
    panel_width: int,
    panel_height: int,
) -> None:
    draw.text(
        (left, top),
        "Coverage and rejection diagnostics",
        fill="#17202a",
        font=_font(21),
    )
    plot_left = left + 235
    plot_top = top + 70
    plot_right = left + panel_width - 35
    row_height = 130
    for index, row in enumerate(rows):
        y = plot_top + index * row_height
        draw.text(
            (left, y + 15),
            METHOD_LABELS[row.method],
            fill="#2f3b46",
            font=_font(17),
        )
        coverage_end = plot_left + int(
            row.interval_coverage * (plot_right - plot_left)
        )
        rejection_end = plot_left + int(
            row.rejection_rate * (plot_right - plot_left)
        )
        draw.rectangle(
            (plot_left, y, coverage_end, y + 32),
            fill=METHOD_COLORS[row.method],
        )
        draw.rectangle(
            (plot_left, y + 40, rejection_end, y + 62),
            fill="#8f969e",
        )
        draw.text(
            (plot_right - 145, y + 2),
            f"cov {row.interval_coverage:.3f}",
            fill="#2f3b46",
            font=_font(14),
        )
        draw.text(
            (plot_right - 145, y + 40),
            f"rej {row.rejection_rate:.3f}",
            fill="#4d5966",
            font=_font(14),
        )
    for tick in range(6):
        x = plot_left + int(tick / 5 * (plot_right - plot_left))
        draw.line(
            (x, plot_top - 12, x, plot_top + row_height * len(rows) - 58),
            fill="#e5e8eb" if tick else "#68727d",
            width=1 if tick else 2,
        )
        draw.text(
            (x - 14, plot_top + row_height * len(rows) - 40),
            f"{tick / 5:.1f}",
            fill="#4d5966",
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
