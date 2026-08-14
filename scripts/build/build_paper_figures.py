"""Build final paper figures from committed CSV/JSON artifacts only."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from causal_atlas_sim.paper_figures import build_paper_figures
from causal_atlas_sim.reporting import build_artifact_manifest


def main() -> None:
    results_dir = PROJECT_ROOT / "results"
    outputs = build_paper_figures(results_dir)
    manifest_path = results_dir / "experiment_manifest.json"
    manifest_path.write_text(
        json.dumps(
            build_artifact_manifest(PROJECT_ROOT),
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "outputs": [str(path) for path in outputs],
                "manifest": str(manifest_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
