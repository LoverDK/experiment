"""Generate the first certified synthetic archive and print its certificates."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from causal_atlas_sim import generate_minimal_archive, minimal_assumption_report


def main() -> None:
    generated = generate_minimal_archive(seed=20260805)
    report = minimal_assumption_report(generated)
    summary = {
        "archive_size": len(generated.archive),
        "target_true_effect": generated.target.true_effect,
        "target_estimated_effect": generated.target.estimated_effect,
        "target_support_residual": generated.support_residual(),
        "assumptions": report,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
