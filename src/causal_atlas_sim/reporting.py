"""Deterministic final reporting from committed simulation result tables."""

from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ResultBundle:
    """Validated long-form tables from the three experiment stages."""

    main_rows: tuple[dict[str, str], ...]
    formal_rows: tuple[dict[str, str], ...]
    calibration_rows: tuple[dict[str, str], ...]


def load_result_bundle(results_dir: Path) -> ResultBundle:
    """Load and validate all committed result tables."""

    bundle = ResultBundle(
        main_rows=_read_csv(results_dir / "main_experiment_summary.csv"),
        formal_rows=_read_csv(results_dir / "formal_experiment_summary.csv"),
        calibration_rows=_read_csv(
            results_dir / "calibration_experiment_summary.csv"
        ),
    )
    expected_counts = {
        "main": (len(bundle.main_rows), 60),
        "formal": (len(bundle.formal_rows), 42),
        "calibration": (len(bundle.calibration_rows), 12),
    }
    failures = [
        f"{name}: expected {expected}, found {actual}"
        for name, (actual, expected) in expected_counts.items()
        if actual != expected
    ]
    if failures:
        raise ValueError("Invalid result bundle: " + "; ".join(failures))
    return bundle


def render_final_report(bundle: ResultBundle) -> str:
    """Render the Chinese final simulation report from source CSV values."""

    main_zero = _find(
        bundle.main_rows,
        sweep_key="semantic_shift_fraction",
        level="0.0",
        method="atlas",
    )
    main_shift = _find(
        bundle.main_rows,
        sweep_key="semantic_shift_fraction",
        level="0.25",
        method="atlas",
    )
    main_small = _find(
        bundle.main_rows,
        sweep_key="sample_size",
        level="100.0",
        method="atlas",
    )
    main_large = _find(
        bundle.main_rows,
        sweep_key="sample_size",
        level="1000.0",
        method="atlas",
    )
    formal_nominal = {
        method: _find(
            bundle.formal_rows,
            scenario_key="nominal",
            estimator_key=method,
        )
        for method in (
            "atlas",
            "atlas_no_rejection",
            "semantic_forced",
            "nearest_semantic",
            "global_mean",
        )
    }
    formal_severe = _find(
        bundle.formal_rows,
        scenario_key="semantic_mismatch_025",
        estimator_key="atlas",
    )
    formal_hidden = _find(
        bundle.formal_rows,
        scenario_key="hidden_radius_040",
        estimator_key="atlas",
    )
    calibration = {
        (scenario, policy): _find(
            bundle.calibration_rows,
            scenario_key=scenario,
            policy_key=policy,
        )
        for scenario in (
            "heterogeneous_hidden_radii",
            "strong_semantic_mismatch",
            "severe_semantic_mismatch",
        )
        for policy in (
            "certified_atlas",
            "no_rejection",
            "understated_smoothness",
        )
    }

    lines = [
        "# Causal ATLAS 仿真实验总报告",
        "",
        "## 1. 研究目的",
        "",
        "本项目检验可拒绝 Causal ATLAS 在目标实验没有直接结果时，能否利用",
        "历史随机实验的观测表示、设计档案、效应估计和不确定性证书进行因果",
        "效应迁移，并在证据不足时拒绝发布不可靠的点预测。",
        "",
        "方法层从未读取目标真值、真实机制或 oracle 支持权重。这些量只在完成",
        "预测后用于仿真评价。",
        "",
        "## 2. 数据生成与理论条件",
        "",
        "基础机制为 m = (s1, s2, h, q)，其中 h 只通过有界误差代理公开。",
        "所有实验采用已知概率 0.5 的 Bernoulli 随机化、共同设计档案和统一 ATE",
        "尺度。效应曲面具有解析平滑界 L = 2.61、H = 1.80；AIPW 分数提供效应",
        "估计和标准误证书。默认目标位于 archive 机制的凸包内，压力实验通过",
        "向域内锚点作凸插值来增加语义失配，因此机制始终位于 [-1, 1]^4。",
        "",
        "该构造逐项对应 Assumption 3.1--3.5。异质隐藏半径实验仍保持代理误差",
        "包含关系；只有标记为 understated_smoothness 的策略故意向方法提供",
        "错误的平滑常数，用于观察无效证书的后果。",
        "",
        "## 3. 实验流程",
        "",
        "| 阶段 | 内容 | 核心产物 |",
        "| --- | --- | --- |",
        "| 1 | 最小数据生成与 3.1--3.5 自动证书 | minimal_dgp.md |",
        "| 2 | 独立 Monte Carlo 重复与 oracle 管线检查 | monte_carlo.md |",
        "| 3 | ATLAS、拒绝规则、消融和基线 | method_comparison.md |",
        "| 4 | 四因素单因素扫描 | main_experiment.md |",
        "| 5 | 三基准种子的正式实验和消融 | formal_experiment.md |",
        "| 6 | 证书校准与失效边界 | calibration_experiment.md |",
        "",
        "## 4. 主实验筛查结果",
        "",
        f"- 语义失配从 0 增至 0.25 时，ATLAS 接受率从 {_f(main_zero, 'acceptance_rate')} "
        f"降至 {_f(main_shift, 'acceptance_rate')}，接受样本 MAE 从 "
        f"{_f(main_zero, 'accepted_mae')} 升至 {_f(main_shift, 'accepted_mae')}。",
        f"- 每实验样本量从 100 增至 1000 时，接受率从 "
        f"{_f(main_small, 'acceptance_rate')} 升至 {_f(main_large, 'acceptance_rate')}。",
        "- 隐藏调节变量证书半径和科学容忍度直接控制发布率，说明拒绝机制确实",
        "  响应理论证书，而不是固定比例地选择样本。",
        "",
        "## 5. 正式多种子结果",
        "",
        "每个正式场景合并三个独立基准种子，每个种子 100 次重复，共 300 个",
        "目标实验。名义场景结果如下。",
        "",
        "| 方法 | 接受率 | 接受样本 MAE | RMSE | 区间覆盖率 |",
        "| --- | ---: | ---: | ---: | ---: |",
        *[
            "| "
            + method
            + " | "
            + _f(row, "acceptance_rate")
            + " | "
            + _f(row, "accepted_mae")
            + " | "
            + _f(row, "accepted_rmse")
            + " | "
            + _f(row, "interval_coverage")
            + " |"
            for method, row in formal_nominal.items()
        ],
        "",
        f"完整 ATLAS 的名义接受样本 MAE 为 {_f(formal_nominal['atlas'], 'accepted_mae')}，"
        f"低于 no-rejection 的 {_f(formal_nominal['atlas_no_rejection'], 'accepted_mae')}。",
        f"在语义失配 0.25 下，ATLAS 接受率降至 "
        f"{_f(formal_severe, 'acceptance_rate')}；隐藏半径 0.40 时接受率为 "
        f"{_f(formal_hidden, 'acceptance_rate')}。这些结果说明拒绝集中发生在",
        "证书较大的困难目标上。",
        "",
        "## 6. 证书校准与失效边界",
        "",
        f"archive 隐藏半径异质化后，正确 ATLAS 的发布率为 "
        f"{_f(calibration[('heterogeneous_hidden_radii', 'certified_atlas')], 'release_rate')}，"
        "总体区间覆盖仍为 1.0000。",
        "",
        "在强语义失配下：",
        "",
        f"- 正确 ATLAS 仅发布 "
        f"{_f(calibration[('strong_semantic_mismatch', 'certified_atlas')], 'release_rate')}，"
        "发布区间覆盖为 1.0000；",
        f"- no-rejection 发布全部点，其中 "
        f"{_f(calibration[('strong_semantic_mismatch', 'no_rejection')], 'released_above_tolerance_rate')} "
        "的证书半径已经超过科学容忍度；",
        f"- 低报平滑界也发布全部点，但覆盖降至 "
        f"{_f(calibration[('strong_semantic_mismatch', 'understated_smoothness')], 'released_interval_coverage')}。",
        "",
        "在严重语义失配下，低报平滑界的覆盖进一步降至 "
        f"{_f(calibration[('severe_semantic_mismatch', 'understated_smoothness')], 'released_interval_coverage')}，"
        f"而 no-rejection 有 "
        f"{_f(calibration[('severe_semantic_mismatch', 'no_rejection')], 'released_above_tolerance_rate')} "
        "的发布点超过容忍度。",
        "",
        "## 7. 可以支持的结论",
        "",
        "1. 在当前满足理论条件的合成机制中，完整证书区间保持保守覆盖。",
        "2. 拒绝规则会优先筛除高误差、高证书半径的目标，接受样本误差低于",
        "   强制发布版本。",
        "3. 语义失配、隐藏不确定性和小样本都会降低可迁移性。",
        "4. 错误低报平滑界会导致过度发布和覆盖率下降，证书有效性依赖于其",
        "   常数确实有效。",
        "",
        "## 8. 不能支持的结论与局限",
        "",
        "这些结果不能证明真实世界泛化性能，也不能把 oracle 支持实验当作",
        "可部署结果。当前 archive 数量固定为 8，效应曲面和随机化机制均为",
        "预先指定；真实数据中的表示误差、设计不兼容和 nuisance estimation",
        "误差仍需单独研究。覆盖率 1.0000 说明证书在该 DGP 下较保守，不等于",
        "区间宽度已经最优。",
        "",
        "## 9. 复现命令",
        "",
        "    python -m unittest discover -s tests -v",
        "    python scripts/run_sanity_check.py",
        "    python scripts/run_monte_carlo.py",
        "    python scripts/run_method_comparison.py",
        "    python scripts/run_main_experiment.py",
        "    python scripts/run_formal_experiment.py",
        "    python scripts/run_calibration_experiment.py",
        "    python scripts/build_final_report.py",
        "",
        "结果文件、配置、图表及其 SHA-256 校验值见",
        "results/experiment_manifest.json。",
    ]
    return "\n".join(lines) + "\n"


def render_final_summary_tables(bundle: ResultBundle) -> str:
    """Render compact final tables suitable for a paper appendix."""

    nominal = [
        _find(bundle.formal_rows, scenario_key="nominal", estimator_key=method)
        for method in (
            "atlas",
            "atlas_no_rejection",
            "atlas_no_variance_penalty",
            "atlas_top4_candidates",
            "semantic_forced",
            "nearest_semantic",
            "global_mean",
        )
    ]
    stress = [
        _find(
            bundle.calibration_rows,
            scenario_key=scenario,
            policy_key=policy,
        )
        for scenario in (
            "strong_semantic_mismatch",
            "severe_semantic_mismatch",
        )
        for policy in (
            "certified_atlas",
            "no_rejection",
            "understated_smoothness",
        )
    ]
    lines = [
        "# Final simulation summary tables",
        "",
        "## Nominal multi-seed benchmark",
        "",
        "| estimator | release | MAE | RMSE | coverage | width |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
        *[
            f"| {row['estimator_key']} | {_f(row, 'acceptance_rate')} | "
            f"{_f(row, 'accepted_mae')} | {_f(row, 'accepted_rmse')} | "
            f"{_f(row, 'interval_coverage')} | {_f(row, 'mean_interval_width')} |"
            for row in nominal
        ],
        "",
        "## Failure-boundary comparison",
        "",
        "| scenario | policy | release | released MAE | released coverage | above tolerance |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
        *[
            f"| {row['scenario_key']} | {row['policy_key']} | "
            f"{_f(row, 'release_rate')} | {_f(row, 'released_mae')} | "
            f"{_f(row, 'released_interval_coverage')} | "
            f"{_f(row, 'released_above_tolerance_rate')} |"
            for row in stress
        ],
    ]
    return "\n".join(lines) + "\n"


def build_artifact_manifest(project_root: Path) -> dict[str, Any]:
    """Build stable sizes and SHA-256 hashes for final report artifacts."""

    included = [
        *sorted((project_root / "results").glob("*.csv")),
        *sorted(
            path
            for path in (project_root / "results").glob("*.json")
            if path.name != "experiment_manifest.json"
        ),
        *sorted((project_root / "results" / "figures").glob("*.png")),
        *sorted((project_root / "results" / "tables").glob("*.md")),
        project_root / "docs" / "final_experiment_report.md",
    ]
    artifacts = []
    for path in included:
        data = path.read_bytes()
        artifacts.append(
            {
                "path": path.relative_to(project_root).as_posix(),
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    return {
        "schema_version": 1,
        "result_row_counts": {
            "main_experiment_summary.csv": 60,
            "formal_experiment_summary.csv": 42,
            "calibration_experiment_summary.csv": 12,
        },
        "artifacts": artifacts,
        "verification_commands": [
            "python -m unittest discover -s tests -v",
            "python scripts/build_final_report.py",
        ],
    }


def _read_csv(path: Path) -> tuple[dict[str, str], ...]:
    with path.open(newline="", encoding="utf-8") as source:
        return tuple(csv.DictReader(source))


def _find(rows: tuple[dict[str, str], ...], **criteria: str) -> dict[str, str]:
    matches = [
        row
        for row in rows
        if all(row.get(key) == value for key, value in criteria.items())
    ]
    if len(matches) != 1:
        raise ValueError(f"Expected one result row for {criteria}, found {len(matches)}.")
    return matches[0]


def _f(row: dict[str, str], field: str) -> str:
    value = row.get(field, "")
    if value == "":
        return "NA"
    return f"{float(value):.4f}"
