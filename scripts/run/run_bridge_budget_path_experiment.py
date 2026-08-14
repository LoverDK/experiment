"""Run a focused severe-mismatch bridge budget-path diagnostic."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from causal_atlas_sim.bridge_experiment import (
    BridgeExperimentConfig,
    BridgeScenario,
    bridge_budget_path_rows,
    run_bridge_experiment,
)

RESULTS_DIR = PROJECT_ROOT / "results"


def main() -> None:
    config = BridgeExperimentConfig(
        repetitions_per_seed=30,
        scenarios=(BridgeScenario("severe", "severe mismatch", 0.80),),
    )
    result = run_bridge_experiment(config)
    values = [row.as_dict() for row in bridge_budget_path_rows(result)]
    summary_path = RESULTS_DIR / "bridge_budget_path_summary.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=list(values[0]))
        writer.writeheader()
        writer.writerows(values)
    metadata_path = RESULTS_DIR / "bridge_budget_path_metadata.json"
    metadata_path.write_text(
        json.dumps(
            {
                "purpose": "Figure 4 bridge-budget path diagnostic",
                "scenario": "severe mismatch",
                "repetitions_per_seed": config.repetitions_per_seed,
                "base_seeds": list(config.base_seeds),
                "policies": [policy.as_dict() for policy in config.policies],
                "bridge_budget": config.bridge_budget,
                "scope": (
                    "This focused path run supports visualization only. The formal "
                    "300-repetition policy claims remain in bridge_experiment_summary.csv."
                ),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "records": len(result.records),
                "rows": len(values),
                "summary": str(summary_path),
                "metadata": str(metadata_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
