"""Run the small-library exhaustive bridge benchmark."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from causal_atlas_sim.bridge_experiment import run_bridge_optimality_experiment

RESULTS_DIR = PROJECT_ROOT / "results"
TABLES_DIR = RESULTS_DIR / "tables"


def main() -> None:
    rows = run_bridge_optimality_experiment()
    RESULTS_DIR.mkdir(exist_ok=True)
    TABLES_DIR.mkdir(exist_ok=True)
    values = [row.as_dict() for row in rows]
    with (RESULTS_DIR / "bridge_optimality_summary.csv").open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=list(values[0]))
        writer.writeheader()
        writer.writerows(values)
    (RESULTS_DIR / "bridge_optimality_metadata.json").write_text(
        json.dumps(
            {
                "scenario": "severe mismatch",
                "candidate_library_size": 12,
                "budgets": [1, 2, 3],
                "repetitions": 30,
                "selection_information": "causal greedy uses only public coordinates; exhaustive optimum is evaluation-only",
                "interpretation": "This compares greedy with a small-scale combinatorial optimum; it does not estimate gamma or prove Theorem 5.6.",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Bridge greedy 与小规模穷举最优",
        "",
        "在严重支持失配场景中，候选库固定为 12 个，分别枚举预算 1、2、3 的所有",
        "组合。穷举最优使用已经观测到的 bridge 结果，故只能作为事后评价基准；",
        "causal greedy 仍按照 Algorithm 1 的公开信息约束选择。这个实验不估计弱次模",
        "参数，也不证明 Theorem 5.6 的近似系数。",
        "",
        "| budget | repetitions | exhaustive sets | greedy final diameter | optimal final diameter | greedy/optimal value | same-set rate |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row.budget} | {row.repetitions} | {row.exhaustive_sets_per_repetition} | "
            f"{row.greedy_mean_final_diameter:.4f} | {row.optimal_mean_final_diameter:.4f} | "
            f"{_f(row.greedy_to_optimal_value_ratio)} | {row.greedy_optimal_selection_rate:.4f} |"
        )
    (TABLES_DIR / "bridge_optimality_tables.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(rows), "summary": str(RESULTS_DIR / "bridge_optimality_summary.csv")}, ensure_ascii=False, indent=2))


def _f(value) -> str:
    return "NA" if value is None else f"{value:.4f}"


if __name__ == "__main__":
    main()
