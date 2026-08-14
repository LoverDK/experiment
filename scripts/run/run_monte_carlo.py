"""Run the Monte Carlo scaffold and print a JSON summary."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from causal_atlas_sim.monte_carlo import MonteCarloConfig, run_monte_carlo


def main() -> None:
    result = run_monte_carlo(MonteCarloConfig(repetitions=200, base_seed=20260805))
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
