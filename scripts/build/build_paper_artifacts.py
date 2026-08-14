"""Build paper-facing tables and prose from the committed simulation results."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from causal_atlas_sim.paper_artifacts import (
    render_paper_results_section,
    render_paper_results_tables,
)
from causal_atlas_sim.reporting import build_artifact_manifest, load_result_bundle


def main() -> None:
    """Write deterministic paper artifacts and refresh the result manifest."""

    results_dir = PROJECT_ROOT / "results"
    section_path = PROJECT_ROOT / "docs" / "paper" / "paper_results_section.md"
    table_path = results_dir / "tables" / "paper_results_tables.tex"
    manifest_path = results_dir / "experiment_manifest.json"

    bundle = load_result_bundle(results_dir)
    section_path.write_text(render_paper_results_section(bundle), encoding="utf-8")
    table_path.write_text(render_paper_results_tables(bundle), encoding="utf-8")
    manifest = build_artifact_manifest(PROJECT_ROOT)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "section": str(section_path),
                "tables": str(table_path),
                "manifest": str(manifest_path),
                "artifact_count": len(manifest["artifacts"]),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
