"""Build the final report, compact tables, and artifact manifest."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from causal_atlas_sim.reporting import (
    build_artifact_manifest,
    load_result_bundle,
    render_final_report,
    render_final_summary_tables,
)


def main() -> None:
    results_dir = PROJECT_ROOT / "results"
    report_path = PROJECT_ROOT / "docs" / "final_experiment_report.md"
    table_path = results_dir / "tables" / "final_summary_tables.md"
    manifest_path = results_dir / "experiment_manifest.json"

    bundle = load_result_bundle(results_dir)
    report_path.write_text(render_final_report(bundle), encoding="utf-8")
    table_path.write_text(render_final_summary_tables(bundle), encoding="utf-8")
    manifest = build_artifact_manifest(PROJECT_ROOT)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "report": str(report_path),
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
