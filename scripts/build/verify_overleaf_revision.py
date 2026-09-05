"""Audit the paper snapshot against the downloaded Overleaf baseline and results."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import statistics
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PAPER = ROOT / "docs/paper/overleaf"
EVIDENCE = ROOT / "docs/paper/revision_evidence"


def digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def main() -> None:
    baseline = (EVIDENCE / "01_before_20260906.tex").read_text(encoding="utf-8")
    source = (PAPER / "01_causal_atlas_bridge.tex").read_text(encoding="utf-8")
    protected = {}
    for name, start, end in (
        ("preamble", r"\documentclass", r"\begin{abstract}"),
        ("theory_and_introduction", r"\section{Introduction}", r"\section{Experiments:"),
        ("discussion_and_proofs", r"\section{Discussion}", r"\section{Appendix: Experimental Details}"),
        ("references", r"\begin{thebibliography}", r"\end{document}"),
    ):
        old = baseline[baseline.index(start):baseline.index(end)]
        new = source[source.index(start):source.index(end)]
        if old != new:
            raise ValueError(f"Protected section changed: {name}")
        protected[name] = {"characters": len(old), "sha256": digest(old.encode("utf-8"))}

    pattern = r"\\(?:includegraphics(?:\[[^\]]*\])?|input)\{(experiments/causal_atlas_bridge/[^}]+)\}"
    assets = {}
    all_tex = source
    for relative in sorted(set(re.findall(pattern, source))):
        path = PAPER / relative
        assets[relative] = digest(path.read_bytes())
        if path.suffix == ".tex":
            all_tex += "\n" + path.read_text(encoding="utf-8")
        elif path.suffix == ".pdf":
            committed = ROOT / "results/figures" / path.name
            if path.read_bytes() != committed.read_bytes():
                raise ValueError(f"Figure differs from repository asset: {relative}")

    labels = re.findall(r"\\label\{([^}]+)\}", all_tex)
    refs = set(re.findall(r"\\(?:eqref|ref)\{([^}]+)\}", all_tex))
    missing = sorted(refs - set(labels))
    duplicates = sorted({label for label in labels if labels.count(label) > 1})
    if missing or duplicates:
        raise ValueError(f"Reference mismatch: missing={missing}, duplicate={duplicates}")

    with (ROOT / "results/certificate_diagnostics_summary.csv").open(newline="", encoding="utf-8") as stream:
        records = list(csv.DictReader(stream))
    errors = [float(row["atlas_absolute_error"]) for row in records if row["atlas_accepted"] == "True"]
    n, k = len(records), len(errors)
    p, z = k / n, statistics.NormalDist().inv_cdf(0.975)
    denominator = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denominator
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denominator
    log_path = EVIDENCE / "overleaf_compile.log"
    log = log_path.read_text(encoding="utf-8")
    diagnostics = re.findall(r"^.*(?:Warning|Overfull|Underfull).*$|^!.*$", log, re.MULTILINE)
    if diagnostics:
        raise ValueError(f"Compiler diagnostics: {diagnostics}")
    if "**01_causal_atlas_bridge.tex" not in log:
        raise ValueError("Compiler log does not identify the expected main document")
    output = re.search(r"Output written on .+ \((\d+) pages,", log)
    if output is None:
        raise ValueError("Compiler log does not show completed output")
    result = {
        "source_sha256": digest(source.encode("utf-8")),
        "baseline_sha256": digest(baseline.encode("utf-8")),
        "text_hash_convention": "UTF-8, normalized LF line endings",
        "protected_sections_identical": protected,
        "paper_assets_sha256": assets,
        "undefined_references": missing,
        "duplicate_labels": duplicates,
        "overleaf_compile": {
            "log_sha256": digest(log_path.read_bytes()),
            "pdf_sha256": digest((PAPER / "01_causal_atlas_bridge.pdf").read_bytes()),
            "compiler_header": log.splitlines()[0],
            "pages": int(output.group(1)),
            "warnings_errors_and_box_diagnostics": diagnostics,
        },
        "shared_target_statistics": {
            "targets": n,
            "released": k,
            "release_rate": p,
            "wilson_95": [center - half, center + half],
            "released_mae": statistics.mean(errors),
            "released_mae_mcse": statistics.stdev(errors) / math.sqrt(k),
        },
    }
    destination = EVIDENCE / "source_and_results_audit.json"
    destination.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Verified protected sections, {len(assets)} assets, references, shared-target statistics, and compiler log.")


if __name__ == "__main__":
    main()
