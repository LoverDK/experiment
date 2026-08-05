"""Run the Causal ATLAS method comparison and print a JSON summary."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from causal_atlas_sim.comparison import MethodComparisonConfig, run_method_comparison


def main() -> None:
    result = run_method_comparison(MethodComparisonConfig(repetitions=200, base_seed=20260805))
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
