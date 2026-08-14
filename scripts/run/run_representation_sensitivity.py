"""Run the paper-level two-dimensional representation sensitivity grid."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from causal_atlas_sim.representation_sensitivity import (
    RepresentationSensitivityConfig,
    run_representation_sensitivity,
)

RESULTS_DIR = PROJECT_ROOT / "results"
TABLES_DIR = RESULTS_DIR / "tables"


def main() -> None:
    result = run_representation_sensitivity(RepresentationSensitivityConfig())
    RESULTS_DIR.mkdir(exist_ok=True)
    TABLES_DIR.mkdir(exist_ok=True)
    values = [row.as_dict() for row in result.rows]
    summary_path = RESULTS_DIR / "representation_sensitivity_summary.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=list(values[0]))
        writer.writeheader()
        writer.writerows(values)
    metadata = result.to_dict()["config"] | {
        "purpose": (
            "separate the gain from design/moderator-enriched representation "
            "from the empirical gain associated with selective release"
        ),
        "paired_comparison": (
            "ATLAS no-rejection and semantic forced use the same generated targets; "
            "semantic forced is restricted to public coordinates (s1, s2)"
        ),
        "representation_advantage": (
            "semantic_forced_mae - atlas_no_rejection_mae"
        ),
        "selection_gain": (
            "atlas_no_rejection_mae - atlas_accepted_mae; an empirical diagnostic, "
            "not an additive causal decomposition"
        ),
    }
    metadata_path = RESULTS_DIR / "representation_sensitivity_metadata.json"
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    _write_table(values)
    print(
        json.dumps(
            {
                "grid_cells": len(result.rows),
                "target_draws": len(result.records),
                "summary": str(summary_path),
                "metadata": str(metadata_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def _write_table(rows: list[dict]) -> None:
    lines = [
        "# 表示敏感性二维扫描",
        "",
        "每个单元格使用 3 个固定基础种子、每个种子 100 次重复。表示优势只比较",
        "ATLAS 不拒绝版本与仅使用 (s1, s2) 的 semantic forced；选择增益单独报告。",
        "",
        "| hidden shift | proxy uncertainty | release | ATLAS no-reject MAE | semantic MAE | representation advantage | selection gain |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row['hidden_shift_fraction']:.2f} | {row['proxy_uncertainty']:.2f} | "
            f"{row['atlas_acceptance_rate']:.4f} | {row['atlas_no_rejection_mae']:.4f} | "
            f"{row['semantic_forced_mae']:.4f} | {row['representation_advantage']:.4f} | "
            f"{_f(row['selection_gain'])} |"
        )
    (TABLES_DIR / "representation_sensitivity_tables.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def _f(value) -> str:
    return "NA" if value is None else f"{value:.4f}"


if __name__ == "__main__":
    main()
